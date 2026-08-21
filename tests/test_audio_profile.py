"""Tests for comfy_headless/audio.py -- the audio profile."""

import pytest

from comfy_headless.audio import (
    AUDIO_MODEL_INFO,
    AUDIO_PRESETS,
    SEPARATION_STEMS,
    AudioFormat,
    AudioSettings,
    build_audio_separation_workflow,
    build_audio_workflow,
    get_audio_builder,
    list_audio_presets,
)
from comfy_headless.exceptions import GraphAddressError

_AUDIO_REF = "song_00001.flac"


def _node_of_type(workflow, class_type):
    matches = [n for n in workflow.values() if n["class_type"] == class_type]
    assert len(matches) == 1, f"expected exactly one {class_type}, got {len(matches)}"
    return matches[0]


def _nodes_of_type(workflow, class_type):
    return [n for n in workflow.values() if n["class_type"] == class_type]


class TestAudioWorkflowShape:
    def test_reference_graph_shape(self):
        workflow = build_audio_workflow("lo-fi, jazz, mellow")
        classes = {n["class_type"] for n in workflow.values()}
        assert classes == {
            "CheckpointLoaderSimple",
            "TextEncodeAceStepAudio1.5",
            "EmptyAceStep1.5LatentAudio",
            "KSampler",
            "VAEDecodeAudio",
            "SaveAudioAdvanced",
        }
        assert len(_nodes_of_type(workflow, "TextEncodeAceStepAudio1.5")) == 2

    def test_turbo_defaults(self):
        """turbo AIO is built for low-step / cfg-1 operation."""
        workflow = build_audio_workflow("x")
        sampler = _node_of_type(workflow, "KSampler")
        assert sampler["inputs"]["steps"] == 8
        assert sampler["inputs"]["cfg"] == 1.0
        loader = _node_of_type(workflow, "CheckpointLoaderSimple")
        assert loader["inputs"]["ckpt_name"] == "ace_step_1.5_turbo_aio.safetensors"

    def test_duration_seconds_single_source_invariant(self):
        """
        THE COUPLING INVARIANT: encoder duration and latent seconds are one
        logical parameter. The runtime does not cross-validate them, so a
        drift completes "successfully" with silently wrong output.
        """
        workflow = build_audio_workflow("x", seconds=42.0)
        latent = _node_of_type(workflow, "EmptyAceStep1.5LatentAudio")
        encoders = _nodes_of_type(workflow, "TextEncodeAceStepAudio1.5")
        assert latent["inputs"]["seconds"] == 42.0
        for encoder in encoders:
            assert encoder["inputs"]["duration"] == 42.0

    def test_invariant_holds_across_every_preset(self):
        for preset in AUDIO_PRESETS:
            workflow = build_audio_workflow("x", preset=preset)
            latent = _node_of_type(workflow, "EmptyAceStep1.5LatentAudio")
            for encoder in _nodes_of_type(workflow, "TextEncodeAceStepAudio1.5"):
                assert encoder["inputs"]["duration"] == latent["inputs"]["seconds"], preset

    def test_negative_encoder_skips_audio_codes(self):
        """The LLM audio-codes stage is pointless on the negative encode."""
        workflow = build_audio_workflow("good tags", negative_tags="bad tags")
        encoders = _nodes_of_type(workflow, "TextEncodeAceStepAudio1.5")
        by_tags = {e["inputs"]["tags"]: e for e in encoders}
        assert by_tags["good tags"]["inputs"]["generate_audio_codes"] is True
        assert by_tags["bad tags"]["inputs"]["generate_audio_codes"] is False

    def test_lyrics_flow_to_positive_only(self):
        workflow = build_audio_workflow("tags", lyrics="la la la")
        encoders = _nodes_of_type(workflow, "TextEncodeAceStepAudio1.5")
        lyrics = sorted(e["inputs"]["lyrics"] for e in encoders)
        assert lyrics == ["", "la la la"]

    def test_flac_terminator_emits_no_quality(self):
        """Lossless provenance: format=flac and NO quality field at all."""
        workflow = build_audio_workflow("x", preset="music")
        save = _node_of_type(workflow, "SaveAudioAdvanced")
        assert save["inputs"]["format"] == "flac"
        assert "format.quality" not in save["inputs"]
        assert "quality" not in save["inputs"]  # never flat either

    def test_mp3_terminator_emits_dotted_quality(self):
        workflow = build_audio_workflow("x", preset="music_mp3")
        save = _node_of_type(workflow, "SaveAudioAdvanced")
        assert save["inputs"]["format"] == "mp3"
        assert save["inputs"]["format.quality"] == "320k"

    def test_opus_default_quality(self):
        workflow = build_audio_workflow("x", format="opus")
        save = _node_of_type(workflow, "SaveAudioAdvanced")
        assert save["inputs"]["format"] == "opus"
        assert save["inputs"]["format.quality"] == "V0"

    def test_flac_with_quality_setting_is_rejected_not_silently_sent(self):
        """A stale quality on a flac settings object must not slip through."""
        settings = AudioSettings(format=AudioFormat.FLAC, quality="320k")
        workflow = get_audio_builder().build("x", settings=settings)
        save = _node_of_type(workflow, "SaveAudioAdvanced")
        assert "format.quality" not in save["inputs"]

    def test_deprecated_terminators_never_emitted(self):
        """SaveAudio / SaveAudioMP3 / SaveAudioOpus are all deprecated."""
        for preset in AUDIO_PRESETS:
            workflow = build_audio_workflow("x", preset=preset)
            classes = {n["class_type"] for n in workflow.values()}
            assert not classes & {"SaveAudio", "SaveAudioMP3", "SaveAudioOpus"}, preset

    def test_seed_resolution(self):
        workflow = build_audio_workflow("x", seed=777)
        assert _node_of_type(workflow, "KSampler")["inputs"]["seed"] == 777


