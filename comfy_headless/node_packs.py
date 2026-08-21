"""
Comfy Headless - Custom Node Pack Provenance
============================================

Not every class_type the profile builders emit ships with ComfyUI. Nodes that
come from a custom node pack are declared here so ComfyClient can validate a
workflow against /object_info and report "class X missing -- install pack Y"
instead of letting POST /prompt reject the graph with an opaque validation
error. Anything NOT listed here is expected to be a built-in (core) node.

Every entry below was checked against the live ComfyUI node catalog
(2026-08-21). This registry is shared by all profile modules (image, video,
3D, audio, inference); ``video.py`` re-exports it for backwards
compatibility with the pre-3.1 import surface.
"""

from dataclasses import dataclass
from typing import Any

__all__ = [
    "NodePack",
    "NODE_PACK_INFO",
    "NODE_PACKS",
    "get_node_pack",
    "required_node_packs",
]


@dataclass(frozen=True)
class NodePack:
    """A custom node pack that some workflows depend on."""

    id: str
    name: str
    url: str
    install_hint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "install_hint": self.install_hint,
        }


NODE_PACK_INFO: dict[str, NodePack] = {
    "comfyui-videohelpersuite": NodePack(
        id="comfyui-videohelpersuite",
        name="ComfyUI-VideoHelperSuite",
        url="https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'Video Helper Suite'",
    ),
    "comfyui-animatediff-evolved": NodePack(
        id="comfyui-animatediff-evolved",
        name="ComfyUI-AnimateDiff-Evolved",
        url="https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'AnimateDiff Evolved'",
    ),
    "comfyui-cogvideoxwrapper": NodePack(
        id="comfyui-cogvideoxwrapper",
        name="ComfyUI-CogVideoXWrapper",
        url="https://github.com/kijai/ComfyUI-CogVideoXWrapper",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'CogVideoX Wrapper'",
    ),
    "comfyui-frame-interpolation": NodePack(
        id="comfyui-frame-interpolation",
        name="ComfyUI-Frame-Interpolation",
        url="https://github.com/Fannovel16/ComfyUI-Frame-Interpolation",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'Frame Interpolation'",
    ),
    # v3.1.0: inference profile
    "comfyui-florence2": NodePack(
        id="comfyui-florence2",
        name="ComfyUI-Florence2",
        url="https://github.com/kijai/ComfyUI-Florence2",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'ComfyUI-Florence2'",
    ),
    "comfyui-segment-anything-2": NodePack(
        id="comfyui-segment-anything-2",
        name="ComfyUI-segment-anything-2",
        url="https://github.com/kijai/ComfyUI-segment-anything-2",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'ComfyUI-segment-anything-2'",
    ),
    # v3.1.0: audio profile (stem separation)
    "audio-separation-nodes-comfyui": NodePack(
        id="audio-separation-nodes-comfyui",
        name="audio-separation-nodes-comfyui",
        url="https://github.com/christian-byrne/audio-separation-nodes-comfyui",
        install_hint="ComfyUI Manager -> Install Custom Nodes -> 'audio-separation-nodes-comfyui'",
    ),
}
"""Metadata for every custom node pack referenced by NODE_PACKS."""


NODE_PACKS: dict[str, str] = {
    # --- ComfyUI-VideoHelperSuite -------------------------------------------
    # Used by the video builders as the default muxing / output node.
    "VHS_VideoCombine": "comfyui-videohelpersuite",
    # --- ComfyUI-AnimateDiff-Evolved ----------------------------------------
    "ADE_LoadAnimateDiffModel": "comfyui-animatediff-evolved",
    "ADE_ApplyAnimateDiffModel": "comfyui-animatediff-evolved",
    "ADE_EmptyLatentImageLarge": "comfyui-animatediff-evolved",
    # --- ComfyUI-CogVideoXWrapper -------------------------------------------
    # CogVideoX has no native core path; the whole family lives in this pack.
    "DownloadAndLoadCogVideoModel": "comfyui-cogvideoxwrapper",
    "CogVideoTextEncode": "comfyui-cogvideoxwrapper",
    "CogVideoSampler": "comfyui-cogvideoxwrapper",
    "CogVideoDecode": "comfyui-cogvideoxwrapper",
    # --- ComfyUI-Frame-Interpolation ----------------------------------------
    "RIFE VFI": "comfyui-frame-interpolation",
    # --- ComfyUI-Florence2 (inference profile) ------------------------------
    # There is no core captioner / tagger / detector; Florence-2 provides all
    # three through one pack. NOTE: the local-path loader class
    # ``Florence2ModelLoader`` was NOT present in the live catalog (2026-08-21)
    # -- only the auto-downloading loader is emitted.
    "Florence2Run": "comfyui-florence2",
    "DownloadAndLoadFlorence2Model": "comfyui-florence2",
    # --- ComfyUI-segment-anything-2 (inference profile, detect leg) ---------
    # Converts Florence2Run's JSON detection data into a coordinates STRING
    # that core SaveText can persist (JSON -> STRING is not a valid edge).
    "Florence2toCoordinates": "comfyui-segment-anything-2",
    # --- audio-separation-nodes-comfyui (audio profile) ---------------------
    # NOT core, despite bundling no loader. Outputs 4x AUDIO in documented
    # order: bass, drums, other, vocals.
    "AudioSeparation": "audio-separation-nodes-comfyui",
}
"""Maps a non-core class_type to the id of the pack that provides it."""


def get_node_pack(class_type: str) -> str | None:
    """
    Return the custom node pack id that provides ``class_type``.

    Returns ``None`` for nodes that ship with ComfyUI itself (core nodes).
    """
    return NODE_PACKS.get(class_type)


def required_node_packs(workflow: dict[str, Any]) -> dict[str, list[str]]:
    """
    Group the custom-pack class_types used by a workflow by their pack id.

    Args:
        workflow: A ComfyUI API-format workflow (node_id -> {class_type, inputs}).

    Returns:
        ``{pack_id: [class_type, ...]}`` with only non-core nodes present.
        An empty dict means the workflow needs no custom node packs.
    """
    packs: dict[str, list[str]] = {}
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        class_type = node.get("class_type")
        if not isinstance(class_type, str):
            continue
        pack_id = NODE_PACKS.get(class_type)
        if pack_id is None:
            continue
        bucket = packs.setdefault(pack_id, [])
        if class_type not in bucket:
            bucket.append(class_type)
    return {pack_id: sorted(names) for pack_id, names in sorted(packs.items())}
