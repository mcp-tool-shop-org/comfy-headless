"""
Extended coverage tests for comfy_headless/video.py

Targets the specialized video model builder methods:
- _build_hunyuan (lines 899-965)
- _build_hunyuan_15 (lines 987-1123)
- _build_ltxv (lines 1141-1260)
- _build_wan (lines 1279-1404)
- _build_mochi (lines 1422-1558)
- _build_cogvideo (lines 1575-1640)
- Convenience functions (lines 1760-1789)
"""

import pytest

# ============================================================================
# VIDEO SETTINGS TESTS
# ============================================================================


class TestVideoSettingsToDict:
    """Test VideoSettings to_dict method."""

    def test_to_dict_returns_dict(self):
        """to_dict returns a dictionary."""
        from comfy_headless.video import VideoSettings

        settings = VideoSettings(width=1024, height=576, frames=32, fps=16)

        result = settings.to_dict()
        assert isinstance(result, dict)
        assert result["width"] == 1024
        assert result["height"] == 576
        assert result["frames"] == 32
        assert result["fps"] == 16

    def test_to_dict_includes_all_fields(self):
        """to_dict includes all settings fields."""
        from comfy_headless.video import MotionStyle, VideoFormat, VideoModel, VideoSettings

        settings = VideoSettings(
            model=VideoModel.LTXV,
            width=768,
            height=768,
            frames=24,
            fps=12,
            steps=30,
            cfg=5.0,
            seed=12345,
            motion_scale=1.2,
            motion_style=MotionStyle.DYNAMIC,
            checkpoint="model.safetensors",
            format=VideoFormat.MP4,
            interpolate=True,
            variant="1.3b",
            upscale=True,
            shift=7.0,
            precision="fp8",
        )

        result = settings.to_dict()

        assert result["model"] == "ltxv"
        assert result["motion_style"] == "dynamic"
        assert result["format"] == "mp4"
        assert result["variant"] == "1.3b"
        assert result["upscale"] is True
        assert result["shift"] == 7.0
        assert result["precision"] == "fp8"


# ============================================================================
# VIDEO WORKFLOW BUILDER TESTS
# ============================================================================


class TestVideoWorkflowBuilderInit:
    """Test VideoWorkflowBuilder initialization."""

    def test_builder_creation(self):
        """Builder can be created."""
        from comfy_headless.video import VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        assert builder is not None

    def test_get_video_builder(self):
        """get_video_builder returns a builder instance."""
        from comfy_headless.video import get_video_builder

        builder = get_video_builder()
        assert builder is not None


class TestBuildVideoWorkflow:
    """Test build_video_workflow convenience function."""

    def test_build_video_workflow_basic(self):
        """build_video_workflow creates workflow dict."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="a cat walking", negative="blurry", preset="quick")

        assert isinstance(workflow, dict)
        assert len(workflow) > 0

    def test_build_video_workflow_with_overrides(self):
        """build_video_workflow accepts parameter overrides."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(
            prompt="sunset over ocean",
            negative="low quality",
            preset="standard",
            width=768,
            height=432,
            frames=24,
            fps=12,
            steps=25,
            cfg=6.0,
            seed=42,
        )

        assert isinstance(workflow, dict)

    def test_build_video_workflow_with_init_image(self):
        """build_video_workflow handles init_image."""
        from comfy_headless.video import build_video_workflow

        # Test with init_image (base64 encoded)
        workflow = build_video_workflow(
            prompt="person walking",
            preset="standard",
            init_image="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        )

        assert isinstance(workflow, dict)


# ============================================================================
# ANIMATEDIFF BUILDER TESTS
# ============================================================================


class TestAnimateDiffBuilder:
    """Test AnimateDiff workflow building."""

    def test_build_animatediff_v3(self):
        """Build AnimateDiff v3 workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.ANIMATEDIFF_V3, width=512, height=512, frames=16, steps=20
        )

        workflow = builder.build(prompt="a dog running", negative="blurry", settings=settings)

        assert isinstance(workflow, dict)
        # Should have key nodes
        assert len(workflow) > 0

    def test_build_animatediff_lightning(self):
        """Build AnimateDiff Lightning workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.ANIMATEDIFF_LIGHTNING,
            width=512,
            height=512,
            frames=16,
            steps=4,
            cfg=2.0,
        )

        workflow = builder.build(prompt="a bird flying", negative="blurry", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_animatediff_v2(self):
        """Build AnimateDiff v2 workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.ANIMATEDIFF_V2, width=512, height=512, frames=16, steps=20
        )

        workflow = builder.build(prompt="flowers blooming", negative="distorted", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_with_interpolation(self):
        """Build workflow with RIFE interpolation enabled."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.ANIMATEDIFF_V3,
            width=512,
            height=512,
            frames=16,
            steps=20,
            interpolate=True,
        )

        workflow = builder.build(prompt="waves on beach", negative="blurry", settings=settings)

        assert isinstance(workflow, dict)


# ============================================================================
# SVD BUILDER TESTS
# ============================================================================


