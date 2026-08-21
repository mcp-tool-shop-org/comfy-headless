"""Tests for comfy_headless/three_d.py -- the 3D profile."""

import pytest

from comfy_headless.three_d import (
    THREE_D_MODEL_INFO,
    THREE_D_PRESETS,
    MeshAlgorithm,
    ThreeDSettings,
    ThreeDWorkflowBuilder,
    build_3d_workflow,
    get_three_d_builder,
    list_3d_presets,
)

_REF = "uploaded_00001.png"


def _node_of_type(workflow, class_type):
    matches = [n for n in workflow.values() if n["class_type"] == class_type]
    assert len(matches) == 1, f"expected exactly one {class_type}, got {len(matches)}"
    return matches[0]


class TestThreeDWorkflowShape:
    def test_reference_graph_shape(self):
        """The validated Hunyuan3D-2 chain, node for node."""
        workflow = build_3d_workflow(_REF)
        classes = {n["class_type"] for n in workflow.values()}
        assert classes == {
            "LoadImage",
            "ImageOnlyCheckpointLoader",
            "CLIPVisionLoader",
            "CLIPVisionEncode",
            "Hunyuan3Dv2Conditioning",
            "EmptyLatentHunyuan3Dv2",
            "KSampler",
            "VAEDecodeHunyuan3D",
            "VoxelToMesh",
            "SaveGLB",
        }

    def test_image_conditioned_no_text_prompt(self):
        """Hunyuan3D-2 is pure image-conditioned: no CLIPTextEncode anywhere."""
        workflow = build_3d_workflow(_REF)
        assert "CLIPTextEncode" not in {n["class_type"] for n in workflow.values()}

    def test_conditioning_wiring(self):
        workflow = build_3d_workflow(_REF)
        cond = _node_of_type(workflow, "Hunyuan3Dv2Conditioning")
        sampler = _node_of_type(workflow, "KSampler")
        encode = _node_of_type(workflow, "CLIPVisionEncode")
        # encoder output feeds conditioning; both conditioning outputs feed sampler
        assert cond["inputs"]["clip_vision_output"][1] == 0
        assert sampler["inputs"]["positive"][1] == 0
        assert sampler["inputs"]["negative"][1] == 1
        assert encode["inputs"]["crop"] == "center"

    def test_defaults_match_validated_reference(self):
        workflow = build_3d_workflow(_REF)
        sampler = _node_of_type(workflow, "KSampler")
        assert sampler["inputs"]["steps"] == 30
        assert sampler["inputs"]["cfg"] == 5.5
        assert sampler["inputs"]["sampler_name"] == "euler"
        assert sampler["inputs"]["scheduler"] == "simple"
        latent = _node_of_type(workflow, "EmptyLatentHunyuan3Dv2")
        assert latent["inputs"]["resolution"] == 3072
        decode = _node_of_type(workflow, "VAEDecodeHunyuan3D")
        assert decode["inputs"]["num_chunks"] == 8000
        assert decode["inputs"]["octree_resolution"] == 256
        mesh = _node_of_type(workflow, "VoxelToMesh")
        assert mesh["inputs"]["algorithm"] == "surface net"
        assert mesh["inputs"]["threshold"] == 0.6

    def test_mesh_feeds_save_glb(self):
        """The union-superset edge: MESH into SaveGLB's FILE_3D_* union."""
        workflow = build_3d_workflow(_REF)
        save = _node_of_type(workflow, "SaveGLB")
        voxel_to_mesh_id = next(
            nid for nid, n in workflow.items() if n["class_type"] == "VoxelToMesh"
        )
        assert save["inputs"]["mesh"] == [voxel_to_mesh_id, 0]
        assert save["inputs"]["filename_prefix"] == "3d/ComfyUI"

    def test_vae_comes_from_checkpoint_not_separate_loader(self):
        workflow = build_3d_workflow(_REF)
        decode = _node_of_type(workflow, "VAEDecodeHunyuan3D")
        loader_id = next(
            nid for nid, n in workflow.items() if n["class_type"] == "ImageOnlyCheckpointLoader"
        )
        assert decode["inputs"]["vae"] == [loader_id, 2]

    def test_requires_image_ref(self):
        with pytest.raises(ValueError, match="image"):
            build_3d_workflow("")

    def test_seed_resolution(self):
        workflow = build_3d_workflow(_REF, seed=1234)
        assert _node_of_type(workflow, "KSampler")["inputs"]["seed"] == 1234
        workflow = build_3d_workflow(_REF)  # seed -1 -> concrete random
        assert _node_of_type(workflow, "KSampler")["inputs"]["seed"] >= 0


class TestThreeDPresets:
    def test_preset_names(self):
        assert set(list_3d_presets()) == {"standard", "draft", "detail"}

    def test_presets_differ_where_promised(self):
        assert THREE_D_PRESETS["draft"].steps < THREE_D_PRESETS["standard"].steps
        assert (
            THREE_D_PRESETS["detail"].octree_resolution
            > THREE_D_PRESETS["standard"].octree_resolution
        )

    def test_overrides_apply(self):
        workflow = build_3d_workflow(_REF, preset="draft", steps=7, threshold=0.4)
        sampler = _node_of_type(workflow, "KSampler")
        assert sampler["inputs"]["steps"] == 7
        assert _node_of_type(workflow, "VoxelToMesh")["inputs"]["threshold"] == 0.4

    def test_unknown_preset_falls_back_to_standard(self):
        workflow = build_3d_workflow(_REF, preset="nope")
        assert _node_of_type(workflow, "KSampler")["inputs"]["steps"] == 30

    def test_settings_to_dict_round_trip(self):
        settings = ThreeDSettings(algorithm=MeshAlgorithm.BASIC, steps=12)
        d = settings.to_dict()
        assert d["algorithm"] == "basic"
        assert d["steps"] == 12


class TestThreeDModelInfo:
    def test_default_family_is_core_only(self):
        """Hunyuan3D-2 native core is the point; no packs may creep in."""
        assert THREE_D_MODEL_INFO["hunyuan3d_v2"].requires_packs == []

    def test_declared_presets_exist(self):
        for info in THREE_D_MODEL_INFO.values():
            for preset in info.presets:
                assert preset in THREE_D_PRESETS

    def test_builder_singleton(self):
        assert get_three_d_builder() is get_three_d_builder()
        assert isinstance(get_three_d_builder(), ThreeDWorkflowBuilder)
