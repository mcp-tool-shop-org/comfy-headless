# Addressing and typing layer

Summary: The three mechanics under every profile — server-parity union type matching, dotted dynamic-combo sub-fields, and presence-aware conditional inputs.
Keywords: addressing, types, union, dynamic-combo, dotted-fields, validate_node_input, typestate

Module: `comfy_headless/addressing.py`. Everything here exists because three
independent failure classes land on the same layer, and shipping profiles on
a flat emitter produces failures that look like model problems.

## 1. Union-superset type matching

`validate_node_input(received, declared, strict=False)` is a **transcription
of ComfyUI's own** `comfy_execution/validation.py` — the server's acceptance
rule, verbatim. Order of checks: exact string match (pre-union `__ne__`
form), `*` AnyType on either side, `COMFY_MATCHTYPE_V3` on either side,
options-list into `COMBO`, then split both sides on `,`, strip whitespace:
strict ⇒ received ⊆ declared; default ⇒ intersection non-empty.

Why transcription and not judgment: a client stricter than the server
manufactures false rejections **by construction**. Measured case:
`VoxelToMesh` emits `MESH` into `SaveGLB.mesh`, which declares a 14-member
`FILE_3D_*` union — a correct edge a naive equality check rejects.

`match_types()` adds resolution for tooling: SUBSET (accept), OVERLAP
(accept **with warning** — partial intersection), DISJOINT (the only
rejection). `GraphTypeChecker` applies this per edge against an
`/object_info`-shaped catalog, skipping unknown nodes (enum contents drift
constantly; a checker that guesses is worse than one that abstains).
`ComfyClient.check_workflow_types()` runs it against the live server.

**Release gate**: `tests/test_addressing.py::TestZeroRejectionsCorpusGate` —
zero errors on every known-good graph the builders emit, with a
coverage assertion so no edge escapes via skip-unknown.

## 2. Dotted sub-field addressing

Dynamic-combo fields (`COMFY_DYNAMICCOMBO_V3`) serialize as **flattened
dotted keys** in a node's `inputs`:

```json
{"codec": "h264", "codec.encoding": "re-encode", "codec.encoding.crf": 23}
```

Sent flat (`{"crf": 23}`) they fail with `required_input_missing`. Confirmed
sites: `SaveVideo.codec(.encoding(.crf))` and
`SaveAudioAdvanced.format(.quality)`; subgraph interiors address as
`<outer_id>/<inner_id>.<field>`.

`parse_field_path` / `join_field_path` are escape-aware (`\.` for a literal
dot) and never split-and-vivify; `set_node_input` writes exactly one
flattened key on an **existing** node — intermediate structure is never
auto-created (the lodash CVE-2020-8203 lesson).

## 3. Presence-aware conditional fields

`DynamicCombo` models the tagged union: `SAVE_AUDIO_FORMAT.build("mp3",
quality="320k")` → `{"format": "mp3", "format.quality": "320k"}`, while
`build("flac", quality=...)` **raises at construction time** — a field from
an inactive branch is its own bug class (the server may silently ignore it,
or reject). Because the fragment is always built fresh from the tag, a stale
sibling cannot survive a tag change (protobuf's clear-siblings rule;
construction-time beats validation-time). Nested selectors compose:
`SAVE_VIDEO_CODEC.build("h264", {"encoding": "re-encode", "encoding.crf": 20})`.

## 4. The output-node guard

`require_output_node(workflow)` rejects any graph with no
`OUTPUT_NODE=True` terminator — the run-green-return-nothing failure. The
inference builders apply it to every graph. `HISTORY_OUTPUT_KEYS` maps each
terminator class to its `/history` outputs key (see `retrieval.md`).
