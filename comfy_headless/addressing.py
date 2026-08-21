"""
Comfy Headless - Graph Addressing / Typing Layer
================================================

v3.1.0: the shared layer under the image, video, 3D, audio and inference
profiles. Three independent mechanics live here:

1. **Union-superset type matching** -- :func:`validate_node_input` is a
   transcription of ComfyUI's own ``comfy_execution/validation.py`` so this
   client can never be stricter than the server. A client stricter than the
   server manufactures false rejections by construction: ``VoxelToMesh``
   emits ``MESH`` into ``SaveGLB.mesh``, which declares a 14-member
   ``FILE_3D_*`` union -- that edge is correct and must pass.
   :func:`match_types` is the richer wrapper that distinguishes "accept",
   "accept with warning" (partial overlap) and "reject" (empty intersection).

2. **Dotted sub-field addressing** -- dynamic-combo fields
   (``COMFY_DYNAMICCOMBO_V3``) serialize as *flattened dotted keys* in a
   node's inputs dict: ``SaveVideo`` takes ``{"codec": "h264",
   "codec.encoding": "re-encode", "codec.encoding.crf": 23}``. Sent flat
   (``{"crf": 23}``) they fail with ``required_input_missing``. Paths parse
   to typed segment tuples (escape-aware, ``\\.`` for a literal dot) and are
   never split-and-vivified: writing through an address never creates
   intermediate structure (cf. CVE-2020-8203).

3. **Presence-aware conditional fields** -- :class:`DynamicCombo` models the
   tagged union: selecting a choice exposes only that branch's fields, and a
   field from an inactive branch is a *construction-time* error. A
   validate-at-send check cannot stop a caller carrying a stale ``crf``
   across a codec switch; building the inputs fragment fresh from the tag
   can.

Also here: :class:`GraphTypeChecker` (client-side edge validation against an
``/object_info``-shaped catalog, tolerant of unknown nodes because enum
contents drift constantly) and the output-node guard
(:func:`require_output_node`) -- a graph whose terminal data node is not an
``OUTPUT_NODE`` runs green and returns nothing.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exceptions import GraphAddressError, InvalidParameterError, ValidationError
from .logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    # Type-name constants
    "ANY_TYPE",
    "MATCH_TYPE",
    "COMBO_TYPE",
    "DYNAMIC_COMBO_TYPE",
    # Union-superset matching
    "validate_node_input",
    "TypeMatch",
    "match_types",
    # Dotted field paths
    "parse_field_path",
    "join_field_path",
    "get_node_input",
    "set_node_input",
    # Presence-aware dynamic combos
    "DynamicCombo",
    "SAVE_AUDIO_FORMAT",
    "SAVE_VIDEO_CODEC",
    # Graph-level checking
    "TypeIssue",
    "GraphTypeChecker",
    "extract_object_info_types",
    # Output-node guard / retrieval contract
    "KNOWN_OUTPUT_NODE_CLASSES",
    "HISTORY_OUTPUT_KEYS",
    "has_output_node",
    "require_output_node",
]


# =============================================================================
# TYPE-NAME CONSTANTS
# =============================================================================
# Literal io_type strings from ComfyUI's comfy_api.latest._io (verified against
# the source on this date): AnyType is "*", MatchType is "COMFY_MATCHTYPE_V3".

ANY_TYPE = "*"
MATCH_TYPE = "COMFY_MATCHTYPE_V3"
COMBO_TYPE = "COMBO"
DYNAMIC_COMBO_TYPE = "COMFY_DYNAMICCOMBO_V3"


# =============================================================================
# UNION-SUPERSET TYPE MATCHING (transcribed from ComfyUI)
# =============================================================================


def validate_node_input(received_type: Any, input_type: Any, strict: bool = False) -> bool:
    """
    Decide whether an edge's source type is accepted by an input's declared
    type, exactly as the ComfyUI server does.

    Transcribed from ``comfy_execution/validation.py::validate_node_input``
    (the server's own implementation) -- do not "improve" this: any client
    stricter than the server manufactures false rejections.

    ``received_type`` and ``input_type`` are both strings of the form
    ``"T1,T2,..."``.

    If ``strict`` is True, the input_type must contain the received_type.
    For example, if received_type is ``"STRING"`` and input_type is
    ``"STRING,INT"``, this returns True. But if received_type is
    ``"STRING,INT"`` and input_type is ``"INT"``, this returns False.

    If ``strict`` is False, the input_type must have overlap with the
    received_type. For example, received ``"STRING,BOOLEAN"`` against
    declared ``"STRING,INT"`` returns True.

    Supports pre-union type extension behaviour of ``__ne__`` overrides.
    """
    # If the types are exactly the same, we can return immediately
    # Use pre-union behaviour: inverse of `__ne__`
    # NOTE: this lets legacy '*' Any types work that override the __ne__
    # method of the str class. Deliberately NOT simplified to `==` -- the
    # transcription is verbatim from the server.
    if not received_type != input_type:  # noqa: SIM202
        return True

    # If one of the types is '*', we can return True immediately; this is the 'Any' type.
    if received_type == ANY_TYPE or input_type == ANY_TYPE:
        return True

    # If the received type or input_type is a MatchType, we can return True
    # immediately; validation for this is handled by the frontend.
    if received_type == MATCH_TYPE or input_type == MATCH_TYPE:
        return True

    # This accounts for some custom nodes that output lists of options as the
    # type; if the server ever breaks them on purpose, mirror that change here.
    if isinstance(received_type, list) and input_type == COMBO_TYPE:
        return True

    # Not equal, and not strings
    if not isinstance(received_type, str) or not isinstance(input_type, str):
        return False

    # Split the type strings into sets for comparison (verbatim server form)
    received_types = set(t.strip() for t in received_type.split(","))  # noqa: C401
    input_types = set(t.strip() for t in input_type.split(","))  # noqa: C401

    # If any of the types is '*', we can return True immediately; this is the 'Any' type.
    if ANY_TYPE in received_types or ANY_TYPE in input_types:
        return True

    if strict:
        # In strict mode, all received types must be in the input types
        return received_types.issubset(input_types)
    else:
        # In non-strict mode, there must be at least one type in common
        return len(received_types.intersection(input_types)) > 0


class TypeMatch(str, Enum):
    """
    How an edge's source type relates to an input's declared type.

    Everything except :attr:`DISJOINT` is accepted by the server;
    :attr:`OVERLAP` (partial, non-subset intersection) is accepted but worth
    a warning because the runtime value may still be one of the unmatched
    members.
    """

    EXACT = "exact"  # identical type strings
    ANY = "any"  # '*' on either side
    MATCH_TEMPLATE = "match_template"  # COMFY_MATCHTYPE_V3 (frontend-resolved)
    COMBO_OPTIONS = "combo_options"  # list-of-options output into a COMBO input
    SUBSET = "subset"  # received ⊆ declared (the union-superset case)
    OVERLAP = "overlap"  # non-empty intersection, not a subset
    DISJOINT = "disjoint"  # empty intersection: the server rejects this

    @property
    def accepted(self) -> bool:
        """True when the server's non-strict validator accepts this edge."""
        return self is not TypeMatch.DISJOINT

    @property
    def warning(self) -> bool:
        """True when accepted but worth surfacing to the caller."""
        return self is TypeMatch.OVERLAP


def match_types(received_type: Any, input_type: Any) -> TypeMatch:
    """
    Classify an edge the way :func:`validate_node_input` sees it, but with
    enough resolution to warn on partial overlap instead of only pass/fail.

    ``match_types(r, d).accepted`` agrees with
    ``validate_node_input(r, d, strict=False)`` for every input.
    """
    # Same pre-union `__ne__` form as the transcribed validator above.
    if not received_type != input_type:  # noqa: SIM202
        return TypeMatch.EXACT
    if received_type == ANY_TYPE or input_type == ANY_TYPE:
        return TypeMatch.ANY
    if received_type == MATCH_TYPE or input_type == MATCH_TYPE:
        return TypeMatch.MATCH_TEMPLATE
    if isinstance(received_type, list) and input_type == COMBO_TYPE:
        return TypeMatch.COMBO_OPTIONS
    if not isinstance(received_type, str) or not isinstance(input_type, str):
        return TypeMatch.DISJOINT

    received_types = {t.strip() for t in received_type.split(",")}
    input_types = {t.strip() for t in input_type.split(",")}

    if ANY_TYPE in received_types or ANY_TYPE in input_types:
        return TypeMatch.ANY
    if not received_types.intersection(input_types):
        return TypeMatch.DISJOINT
    if received_types.issubset(input_types):
        return TypeMatch.SUBSET
    return TypeMatch.OVERLAP


# =============================================================================
# DOTTED FIELD PATHS
# =============================================================================
#
# A field path is a tuple of segments. Its flattened form joins segments with
# "." -- that flattened string is the literal inputs-dict key ComfyUI expects
# for dynamic-combo sub-fields. A literal dot inside a segment is escaped as
# "\." (and a literal backslash as "\\").


def parse_field_path(path: "str | tuple[str, ...] | list[str]") -> tuple[str, ...]:
    """
    Parse a dotted field path into typed segments.

    Escape-aware: ``r"a\\.b.c"`` parses to ``("a.b", "c")``. A tuple/list is
    accepted as already-parsed segments (validated, not re-split). Empty
    segments (leading/trailing/double dots) are an error -- paths are never
    silently normalized.

    Raises:
        GraphAddressError: If the path is empty or contains empty segments.
    """
    if isinstance(path, (tuple, list)):
        segments = tuple(path)
        if not segments or any(not isinstance(s, str) or not s for s in segments):
            raise GraphAddressError(
                f"Invalid field path segments: {path!r}",
                suggestions=["Every segment must be a non-empty string"],
            )
        return segments

    if not isinstance(path, str) or not path:
        raise GraphAddressError(
            f"Field path must be a non-empty string, got {path!r}",
        )

    segments: list[str] = []
    current: list[str] = []
    escaped = False
    for ch in path:
        if escaped:
            current.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == ".":
            segments.append("".join(current))
            current = []
        else:
            current.append(ch)
    if escaped:
        raise GraphAddressError(f"Field path ends with a dangling escape: {path!r}")
    segments.append("".join(current))

    if any(not s for s in segments):
        raise GraphAddressError(
            f"Field path contains an empty segment: {path!r}",
            suggestions=[r"Escape literal dots as '\.'", "Remove leading/trailing/double dots"],
        )
    return tuple(segments)


def join_field_path(segments: "tuple[str, ...] | list[str]") -> str:
    """
    Flatten segments into the dotted inputs-dict key, escaping literal dots.

    Inverse of :func:`parse_field_path` for round-trip safety.
    """
    return ".".join(s.replace("\\", "\\\\").replace(".", "\\.") for s in segments)


def _resolve_node(workflow: Mapping[str, Any], node_id: str) -> dict[str, Any]:
    """Look up a node by id; never create one (no auto-vivification)."""
    node = workflow.get(str(node_id), workflow.get(node_id))
    if not isinstance(node, dict):
        raise GraphAddressError(
            f"Node '{node_id}' does not exist in the workflow",
            details={"node_id": str(node_id)},
            suggestions=["Addressing never creates nodes; build the node first"],
        )
    return node


def set_node_input(
    workflow: Mapping[str, Any],
    node_id: str,
    path: "str | tuple[str, ...]",
    value: Any,
) -> None:
    """
    Write one input on an existing node, flattening a dotted sub-field path
    into the single dotted key ComfyUI's API format expects.

    The node must already exist -- intermediate structure is never created.
    For dynamic-combo sub-fields prefer :meth:`DynamicCombo.build`, which is
    also presence-aware; this is the raw primitive under it.
    """
    node = _resolve_node(workflow, node_id)
    key = join_field_path(parse_field_path(path))
    inputs = node.setdefault("inputs", {})
    if not isinstance(inputs, dict):
        raise GraphAddressError(
            f"Node '{node_id}' has a non-dict 'inputs' entry",
            details={"node_id": str(node_id), "inputs_type": type(inputs).__name__},
        )
    inputs[key] = value


def get_node_input(
    workflow: Mapping[str, Any],
    node_id: str,
    path: "str | tuple[str, ...]",
    default: Any = None,
) -> Any:
    """Read one (possibly dotted) input from an existing node."""
    node = _resolve_node(workflow, node_id)
    key = join_field_path(parse_field_path(path))
    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        return default
    return inputs.get(key, default)


# =============================================================================
# PRESENCE-AWARE DYNAMIC COMBOS
# =============================================================================


@dataclass(frozen=True)
class DynamicCombo:
    """
    A ``COMFY_DYNAMICCOMBO_V3`` selector modeled as a tagged union.

    ``branches`` maps each selectable choice to its active sub-fields, where a
    sub-field maps to ``None`` (a plain value field) or a nested
    :class:`DynamicCombo` (a conditional selector of its own, e.g.
    ``SaveVideo.codec.encoding``).

    :meth:`build` returns the flattened inputs-dict fragment for one
    selection and refuses, at construction time, any field the selected
    branch does not activate. Because the fragment is always built fresh from
    the tag, a stale sibling from a previous choice cannot survive a tag
    change (protobuf's clear-siblings rule).
    """

    name: str
    branches: Mapping[str, Mapping[str, "DynamicCombo | None"]]

    @property
    def choices(self) -> tuple[str, ...]:
        return tuple(self.branches)

    def build(
        self,
        choice: str,
        values: Mapping[str, Any] | None = None,
        **kw: Any,
    ) -> dict[str, Any]:
        """
        Build the flattened inputs fragment for ``choice``.

        Args:
            choice: The selector value (e.g. ``"mp3"``).
            values: Sub-field values keyed by their path *relative to this
                selector* (e.g. ``{"quality": "320k"}`` or
                ``{"encoding": "re-encode", "encoding.crf": 20}``).
            **kw: Convenience for non-dotted sub-fields
                (``build("mp3", quality="320k")``).

        Returns:
            e.g. ``{"format": "mp3", "format.quality": "320k"}`` --
            ready to merge into a node's ``inputs``.

        Raises:
            InvalidParameterError: If ``choice`` is not a valid selector value.
            GraphAddressError: If a sub-field is not active under the
                selection that was made (the inactive-branch bug class).
        """
        if choice not in self.branches:
            raise InvalidParameterError(
                parameter=self.name,
                value=choice,
                reason="not a valid dynamic-combo choice",
                allowed_values=list(self.branches),
            )

        merged: dict[str, Any] = dict(values or {})
        for k, v in kw.items():
            merged[k] = v

        out: dict[str, Any] = {self.name: choice}

        # Sort so parent selectors ("encoding") are validated before their
        # children ("encoding.crf") regardless of caller ordering.
        for rel_key in sorted(merged, key=lambda k: len(parse_field_path(k))):
            segments = parse_field_path(rel_key)
            self._check_active(choice, segments, merged, rel_key)
            out[join_field_path((self.name, *segments))] = merged[rel_key]

        return out

    def _check_active(
        self,
        choice: str,
        segments: tuple[str, ...],
        merged: Mapping[str, Any],
        rel_key: str,
    ) -> None:
        """Walk the branch tree, proving every segment is active."""
        active = self.branches[choice]
        path_so_far: list[str] = []
        for i, seg in enumerate(segments):
            if seg not in active:
                where = (
                    f"{self.name}={choice!r}"
                    if not path_so_far
                    else f"{join_field_path(path_so_far)}={merged.get(join_field_path(path_so_far))!r}"
                )
                raise GraphAddressError(
                    f"Field '{rel_key}' is not active under {where}",
                    details={
                        "selector": self.name,
                        "choice": choice,
                        "field": rel_key,
                        "active_fields": sorted(active),
                    },
                    suggestions=[
                        f"Active fields here: {', '.join(sorted(active)) or '(none)'}",
                        "Fields from an inactive branch are silently ignored or "
                        "rejected by the server; never send them",
                    ],
                )
            spec = active[seg]
            last = i == len(segments) - 1
            path_so_far.append(seg)
            if last:
                if isinstance(spec, DynamicCombo):
                    # The value selects the nested combo's own choice.
                    nested_choice = merged[rel_key]
                    if nested_choice not in spec.branches:
                        raise InvalidParameterError(
                            parameter=join_field_path((self.name, *segments)),
                            value=nested_choice,
                            reason="not a valid dynamic-combo choice",
                            allowed_values=list(spec.branches),
                        )
                return
            if not isinstance(spec, DynamicCombo):
                raise GraphAddressError(
                    f"Field '{join_field_path(path_so_far)}' has no sub-fields "
                    f"(while addressing '{rel_key}')",
                    details={"selector": self.name, "field": rel_key},
                )
            parent_key = join_field_path(path_so_far)
            if parent_key not in merged:
                raise GraphAddressError(
                    f"Select a value for '{parent_key}' before setting '{rel_key}'",
                    details={"selector": self.name, "field": rel_key, "missing": parent_key},
                    suggestions=[f"Pass {parent_key!r} (one of: {', '.join(spec.branches)})"],
                )
            nested_choice = merged[parent_key]
            if nested_choice not in spec.branches:
                raise InvalidParameterError(
                    parameter=join_field_path((self.name, *path_so_far)),
                    value=nested_choice,
                    reason="not a valid dynamic-combo choice",
                    allowed_values=list(spec.branches),
                )
            active = spec.branches[nested_choice]


# Verified against the live catalog (2026-08-21):
#
# SaveAudioAdvanced.format is COMFY_DYNAMICCOMBO_V3 (flac | mp3 | opus);
# format.quality exists ONLY under mp3/opus (options V0|128k|320k|64k|96k|192k)
# and is absent under flac -- for lossless output emit NO quality key at all.
SAVE_AUDIO_FORMAT = DynamicCombo(
    name="format",
    branches={
        "flac": {},
        "mp3": {"quality": None},
        "opus": {"quality": None},
    },
)

# SaveVideo.codec is COMFY_DYNAMICCOMBO_V3 (auto | h264); codec.encoding is a
# nested dynamic combo that exists only under h264 (auto | re-encode), and
# codec.encoding.crf (FLOAT, default 23) exists only under re-encode.
SAVE_VIDEO_CODEC = DynamicCombo(
    name="codec",
    branches={
        "auto": {},
        "h264": {
            "encoding": DynamicCombo(
                name="encoding",
                branches={
                    "auto": {},
                    "re-encode": {"crf": None},
                },
            ),
        },
    },
)


# =============================================================================
# GRAPH-LEVEL TYPE CHECKING
# =============================================================================


@dataclass
class TypeIssue:
    """One suspicious or invalid edge found by :class:`GraphTypeChecker`."""

    severity: str  # "error" (server would reject) | "warning" (accepted, partial overlap)
    node_id: str
    input_name: str
    source_id: str
    output_index: int
    received: Any
    declared: Any
    match: TypeMatch
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            self.message = (
                f"{self.source_id}[{self.output_index}] ({self.received}) -> "
                f"{self.node_id}.{self.input_name} ({self.declared}): {self.match.value}"
            )


def extract_object_info_types(object_info: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Normalize a raw ``/object_info`` payload into the catalog shape
    :class:`GraphTypeChecker` consumes:
    ``{class_type: {"inputs": {name: type}, "outputs": [type, ...]}}``.

    Parsing is deliberately tolerant -- top-level shape is stable but enum
    contents drift constantly and custom nodes emit non-conforming entries,
    so anything malformed is skipped rather than asserted on. An input whose
    declared type is a list of options is recorded as ``COMBO``.
    """
    catalog: dict[str, dict[str, Any]] = {}
    for class_type, info in object_info.items():
        if not isinstance(info, dict):
            continue
        inputs: dict[str, Any] = {}
        input_section = info.get("input")
        if isinstance(input_section, dict):
            for group in ("required", "optional"):
                section = input_section.get(group)
                if not isinstance(section, dict):
                    continue
                for name, spec in section.items():
                    declared = spec[0] if isinstance(spec, (list, tuple)) and spec else spec
                    if isinstance(declared, (list, tuple)):
                        declared = COMBO_TYPE
                    if isinstance(declared, str):
                        inputs[name] = declared
        outputs_raw = info.get("output", [])
        outputs: list[Any] = []
        if isinstance(outputs_raw, (list, tuple)):
            for out in outputs_raw:
                # A list here is a legacy options-as-type output; keep the
                # list so the COMBO acceptance branch can see it.
                outputs.append(out if isinstance(out, (str, list)) else ANY_TYPE)
        catalog[class_type] = {"inputs": inputs, "outputs": outputs}
    return catalog


class GraphTypeChecker:
    """
    Client-side edge validation for API-format workflows.

    Uses :func:`match_types` -- i.e. the server's own acceptance rule -- so a
    union-superset edge (``MESH`` into a 14-member ``FILE_3D_*`` union) is
    NEVER reported as an error. Only a provably empty intersection is; a
    partial overlap is a warning.

    Unknown class_types, unknown inputs and out-of-range output indices are
    skipped silently: the catalog may be stale or partial, and a checker that
    guesses is worse than one that abstains. (Missing *nodes* are the
    dependency checker's job, not the type checker's.)
    """

    def __init__(self, catalog: Mapping[str, Any]):
        """
        Args:
            catalog: ``{class_type: {"inputs": {name: type}, "outputs": [...]}}``
                -- build one from a live server with
                :func:`extract_object_info_types`.
        """
        self.catalog = catalog

    def check(self, workflow: Mapping[str, Any]) -> list[TypeIssue]:
        """Validate every edge; return issues (empty list == fully clean)."""
        issues: list[TypeIssue] = []
        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
            class_type = node.get("class_type")
            entry = self.catalog.get(class_type) if isinstance(class_type, str) else None
            if not isinstance(entry, dict):
                continue
            declared_inputs = entry.get("inputs", {})
            inputs = node.get("inputs", {})
            if not isinstance(inputs, dict):
                continue
            for input_name, value in inputs.items():
                if not (isinstance(value, list) and len(value) == 2):
                    continue  # literal value, not an edge
                declared = declared_inputs.get(input_name)
                if declared is None:
                    continue
                source_id, output_index = str(value[0]), value[1]
                source = workflow.get(source_id)
                if not isinstance(source, dict):
                    continue
                source_entry = self.catalog.get(source.get("class_type"))
                if not isinstance(source_entry, dict):
                    continue
                outputs = source_entry.get("outputs", [])
                if not isinstance(output_index, int) or output_index >= len(outputs):
                    continue
                received = outputs[output_index]
                match = match_types(received, declared)
                if match is TypeMatch.DISJOINT:
                    issues.append(
                        TypeIssue(
                            severity="error",
                            node_id=str(node_id),
                            input_name=input_name,
                            source_id=source_id,
                            output_index=output_index,
                            received=received,
                            declared=declared,
                            match=match,
                        )
                    )
                elif match.warning:
                    issues.append(
                        TypeIssue(
                            severity="warning",
                            node_id=str(node_id),
                            input_name=input_name,
                            source_id=source_id,
                            output_index=output_index,
                            received=received,
                            declared=declared,
                            match=match,
                        )
                    )
        return issues

    def errors(self, workflow: Mapping[str, Any]) -> list[TypeIssue]:
        """Only the edges the server would actually reject."""
        return [i for i in self.check(workflow) if i.severity == "error"]


# =============================================================================
# OUTPUT-NODE GUARD
# =============================================================================

# Which /history outputs key each terminator reports under, verified against
# the server source. This is the retrieval contract: after wait_for_completion,
# results are found at history["outputs"][<node_id>][<key>]. SaveVideo lands
# under "images" WITH an "animated" flag (not "gifs" -- that's VHS); SaveText
# reports the inline text under "text" AND the written file under "files".
HISTORY_OUTPUT_KEYS: dict[str, tuple[str, ...]] = {
    "SaveImage": ("images",),
    "SaveGLB": ("3d",),
    "SaveText": ("text", "files"),
    "SaveAudioAdvanced": ("audio",),
    "SaveVideo": ("images",),  # + "animated" flag distinguishes it from stills
    "VHS_VideoCombine": ("gifs",),
}

# class_types with OUTPUT_NODE=True that comfy-headless emits or commonly
# meets. A STRING/JSON/mesh/audio result reaches /history ONLY through a node
# flagged as an output node; a bare captioner's output is invisible to a
# headless caller. Every entry verified against the live catalog (2026-08-21).
KNOWN_OUTPUT_NODE_CLASSES: frozenset[str] = frozenset(
    {
        "SaveImage",
        "PreviewImage",
        "SaveGLB",
        "SaveText",
        "SaveAudioAdvanced",
        "SaveVideo",
        "SaveAnimatedWEBP",
        "SaveAnimatedPNG",
        # Deprecated audio terminators -- still output nodes if present.
        "SaveAudio",
        "SaveAudioMP3",
        "SaveAudioOpus",
        # Pack terminators.
        "VHS_VideoCombine",
    }
)


def has_output_node(
    workflow: Mapping[str, Any],
    known_output_classes: frozenset[str] = KNOWN_OUTPUT_NODE_CLASSES,
) -> bool:
    """True if at least one node in the workflow is a known output node."""
    return any(
        isinstance(node, dict) and node.get("class_type") in known_output_classes
        for node in workflow.values()
    )


def require_output_node(
    workflow: Mapping[str, Any],
    known_output_classes: frozenset[str] = KNOWN_OUTPUT_NODE_CLASSES,
) -> None:
    """
    Reject a graph whose results would be invisible to a headless caller.

    A graph with no OUTPUT_NODE terminator runs green and returns nothing --
    the single most likely silent failure for inference-style workflows.

    Raises:
        ValidationError: If no known output node is present.
    """
    if not has_output_node(workflow, known_output_classes):
        raise ValidationError(
            "Workflow has no output node - it would execute and return nothing",
            details={
                "known_output_classes": sorted(known_output_classes),
                "workflow_classes": sorted(
                    {
                        node.get("class_type")
                        for node in workflow.values()
                        if isinstance(node, dict) and isinstance(node.get("class_type"), str)
                    }
                ),
            },
            suggestions=[
                "Terminate data outputs in a node with OUTPUT_NODE=True "
                "(SaveText for STRING/JSON, SaveImage for IMAGE, "
                "SaveAudioAdvanced for AUDIO, SaveGLB for meshes)",
            ],
        )