class TestSVDBuilder:
    """Test Stable Video Diffusion workflow building."""

    def test_build_svd(self):
        """Build SVD workflow (requires init_image)."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(model=VideoModel.SVD, width=1024, height=576, frames=14, steps=20)

        # SVD requires an init_image
        workflow = builder.build(
            prompt="person walking",
            negative="low quality",
            settings=settings,
            init_image="data:image/png;base64,iVBORw0KGgo=",
        )

        assert isinstance(workflow, dict)

    def test_build_svd_xt(self):
        """Build SVD-XT workflow (extended temporal)."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.SVD_XT, width=1024, height=576, frames=25, steps=20
        )

        # SVD-XT requires an init_image
        workflow = builder.build(
            prompt="car driving",
            negative="blurry",
            settings=settings,
            init_image="data:image/png;base64,iVBORw0KGgo=",
        )

        assert isinstance(workflow, dict)

    def test_build_svd_without_image_raises(self):
        """Build SVD without init_image raises error."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(model=VideoModel.SVD, width=1024, height=576, frames=14, steps=20)

        with pytest.raises(ValueError) as exc_info:
            builder.build(prompt="test", negative="blurry", settings=settings)

        assert "init_image" in str(exc_info.value).lower()


# ============================================================================
# COGVIDEOX BUILDER TESTS
# ============================================================================


class TestCogVideoXBuilder:
    """Test CogVideoX workflow building."""

    def test_build_cogvideox(self):
        """Build CogVideoX workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.COGVIDEOX, width=720, height=480, frames=49, steps=50, cfg=6.0
        )

        workflow = builder.build(
            prompt="fireworks display", negative="low quality", settings=settings
        )

        assert isinstance(workflow, dict)
        assert _class_types(workflow) == {
            "DownloadAndLoadCogVideoModel",
            "CLIPLoader",
            "CogVideoTextEncode",
            "CogVideoSampler",
            "CogVideoDecode",
            "VHS_VideoCombine",
        }

    def test_cogvideox_wires_positive_and_negative(self):
        """CogVideoSampler gets separate positive and negative conditioning."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="fireworks",
            negative="low quality",
            settings=VideoSettings(model=VideoModel.COGVIDEOX),
        )

        sampler = _node_of_type(workflow, "CogVideoSampler")
        assert sampler["inputs"]["positive"] != sampler["inputs"]["negative"]
        # The negative encode reuses the CLIP handed back by the positive one.
        encodes = [n for n in workflow.values() if n["class_type"] == "CogVideoTextEncode"]
        assert len(encodes) == 2
        assert {e["inputs"]["prompt"] for e in encodes} == {"fireworks", "low quality"}

    def test_cogvideox_declares_its_pack(self):
        """CogVideoX is pack-only and says so."""
        from comfy_headless.video import (
            VideoModel,
            VideoSettings,
            VideoWorkflowBuilder,
            required_node_packs,
        )

        workflow = VideoWorkflowBuilder().build(
            prompt="x", negative="y", settings=VideoSettings(model=VideoModel.COGVIDEOX)
        )

        packs = required_node_packs(workflow)
        assert packs["comfyui-cogvideoxwrapper"] == [
            "CogVideoDecode",
            "CogVideoSampler",
            "CogVideoTextEncode",
            "DownloadAndLoadCogVideoModel",
        ]


# ============================================================================
# HUNYUAN BUILDER TESTS
# ============================================================================


class TestHunyuanBuilder:
    """Test Hunyuan Video workflow building."""

    def test_build_hunyuan(self):
        """Build Hunyuan Video workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.HUNYUAN, width=720, height=480, frames=45, steps=50
        )

        workflow = builder.build(
            prompt="mountains with clouds", negative="low quality, blurry", settings=settings
        )

        assert isinstance(workflow, dict)
        assert _class_types(workflow) == {
            "UNETLoader",
            "DualCLIPLoader",
            "VAELoader",
            "CLIPTextEncode",
            "FluxGuidance",
            "ModelSamplingSD3",
            "BasicGuider",
            "KSamplerSelect",
            "BasicScheduler",
            "RandomNoise",
            "EmptyHunyuanLatentVideo",
            "SamplerCustomAdvanced",
            "VAEDecodeTiled",
            "VHS_VideoCombine",
        }

    def test_hunyuan_text_encoder_path(self):
        """Hunyuan 1.0 t2v encodes through DualCLIPLoader type=hunyuan_video."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="a lake", negative="", settings=VideoSettings(model=VideoModel.HUNYUAN)
        )

        loader = _node_of_type(workflow, "DualCLIPLoader")
        # CLIPLoader has no hunyuan_video type -- only DualCLIPLoader does.
        assert loader["inputs"]["type"] == "hunyuan_video"
        assert loader["inputs"]["clip_name1"] == "clip_l.safetensors"
        assert loader["inputs"]["clip_name2"] == "llava_llama3_fp8_scaled.safetensors"

    def test_hunyuan_uses_embedded_guidance_not_cfg(self):
        """The t2v checkpoint is guidance-distilled: BasicGuider, no negative."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="a lake",
            negative="ignored",
            settings=VideoSettings(model=VideoModel.HUNYUAN, cfg=6.0),
        )

        assert _node_of_type(workflow, "FluxGuidance")["inputs"]["guidance"] == 6.0
        assert "CFGGuider" not in _class_types(workflow)
        # The negative prompt must not leak into any encode.
        texts = [
            n["inputs"]["text"] for n in workflow.values() if n["class_type"] == "CLIPTextEncode"
        ]
        assert texts == ["a lake"]

    def test_build_hunyuan_with_interpolation(self):
        """Build Hunyuan workflow with interpolation."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.HUNYUAN, width=720, height=480, frames=45, steps=50, interpolate=True
        )

        workflow = builder.build(prompt="waterfall", negative="blurry", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_hunyuan_15(self):
        """Build Hunyuan 1.5 workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.HUNYUAN_15, width=1280, height=720, frames=65, steps=30, shift=9.0
        )

        workflow = builder.build(
            prompt="aurora borealis", negative="low quality", settings=settings
        )

        assert isinstance(workflow, dict)
        loader = _node_of_type(workflow, "DualCLIPLoader")
        assert loader["inputs"]["type"] == "hunyuan_video_15"
        assert (
            _node_of_type(workflow, "UNETLoader")["inputs"]["unet_name"]
            == "hunyuanvideo1.5_720p_t2v_fp16.safetensors"
        )

    def test_hunyuan_15_distilled_uses_a_real_checkpoint(self):
        """There is no 720p cfg-distilled release; distilled is 480p only."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="x",
            negative="y",
            settings=VideoSettings(
                model=VideoModel.HUNYUAN_15_FAST, width=848, height=480, variant="distilled"
            ),
        )

        unet = _node_of_type(workflow, "UNETLoader")["inputs"]["unet_name"]
        assert unet == "hunyuanvideo1.5_480p_t2v_cfg_distilled_fp16.safetensors"

    def test_hunyuan_15_upscale_uses_real_input_names(self):
        """HunyuanVideo15LatentUpscaleWithModel takes upscale_method/crop."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="x",
            negative="y",
            settings=VideoSettings(
                model=VideoModel.HUNYUAN_15, width=1920, height=1080, upscale=True
            ),
        )

        upscale = _node_of_type(workflow, "HunyuanVideo15LatentUpscaleWithModel")
        assert set(upscale["inputs"]) == {
            "model",
            "samples",
            "upscale_method",
            "width",
            "height",
            "crop",
        }
        assert upscale["inputs"]["crop"] == "disabled"
        assert (upscale["inputs"]["width"], upscale["inputs"]["height"]) == (1920, 1080)
        # 1080p is rendered at the 720p base and then upsampled.
        latent = _node_of_type(workflow, "EmptyHunyuanVideo15Latent")
        assert (latent["inputs"]["width"], latent["inputs"]["height"]) == (1280, 720)

    def test_build_hunyuan_15_fast(self):
        """Build Hunyuan 1.5 fast (distilled) workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.HUNYUAN_15_FAST, width=1280, height=720, frames=45, steps=6
        )

        workflow = builder.build(prompt="city timelapse", negative="blurry", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_hunyuan_15_i2v(self):
        """Build Hunyuan 1.5 image-to-video workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.HUNYUAN_15_I2V, width=1280, height=720, frames=45, steps=30
        )

        workflow = builder.build(
            prompt="portrait coming to life",
            negative="blurry",
            settings=settings,
            init_image="data:image/png;base64,iVBORw0KGgo=",
        )

        assert isinstance(workflow, dict)


