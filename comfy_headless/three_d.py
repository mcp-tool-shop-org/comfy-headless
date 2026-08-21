"""
Comfy Headless - 3D Generation Module
=====================================

v3.1.0: the 3D profile. Image-to-mesh via Hunyuan3D-2, entirely core --
no ComfyUI-3D-Pack required (that pack's nvdiffrast / gaussian-rasterization
dependencies are the least stable in the ecosystem, so the default path
deliberately avoids it).

Headless 3D works with the routes the client already has: ``SaveGLB`` writes
the file and registers it in ``/history`` exactly like ``SaveImage`` does for
PNGs (under the ``"3d"`` outputs key), and the file comes back through
``GET /view?filename=...&type=output``. No new route needed.

Reference graph (validated clean against the live catalog, 2026-08-21)::

    LoadImage -> CLIPVisionEncode(crop=center) <- CLIPVisionLoader(clip_vision_g)
        -> Hunyuan3Dv2Conditioning -> (positive, negative)
    ImageOnlyCheckpointLoader(hunyuan3d-dit-v2_fp16) -> MODEL, _, VAE
    EmptyLatentHunyuan3Dv2(resolution 3072) -> KSampler(steps 30, cfg 5.5)
        -> VAEDecodeHunyuan3D(num_chunks 8000, octree 256)   -> VOXEL
        -> VoxelToMesh(algorithm "surface net", threshold 0.6) -> MESH
        -> SaveGLB(filename_prefix "3d/ComfyUI")

The VoxelToMesh -> SaveGLB edge is the canonical union-superset case:
``MESH`` into a 14-member ``FILE_3D_*`` union input. It is correct and any
validator that rejects it is wrong (see ``addressing.validate_node_input``).

Not covered here (deliberately): multi-view conditioning (the ``-mv``
checkpoints exist but their conditioning class is unverified), texture/PBR
baking (a separate second graph that takes the finished mesh), and
wrapper-pack models (TRELLIS, TripoSG, Hi3DGen) -- all pack-dependent.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "ThreeDModel",
    "MeshAlgorithm",
    "ThreeDSettings",
    "ThreeDModelInfo",
    "THREE_D_PRESETS",
    "THREE_D_MODEL_INFO",
    "ThreeDWorkflowBuilder",
    "get_three_d_builder",
    "build_3d_workflow",
    "list_3d_presets",
]


class ThreeDModel(str, Enum):
    """Available image-to-3D models."""

    HUNYUAN3D_V2 = "hunyuan3d_v2"


class MeshAlgorithm(str, Enum):
    """VoxelToMesh extraction algorithms."""

    SURFACE_NET = "surface net"
    BASIC = "basic"


@dataclass
class ThreeDSettings:
    """Settings for image-to-3D generation."""

    model: ThreeDModel = ThreeDModel.HUNYUAN3D_V2
    checkpoint: str = "hunyuan3d-dit-v2_fp16.safetensors"
    clip_vision: str = "clip_vision_g.safetensors"
    resolution: int = 3072  # EmptyLatentHunyuan3Dv2 latent resolution
    steps: int = 30
    cfg: float = 5.5
    sampler: str = "euler"
    scheduler: str = "simple"
    seed: int = -1
    num_chunks: int = 8000  # VAEDecodeHunyuan3D
    octree_resolution: int = 256  # VAEDecodeHunyuan3D (16..512)
    algorithm: MeshAlgorithm = MeshAlgorithm.SURFACE_NET
    threshold: float = 0.6  # VoxelToMesh iso threshold
    filename_prefix: str = "3d/ComfyUI"

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "checkpoint": self.checkpoint,
            "clip_vision": self.clip_vision,
            "resolution": self.resolution,
            "steps": self.steps,
            "cfg": self.cfg,
            "sampler": self.sampler,
            "scheduler": self.scheduler,
            "seed": self.seed,
            "num_chunks": self.num_chunks,
            "octree_resolution": self.octree_resolution,
            "algorithm": self.algorithm.value,
            "threshold": self.threshold,
            "filename_prefix": self.filename_prefix,
        }


THREE_D_PRESETS: dict[str, ThreeDSettings] = {
    # The validated reference configuration.
    "standard": ThreeDSettings(),
    # Fewer steps + coarser octree for quick silhouette checks.
    "draft": ThreeDSettings(steps=15, octree_resolution=128),
    # More steps + finer octree for the final export.
    "detail": ThreeDSettings(steps=50, octree_resolution=384),
}


@dataclass
class ThreeDModelInfo:
    """Information about a 3D model family."""

    id: str
    name: str
    description: str
    model: ThreeDModel
    min_vram_gb: int = 12
    estimated_time_seconds: int = 60
    presets: list[str] = field(default_factory=list)
    # Custom node packs this family's workflows depend on. Empty == core only.
    requires_packs: list[str] = field(default_factory=list)


THREE_D_MODEL_INFO: dict[str, ThreeDModelInfo] = {
    "hunyuan3d_v2": ThreeDModelInfo(
        id="hunyuan3d_v2",
        name="Hunyuan3D-2",
        description=(
            "Tencent image-to-mesh, native ComfyUI core path (no custom packs). "
            "Pure image-conditioned: no text prompt. Exports GLB via SaveGLB."
        ),
        model=ThreeDModel.HUNYUAN3D_V2,
        min_vram_gb=12,
        estimated_time_seconds=60,
        presets=["standard", "draft", "detail"],
        requires_packs=[],  # entirely core -- the point of this default
    ),
}


class ThreeDWorkflowBuilder:
    """
    Builds ComfyUI workflows for image-to-3D generation.

    The input image must already be on the ComfyUI server -- upload it with
    ``ComfyClient.upload_image()`` and pass the returned ``"ref"``.
    """

    def build(self, image_ref: str, settings: ThreeDSettings) -> dict[str, Any]:
        """
        Build a Hunyuan3D-2 image-to-mesh workflow.

        Args:
            image_ref: Name of an image already in ComfyUI's input folder,
                as returned by ``ComfyClient.upload_image()["ref"]``.
            settings: 3D generation settings.

        Returns:
            ComfyUI API-format workflow JSON.
        """
        if not image_ref:
            raise ValueError("3D generation requires an input image (image_ref)")

        seed = settings.seed
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        return {
            # Input image (already uploaded to ComfyUI's input folder)
            "1": {"class_type": "LoadImage", "inputs": {"image": image_ref}},
            # DiT + VAE from the image-only checkpoint loader
            "2": {
                "class_type": "ImageOnlyCheckpointLoader",
                "inputs": {"ckpt_name": settings.checkpoint},
            },
            # Vision encoder (separate loader; the checkpoint's own
            # CLIP_VISION slot is not used by the official Hunyuan3D graph)
            "3": {
                "class_type": "CLIPVisionLoader",
                "inputs": {"clip_name": settings.clip_vision},
            },
            "4": {
                "class_type": "CLIPVisionEncode",
                "inputs": {"clip_vision": ["3", 0], "image": ["1", 0], "crop": "center"},
            },
            # Image-conditioned positive/negative -- no text prompt at all
            "5": {
                "class_type": "Hunyuan3Dv2Conditioning",
                "inputs": {"clip_vision_output": ["4", 0]},
            },
            "6": {
                "class_type": "EmptyLatentHunyuan3Dv2",
                "inputs": {"resolution": settings.resolution, "batch_size": 1},
            },
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": ["5", 0],
                    "negative": ["5", 1],
                    "latent_image": ["6", 0],
                    "seed": seed,
                    "steps": settings.steps,
                    "cfg": settings.cfg,
                    "sampler_name": settings.sampler,
                    "scheduler": settings.scheduler,
                    "denoise": 1.0,
                },
            },
            "8": {
                "class_type": "VAEDecodeHunyuan3D",
                "inputs": {
                    "samples": ["7", 0],
                    "vae": ["2", 2],
                    "num_chunks": settings.num_chunks,
                    "octree_resolution": settings.octree_resolution,
                },
            },
            "9": {
                "class_type": "VoxelToMesh",
                "inputs": {
                    "voxel": ["8", 0],
                    "algorithm": settings.algorithm.value,
                    "threshold": settings.threshold,
                },
            },
            # MESH into SaveGLB's FILE_3D_* union input -- the union-superset
            # edge; correct, and covered by the addressing-layer corpus gate.
            "10": {
                "class_type": "SaveGLB",
                "inputs": {"mesh": ["9", 0], "filename_prefix": settings.filename_prefix},
            },
        }


_builder: ThreeDWorkflowBuilder | None = None


def get_three_d_builder() -> ThreeDWorkflowBuilder:
    """Get singleton 3D workflow builder."""
    global _builder
    if _builder is None:
        _builder = ThreeDWorkflowBuilder()
    return _builder


def build_3d_workflow(
    image_ref: str,
    preset: str = "standard",
    **overrides: Any,
) -> dict[str, Any]:
    """
    Build an image-to-3D workflow with preset settings.

    Simple usage::

        uploaded = client.upload_image("character.png")
        workflow = build_3d_workflow(uploaded["ref"], preset="detail")
    """
    base = THREE_D_PRESETS.get(preset, THREE_D_PRESETS["standard"])
    if overrides:
        merged = base.to_dict()
        merged.update(overrides)
        settings = ThreeDSettings(
            model=ThreeDModel(merged.get("model", base.model.value)),
            checkpoint=merged.get("checkpoint", base.checkpoint),
            clip_vision=merged.get("clip_vision", base.clip_vision),
            resolution=int(merged.get("resolution", base.resolution)),
            steps=int(merged.get("steps", base.steps)),
            cfg=float(merged.get("cfg", base.cfg)),
            sampler=merged.get("sampler", base.sampler),
            scheduler=merged.get("scheduler", base.scheduler),
            seed=int(merged.get("seed", base.seed)),
            num_chunks=int(merged.get("num_chunks", base.num_chunks)),
            octree_resolution=int(merged.get("octree_resolution", base.octree_resolution)),
            algorithm=MeshAlgorithm(merged.get("algorithm", base.algorithm.value)),
            threshold=float(merged.get("threshold", base.threshold)),
            filename_prefix=merged.get("filename_prefix", base.filename_prefix),
        )
    else:
        settings = base

    return get_three_d_builder().build(image_ref, settings)


def list_3d_presets() -> list[str]:
    """List available 3D preset names."""
    return list(THREE_D_PRESETS.keys())