class TestAudioSeparation:
    def test_four_stems_by_documented_order(self):
        """bass, drums, other, vocals -- wired by name, never slot guess."""
        workflow = build_audio_separation_workflow(_AUDIO_REF)
        saves = _nodes_of_type(workflow, "SaveAudioAdvanced")
        assert len(saves) == 4
        sep_id = next(nid for nid, n in workflow.items() if n["class_type"] == "AudioSeparation")
        by_prefix = {n["inputs"]["filename_prefix"]: n for n in saves}
        for index, stem in enumerate(SEPARATION_STEMS):
            node = by_prefix[f"audio/stems_{stem}"]
            assert node["inputs"]["audio"] == [sep_id, index], stem

    def test_stem_subset(self):
        workflow = build_audio_separation_workflow(_AUDIO_REF, stems=["vocals"])
        saves = _nodes_of_type(workflow, "SaveAudioAdvanced")
        assert len(saves) == 1
        # vocals is output index 3 in the documented order
        assert saves[0]["inputs"]["audio"][1] == 3

    def test_stems_are_lossless(self):
        workflow = build_audio_separation_workflow(_AUDIO_REF)
        for save in _nodes_of_type(workflow, "SaveAudioAdvanced"):
            assert save["inputs"]["format"] == "flac"
            assert "format.quality" not in save["inputs"]

    def test_unknown_stem_rejected(self):
        with pytest.raises(ValueError, match="stems"):
            build_audio_separation_workflow(_AUDIO_REF, stems=["guitar"])

    def test_requires_audio_ref(self):
        with pytest.raises(ValueError, match="audio"):
            build_audio_separation_workflow("")

    def test_loads_via_core_load_audio(self):
        workflow = build_audio_separation_workflow(_AUDIO_REF)
        loader = _node_of_type(workflow, "LoadAudio")
        assert loader["inputs"]["audio"] == _AUDIO_REF


class TestAudioPresetsAndInfo:
    def test_preset_names(self):
        assert set(list_audio_presets()) == {
            "music",
            "music_long",
            "jingle",
            "music_mp3",
            "draft",
        }

    def test_t2m_family_is_core_only(self):
        assert AUDIO_MODEL_INFO["ace_step_1.5"].requires_packs == []

    def test_declared_presets_exist(self):
        for info in AUDIO_MODEL_INFO.values():
            for preset in info.presets:
                assert preset in AUDIO_PRESETS

    def test_overrides_apply(self):
        workflow = build_audio_workflow("x", preset="jingle", bpm=90, keyscale="A minor")
        encoders = _nodes_of_type(workflow, "TextEncodeAceStepAudio1.5")
        for encoder in encoders:
            assert encoder["inputs"]["bpm"] == 90
            assert encoder["inputs"]["keyscale"] == "A minor"

    def test_settings_to_dict(self):
        d = AudioSettings(format=AudioFormat.OPUS, seconds=15.0).to_dict()
        assert d["format"] == "opus"
        assert d["seconds"] == 15.0


class TestPresenceAwareness:
    def test_dynamic_combo_layer_guards_the_terminator(self):
        """Direct proof the audio module goes through the addressing layer."""
        from comfy_headless.addressing import SAVE_AUDIO_FORMAT

        with pytest.raises(GraphAddressError):
            SAVE_AUDIO_FORMAT.build("flac", quality="V0")