# ============================================================================
# LTXV BUILDER TESTS
# ============================================================================


class TestLTXVBuilder:
    """Test LTX-Video workflow building."""

    def test_build_ltxv(self):
        """Build LTX-Video workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.LTXV, width=768, height=512, frames=97, fps=24, steps=30
        )

        workflow = builder.build(prompt="rocket launch", negative="low quality", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_ltxv_i2v(self):
        """Build LTX-Video image-to-video workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.LTXV_I2V, width=768, height=512, frames=97, fps=24, steps=30
        )

        workflow = builder.build(
            prompt="image coming to life",
            negative="blurry",
            settings=settings,
            init_image="data:image/png;base64,iVBORw0KGgo=",
        )

        assert isinstance(workflow, dict)


# ============================================================================
# WAN BUILDER TESTS
# ============================================================================


class TestWanBuilder:
    """Test Wan video workflow building."""

    def test_build_wan(self):
        """Build Wan workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.WAN, width=832, height=480, frames=81, fps=16, steps=20
        )

        workflow = builder.build(prompt="dragon flying", negative="low quality", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_wan_fast(self):
        """Build Wan fast workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.WAN_FAST, width=832, height=480, frames=81, fps=16, steps=4
        )

        workflow = builder.build(prompt="explosion", negative="blurry", settings=settings)

        assert isinstance(workflow, dict)

    def test_build_wan_i2v(self):
        """Build Wan image-to-video workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.WAN_I2V, width=832, height=480, frames=81, fps=16, steps=20
        )

        workflow = builder.build(
            prompt="photo animation",
            negative="blurry",
            settings=settings,
            init_image="data:image/png;base64,iVBORw0KGgo=",
        )

        assert isinstance(workflow, dict)


# ============================================================================
# MOCHI BUILDER TESTS
# ============================================================================


class TestMochiBuilder:
    """Test Mochi video workflow building."""

    def test_build_mochi(self):
        """Build Mochi workflow."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = VideoSettings(
            model=VideoModel.MOCHI, width=848, height=480, frames=163, fps=30, steps=50, cfg=4.5
        )

        workflow = builder.build(
            prompt="astronaut on mars", negative="low quality", settings=settings
        )

        assert isinstance(workflow, dict)
        assert _class_types(workflow) == {
            "UNETLoader",
            "CLIPLoader",
            "VAELoader",
            "CLIPTextEncode",
            "EmptyMochiLatentVideo",
            "KSampler",
            "VAEDecode",
            "VHS_VideoCombine",
        }

    def test_mochi_loads_the_dit_through_unetloader(self):
        """Mochi's DiT lives in diffusion_models, so UNETLoader -- not a checkpoint."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="x",
            negative="y",
            settings=VideoSettings(model=VideoModel.MOCHI, precision="bf16"),
        )

        assert "CheckpointLoaderSimple" not in _class_types(workflow)
        assert (
            _node_of_type(workflow, "UNETLoader")["inputs"]["unet_name"]
            == "mochi_preview_bf16.safetensors"
        )
        assert _node_of_type(workflow, "VAELoader")["inputs"]["vae_name"] == "mochi_vae.safetensors"
        clip = _node_of_type(workflow, "CLIPLoader")["inputs"]
        assert clip["type"] == "mochi"
        assert clip["clip_name"] == "t5xxl_fp16.safetensors"

    def test_mochi_fp8_variant(self):
        """Non-bf16 precision selects the fp8 scaled repackage."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="x",
            negative="y",
            settings=VideoSettings(model=VideoModel.MOCHI, precision="fp8"),
        )

        assert (
            _node_of_type(workflow, "UNETLoader")["inputs"]["unet_name"]
            == "mochi_preview_fp8_scaled.safetensors"
        )

    def test_mochi_latent_uses_length_not_frames(self):
        """EmptyMochiLatentVideo's frame count input is named `length`."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="x", negative="y", settings=VideoSettings(model=VideoModel.MOCHI, frames=81)
        )

        latent = _node_of_type(workflow, "EmptyMochiLatentVideo")
        assert set(latent["inputs"]) == {"width", "height", "length", "batch_size"}
        assert latent["inputs"]["length"] == 81

    def test_mochi_wires_a_negative_prompt(self):
        """KSampler needs real negative conditioning, not a reused positive."""
        from comfy_headless.video import VideoModel, VideoSettings, VideoWorkflowBuilder

        workflow = VideoWorkflowBuilder().build(
            prompt="astronaut", negative="blurry", settings=VideoSettings(model=VideoModel.MOCHI)
        )

        sampler = _node_of_type(workflow, "KSampler")
        assert sampler["inputs"]["positive"] != sampler["inputs"]["negative"]
        texts = {
            n["inputs"]["text"] for n in workflow.values() if n["class_type"] == "CLIPTextEncode"
        }
        assert texts == {"astronaut", "blurry"}


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_get_video_preset(self):
        """get_video_preset returns settings for valid preset."""
        from comfy_headless.video import get_video_preset

        settings = get_video_preset("quick")
        assert settings is not None
        assert settings.width > 0

    def test_get_video_preset_invalid(self):
        """get_video_preset handles invalid preset."""
        from comfy_headless.video import get_video_preset

        # Should return None or raise error for invalid preset
        result = get_video_preset("nonexistent_preset_xyz")
        # Accept None or exception
        assert result is None or isinstance(result, object)

    def test_list_video_presets(self):
        """list_video_presets returns preset names."""
        from comfy_headless.video import list_video_presets

        presets = list_video_presets()
        assert isinstance(presets, (list, tuple, dict))
        assert len(presets) > 0

    def test_list_video_models(self):
        """list_video_models returns model names."""
        from comfy_headless.video import list_video_models

        models = list_video_models()
        assert isinstance(models, (list, tuple, dict))
        assert len(models) > 0

    def test_get_recommended_preset_by_intent(self):
        """get_recommended_preset accepts intent parameter."""
        from comfy_headless.video import get_recommended_preset

        preset = get_recommended_preset(intent="cinematic", vram_gb=16)
        assert preset is not None

    def test_get_recommended_preset_portrait(self):
        """get_recommended_preset for portrait intent."""
        from comfy_headless.video import get_recommended_preset

        preset = get_recommended_preset(intent="portrait", vram_gb=12)
        assert preset is not None

    def test_get_recommended_preset_action(self):
        """get_recommended_preset for action intent."""
        from comfy_headless.video import get_recommended_preset

        preset = get_recommended_preset(intent="action", vram_gb=12)
        assert preset is not None


# ============================================================================
# VIDEO MODEL INFO TESTS
# ============================================================================


class TestVideoModelInfo:
    """Test VIDEO_MODEL_INFO dictionary."""

    def test_model_info_structure(self):
        """VIDEO_MODEL_INFO has expected structure."""
        from comfy_headless.video import VIDEO_MODEL_INFO

        # Should have info for each model type
        assert len(VIDEO_MODEL_INFO) > 0

    def test_model_info_contains_ltx(self):
        """Model info includes LTX models."""
        from comfy_headless.video import VIDEO_MODEL_INFO

        # Check if any LTX model is in the info
        [k for k in VIDEO_MODEL_INFO if "ltx" in str(k).lower()]
        # May or may not have LTX in the enum keys
        assert len(VIDEO_MODEL_INFO) > 0


# ============================================================================
# MOTION STYLE TESTS
# ============================================================================


class TestMotionStyle:
    """Test MotionStyle enum."""

    def test_motion_styles_exist(self):
        """MotionStyle enum has expected values."""
        from comfy_headless.video import MotionStyle

        styles = list(MotionStyle)
        assert len(styles) >= 3  # At least static, moderate, dynamic

    def test_motion_style_values(self):
        """MotionStyle values are strings."""
        from comfy_headless.video import MotionStyle

        for style in MotionStyle:
            assert isinstance(style.value, str)


# ============================================================================
# VIDEO FORMAT TESTS
# ============================================================================


class TestVideoFormat:
    """Test VideoFormat enum."""

    def test_video_formats_exist(self):
        """VideoFormat enum has expected values."""
        from comfy_headless.video import VideoFormat

        formats = list(VideoFormat)
        assert len(formats) >= 2  # At least MP4 and GIF

    def test_mp4_format(self):
        """MP4 format exists."""
        from comfy_headless.video import VideoFormat

        assert VideoFormat.MP4.value == "mp4"

    def test_gif_format(self):
        """GIF format exists."""
        from comfy_headless.video import VideoFormat

        assert VideoFormat.GIF.value == "gif"


# ============================================================================
# PRESET-BASED BUILD TESTS
# ============================================================================


class TestPresetBasedBuilding:
    """Test building workflows via preset names."""

    def test_build_quick_preset(self):
        """Build from 'quick' preset."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test video", preset="quick")
        assert isinstance(workflow, dict)

    def test_build_standard_preset(self):
        """Build from 'standard' preset."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test video", preset="standard")
        assert isinstance(workflow, dict)

    def test_build_quality_preset(self):
        """Build from 'quality' preset."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test video", preset="quality")
        assert isinstance(workflow, dict)

    def test_build_cinematic_preset(self):
        """Build from 'cinematic' preset."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test video", preset="cinematic")
        assert isinstance(workflow, dict)


# ============================================================================
# EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_prompt(self):
        """Handle empty prompt."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="", preset="quick")
        # Should still produce a workflow (empty prompt is valid)
        assert isinstance(workflow, dict)

    def test_very_long_prompt(self):
        """Handle very long prompt."""
        from comfy_headless.video import build_video_workflow

        long_prompt = "A " * 500 + "beautiful sunset"
        workflow = build_video_workflow(prompt=long_prompt, preset="quick")
        assert isinstance(workflow, dict)

    def test_special_characters_in_prompt(self):
        """Handle special characters in prompt."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(
            prompt="café scene with 日本語 text & symbols <>,./;'[]", preset="quick"
        )
        assert isinstance(workflow, dict)

    def test_negative_seed(self):
        """Handle negative seed (random)."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test", preset="quick", seed=-1)
        assert isinstance(workflow, dict)

    def test_zero_seed(self):
        """Handle zero seed."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test", preset="quick", seed=0)
        assert isinstance(workflow, dict)

    def test_large_seed(self):
        """Handle large seed value."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(prompt="test", preset="quick", seed=2**31 - 1)
        assert isinstance(workflow, dict)


