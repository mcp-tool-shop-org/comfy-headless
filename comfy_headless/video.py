"""
Comfy Headless - Video Generation Module
========================================

v2.5.0: Added LTX-Video 2, Hunyuan 1.5, Wan 2.1/2.2

Complete video generation support for multiple models:
- AnimateDiff v2/v3/Lightning
- Stable Video Diffusion (SVD/SVD-XT)
- CogVideoX
- Hunyuan Video / Hunyuan Video 1.5
- LTX-Video 2 (Lightricks) - NEW
- Wan 2.1/2.2 (Alibaba) - NEW
- Mochi (Genmo)

Makes video generation accessible through simple presets and settings.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    # Enums
    "VideoModel",
    "VideoFormat",
    "MotionStyle",
    # Data classes
    "VideoSettings",
    "VideoModelInfo",
    # Presets
    "VIDEO_PRESETS",
    "VIDEO_MODEL_INFO",
    # Custom node pack provenance
    "NodePack",
    "NODE_PACKS",
    "NODE_PACK_INFO",
    "get_node_pack",
    "required_node_packs",
    # Builder
    "VideoWorkflowBuilder",
    "get_video_builder",
    # Convenience functions
    "build_video_workflow",
    "get_video_preset",
    "list_video_presets",
    "list_video_models",
    "get_recommended_preset",
]


# =============================================================================
# VIDEO ENUMS
# =============================================================================


class VideoModel(str, Enum):
    """Available video generation models."""

    # AnimateDiff family
    ANIMATEDIFF_V2 = "animatediff_v2"
    ANIMATEDIFF_V3 = "animatediff_v3"
    ANIMATEDIFF_LIGHTNING = "animatediff_lightning"

    # Stable Video Diffusion
    SVD = "svd"
    SVD_XT = "svd_xt"

    # CogVideoX
    COGVIDEOX = "cogvideox"

    # Hunyuan Video (Tencent)
    HUNYUAN = "hunyuan"
    HUNYUAN_15 = "hunyuan_15"  # v2.5.0: Hunyuan 1.5 with new encoders
    HUNYUAN_15_FAST = "hunyuan_15_fast"  # v2.5.0: 6-step distilled variant
    HUNYUAN_15_I2V = "hunyuan_15_i2v"  # v2.5.0: Image-to-video variant

    # LTX-Video (Lightricks) - v2.5.0
    LTXV = "ltxv"  # LTX-Video 2 text-to-video
    LTXV_I2V = "ltxv_i2v"  # LTX-Video 2 image-to-video

    # Wan (Alibaba/WaveSpeed) - v2.5.0
    WAN = "wan"  # Wan 2.1/2.2 standard
    WAN_FAST = "wan_fast"  # Wan 2.2 4-step with LoRA
    WAN_I2V = "wan_i2v"  # Wan image-to-video

    # Mochi (Genmo) - v2.5.0
    MOCHI = "mochi"  # Mochi 1 (best text adherence)


class VideoFormat(str, Enum):
    """Output video formats."""

    MP4 = "mp4"
    GIF = "gif"
    WEBM = "webm"
    FRAMES = "frames"


class MotionStyle(str, Enum):
    """Motion intensity presets."""

    STATIC = "static"  # Minimal movement
    SUBTLE = "subtle"  # Gentle, slow movements
    MODERATE = "moderate"  # Normal motion
    DYNAMIC = "dynamic"  # Fast, energetic movement
    EXTREME = "extreme"  # Maximum motion


# =============================================================================
# VIDEO SETTINGS
# =============================================================================


@dataclass
class VideoSettings:
    """Settings for video generation."""

    model: VideoModel = VideoModel.ANIMATEDIFF_V3
    width: int = 512
    height: int = 512
    frames: int = 16
    fps: int = 8
    steps: int = 20
    cfg: float = 7.0
    seed: int = -1
    motion_scale: float = 1.0
    motion_style: MotionStyle = MotionStyle.MODERATE
    checkpoint: str | None = "dreamshaper_8.safetensors"
    format: VideoFormat = VideoFormat.MP4
    interpolate: bool = False  # Use RIFE to double frames

    # v2.5.0: New fields for advanced models
    variant: str | None = None  # Model variant (e.g., "1.3b", "14b", "distilled")
    upscale: bool = False  # Enable super-resolution (Hunyuan 1.5)
    shift: float | None = None  # ModelSamplingSD3 shift override
    precision: str = "fp16"  # Model precision (fp16, fp8, bf16)

    # v3.1.0: video terminator. "vhs" = VHS_VideoCombine (pack, the long-
    # standing default); "core" = CreateVideo -> SaveVideo (no pack needed;
    # SaveVideo's dynamic-combo codec is emitted via the addressing layer).
    # With "core" the output registers in /history under "images" (with an
    # "animated" flag), not "gifs" -- ComfyClient.generate_video handles both.
    output: str = "vhs"

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "width": self.width,
            "height": self.height,
            "frames": self.frames,
            "fps": self.fps,
            "steps": self.steps,
            "cfg": self.cfg,
            "seed": self.seed,
            "motion_scale": self.motion_scale,
            "motion_style": self.motion_style.value,
            "checkpoint": self.checkpoint,
            "format": self.format.value,
            "interpolate": self.interpolate,
            "variant": self.variant,
            "upscale": self.upscale,
            "shift": self.shift,
            "precision": self.precision,
            "output": self.output,
        }


# =============================================================================
# VIDEO PRESETS
# =============================================================================

VIDEO_PRESETS: dict[str, VideoSettings] = {
    # AnimateDiff presets
    "quick": VideoSettings(
        model=VideoModel.ANIMATEDIFF_LIGHTNING,
        width=512,
        height=512,
        frames=16,
        fps=8,
        steps=4,
        cfg=2.0,
        motion_style=MotionStyle.MODERATE,
    ),
    "standard": VideoSettings(
        model=VideoModel.ANIMATEDIFF_V3,
        width=512,
        height=512,
        frames=16,
        fps=8,
        steps=20,
        motion_style=MotionStyle.MODERATE,
    ),
    "quality": VideoSettings(
        model=VideoModel.ANIMATEDIFF_V3,
        width=768,
        height=768,
        frames=24,
        fps=12,
        steps=25,
        motion_style=MotionStyle.MODERATE,
        interpolate=True,
    ),
    "cinematic": VideoSettings(
        model=VideoModel.ANIMATEDIFF_V3,
        width=768,
        height=432,  # 16:9
        frames=32,
        fps=24,
        steps=30,
        motion_style=MotionStyle.SUBTLE,
        interpolate=True,
    ),
    "portrait": VideoSettings(
        model=VideoModel.ANIMATEDIFF_V3,
        width=512,
        height=768,  # 2:3
        frames=24,
        fps=12,
        steps=25,
        motion_style=MotionStyle.SUBTLE,
    ),
    "action": VideoSettings(
        model=VideoModel.ANIMATEDIFF_V3,
        width=512,
        height=512,
        frames=24,
        fps=16,
        steps=25,
        motion_style=MotionStyle.DYNAMIC,
        motion_scale=1.3,
    ),
    # SVD presets (image-to-video)
    "svd_short": VideoSettings(
        model=VideoModel.SVD,
        width=1024,
        height=576,
        frames=14,
        fps=6,
        steps=25,
        checkpoint=None,
    ),
    "svd_long": VideoSettings(
        model=VideoModel.SVD_XT,
        width=1024,
        height=576,
        frames=25,
        fps=6,
        steps=25,
        checkpoint=None,
    ),
    # CogVideoX preset
    "cogvideo": VideoSettings(
        model=VideoModel.COGVIDEOX,
        width=720,
        height=480,
        frames=48,
        fps=8,
        steps=50,
        checkpoint=None,
    ),
    # Hunyuan presets (original)
    "hunyuan": VideoSettings(
        model=VideoModel.HUNYUAN,
        width=1280,
        height=720,
        frames=45,
        fps=15,
        steps=30,
        cfg=6.0,  # embedded guidance (t2v checkpoint is guidance-distilled)
        shift=7.0,
        checkpoint=None,
    ),
    "hunyuan_fast": VideoSettings(
        model=VideoModel.HUNYUAN,
        width=848,
        height=480,
        frames=33,
        fps=15,
        steps=20,
        cfg=6.0,  # embedded guidance (t2v checkpoint is guidance-distilled)
        shift=7.0,
        checkpoint=None,
    ),
    # =========================================================================
    # v2.5.0: NEW VIDEO MODELS
    # =========================================================================
    # Hunyuan Video 1.5 presets (Tencent - improved quality, new encoders)
    "hunyuan15_720p": VideoSettings(
        model=VideoModel.HUNYUAN_15,
        width=1280,
        height=720,
        frames=121,
        fps=24,
        steps=20,
        cfg=6.0,
        shift=9.0,  # Shift for 720p T2V
        checkpoint=None,
    ),
    "hunyuan15_quality": VideoSettings(
        model=VideoModel.HUNYUAN_15,
        width=1280,
        height=720,
        frames=121,
        fps=24,
        steps=50,
        cfg=6.0,
        shift=9.0,
        checkpoint=None,
    ),
    "hunyuan15_fast": VideoSettings(
        model=VideoModel.HUNYUAN_15_FAST,
        width=848,
        height=480,
        frames=81,
        fps=24,
        steps=6,
        cfg=1.0,  # Distilled model uses CFG=1
        shift=5.0,  # 480p distilled shift, per Hunyuan's published table
        variant="distilled",
        checkpoint=None,
    ),
    "hunyuan15_1080p": VideoSettings(
        model=VideoModel.HUNYUAN_15,
        width=1920,
        height=1080,
        frames=121,
        fps=24,
        steps=20,
        cfg=6.0,
        shift=9.0,
        upscale=True,  # Uses super-resolution pipeline
        checkpoint=None,
    ),
    "hunyuan15_i2v": VideoSettings(
        model=VideoModel.HUNYUAN_15_I2V,
        width=848,
        height=480,
        frames=81,
        fps=24,
        steps=20,
        cfg=6.0,
        shift=5.0,  # 480p row of Hunyuan's published shift table
        checkpoint=None,
    ),
    "hunyuan15_i2v_fast": VideoSettings(
        model=VideoModel.HUNYUAN_15_I2V,
        width=848,
        height=480,
        frames=81,
        fps=24,
        steps=6,
        cfg=1.0,  # cfg-distilled i2v checkpoint uses CFG=1
        shift=5.0,
        variant="distilled",
        checkpoint=None,
    ),
    # LTX-Video 2 presets (Lightricks - fast, high quality)
    "ltx_quick": VideoSettings(
        model=VideoModel.LTXV,
        width=768,
        height=512,
        frames=97,
        fps=24,
        steps=20,
        cfg=3.0,  # LTXV uses low CFG
        checkpoint=None,
    ),
    "ltx_standard": VideoSettings(
        model=VideoModel.LTXV,
        width=768,
        height=512,
        frames=97,
        fps=24,
        steps=30,
        cfg=3.0,
        checkpoint=None,
    ),
    "ltx_quality": VideoSettings(
        model=VideoModel.LTXV,
        width=1280,
        height=720,
        frames=97,
        fps=24,
        steps=30,
        cfg=3.0,
        checkpoint=None,
    ),
    # Wan presets (Alibaba - efficient, great quality)
    "wan_1.3b": VideoSettings(
        model=VideoModel.WAN,
        width=832,
        height=480,
        frames=33,
        fps=16,
        steps=30,
        cfg=6.0,
        shift=8.0,  # Wan T2V shift
        variant="1.3b",
        checkpoint=None,
    ),
    "wan_14b": VideoSettings(
        model=VideoModel.WAN,
        width=640,
        height=640,
        frames=81,
        fps=16,
        steps=20,
        cfg=3.5,
        shift=8.0,
        variant="14b",
        precision="fp8",
        checkpoint=None,
    ),
    "wan_fast": VideoSettings(
        model=VideoModel.WAN_FAST,
        width=640,
        height=640,
        frames=81,
        fps=16,
        steps=4,
        cfg=1.0,  # 4-step with LoRA
        shift=5.0,  # Shift=5 for fast mode
        variant="14b_fast",
        checkpoint=None,
    ),
    "wan_quality": VideoSettings(
        model=VideoModel.WAN,
        width=1280,
        height=720,
        frames=81,
        fps=24,
        steps=30,
        cfg=3.5,
        shift=8.0,
        variant="14b",
        precision="fp8",
        checkpoint=None,
    ),
    # Mochi presets (Genmo - best text adherence, EXPERIMENTAL)
    "mochi": VideoSettings(
        model=VideoModel.MOCHI,
        width=848,
        height=480,
        frames=162,
        fps=30,
        steps=64,
        cfg=4.5,
        precision="bf16",
        checkpoint=None,
    ),
    "mochi_short": VideoSettings(
        model=VideoModel.MOCHI,
        width=848,
        height=480,
        frames=81,
        fps=30,
        steps=50,
        cfg=4.5,
        precision="fp8",
        checkpoint=None,
    ),
}


# =============================================================================
# VIDEO MODEL INFO
# =============================================================================


@dataclass
class VideoModelInfo:
    """Information about a video model."""

    id: str
    name: str
    description: str
    model: VideoModel
    text_to_video: bool = True
    image_to_video: bool = False
    min_vram_gb: int = 8
    estimated_time_seconds: int = 30
    max_frames: int = 32
    max_width: int = 768
    max_height: int = 768
    presets: list[str] = field(default_factory=list)
    # Custom node packs this family's workflows depend on. Empty == core only.
    # Every id here is a key of NODE_PACK_INFO.
    requires_packs: list[str] = field(default_factory=list)


VIDEO_MODEL_INFO: dict[str, VideoModelInfo] = {
    "animatediff": VideoModelInfo(
        id="animatediff",
        name="AnimateDiff",
        description="Animate any Stable Diffusion checkpoint. Great balance of quality and speed.",
        model=VideoModel.ANIMATEDIFF_V3,
        text_to_video=True,
        image_to_video=False,
        min_vram_gb=8,
        estimated_time_seconds=30,
        max_frames=32,
        max_width=768,
        max_height=768,
        presets=["quick", "standard", "quality", "cinematic", "portrait", "action"],
        requires_packs=[
            "comfyui-animatediff-evolved",
            "comfyui-frame-interpolation",  # only when interpolate=True
            "comfyui-videohelpersuite",
        ],
    ),
    "animatediff_lightning": VideoModelInfo(
        id="animatediff_lightning",
        name="AnimateDiff Lightning",
        description="Ultra-fast 4-step video generation. Lower quality but very quick.",
        model=VideoModel.ANIMATEDIFF_LIGHTNING,
        text_to_video=True,
        image_to_video=False,
        min_vram_gb=6,
        estimated_time_seconds=10,
        max_frames=24,
        max_width=768,
        max_height=768,
        presets=["quick"],
        requires_packs=["comfyui-animatediff-evolved", "comfyui-videohelpersuite"],
    ),
    "svd": VideoModelInfo(
        id="svd",
        name="Stable Video Diffusion",
        description="Generate video from a single image. High quality motion.",
        model=VideoModel.SVD_XT,
        text_to_video=False,
        image_to_video=True,
        min_vram_gb=12,
        estimated_time_seconds=60,
        max_frames=25,
        max_width=1024,
        max_height=576,
        presets=["svd_short", "svd_long"],
        requires_packs=["comfyui-videohelpersuite"],
    ),
    "cogvideo": VideoModelInfo(
        id="cogvideo",
        name="CogVideoX",
        description="High quality text-to-video with longer durations.",
        model=VideoModel.COGVIDEOX,
        text_to_video=True,
        image_to_video=False,
        min_vram_gb=16,
        estimated_time_seconds=120,
        max_frames=48,
        max_width=720,
        max_height=480,
        presets=["cogvideo"],
        requires_packs=["comfyui-cogvideoxwrapper", "comfyui-videohelpersuite"],
    ),
    "hunyuan": VideoModelInfo(
        id="hunyuan",
        name="Hunyuan Video",
        description="State-of-the-art text-to-video from Tencent. Best quality, needs 24GB+ VRAM.",
        model=VideoModel.HUNYUAN,
        text_to_video=True,
        image_to_video=False,
        min_vram_gb=24,
        estimated_time_seconds=180,
        max_frames=45,
        max_width=1280,
        max_height=720,
        presets=["hunyuan", "hunyuan_fast"],
        requires_packs=[
            "comfyui-frame-interpolation",  # only when interpolate=True
            "comfyui-videohelpersuite",
        ],
    ),
    # =========================================================================
    # v2.5.0: NEW VIDEO MODEL INFO
    # =========================================================================
    "hunyuan_15": VideoModelInfo(
        id="hunyuan_15",
        name="Hunyuan Video 1.5",
        description="Improved Hunyuan with new encoders (Qwen 2.5 VL + ByT5). 720p/1080p via SR.",
        model=VideoModel.HUNYUAN_15,
        text_to_video=True,
        image_to_video=True,
        min_vram_gb=14,
        estimated_time_seconds=120,
        max_frames=121,
        max_width=1920,
        max_height=1080,
        presets=[
            "hunyuan15_720p",
            "hunyuan15_quality",
            "hunyuan15_fast",
            "hunyuan15_1080p",
            "hunyuan15_i2v",
            "hunyuan15_i2v_fast",
        ],
        requires_packs=["comfyui-videohelpersuite"],
    ),
    "ltxv": VideoModelInfo(
        id="ltxv",
        name="LTX-Video 2",
        description="Lightricks fast video model. Up to 4K, excellent quality/speed ratio.",
        model=VideoModel.LTXV,
        text_to_video=True,
        image_to_video=True,
        min_vram_gb=12,
        estimated_time_seconds=30,
        max_frames=97,
        max_width=1920,
        max_height=1080,
        presets=["ltx_quick", "ltx_standard", "ltx_quality"],
        requires_packs=["comfyui-videohelpersuite"],
    ),
    "wan": VideoModelInfo(
        id="wan",
        name="Wan 2.1/2.2",
        description="Alibaba MoE video model. 1.3B efficient or 14B high-quality variants.",
        model=VideoModel.WAN,
        text_to_video=True,
        image_to_video=True,
        min_vram_gb=6,  # 1.3B variant
        estimated_time_seconds=90,
        max_frames=81,
        max_width=1280,
        max_height=720,
        presets=["wan_1.3b", "wan_14b", "wan_fast", "wan_quality"],
        requires_packs=["comfyui-videohelpersuite"],
    ),
    "mochi": VideoModelInfo(
        id="mochi",
        name="Mochi 1",
        description="Genmo 10B model. Best text adherence, 480p@30fps. Requires 12GB+ VRAM.",
        model=VideoModel.MOCHI,
        text_to_video=True,
        image_to_video=False,
        min_vram_gb=12,
        estimated_time_seconds=180,
        max_frames=162,
        max_width=848,
        max_height=480,
        presets=["mochi", "mochi_short"],
        requires_packs=["comfyui-videohelpersuite"],
    ),
}


# =============================================================================
# CUSTOM NODE PACK PROVENANCE
# =============================================================================
#
# The registry moved to node_packs.py in v3.1.0 when it became shared by all
# profile modules (image, video, 3D, audio, inference). Re-exported here so
# ``from comfy_headless.video import NODE_PACKS`` keeps working.

from .node_packs import (  # noqa: E402
    NODE_PACK_INFO,
    NODE_PACKS,
    NodePack,
    get_node_pack,
    required_node_packs,
)

# =============================================================================
# VIDEO WORKFLOW BUILDER
# =============================================================================


class VideoWorkflowBuilder:
    """
    Builds ComfyUI workflows for video generation.

    Each video model requires a different workflow structure.
    This builder abstracts those differences so users just specify
    what they want, not how to build it.
    """

    def __init__(self):
        self._builders = {
            # AnimateDiff family
            VideoModel.ANIMATEDIFF_V2: self._build_animatediff,
            VideoModel.ANIMATEDIFF_V3: self._build_animatediff,
            VideoModel.ANIMATEDIFF_LIGHTNING: self._build_animatediff_lightning,
            # Stable Video Diffusion
            VideoModel.SVD: self._build_svd,
            VideoModel.SVD_XT: self._build_svd,
            # CogVideoX
            VideoModel.COGVIDEOX: self._build_cogvideo,
            # Hunyuan (original)
            VideoModel.HUNYUAN: self._build_hunyuan,
            # v2.5.0: Hunyuan 1.5
            VideoModel.HUNYUAN_15: self._build_hunyuan_15,
            VideoModel.HUNYUAN_15_FAST: self._build_hunyuan_15,
            VideoModel.HUNYUAN_15_I2V: self._build_hunyuan_15,
            # v2.5.0: LTX-Video
            VideoModel.LTXV: self._build_ltxv,
            VideoModel.LTXV_I2V: self._build_ltxv,
            # v2.5.0: Wan
            VideoModel.WAN: self._build_wan,
            VideoModel.WAN_FAST: self._build_wan_fast,
            VideoModel.WAN_I2V: self._build_wan,
            # v2.5.0: Mochi
            VideoModel.MOCHI: self._build_mochi,
        }

    def build(
        self, prompt: str, negative: str, settings: VideoSettings, init_image: str | None = None
    ) -> dict[str, Any]:
        """
        Build a ComfyUI workflow for video generation.

        Args:
            prompt: Positive prompt
            negative: Negative prompt
            settings: Video settings
            init_image: Name of an image already present in ComfyUI's input
                folder, as returned by ``ComfyClient.upload_image()["ref"]``.
                Wired straight into a core ``LoadImage`` node.

        Returns:
            ComfyUI workflow JSON
        """
        builder = self._builders.get(settings.model)
        if not builder:
            raise ValueError(f"Unknown video model: {settings.model}")

        seed = settings.seed
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        workflow = builder(prompt, negative, settings, seed, init_image)
        if settings.output == "core":
            workflow = self._swap_to_core_output(workflow, settings)
        return workflow

    def _swap_to_core_output(
        self, workflow: dict[str, Any], settings: VideoSettings
    ) -> dict[str, Any]:
        """
        Replace the VHS_VideoCombine terminator with core CreateVideo ->
        SaveVideo, dropping the comfyui-videohelpersuite dependency.

        SaveVideo.codec is a COMFY_DYNAMICCOMBO_V3, so its inputs come from
        the presence-aware addressing layer ("auto" activates no sub-fields).
        """
        from .addressing import SAVE_VIDEO_CODEC

        vhs_id = next(
            (
                node_id
                for node_id, node in workflow.items()
                if isinstance(node, dict) and node.get("class_type") == "VHS_VideoCombine"
            ),
            None,
        )
        if vhs_id is None:
            return workflow

        vhs_inputs = workflow[vhs_id].get("inputs", {})
        images_link = vhs_inputs.get("images")
        frame_rate = vhs_inputs.get("frame_rate", settings.fps)
        filename_prefix = vhs_inputs.get("filename_prefix", "comfy_headless_video")

        numeric_ids = [int(i) for i in workflow if str(i).isdigit()]
        create_id = str(max(numeric_ids, default=0) + 1)

        del workflow[vhs_id]
        workflow[create_id] = {
            "class_type": "CreateVideo",
            "inputs": {"images": images_link, "fps": float(frame_rate)},
        }
        save_inputs: dict[str, Any] = {
            "video": [create_id, 0],
            "filename_prefix": filename_prefix,
            "format": "auto",
        }
        save_inputs.update(SAVE_VIDEO_CODEC.build("auto"))
        workflow[vhs_id] = {"class_type": "SaveVideo", "inputs": save_inputs}
        return workflow

    def _get_motion_scale(self, settings: VideoSettings) -> float:
        """Calculate motion scale from style and multiplier."""
        style_scales = {
            MotionStyle.STATIC: 0.5,
            MotionStyle.SUBTLE: 0.75,
            MotionStyle.MODERATE: 1.0,
            MotionStyle.DYNAMIC: 1.25,
            MotionStyle.EXTREME: 1.5,
        }
        base = style_scales.get(settings.motion_style, 1.0)
        return base * settings.motion_scale

    def _build_animatediff(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        _init_image: str | None = None,
    ) -> dict[str, Any]:
        """Build AnimateDiff v2/v3 workflow."""
        motion_scale = self._get_motion_scale(settings)
        motion_module = (
            "v3_sd15_mm.ckpt"
            if settings.model == VideoModel.ANIMATEDIFF_V3
            else "mm_sd_v15_v2.ckpt"
        )

        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": settings.checkpoint or "dreamshaper_8.safetensors"},
            },
            "2": {
                "class_type": "ADE_LoadAnimateDiffModel",
                "inputs": {"model_name": motion_module},
            },
            "3": {
                "class_type": "ADE_ApplyAnimateDiffModel",
                "inputs": {
                    "model": ["1", 0],
                    "motion_model": ["2", 0],
                    "scale_multival": motion_scale,
                },
            },
            "4": {
                "class_type": "ADE_EmptyLatentImageLarge",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "batch_size": settings.frames,
                },
            },
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}},
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["3", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": settings.steps,
                    "cfg": settings.cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                },
            },
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_video",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

        # Add RIFE interpolation if requested
        if settings.interpolate:
            workflow["10"] = {
                "class_type": "RIFE VFI",
                "inputs": {"frames": ["8", 0], "multiplier": 2, "ckpt_name": "rife49.pth"},
            }
            workflow["9"]["inputs"]["images"] = ["10", 0]
            workflow["9"]["inputs"]["frame_rate"] = settings.fps * 2

        return workflow

    def _build_animatediff_lightning(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        _init_image: str | None = None,
    ) -> dict[str, Any]:
        """Build AnimateDiff Lightning (4-step fast) workflow."""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": settings.checkpoint or "dreamshaper_8.safetensors"},
            },
            "2": {
                "class_type": "ADE_LoadAnimateDiffModel",
                "inputs": {"model_name": "animatediff_lightning_4step.safetensors"},
            },
            "3": {
                "class_type": "ADE_ApplyAnimateDiffModel",
                "inputs": {
                    "model": ["1", 0],
                    "motion_model": ["2", 0],
                },
            },
            "4": {
                "class_type": "ADE_EmptyLatentImageLarge",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "batch_size": settings.frames,
                },
            },
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}},
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["3", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": 4,  # Lightning is 4-step
                    "cfg": 2.0,  # Lower CFG for Lightning
                    "sampler_name": "euler",
                    "scheduler": "sgm_uniform",
                    "denoise": 1.0,
                },
            },
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_lightning",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

    def _build_svd(
        self,
        _prompt: str,
        _negative: str,
        settings: VideoSettings,
        seed: int,
        init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build Stable Video Diffusion workflow (img2vid).

        ``init_image`` is a ComfyUI-side image name (see the class docstring),
        not image data.
        """
        if not init_image:
            raise ValueError("SVD requires an init_image")

        model_name = (
            "svd_xt.safetensors" if settings.model == VideoModel.SVD_XT else "svd.safetensors"
        )
        num_frames = 25 if settings.model == VideoModel.SVD_XT else 14

        return {
            "1": {"class_type": "LoadImage", "inputs": {"image": init_image}},
            "2": {"class_type": "ImageOnlyCheckpointLoader", "inputs": {"ckpt_name": model_name}},
            "3": {
                "class_type": "SVD_img2vid_Conditioning",
                "inputs": {
                    "clip_vision": ["2", 1],
                    "init_image": ["1", 0],
                    "vae": ["2", 2],
                    "width": settings.width,
                    "height": settings.height,
                    "video_frames": num_frames,
                    "motion_bucket_id": 127,
                    "fps": 6,
                    "augmentation_level": 0.0,
                },
            },
            "4": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": ["3", 0],
                    "negative": ["3", 1],
                    "latent_image": ["3", 2],
                    "seed": seed,
                    "steps": settings.steps,
                    "cfg": 2.5,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "denoise": 1.0,
                },
            },
            "5": {"class_type": "VAEDecode", "inputs": {"samples": ["4", 0], "vae": ["2", 2]}},
            "6": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["5", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_svd",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

    def _build_cogvideo(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        _init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a CogVideoX workflow (ComfyUI-CogVideoXWrapper).

        CogVideoX has no native (core) ComfyUI path -- the loader, text
        encoder, sampler and decoder all live in the
        ``comfyui-cogvideoxwrapper`` custom node pack. Every non-core
        class_type emitted here is declared in :data:`NODE_PACKS`, so
        :meth:`ComfyClient.check_workflow_dependencies` can report
        "install comfyui-cogvideoxwrapper" instead of letting ``POST /prompt``
        reject the graph with an opaque validation error.

        The 5B checkpoint is loaded in bf16 as the pack itself recommends
        (2B wants fp16, 5B wants bf16).
        """
        return {
            # COGVIDEOMODEL + VAE from a single (down)loader node
            "1": {
                "class_type": "DownloadAndLoadCogVideoModel",
                "inputs": {
                    "model": "THUDM/CogVideoX-5b",
                    "precision": "bf16",
                    "quantization": "disabled",
                    "enable_sequential_cpu_offload": False,
                    "attention_mode": "sdpa",
                    "load_device": "main_device",
                },
            },
            # T5-XXL text encoder (core loader, cogvideox tokenizer padding)
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "t5xxl_fp16.safetensors",
                    "type": "cogvideox",
                    "device": "default",
                },
            },
            # Positive: CogVideoTextEncode returns (CONDITIONING, CLIP)
            "3": {
                "class_type": "CogVideoTextEncode",
                "inputs": {
                    "clip": ["2", 0],
                    "prompt": prompt,
                    "strength": 1.0,
                    "force_offload": True,
                },
            },
            # Negative: reuse the CLIP handed back by the positive encode
            "4": {
                "class_type": "CogVideoTextEncode",
                "inputs": {
                    "clip": ["3", 1],
                    "prompt": negative,
                    "strength": 1.0,
                    "force_offload": True,
                },
            },
            "5": {
                "class_type": "CogVideoSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "num_frames": settings.frames,
                    "steps": settings.steps,
                    "cfg": settings.cfg,
                    "seed": seed,
                    "scheduler": "CogVideoXDDIM",
                },
            },
            "6": {
                "class_type": "CogVideoDecode",
                "inputs": {
                    "vae": ["1", 1],
                    "samples": ["5", 0],
                    "enable_vae_tiling": True,
                    "tile_sample_min_height": settings.height // 2,
                    "tile_sample_min_width": settings.width // 2,
                    "tile_overlap_factor_height": 0.2,
                    "tile_overlap_factor_width": 0.2,
                    "auto_tile_size": True,
                },
            },
            "7": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["6", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_cogvideo",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }

    def _build_hunyuan(
        self,
        prompt: str,
        _negative: str,
        settings: VideoSettings,
        seed: int,
        _init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a HunyuanVideo 1.0 text-to-video workflow (native core path).

        Wiring verified against the official ``hunyuan_video_text_to_video``
        workflow template. Notes that are easy to get wrong:

        * The text encoders load through ``DualCLIPLoader`` with
          ``type="hunyuan_video"`` (clip_l + llava_llama3). ``CLIPLoader``
          has no ``hunyuan_video`` type -- only ``hunyuan_image``.
        * The t2v checkpoint is guidance-distilled, so it is steered by
          ``FluxGuidance`` -> ``BasicGuider`` (embedded guidance) and takes
          no negative prompt. ``negative`` is accepted for API symmetry with
          the other builders and is intentionally unused.
        * Decoding uses the tiled VAE decoder, matching the template default,
          because the full-frame decode does not fit on most cards.
        """
        shift = settings.shift or 7.0
        guidance = settings.cfg if settings.cfg and settings.cfg > 0 else 6.0
        weight_dtype = "fp8_e4m3fn" if settings.precision.startswith("fp8") else "default"

        workflow = {
            # Diffusion model
            "1": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "hunyuan_video_t2v_720p_bf16.safetensors",
                    "weight_dtype": weight_dtype,
                },
            },
            # Text encoders (clip_l + llava_llama3)
            "2": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "clip_l.safetensors",
                    "clip_name2": "llava_llama3_fp8_scaled.safetensors",
                    "type": "hunyuan_video",
                    "device": "default",
                },
            },
            # VAE
            "3": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": "hunyuan_video_vae_bf16.safetensors"},
            },
            # Prompt
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
            # Embedded guidance (this checkpoint is guidance-distilled)
            "5": {
                "class_type": "FluxGuidance",
                "inputs": {"conditioning": ["4", 0], "guidance": guidance},
            },
            # Model sampling shift
            "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": shift}},
            # Guider (no negative -- distilled model)
            "7": {
                "class_type": "BasicGuider",
                "inputs": {"model": ["6", 0], "conditioning": ["5", 0]},
            },
            "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
            "9": {
                "class_type": "BasicScheduler",
                "inputs": {
                    "model": ["1", 0],
                    "scheduler": "simple",
                    "steps": settings.steps,
                    "denoise": 1.0,
                },
            },
            "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
            "11": {
                "class_type": "EmptyHunyuanLatentVideo",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            },
            "12": {
                "class_type": "SamplerCustomAdvanced",
                "inputs": {
                    "noise": ["10", 0],
                    "guider": ["7", 0],
                    "sampler": ["8", 0],
                    "sigmas": ["9", 0],
                    "latent_image": ["11", 0],
                },
            },
            "13": {
                "class_type": "VAEDecodeTiled",
                "inputs": {
                    "samples": ["12", 0],
                    "vae": ["3", 0],
                    "tile_size": 256,
                    "overlap": 64,
                    "temporal_size": 64,
                    "temporal_overlap": 8,
                },
            },
            "14": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["13", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_hunyuan",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }

        # Add RIFE interpolation if requested (comfyui-frame-interpolation)
        if settings.interpolate:
            workflow["15"] = {
                "class_type": "RIFE VFI",
                "inputs": {
                    "ckpt_name": "rife49.pth",
                    "frames": ["13", 0],
                    "clear_cache_after_n_frames": 10,
                    "multiplier": 2,
                    "fast_mode": True,
                    "ensemble": True,
                    "scale_factor": 1,
                    "dtype": "float32",
                    "torch_compile": False,
                    "batch_size": 1,
                },
            }
            workflow["14"]["inputs"]["images"] = ["15", 0]
            workflow["14"]["inputs"]["frame_rate"] = settings.fps * 2

        return workflow

    # =========================================================================
    # v2.5.0: NEW VIDEO MODEL BUILDERS
    # =========================================================================

    def _build_hunyuan_15(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build Hunyuan Video 1.5 workflow (t2v and i2v).

        Uses new architecture:
        - DualCLIPLoader (Qwen 2.5 VL + ByT5), type="hunyuan_video_15"
        - SamplerCustomAdvanced with CFGGuider
        - Optional latent upsample for 1080p

        i2v (v3.1.0 repair -- HUNYUAN_15_I2V previously ignored init_image
        and silently built a t2v graph): the plain-text conditioning feeds
        core ``HunyuanVideo15ImageToVideo`` together with the VAE and the
        start image; its CONDITIONING/CONDITIONING/LATENT outputs replace
        the empty latent and the raw text conditionings. Its optional
        clip_vision_output input is left unwired (no CLIP-Vision leg in the
        minimal official shape).

        Checkpoint naming is resolution-specific. t2v cfg-distilled exists
        at 480p only; i2v cfg-distilled exists at both 480p and 720p
        (verified in the live catalog 2026-08-21).
        """
        i2v = settings.model == VideoModel.HUNYUAN_15_I2V or init_image is not None
        if i2v and not init_image:
            raise ValueError("hunyuan_15_i2v requires an init_image (upload first, pass its 'ref')")

        shift = settings.shift or 9.0  # Default shift for 720p T2V

        # 1080p is produced by upscaling a 720p render, not by sampling at 1080p.
        if settings.upscale:
            base_width, base_height = 1280, 720
        else:
            base_width, base_height = settings.width, settings.height

        res_tag = "720p" if base_height >= 720 else "480p"
        mode_tag = "i2v" if i2v else "t2v"

        # Determine model paths based on variant
        if settings.variant == "distilled":
            if i2v:
                # i2v has cfg-distilled releases at BOTH 480p and 720p.
                suffix = "fp8_scaled" if settings.precision.startswith("fp8") else "fp16"
                unet_name = f"hunyuanvideo1.5_{res_tag}_i2v_cfg_distilled_{suffix}.safetensors"
            else:
                # Only the 480p t2v checkpoint has a cfg-distilled release.
                unet_name = (
                    "hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors"
                    if settings.precision.startswith("fp8")
                    else "hunyuanvideo1.5_480p_t2v_cfg_distilled_fp16.safetensors"
                )
            cfg_value = 1.0  # Distilled uses CFG=1
        else:
            unet_name = f"hunyuanvideo1.5_{res_tag}_{mode_tag}_fp16.safetensors"
            cfg_value = settings.cfg

        workflow = {
            # DualCLIPLoader for text encoders
            "1": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                    "clip_name2": "byt5_small_glyphxl_fp16.safetensors",
                    "type": "hunyuan_video_15",
                    "device": "default",
                },
            },
            # VAE
            "2": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": "hunyuanvideo15_vae_fp16.safetensors"},
            },
            # Diffusion model
            "3": {
                "class_type": "UNETLoader",
                "inputs": {"unet_name": unet_name, "weight_dtype": "default"},
            },
            # Latent
            "4": {
                "class_type": "EmptyHunyuanVideo15Latent",
                "inputs": {
                    "width": base_width,
                    "height": base_height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            },
            # Text encoding
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 0]}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 0]}},
            # Model sampling with shift
            "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": shift}},
            # CFG Guider
            "8": {
                "class_type": "CFGGuider",
                "inputs": {
                    "model": ["7", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "cfg": cfg_value,
                },
            },
            # Scheduler
            "9": {
                "class_type": "BasicScheduler",
                "inputs": {
                    "model": ["3", 0],
                    "scheduler": "simple",
                    "steps": settings.steps,
                    "denoise": 1.0,
                },
            },
            # Noise
            "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
            # Sampler
            "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
            # Custom sampler
            "12": {
                "class_type": "SamplerCustomAdvanced",
                "inputs": {
                    "noise": ["10", 0],
                    "guider": ["8", 0],
                    "sampler": ["11", 0],
                    "sigmas": ["9", 0],
                    "latent_image": ["4", 0],
                },
            },
            # Decode
            "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["2", 0]}},
            "14": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["13", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_hunyuan15",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }

        # i2v: replace the empty latent with HunyuanVideo15ImageToVideo,
        # which encodes the start image through the VAE and hands back
        # (positive, negative, latent) for the guider and sampler.
        if i2v:
            workflow["17"] = {"class_type": "LoadImage", "inputs": {"image": init_image}}
            workflow["4"] = {
                "class_type": "HunyuanVideo15ImageToVideo",
                "inputs": {
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "vae": ["2", 0],
                    "width": base_width,
                    "height": base_height,
                    "length": settings.frames,
                    "batch_size": 1,
                    "start_image": ["17", 0],
                },
            }
            workflow["8"]["inputs"]["positive"] = ["4", 0]
            workflow["8"]["inputs"]["negative"] = ["4", 1]
            workflow["12"]["inputs"]["latent_image"] = ["4", 2]

        # Latent upsample to the requested output size (1080p presets).
        #
        # NOTE: this is the upsample only. The official template follows it
        # with a HunyuanVideo15SuperResolution conditioning pass and a second
        # sampler using the dedicated SR checkpoint; that refinement pass is
        # not emitted here, so the 1080p output is a clean upscale rather than
        # a re-detailed render.
        if settings.upscale:
            upsampler = (
                "hunyuanvideo15_latent_upsampler_1080p.safetensors"
                if settings.height >= 1080
                else "hunyuanvideo15_latent_upsampler_720p.safetensors"
            )
            workflow["15"] = {
                "class_type": "LatentUpscaleModelLoader",
                "inputs": {"model_name": upsampler},
            }
            workflow["16"] = {
                "class_type": "HunyuanVideo15LatentUpscaleWithModel",
                "inputs": {
                    "model": ["15", 0],
                    "samples": ["12", 0],
                    "upscale_method": "bilinear",
                    "width": settings.width,
                    "height": settings.height,
                    "crop": "disabled",
                },
            }
            # Update decode to use upscaled latent
            workflow["13"]["inputs"]["samples"] = ["16", 0]

        return workflow

    def _build_ltxv(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build LTX-Video 2 workflow.

        Uses:
        - SamplerCustom with LTXVScheduler
        - CLIPLoader type="ltxv" for T5 encoder
        - Low CFG (typically 3.0)
        """
        workflow = {
            # Checkpoint
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "ltx-video-2b-v0.9.5.safetensors"},
            },
            # T5 text encoder
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "t5xxl_fp16.safetensors",
                    "type": "ltxv",
                    "device": "default",
                },
            },
            # Latent
            "3": {
                "class_type": "EmptyLTXVLatentVideo",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            },
            # Text encoding
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
            # Conditioning with frame rate
            "6": {
                "class_type": "LTXVConditioning",
                "inputs": {"positive": ["4", 0], "negative": ["5", 0], "frame_rate": settings.fps},
            },
            # Scheduler
            "7": {
                "class_type": "LTXVScheduler",
                "inputs": {
                    "latent": ["3", 0],
                    "steps": settings.steps,
                    "max_shift": 2.05,
                    "base_shift": 0.95,
                    "stretch": True,
                    "terminal": 0.1,
                },
            },
            # Sampler select
            "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
            # Custom sampler
            "9": {
                "class_type": "SamplerCustom",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["6", 0],
                    "negative": ["6", 1],
                    "sampler": ["8", 0],
                    "sigmas": ["7", 0],
                    "latent_image": ["3", 0],
                    "add_noise": True,
                    "noise_seed": seed,
                    "cfg": settings.cfg,  # Typically 3.0 for LTXV
                },
            },
            # Decode
            "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["1", 2]}},
            # Output
            "11": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["10", 0],
                    "frame_rate": settings.fps,
                    "filename_prefix": "comfy_headless_ltxv",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

        # Image-to-video variant
        if init_image:
            workflow["2.5"] = {
                "class_type": "LoadImage",
                "inputs": {"image": init_image},
            }
            workflow["3"] = {
                "class_type": "LTXVImgToVideo",
                "inputs": {
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "vae": ["1", 2],
                    "image": ["2.5", 0],
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                    "image_noise_scale": 0.15,
                },
            }
            # Update conditioning to use I2V outputs
            workflow["6"]["inputs"]["positive"] = ["3", 0]
            workflow["6"]["inputs"]["negative"] = ["3", 1]
            workflow["7"]["inputs"]["latent"] = ["3", 2]
            workflow["9"]["inputs"]["latent_image"] = ["3", 2]

        return workflow

    def _build_wan(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build Wan 2.1/2.2 workflow.

        Uses:
        - UNETLoader for diffusion model
        - CLIPLoader type="wan" for UMT5-XXL
        - ModelSamplingSD3 with shift=8 (T2V)
        """
        # Model selection based on variant
        model_map = {
            "1.3b": "wan2.1_t2v_1.3B_fp16.safetensors",
            "14b": "wan2.2_t2v_14B_fp8_scaled.safetensors",
        }
        unet_name = model_map.get(settings.variant, model_map["1.3b"])
        shift = settings.shift or 8.0

        workflow = {
            # UNET
            "1": {
                "class_type": "UNETLoader",
                "inputs": {"unet_name": unet_name, "weight_dtype": "default"},
            },
            # Text encoder
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "wan",
                    "device": "default",
                },
            },
            # VAE
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
            # Latent (shared with Hunyuan)
            "4": {
                "class_type": "EmptyHunyuanLatentVideo",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            },
            # Text encoding
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
            # Model sampling with shift
            "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": shift}},
            # KSampler
            "8": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["7", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": settings.steps,
                    "cfg": settings.cfg,
                    "sampler_name": "uni_pc",
                    "scheduler": "simple",
                    "denoise": 1.0,
                },
            },
            # Decode
            "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
            # Output
            "10": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["9", 0],
                    "frame_rate": settings.fps,
                    "filename_prefix": "comfy_headless_wan",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

        # Image-to-video extension
        if init_image:
            workflow["11"] = {
                "class_type": "LoadImage",
                "inputs": {"image": init_image},
            }
            workflow["12"] = {
                "class_type": "CLIPVisionLoader",
                "inputs": {"clip_name": "clip_vision_h.safetensors"},
            }
            workflow["13"] = {
                "class_type": "CLIPVisionEncode",
                "inputs": {"clip_vision": ["12", 0], "image": ["11", 0], "crop": "none"},
            }
            workflow["14"] = {
                "class_type": "WanImageToVideo",
                "inputs": {
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "vae": ["3", 0],
                    "clip_vision_output": ["13", 0],
                    "start_image": ["11", 0],
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            }
            # Reconnect sampler
            workflow["8"]["inputs"]["positive"] = ["14", 0]
            workflow["8"]["inputs"]["negative"] = ["14", 1]
            workflow["8"]["inputs"]["latent_image"] = ["14", 2]

        return workflow

    def _build_wan_fast(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        _init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build Wan 2.2 4-step fast workflow.

        Uses dual model approach:
        - High noise model (steps 0-2)
        - Low noise model (steps 2-4)
        - LoRA for each model
        """
        shift = settings.shift or 5.0  # Shift=5 for fast mode

        workflow = {
            # High noise model
            "1": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                    "weight_dtype": "default",
                },
            },
            # Low noise model
            "2": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
                    "weight_dtype": "default",
                },
            },
            # LoRA for high noise
            "3": {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {
                    "model": ["1", 0],
                    "lora_name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                    "strength_model": 1.0,
                },
            },
            # LoRA for low noise
            "4": {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {
                    "model": ["2", 0],
                    "lora_name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors",
                    "strength_model": 1.0,
                },
            },
            # Text encoder
            "5": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "wan",
                    "device": "default",
                },
            },
            # VAE
            "6": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
            # Latent
            "7": {
                "class_type": "EmptyHunyuanLatentVideo",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            },
            # Text encoding
            "8": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["5", 0]}},
            "9": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["5", 0]}},
            # Model sampling for high noise
            "10": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": shift}},
            # Model sampling for low noise
            "11": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": shift}},
            # First sampler (high noise, steps 0-2)
            "12": {
                "class_type": "KSamplerAdvanced",
                "inputs": {
                    "model": ["10", 0],
                    "positive": ["8", 0],
                    "negative": ["9", 0],
                    "latent_image": ["7", 0],
                    "noise_seed": seed,
                    "steps": 4,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 0,
                    "end_at_step": 2,
                    "add_noise": "enable",
                    "return_with_leftover_noise": "enable",
                },
            },
            # Second sampler (low noise, steps 2-4)
            "13": {
                "class_type": "KSamplerAdvanced",
                "inputs": {
                    "model": ["11", 0],
                    "positive": ["8", 0],
                    "negative": ["9", 0],
                    "latent_image": ["12", 0],
                    "noise_seed": seed,
                    "steps": 4,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 2,
                    "end_at_step": 4,
                    "add_noise": "disable",
                    "return_with_leftover_noise": "disable",
                },
            },
            # Decode
            "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["6", 0]}},
            # Output
            "15": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["14", 0],
                    "frame_rate": settings.fps,
                    "filename_prefix": "comfy_headless_wan_fast",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

        return workflow

    def _build_mochi(
        self,
        prompt: str,
        negative: str,
        settings: VideoSettings,
        seed: int,
        _init_image: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a Mochi 1 workflow (native core path).

        Mochi ships as a split repackage, so the pieces load separately:

        * The DiT lives in ``models/diffusion_models`` -> ``UNETLoader``.
          (The model catalog's ``recommended.loader`` field says
          ``CheckpointLoaderSimple``, which contradicts the directory. The
          directory wins: no mochi file appears in ``CheckpointLoaderSimple``'s
          option list, and both appear in ``UNETLoader``'s.)
        * The VAE lives in ``models/vae`` -> ``VAELoader``.
        * The text encoder is t5xxl through ``CLIPLoader`` with ``type="mochi"``.

        From there it is the generic core sampler: ``EmptyMochiLatentVideo``
        -> ``KSampler`` -> ``VAEDecode``.
        """
        unet_name = (
            "mochi_preview_bf16.safetensors"
            if settings.precision == "bf16"
            else "mochi_preview_fp8_scaled.safetensors"
        )

        return {
            # Diffusion model (DiT)
            "1": {
                "class_type": "UNETLoader",
                "inputs": {"unet_name": unet_name, "weight_dtype": "default"},
            },
            # T5-XXL text encoder
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "t5xxl_fp16.safetensors",
                    "type": "mochi",
                    "device": "default",
                },
            },
            # VAE
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "mochi_vae.safetensors"}},
            # Prompts
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
            # Latent
            "6": {
                "class_type": "EmptyMochiLatentVideo",
                "inputs": {
                    "width": settings.width,
                    "height": settings.height,
                    "length": settings.frames,
                    "batch_size": 1,
                },
            },
            # Sampler
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "seed": seed,
                    "steps": settings.steps,
                    "cfg": settings.cfg,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "latent_image": ["6", 0],
                    "denoise": 1.0,
                },
            },
            # Decode
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
            # Output
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": settings.fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_mochi",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_builder: VideoWorkflowBuilder | None = None


def get_video_builder() -> VideoWorkflowBuilder:
    """Get singleton video workflow builder."""
    global _builder
    if _builder is None:
        _builder = VideoWorkflowBuilder()
    return _builder


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def build_video_workflow(
    prompt: str,
    negative: str = "ugly, blurry, low quality",
    preset: str = "standard",
    init_image: str | None = None,
    **overrides,
) -> dict[str, Any]:
    """
    Build a video workflow with preset settings.

    Simple usage:
        workflow = build_video_workflow(
            prompt="a cat walking",
            preset="quality"
        )
    """
    settings = VIDEO_PRESETS.get(preset, VIDEO_PRESETS["standard"])

    # Apply any overrides
    if overrides:
        settings_dict = settings.to_dict()
        settings_dict.update(overrides)
        settings = VideoSettings(
            model=VideoModel(settings_dict.get("model", settings.model.value)),
            width=settings_dict.get("width", settings.width),
            height=settings_dict.get("height", settings.height),
            frames=settings_dict.get("frames", settings.frames),
            fps=settings_dict.get("fps", settings.fps),
            steps=settings_dict.get("steps", settings.steps),
            cfg=settings_dict.get("cfg", settings.cfg),
            seed=settings_dict.get("seed", settings.seed),
            motion_scale=settings_dict.get("motion_scale", settings.motion_scale),
            motion_style=MotionStyle(
                settings_dict.get("motion_style", settings.motion_style.value)
            ),
            checkpoint=settings_dict.get("checkpoint", settings.checkpoint),
            format=VideoFormat(settings_dict.get("format", settings.format.value)),
            interpolate=settings_dict.get("interpolate", settings.interpolate),
            # v3.1.0 fix: these four were dropped by the override path, so
            # e.g. preset="hunyuan15_fast" + any override silently lost
            # variant="distilled" and built the wrong graph.
            variant=settings_dict.get("variant", settings.variant),
            upscale=settings_dict.get("upscale", settings.upscale),
            shift=settings_dict.get("shift", settings.shift),
            precision=settings_dict.get("precision", settings.precision),
            output=settings_dict.get("output", settings.output),
        )

    builder = get_video_builder()
    return builder.build(prompt, negative, settings, init_image)


def get_video_preset(name: str) -> VideoSettings | None:
    """Get a video preset by name."""
    return VIDEO_PRESETS.get(name)


def list_video_presets() -> list[str]:
    """List available video preset names."""
    return list(VIDEO_PRESETS.keys())


def list_video_models() -> dict[str, VideoModelInfo]:
    """List available video models with their info."""
    return VIDEO_MODEL_INFO.copy()


def get_recommended_preset(
    intent: str = "general", quality: str = "standard", vram_gb: float = 8.0
) -> str:
    """
    Get recommended video preset based on intent and hardware.

    v2.5.0: Updated with new models (LTX, Wan, Hunyuan 1.5)

    Makes it easy for users - they say what they want, we pick the best preset.
    """
    # v2.5.0: Updated VRAM tiers with new models
    if vram_gb < 8:
        # Very low VRAM: AnimateDiff Lightning or Wan 1.3B
        if quality == "fast":
            return "quick"  # Lightning is fastest
        return "wan_1.3b"  # Wan 1.3B is efficient and high quality

    elif vram_gb < 12:
        # 8-12GB: Wan 1.3B, LTX quick, AnimateDiff
        candidates = ["wan_1.3b", "ltx_quick", "quick", "standard", "portrait", "action"]

    elif vram_gb < 16:
        # 12-16GB: LTX standard, Wan 14B, Mochi short
        candidates = [
            "ltx_standard",
            "ltx_quality",
            "wan_14b",
            "mochi_short",
            "standard",
            "quality",
            "cinematic",
            "portrait",
            "action",
        ]

    elif vram_gb < 24:
        # 16-24GB: Hunyuan 1.5 720p, LTX quality, Wan quality
        candidates = [
            "hunyuan15_720p",
            "hunyuan15_fast",
            "ltx_quality",
            "wan_quality",
            "wan_fast",
            "quality",
            "cinematic",
            "svd_short",
            "svd_long",
            "cogvideo",
        ]

    else:
        # 24GB+: All presets available including Hunyuan 1.5 quality and Mochi
        candidates = list(VIDEO_PRESETS.keys())

    # Quality preference
    if quality == "fast":
        # Fastest options per tier
        fast_order = ["quick", "wan_fast", "hunyuan15_fast", "ltx_quick", "wan_1.3b"]
        for preset in fast_order:
            if preset in candidates:
                return preset
        return candidates[0]

    elif quality == "best":
        # Best quality options
        best_order = [
            "hunyuan15_quality",
            "mochi",
            "hunyuan15_720p",
            "wan_quality",
            "ltx_quality",
            "hunyuan",
            "quality",
            "cinematic",
        ]
        for preset in best_order:
            if preset in candidates:
                return preset

    # Intent-based selection
    if intent in ["portrait", "character", "person"]:
        if "portrait" in candidates:
            return "portrait"
    elif intent in ["landscape", "scene", "environment", "cinematic", "film"]:
        # Prefer newer high-quality models for cinematic
        cinematic_order = ["hunyuan15_720p", "ltx_quality", "cinematic"]
        for preset in cinematic_order:
            if preset in candidates:
                return preset
    elif intent in ["action", "dynamic", "motion"]:
        # Action prefers high frame rate
        if "action" in candidates:
            return "action"
        if "ltx_standard" in candidates:
            return "ltx_standard"  # LTX has good motion

    # Default: prefer newer models
    default_order = ["ltx_standard", "wan_1.3b", "standard"]
    for preset in default_order:
        if preset in candidates:
            return preset

    return candidates[0] if candidates else "standard"
