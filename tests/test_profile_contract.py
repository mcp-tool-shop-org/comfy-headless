"""
Cross-profile node-catalog contract (v3.1.0).

Extends the video contract (tests/test_video_coverage.py::TestNodeCatalogContract)
across all six profiles: every class_type any profile builder can emit must
either be a verified core node or be declared in NODE_PACKS with full pack
metadata. This is the guarantee behind
ComfyClient.check_workflow_dependencies(): a missing node is reported as
"install pack Y", never as an opaque /prompt rejection.
"""

import pytest

# Built-in ComfyUI nodes the v3.1.0 profile builders are allowed to emit.
# Every name here was checked against the live node catalog (2026-08-21) and
# reported pack "core". Adding a name to this set means asserting you
# verified it the same way.
VERIFIED_CORE_NODES_V31 = frozenset(
    {
        # shared
        "CLIPTextEncode",
        "CLIPVisionEncode",
        "CLIPVisionLoader",
        "CheckpointLoaderSimple",
        "KSampler",
        "LoadImage",
        "SaveImage",
        "UNETLoader",
        "CLIPLoader",
        "VAELoader",
        "VAEDecode",
        # 3D profile
        "ImageOnlyCheckpointLoader",
        "Hunyuan3Dv2Conditioning",
        "EmptyLatentHunyuan3Dv2",
        "VAEDecodeHunyuan3D",
        "VoxelToMesh",
        "SaveGLB",
        # audio profile
        "TextEncodeAceStepAudio1.5",
        "EmptyAceStep1.5LatentAudio",
        "VAEDecodeAudio",
        "SaveAudioAdvanced",
        "LoadAudio",
        # inference profile terminators (the models are pack nodes)
        "SaveText",
        "MaskToImage",
        # image profile (Qwen / ControlNet)
        "ModelSamplingAuraFlow",
        "EmptySD3LatentImage",
        "TextEncodeQwenImageEditPlus",
        "ControlNetLoader",
        "SetUnionControlNetType",
        "ControlNetApplyAdvanced",
        "Canny",
        "EmptyLatentImage",
    }
)

# Audio terminators that are deprecated in the live catalog. Emitting one is
# a lifecycle regression (right shape, wrong lifecycle).
DEPRECATED_NODES = frozenset({"SaveAudio", "SaveAudioMP3", "SaveAudioOpus"})

_REF = "uploaded_00001.png"
_AUDIO_REF = "song_00001.flac"


def _profile_workflows():
    """Every graph shape the non-video profile builders can emit."""
    from comfy_headless.audio import (
        AUDIO_PRESETS,
        build_audio_separation_workflow,
        build_audio_workflow,
    )
    from comfy_headless.inference import InferenceTask, build_inference_workflow
    from comfy_headless.three_d import THREE_D_PRESETS, build_3d_workflow
    from comfy_headless.workflows import (
        build_controlnet_workflow,
        build_qwen_edit_workflow,
        compile_workflow,
    )

    for preset in THREE_D_PRESETS:
        yield f"3d/{preset}", build_3d_workflow(_REF, preset=preset)
    for preset in AUDIO_PRESETS:
        yield f"audio/{preset}", build_audio_workflow("tags", preset=preset)
    yield "audio/separation", build_audio_separation_workflow(_AUDIO_REF)
    for task in InferenceTask:
        yield (
            f"inference/{task.value}",
            build_inference_workflow(_REF, task=task.value, text_input="query"),
        )
    compiled = compile_workflow(prompt="x", template_id="qwen_txt2img", preset="")
    yield "image/qwen_txt2img", compiled.workflow
    for count in (1, 2, 3):
        yield f"image/qwen_edit_{count}", build_qwen_edit_workflow("edit", [_REF] * count)
    for base in ("qwen", "sdxl"):
        yield (
            f"image/controlnet_{base}",
            build_controlnet_workflow("x", _REF, base=base, control_type="depth"),
        )
        yield (
            f"image/controlnet_{base}_canny",
            build_controlnet_workflow(
                "x",
                _REF,
                base=base,
                control_type="canny/lineart/anime_lineart/mlsd",
                preprocess="canny",
            ),
        )


def _class_types(workflow):
    return {node["class_type"] for node in workflow.values()}