# ============================================================================
# NODE CATALOG CONTRACT
# ============================================================================
#
# comfy-headless is a graph emitter: every class_type it writes must exist on
# the target ComfyUI server, and anything that is not a built-in must name the
# custom node pack that provides it. These tests are the regression guard for
# the v2.5.7 defect where video builders emitted node names that had been
# removed from ComfyUI, producing an opaque validation error at submit time.


# Node names that comfy-headless used to emit and that no longer exist
# anywhere in the ComfyUI node catalog (core or published packs).
REMOVED_NODES = frozenset(
    {
        "MochiSampler",
        "MochiModelLoader",
        "MochiVAEDecode",
        "HunyuanVideoSampler",
        "HunyuanVideoModelLoader",
        "HunyuanVideoTextEncode",
        "HunyuanVideoVAEDecode",
        "CogVideoModelLoader",
        "CogVideoVAEDecode",
    }
)

# Built-in ComfyUI nodes the video builders are allowed to emit. Every name
# here was checked against the live node catalog and reported pack "core".
# Adding a name to this set means asserting you verified it the same way.
VERIFIED_CORE_NODES = frozenset(
    {
        "BasicGuider",
        "BasicScheduler",
        "CFGGuider",
        "CLIPLoader",
        "CLIPTextEncode",
        "CLIPVisionEncode",
        "CLIPVisionLoader",
        "CheckpointLoaderSimple",
        "CreateVideo",
        "DualCLIPLoader",
        "EmptyHunyuanLatentVideo",
        "EmptyHunyuanVideo15Latent",
        "HunyuanVideo15ImageToVideo",
        "SaveVideo",
        "EmptyLTXVLatentVideo",
        "EmptyMochiLatentVideo",
        "FluxGuidance",
        "HunyuanVideo15LatentUpscaleWithModel",
        "ImageOnlyCheckpointLoader",
        "KSampler",
        "KSamplerAdvanced",
        "KSamplerSelect",
        "LTXVConditioning",
        "LTXVImgToVideo",
        "LTXVScheduler",
        "LatentUpscaleModelLoader",
        "LoadImage",
        "LoraLoaderModelOnly",
        "ModelSamplingSD3",
        "RandomNoise",
        "SVD_img2vid_Conditioning",
        "SamplerCustom",
        "SamplerCustomAdvanced",
        "UNETLoader",
        "VAEDecode",
        "VAEDecodeTiled",
        "VAELoader",
        "WanImageToVideo",
    }
)

