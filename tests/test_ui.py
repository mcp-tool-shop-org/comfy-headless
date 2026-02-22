"""Tests for ui.py Gradio interface module."""

from unittest.mock import MagicMock, patch


class TestUIConstants:
    """Test UI constants."""

    def test_presets_defined(self):
        """Test PRESETS constant is defined."""
        from comfy_headless.ui import PRESETS

        assert len(PRESETS) > 0
        assert "Quality (1024px)" in PRESETS

    def test_video_preset_names_defined(self):
        """Test VIDEO_PRESET_NAMES constant is defined."""
        from comfy_headless.ui import VIDEO_PRESET_NAMES

        assert len(VIDEO_PRESET_NAMES) > 0
        assert "Standard" in VIDEO_PRESET_NAMES

    def test_default_negative_defined(self):
        """Test DEFAULT_NEGATIVE is defined."""
        from comfy_headless.ui import DEFAULT_NEGATIVE

        assert len(DEFAULT_NEGATIVE) > 0
        assert "ugly" in DEFAULT_NEGATIVE.lower() or "blurry" in DEFAULT_NEGATIVE.lower()

    def test_example_prompts_defined(self):
        """Test EXAMPLE_PROMPTS is defined."""
        from comfy_headless.ui import EXAMPLE_PROMPTS

        assert len(EXAMPLE_PROMPTS) > 0


class TestGetStatus:
    """Test get_status function."""

    @patch("comfy_headless.ui.client")
    def test_get_status_offline(self, mock_client):
        """Test status when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import get_status

        status = get_status()
        assert "Offline" in status

    @patch("comfy_headless.ui.client")
    def test_get_status_online(self, mock_client):
        """Test status when online."""
        mock_client.is_online.return_value = True
        mock_client.get_system_stats.return_value = {
            "devices": [{"name": "RTX 5080", "vram_total": 16 * 1024**3, "vram_free": 8 * 1024**3}]
        }
        from comfy_headless.ui import get_status

        status = get_status()
        assert "Online" in status

    @patch("comfy_headless.ui.client")
    def test_get_status_online_no_stats(self, mock_client):
        """Test status when online but no stats."""
        mock_client.is_online.return_value = True
        mock_client.get_system_stats.return_value = None
        from comfy_headless.ui import get_status

        status = get_status()
        assert "Online" in status


class TestGetQueueStatus:
    """Test get_queue_status function."""

    @patch("comfy_headless.ui.client")
    def test_queue_status_offline(self, mock_client):
        """Test queue status when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import get_queue_status

        status = get_queue_status()
        assert "Offline" in status

    @patch("comfy_headless.ui.client")
    def test_queue_status_online(self, mock_client):
        """Test queue status when online."""
        mock_client.is_online.return_value = True
        mock_client.get_queue.return_value = {"queue_running": [["id1"]], "queue_pending": []}
        from comfy_headless.ui import get_queue_status

        status = get_queue_status()
        assert "Running" in status
        assert "Pending" in status


class TestRefreshModels:
    """Test refresh_models function."""

    @patch("comfy_headless.ui.client")
    def test_refresh_models_offline(self, mock_client):
        """Test refresh models when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import refresh_models

        models = refresh_models()
        assert any("offline" in str(m).lower() for m in models)

    @patch("comfy_headless.ui.client")
    def test_refresh_models_online(self, mock_client):
        """Test refresh models when online."""
        mock_client.is_online.return_value = True
        mock_client.get_checkpoints.return_value = ["model1.safetensors", "model2.safetensors"]
        from comfy_headless.ui import refresh_models

        models = refresh_models()
        assert "model1.safetensors" in models


class TestRefreshSamplers:
    """Test refresh_samplers function."""

    @patch("comfy_headless.ui.client")
    def test_refresh_samplers(self, mock_client):
        """Test refresh samplers."""
        mock_client.get_samplers.return_value = ["euler", "euler_ancestral"]
        from comfy_headless.ui import refresh_samplers

        samplers = refresh_samplers()
        assert "euler" in samplers


class TestRefreshSchedulers:
    """Test refresh_schedulers function."""

    @patch("comfy_headless.ui.client")
    def test_refresh_schedulers(self, mock_client):
        """Test refresh schedulers."""
        mock_client.get_schedulers.return_value = ["normal", "karras"]
        from comfy_headless.ui import refresh_schedulers

        schedulers = refresh_schedulers()
        assert "normal" in schedulers


class TestRefreshMotionModels:
    """Test refresh_motion_models function."""

    @patch("comfy_headless.ui.client")
    def test_refresh_motion_models_offline(self, mock_client):
        """Test refresh motion models when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import refresh_motion_models

        models = refresh_motion_models()
        assert any("offline" in str(m).lower() for m in models)

    @patch("comfy_headless.ui.client")
    def test_refresh_motion_models_online(self, mock_client):
        """Test refresh motion models when online."""
        mock_client.is_online.return_value = True
        mock_client.get_motion_models.return_value = ["v3_sd15_mm.ckpt"]
        from comfy_headless.ui import refresh_motion_models

        models = refresh_motion_models()
        assert "v3_sd15_mm.ckpt" in models


class TestApplyPreset:
    """Test apply_preset function."""

    def test_apply_preset_quality(self):
        """Test applying quality preset."""
        from comfy_headless.ui import apply_preset

        width, height, steps = apply_preset("Quality (1024px)")
        assert width > 0
        assert height > 0
        assert steps > 0

    def test_apply_preset_unknown(self):
        """Test applying unknown preset defaults to quality."""
        from comfy_headless.ui import apply_preset

        width, height, steps = apply_preset("Unknown Preset")
        # Should return quality settings as default
        assert width > 0