class TestProfileNodeCatalogContract:
    """Every emitted class_type must exist and, if not core, name its pack."""

    def test_every_emitted_node_is_core_or_declared(self):
        from comfy_headless.node_packs import NODE_PACKS

        undeclared = {}
        for name, workflow in _profile_workflows():
            for class_type in _class_types(workflow):
                if class_type in VERIFIED_CORE_NODES_V31 or class_type in NODE_PACKS:
                    continue
                undeclared.setdefault(class_type, set()).add(name)
        assert not undeclared, f"undeclared node types: {undeclared}"

    def test_no_profile_emits_a_deprecated_node(self):
        """The consult's lifecycle lesson: deprecation is checked live."""
        offenders = {}
        for name, workflow in _profile_workflows():
            dead = _class_types(workflow) & DEPRECATED_NODES
            if dead:
                offenders.setdefault(name, set()).update(dead)
        assert not offenders, f"profiles emitting deprecated nodes: {offenders}"

    def test_core_and_pack_registries_do_not_overlap(self):
        from comfy_headless.node_packs import NODE_PACKS

        assert not (VERIFIED_CORE_NODES_V31 & set(NODE_PACKS))

    def test_unverified_nodes_never_emitted(self):
        """
        Classes that could NOT be verified in the live catalog (2026-08-21)
        must not appear in any emitted graph: Florence2ModelLoader was
        absent (only the auto-downloading loader exists) and no WD14 tagger
        node exists in the catalog at all.
        """
        forbidden = {"Florence2ModelLoader", "WD14Tagger|pysssss"}
        for name, workflow in _profile_workflows():
            assert not _class_types(workflow) & forbidden, name

    def test_no_dangling_node_references(self):
        broken = {}
        for name, workflow in _profile_workflows():
            ids = set(workflow)
            for node_id, node in workflow.items():
                for key, value in node.get("inputs", {}).items():
                    if isinstance(value, list) and len(value) == 2:
                        target = value[0]
                        if isinstance(target, str) and target not in ids:
                            broken.setdefault(name, []).append((node_id, key, target))
        assert not broken, f"dangling references: {broken}"

    def test_every_profile_workflow_has_an_output_node(self):
        from comfy_headless.addressing import has_output_node

        for name, workflow in _profile_workflows():
            assert has_output_node(workflow), f"{name} has no output node"

    def test_model_info_declares_packs_across_profiles(self):
        """Every family's requires_packs covers what its graphs actually use."""
        from comfy_headless.audio import AUDIO_MODEL_INFO
        from comfy_headless.inference import INFERENCE_MODEL_INFO
        from comfy_headless.node_packs import NODE_PACK_INFO, required_node_packs
        from comfy_headless.three_d import THREE_D_MODEL_INFO

        for registry in (THREE_D_MODEL_INFO, AUDIO_MODEL_INFO, INFERENCE_MODEL_INFO):
            for family, info in registry.items():
                for pack_id in info.requires_packs:
                    assert pack_id in NODE_PACK_INFO, f"{family}: unknown pack {pack_id!r}"

        # And concretely: what each profile's graphs use is declared somewhere.
        declared_by_family = {
            "3d": set(THREE_D_MODEL_INFO["hunyuan3d_v2"].requires_packs),
            "audio_t2m": set(AUDIO_MODEL_INFO["ace_step_1.5"].requires_packs),
            "inference": set(INFERENCE_MODEL_INFO["florence2"].requires_packs)
            | set(INFERENCE_MODEL_INFO["florence2_coordinates"].requires_packs),
        }
        from comfy_headless.audio import build_audio_workflow
        from comfy_headless.inference import build_inference_workflow
        from comfy_headless.three_d import build_3d_workflow

        assert set(required_node_packs(build_3d_workflow(_REF))) <= declared_by_family["3d"]
        assert (
            set(required_node_packs(build_audio_workflow("x"))) <= declared_by_family["audio_t2m"]
        )
        for task in ("caption", "detect", "segment"):
            used = set(
                required_node_packs(build_inference_workflow(_REF, task=task, text_input="q"))
            )
            assert used <= declared_by_family["inference"], task

    def test_separation_declares_its_pack(self):
        from comfy_headless.audio import build_audio_separation_workflow
        from comfy_headless.node_packs import required_node_packs

        packs = required_node_packs(build_audio_separation_workflow(_AUDIO_REF))
        assert packs == {"audio-separation-nodes-comfyui": ["AudioSeparation"]}

    def test_backcompat_reexport_from_video(self):
        """The pre-3.1 import surface must keep working."""
        from comfy_headless import node_packs, video

        assert video.NODE_PACKS is node_packs.NODE_PACKS
        assert video.NODE_PACK_INFO is node_packs.NODE_PACK_INFO
        assert video.get_node_pack is node_packs.get_node_pack
        assert video.required_node_packs is node_packs.required_node_packs


class TestSixProfilesHavePublicSurfaces:
    """The Director's structure: Image, Video, 3D, Inference, Metadata, Audio."""

    def test_image_surface(self):
        import comfy_headless as ch

        assert callable(ch.compile_workflow)
        assert callable(ch.build_qwen_edit_workflow)
        assert callable(ch.build_controlnet_workflow)

    def test_video_surface(self):
        import comfy_headless as ch

        assert callable(ch.build_video_workflow)
        assert "hunyuan15_i2v" in ch.VIDEO_PRESETS

    def test_three_d_surface(self):
        import comfy_headless as ch

        assert callable(ch.build_3d_workflow)
        assert ch.THREE_D_PRESETS

    def test_inference_surface(self):
        import comfy_headless as ch

        assert callable(ch.build_inference_workflow)
        assert list(ch.InferenceTask)

    def test_metadata_surface(self):
        import comfy_headless as ch

        assert callable(ch.read_workflow_metadata)
        assert callable(ch.extract_prompt_graph)

    def test_audio_surface(self):
        import comfy_headless as ch

        assert callable(ch.build_audio_workflow)
        assert callable(ch.build_audio_separation_workflow)

    @pytest.mark.parametrize(
        "method",
        [
            "generate_image",
            "generate_video",
            "generate_3d",
            "generate_audio",
            "separate_audio",
            "run_inference",
            "edit_image",
            "rerun_from_png",
            "upload_audio",
            "check_workflow_types",
            "get_file",
        ],
    )
    def test_client_methods_exist(self, method):
        from comfy_headless.client import ComfyClient

        assert callable(getattr(ComfyClient, method))