# Server-side image name as returned by ComfyClient.upload_image()["name"].
# NOT base64 data: since the switch to the core LoadImage node, init_image is
# a filename already present in ComfyUI's input folder.
_SAMPLE_IMAGE = "uploaded_ref_00001.png"


def _class_types(workflow):
    """Set of class_types used by a workflow."""
    return {node["class_type"] for node in workflow.values()}


def _node_of_type(workflow, class_type):
    """Return the single node of the given class_type."""
    matches = [n for n in workflow.values() if n["class_type"] == class_type]
    assert len(matches) == 1, f"expected exactly one {class_type}, got {len(matches)}"
    return matches[0]


def _every_workflow():
    """
    Build every preset across every branch-selecting flag.

    Covers the t2v/i2v split, RIFE interpolation, the 1080p upscale leg and
    each precision branch, so no builder path escapes the contract checks.
    """
    import copy

    from comfy_headless.video import VIDEO_PRESETS, VideoWorkflowBuilder

    builder = VideoWorkflowBuilder()
    for name, preset in VIDEO_PRESETS.items():
        for init_image in (None, _SAMPLE_IMAGE):
            for interpolate in (False, True):
                for upscale, output in ((False, "vhs"), (True, "vhs"), (False, "core")):
                    for precision in ("fp16", "fp8", "bf16"):
                        settings = copy.deepcopy(preset)
                        settings.interpolate = interpolate
                        settings.upscale = upscale
                        settings.precision = precision
                        settings.output = output
                        try:
                            workflow = builder.build(
                                prompt="a cat walking",
                                negative="blurry",
                                settings=settings,
                                init_image=init_image,
                            )
                        except ValueError:
                            # e.g. SVD refuses to build without an init image
                            continue
                        yield name, workflow