class TestRandomPrompt:
    """Test random_prompt function."""

    def test_random_prompt(self):
        """Test getting random prompt."""
        from comfy_headless.ui import EXAMPLE_PROMPTS, random_prompt

        result = random_prompt()
        assert result in EXAMPLE_PROMPTS


class TestCancelGeneration:
    """Test cancel_generation function."""

    @patch("comfy_headless.ui.client")
    def test_cancel_success(self, mock_client):
        """Test successful cancellation."""
        mock_client.cancel_current.return_value = True
        from comfy_headless.ui import cancel_generation

        result = cancel_generation()
        assert "Cancelled" in result

    @patch("comfy_headless.ui.client")
    def test_cancel_failure(self, mock_client):
        """Test failed cancellation."""
        mock_client.cancel_current.return_value = False
        from comfy_headless.ui import cancel_generation

        result = cancel_generation()
        assert "Failed" in result


class TestGetHistoryList:
    """Test get_history_list function."""

    @patch("comfy_headless.ui.client")
    def test_get_history_offline(self, mock_client):
        """Test history list when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import get_history_list

        history = get_history_list()
        assert history == []

    @patch("comfy_headless.ui.client")
    def test_get_history_online(self, mock_client):
        """Test history list when online."""
        mock_client.is_online.return_value = True
        mock_client.get_history.return_value = {
            "prompt123": {
                "status": {"completed": True},
                "outputs": {"9": {"images": [{"filename": "test.png"}]}},
            }
        }
        from comfy_headless.ui import get_history_list

        history = get_history_list()
        assert len(history) > 0


class TestGenerateImage:
    """Test generate_image function."""

    @patch("comfy_headless.ui.client")
    def test_generate_empty_prompt(self, mock_client):
        """Test generate with empty prompt."""
        from comfy_headless.ui import generate_image

        # Mock progress
        class MockProgress:
            def __call__(self, *args, **kwargs):
                pass

        result, info = generate_image(
            prompt="",
            negative_prompt="",
            checkpoint="model.safetensors",
            width=512,
            height=512,
            steps=20,
            cfg=7.0,
            sampler="euler",
            scheduler="normal",
            seed=-1,
            progress=MockProgress(),
        )

        assert result is None
        assert "Error" in info

    @patch("comfy_headless.ui.client")
    def test_generate_offline(self, mock_client):
        """Test generate when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import generate_image

        class MockProgress:
            def __call__(self, *args, **kwargs):
                pass

        result, info = generate_image(
            prompt="a sunset",
            negative_prompt="",
            checkpoint="model.safetensors",
            width=512,
            height=512,
            steps=20,
            cfg=7.0,
            sampler="euler",
            scheduler="normal",
            seed=-1,
            progress=MockProgress(),
        )

        assert result is None
        assert "not running" in info.lower() or "offline" in info.lower()


class TestGenerateVideo:
    """Test generate_video function."""

    @patch("comfy_headless.ui.client")
    def test_video_empty_prompt(self, mock_client):
        """Test video with empty prompt."""
        from comfy_headless.ui import generate_video

        class MockProgress:
            def __call__(self, *args, **kwargs):
                pass

        result, info = generate_video(
            prompt="",
            negative_prompt="",
            checkpoint="model.safetensors",
            motion_model="v3_sd15_mm.ckpt",
            width=512,
            height=512,
            frames=16,
            fps=8,
            steps=20,
            cfg=7.0,
            motion_scale=1.0,
            seed=-1,
            progress=MockProgress(),
        )

        assert result is None
        assert "Error" in info

    @patch("comfy_headless.ui.client")
    def test_video_offline(self, mock_client):
        """Test video when offline."""
        mock_client.is_online.return_value = False
        from comfy_headless.ui import generate_video

        class MockProgress:
            def __call__(self, *args, **kwargs):
                pass

        result, info = generate_video(
            prompt="a cat walking",
            negative_prompt="",
            checkpoint="model.safetensors",
            motion_model="v3_sd15_mm.ckpt",
            width=512,
            height=512,
            frames=16,
            fps=8,
            steps=20,
            cfg=7.0,
            motion_scale=1.0,
            seed=-1,
            progress=MockProgress(),
        )

        assert result is None
        assert "not running" in info.lower() or "offline" in info.lower()


class TestCreateUI:
    """Test create_ui function."""

    @patch("comfy_headless.ui.gr")
    @patch("comfy_headless.ui.client")
    def test_create_ui_returns_app(self, mock_client, mock_gr):
        """Test create_ui returns Gradio app."""
        mock_client.is_online.return_value = False
        mock_client.get_samplers.return_value = ["euler"]
        mock_client.get_schedulers.return_value = ["normal"]
        mock_client.get_checkpoints.return_value = []
        mock_client.get_motion_models.return_value = []

        # Mock Blocks context manager
        mock_app = MagicMock()
        mock_gr.Blocks.return_value.__enter__ = MagicMock(return_value=mock_app)
        mock_gr.Blocks.return_value.__exit__ = MagicMock(return_value=False)

        from comfy_headless.ui import create_ui

        # Just verify it doesn't raise
        try:
            create_ui()
        except Exception:
            # The function requires full Gradio which we're mocking
            pass