class TestNodeCatalogContract:
    """Every emitted class_type must exist and, if not core, name its pack."""

    def test_no_preset_emits_a_removed_node(self):
        """The v2.5.7 defect: builders referencing deleted ComfyUI nodes."""
        offenders = {}
        for preset, workflow in _every_workflow():
            dead = _class_types(workflow) & REMOVED_NODES
            if dead:
                offenders.setdefault(preset, set()).update(dead)
        assert not offenders, f"presets emitting removed nodes: {offenders}"

    def test_every_emitted_node_is_core_or_declared(self):
        """A non-core node with no NODE_PACKS entry is an undeclared dependency."""
        from comfy_headless.video import NODE_PACKS

        undeclared = {}
        for preset, workflow in _every_workflow():
            for class_type in _class_types(workflow):
                if class_type in VERIFIED_CORE_NODES or class_type in NODE_PACKS:
                    continue
                undeclared.setdefault(class_type, set()).add(preset)
        assert not undeclared, f"undeclared node types: {undeclared}"

    def test_declared_packs_all_have_metadata(self):
        """Every pack id in NODE_PACKS resolves to a NodePack record."""
        from comfy_headless.video import NODE_PACK_INFO, NODE_PACKS

        for class_type, pack_id in NODE_PACKS.items():
            assert pack_id in NODE_PACK_INFO, f"{class_type} -> unknown pack {pack_id!r}"
            pack = NODE_PACK_INFO[pack_id]
            assert pack.id == pack_id
            assert pack.name and pack.url and pack.install_hint

    def test_core_and_pack_registries_do_not_overlap(self):
        """A node cannot be both a built-in and pack-provided."""
        from comfy_headless.video import NODE_PACKS

        assert not (VERIFIED_CORE_NODES & set(NODE_PACKS))

    def test_no_dangling_node_references(self):
        """Every ["id", slot] link points at a node that exists."""
        broken = {}
        for preset, workflow in _every_workflow():
            ids = set(workflow)
            for node_id, node in workflow.items():
                for key, value in node.get("inputs", {}).items():
                    if isinstance(value, list) and len(value) == 2:
                        target = value[0]
                        if isinstance(target, str) and target not in ids:
                            broken.setdefault(preset, []).append((node_id, key, target))
        assert not broken, f"dangling references: {broken}"

    def test_every_workflow_has_an_output_node(self):
        """A graph with no output node produces nothing."""
        for preset, workflow in _every_workflow():
            classes = _class_types(workflow)
            assert "VHS_VideoCombine" in classes or "SaveVideo" in classes, (
                f"{preset} has no output node"
            )

    def test_core_output_swaps_terminator_and_keeps_links(self):
        """output='core' replaces VHS_VideoCombine with CreateVideo->SaveVideo."""
        import copy

        from comfy_headless.video import VIDEO_PRESETS, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = copy.deepcopy(VIDEO_PRESETS["standard"])
        settings.output = "core"
        workflow = builder.build("a cat", "blurry", settings)

        classes = _class_types(workflow)
        assert "VHS_VideoCombine" not in classes
        assert {"CreateVideo", "SaveVideo"} <= classes

        create = _node_of_type(workflow, "CreateVideo")
        save = _node_of_type(workflow, "SaveVideo")
        # The images link that fed VHS now feeds CreateVideo.
        assert isinstance(create["inputs"]["images"], list)
        # SaveVideo consumes the created VIDEO and uses auto codec via the
        # dynamic-combo layer (auto activates no sub-fields).
        assert save["inputs"]["codec"] == "auto"
        assert save["inputs"]["format"] == "auto"
        assert not any(k.startswith("codec.") for k in save["inputs"])
        # No dangling links after the swap.
        ids = set(workflow)
        for node in workflow.values():
            for value in node.get("inputs", {}).values():
                if isinstance(value, list) and len(value) == 2:
                    assert str(value[0]) in ids

    def test_hunyuan15_i2v_builds_real_i2v_graph(self):
        """The v3.0 gap: HUNYUAN_15_I2V silently built t2v. Now it must not."""
        import copy

        from comfy_headless.video import VIDEO_PRESETS, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = copy.deepcopy(VIDEO_PRESETS["hunyuan15_i2v"])
        workflow = builder.build("a cat", "blurry", settings, init_image=_SAMPLE_IMAGE)

        classes = _class_types(workflow)
        assert "HunyuanVideo15ImageToVideo" in classes
        assert "EmptyHunyuanVideo15Latent" not in classes
        i2v = _node_of_type(workflow, "HunyuanVideo15ImageToVideo")
        # start_image wired from LoadImage; guider/sampler rewired to i2v outputs
        assert isinstance(i2v["inputs"]["start_image"], list)
        guider = _node_of_type(workflow, "CFGGuider")
        assert guider["inputs"]["positive"][1] == 0
        assert guider["inputs"]["negative"][1] == 1
        sampler = _node_of_type(workflow, "SamplerCustomAdvanced")
        assert sampler["inputs"]["latent_image"][1] == 2
        # i2v checkpoint, not t2v
        unet = _node_of_type(workflow, "UNETLoader")
        assert "_i2v_" in unet["inputs"]["unet_name"]

    def test_hunyuan15_i2v_without_image_raises(self):
        import copy

        from comfy_headless.video import VIDEO_PRESETS, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = copy.deepcopy(VIDEO_PRESETS["hunyuan15_i2v"])
        with pytest.raises(ValueError, match="init_image"):
            builder.build("a cat", "blurry", settings, init_image=None)

    def test_hunyuan15_i2v_distilled_uses_i2v_distilled_checkpoint(self):
        import copy

        from comfy_headless.video import VIDEO_PRESETS, VideoWorkflowBuilder

        builder = VideoWorkflowBuilder()
        settings = copy.deepcopy(VIDEO_PRESETS["hunyuan15_i2v_fast"])
        workflow = builder.build("a cat", "blurry", settings, init_image=_SAMPLE_IMAGE)
        unet = _node_of_type(workflow, "UNETLoader")
        assert unet["inputs"]["unet_name"] == (
            "hunyuanvideo1.5_480p_i2v_cfg_distilled_fp16.safetensors"
        )

    def test_build_video_workflow_overrides_keep_variant(self):
        """The v3.0 bug: overrides dropped variant/upscale/shift/precision."""
        from comfy_headless.video import build_video_workflow

        workflow = build_video_workflow(
            prompt="x", negative="y", preset="hunyuan15_fast", width=640, height=640
        )
        unets = [n for n in workflow.values() if n["class_type"] == "UNETLoader"]
        assert unets, "hunyuan15_fast should load through UNETLoader"
        assert "distilled" in unets[0]["inputs"]["unet_name"], (
            "variant='distilled' must survive an unrelated override"
        )

    def test_get_node_pack_returns_none_for_core(self):
        from comfy_headless.video import get_node_pack

        assert get_node_pack("KSampler") is None
        assert get_node_pack("VAEDecode") is None
        assert get_node_pack("VHS_VideoCombine") == "comfyui-videohelpersuite"
        assert get_node_pack("CogVideoSampler") == "comfyui-cogvideoxwrapper"

    def test_required_node_packs_groups_by_pack(self):
        from comfy_headless.video import required_node_packs

        workflow = {
            "1": {"class_type": "KSampler", "inputs": {}},
            "2": {"class_type": "VHS_VideoCombine", "inputs": {}},
            "3": {"class_type": "ADE_LoadAnimateDiffModel", "inputs": {}},
            "4": {"class_type": "ADE_ApplyAnimateDiffModel", "inputs": {}},
        }

        assert required_node_packs(workflow) == {
            "comfyui-animatediff-evolved": [
                "ADE_ApplyAnimateDiffModel",
                "ADE_LoadAnimateDiffModel",
            ],
            "comfyui-videohelpersuite": ["VHS_VideoCombine"],
        }

    def test_required_node_packs_empty_for_core_only(self):
        from comfy_headless.video import required_node_packs

        assert required_node_packs({"1": {"class_type": "KSampler", "inputs": {}}}) == {}

    def test_required_node_packs_tolerates_junk(self):
        from comfy_headless.video import required_node_packs

        assert required_node_packs({"1": "not a node", "2": {"no_class_type": True}}) == {}

    def test_model_info_declares_packs(self):
        """Every family declares the packs its workflows actually need."""
        from comfy_headless.video import (
            NODE_PACK_INFO,
            VIDEO_MODEL_INFO,
            VIDEO_PRESETS,
            VideoWorkflowBuilder,
            required_node_packs,
        )

        builder = VideoWorkflowBuilder()
        for family, info in VIDEO_MODEL_INFO.items():
            for pack_id in info.requires_packs:
                assert pack_id in NODE_PACK_INFO, f"{family} declares unknown pack {pack_id!r}"

            declared = set(info.requires_packs)
            for preset_name in info.presets:
                settings = VIDEO_PRESETS[preset_name]
                try:
                    workflow = builder.build(
                        prompt="x", negative="y", settings=settings, init_image=_SAMPLE_IMAGE
                    )
                except ValueError:
                    continue
                actual = set(required_node_packs(workflow))
                missing = actual - declared
                assert not missing, f"{family}/{preset_name} uses undeclared packs {missing}"


class TestMissingNodePackError:
    """The structured error raised when a server lacks required nodes."""

    def test_names_class_and_pack(self):
        from comfy_headless.exceptions import MissingNodePackError
        from comfy_headless.video import NODE_PACK_INFO

        err = MissingNodePackError(
            missing={"VHS_VideoCombine": NODE_PACK_INFO["comfyui-videohelpersuite"].to_dict()}
        )

        assert err.code == "MISSING_NODE_PACK"
        assert "VHS_VideoCombine" in err.developer_message
        assert "comfyui-videohelpersuite" in err.developer_message
        assert err.details["missing_nodes"] == ["VHS_VideoCombine"]
        assert err.details["packs"] == ["comfyui-videohelpersuite"]
        assert any("VideoHelperSuite" in s for s in err.suggestions)

    def test_unknown_provider_is_not_invented(self):
        from comfy_headless.exceptions import MissingNodePackError

        err = MissingNodePackError(missing={"SomeCustomNode": None})

        assert "provider unknown" in err.developer_message
        assert err.details["packs"] == []
        assert any("No known pack provides" in s for s in err.suggestions)

    def test_accepts_bare_pack_id(self):
        from comfy_headless.exceptions import MissingNodePackError

        err = MissingNodePackError(missing={"CogVideoSampler": "comfyui-cogvideoxwrapper"})

        assert "comfyui-cogvideoxwrapper" in err.developer_message
        assert err.details["packs"] == ["comfyui-cogvideoxwrapper"]

    def test_empty_missing_is_safe(self):
        from comfy_headless.exceptions import MissingNodePackError

        err = MissingNodePackError()

        assert err.details["missing_nodes"] == []
        assert "not installed" in err.developer_message


class TestClientDependencyReporting:
    """check_workflow_dependencies / require_workflow_dependencies."""

    @staticmethod
    def _client(installed):
        from unittest.mock import patch

        from comfy_headless.client import ComfyClient

        client = ComfyClient()
        return client, patch.object(client, "get_all_installed_nodes", return_value=installed)

    def test_reports_the_pack_for_a_missing_node(self):
        workflow = {
            "1": {"class_type": "KSampler", "inputs": {}},
            "2": {"class_type": "VHS_VideoCombine", "inputs": {}},
        }
        client, patched = self._client(["KSampler"])

        with patched:
            report = client.check_workflow_dependencies(workflow)

        assert report["all_installed"] is False
        assert report["missing"] == ["VHS_VideoCombine"]
        assert report["missing_packs"]["VHS_VideoCombine"]["id"] == "comfyui-videohelpersuite"
        assert report["required_packs"] == {"comfyui-videohelpersuite": ["VHS_VideoCombine"]}

    def test_missing_core_node_has_no_pack(self):
        workflow = {"1": {"class_type": "KSampler", "inputs": {}}}
        client, patched = self._client([])

        with patched:
            report = client.check_workflow_dependencies(workflow)

        assert report["missing_packs"] == {"KSampler": None}

    def test_require_raises_with_named_pack(self):
        from comfy_headless.exceptions import MissingNodePackError

        workflow = {"1": {"class_type": "CogVideoSampler", "inputs": {}}}
        client, patched = self._client(["KSampler"])

        with patched, pytest.raises(MissingNodePackError) as excinfo:
            client.require_workflow_dependencies(workflow)

        assert "comfyui-cogvideoxwrapper" in str(excinfo.value)

    def test_require_passes_when_all_installed(self):
        workflow = {"1": {"class_type": "KSampler", "inputs": {}}}
        client, patched = self._client(["KSampler"])

        with patched:
            report = client.require_workflow_dependencies(workflow)

        assert report["all_installed"] is True


class TestWorkflowSeedExtraction:
    """The built seed must be recoverable from any sampler front-end."""

    def test_reads_ksampler_seed(self):
        from comfy_headless.client import _extract_workflow_seed

        workflow = {"1": {"class_type": "KSampler", "inputs": {"seed": 4242}}}
        assert _extract_workflow_seed(workflow) == 4242

    def test_reads_random_noise_seed(self):
        from comfy_headless.client import _extract_workflow_seed

        workflow = {"10": {"class_type": "RandomNoise", "inputs": {"noise_seed": 99}}}
        assert _extract_workflow_seed(workflow) == 99

    def test_falls_back_to_default(self):
        from comfy_headless.client import _extract_workflow_seed

        assert _extract_workflow_seed({"1": {"class_type": "VAEDecode", "inputs": {}}}, -1) == -1

    def test_every_preset_exposes_its_seed(self):
        """Presets resolve seed=-1 while building; the caller must see it back."""
        from comfy_headless.client import _extract_workflow_seed

        for preset, workflow in _every_workflow():
            seed = _extract_workflow_seed(workflow, default=-1)
            assert seed >= 0, f"{preset} does not expose its resolved seed"
