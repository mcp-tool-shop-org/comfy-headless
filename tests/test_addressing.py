"""
Tests for comfy_headless/addressing.py -- the graph addressing/typing layer.

The centerpiece is the ZERO-REJECTIONS CORPUS GATE: every known-good graph
the profile builders emit must pass the client-side type checker with zero
errors against a frozen catalog snapshot. A client stricter than the server
manufactures false rejections by construction (a validator that treated
union mismatch as a hard error rejected 2 of 4 known-good graphs, measured);
this gate keeps that regression class impossible.
"""

import pytest

from comfy_headless.addressing import (
    ANY_TYPE,
    COMBO_TYPE,
    MATCH_TYPE,
    SAVE_AUDIO_FORMAT,
    SAVE_VIDEO_CODEC,
    DynamicCombo,
    GraphTypeChecker,
    TypeMatch,
    extract_object_info_types,
    get_node_input,
    has_output_node,
    join_field_path,
    match_types,
    parse_field_path,
    require_output_node,
    set_node_input,
    validate_node_input,
)
from comfy_headless.exceptions import (
    GraphAddressError,
    InvalidParameterError,
    ValidationError,
)

# =============================================================================
# validate_node_input -- server-parity transcription
# =============================================================================


class TestValidateNodeInput:
    """Behavioural parity with ComfyUI's own comfy_execution/validation.py."""

    def test_exact_match(self):
        assert validate_node_input("IMAGE", "IMAGE") is True

    def test_any_type_either_side(self):
        assert validate_node_input(ANY_TYPE, "IMAGE") is True
        assert validate_node_input("IMAGE", ANY_TYPE) is True

    def test_match_type_either_side(self):
        assert validate_node_input(MATCH_TYPE, "IMAGE") is True
        assert validate_node_input("IMAGE", MATCH_TYPE) is True

    def test_options_list_into_combo(self):
        assert validate_node_input(["a", "b"], COMBO_TYPE) is True

    def test_options_list_into_non_combo_rejected(self):
        assert validate_node_input(["a", "b"], "STRING") is False

    def test_docstring_examples(self):
        # From the server's own docstring:
        assert validate_node_input("STRING", "STRING,INT", strict=True) is True
        assert validate_node_input("STRING,INT", "INT", strict=True) is False
        assert validate_node_input("STRING,BOOLEAN", "STRING,INT") is True

    def test_union_superset_mesh_into_save_glb(self):
        """The canonical case: MESH into SaveGLB's 14-member FILE_3D_* union."""
        declared = (
            "MESH,FILE_3D_GLB,FILE_3D_GLTF,FILE_3D_OBJ,FILE_3D_FBX,FILE_3D_STL,"
            "FILE_3D_USDZ,FILE_3D_PLY,FILE_3D_SPLAT,FILE_3D_SPZ,FILE_3D_KSPLAT,"
            "FILE_3D_SPLAT_ANY,FILE_3D_POINT_CLOUD_ANY,FILE_3D"
        )
        assert validate_node_input("MESH", declared) is True
        assert validate_node_input("MESH", declared, strict=True) is True

    def test_disjoint_rejected(self):
        assert validate_node_input("JSON", "STRING") is False
        assert validate_node_input("IMAGE", "LATENT") is False

    def test_whitespace_in_unions(self):
        assert validate_node_input("A , B", "B , C") is True

    def test_star_inside_union(self):
        assert validate_node_input("A,*", "B") is True
        assert validate_node_input("A", "B,*") is True

    def test_non_string_non_list(self):
        assert validate_node_input(42, "INT") is False


class TestMatchTypes:
    """match_types().accepted must agree with validate_node_input everywhere."""

    CASES = [
        ("IMAGE", "IMAGE"),
        (ANY_TYPE, "IMAGE"),
        ("IMAGE", ANY_TYPE),
        (MATCH_TYPE, "X"),
        (["a"], COMBO_TYPE),
        (["a"], "STRING"),
        ("STRING", "STRING,INT"),
        ("STRING,INT", "INT"),
        ("STRING,BOOLEAN", "STRING,INT"),
        ("JSON", "STRING"),
        ("MESH", "MESH,FILE_3D_GLB"),
        ("A,*", "B"),
        (42, "INT"),
    ]

    @pytest.mark.parametrize("received,declared", CASES)
    def test_accepted_agrees_with_server_rule(self, received, declared):
        assert match_types(received, declared).accepted == validate_node_input(received, declared)

    def test_classifications(self):
        assert match_types("IMAGE", "IMAGE") is TypeMatch.EXACT
        assert match_types("*", "IMAGE") is TypeMatch.ANY
        assert match_types(MATCH_TYPE, "IMAGE") is TypeMatch.MATCH_TEMPLATE
        assert match_types(["a"], COMBO_TYPE) is TypeMatch.COMBO_OPTIONS
        assert match_types("MESH", "MESH,FILE_3D_GLB") is TypeMatch.SUBSET
        assert match_types("STRING,BOOLEAN", "STRING,INT") is TypeMatch.OVERLAP
        assert match_types("JSON", "STRING") is TypeMatch.DISJOINT

    def test_only_overlap_warns(self):
        assert match_types("STRING,BOOLEAN", "STRING,INT").warning is True
        assert match_types("MESH", "MESH,FILE_3D_GLB").warning is False
        assert match_types("JSON", "STRING").warning is False


# =============================================================================
# Dotted field paths
# =============================================================================


class TestFieldPaths:
    def test_simple(self):
        assert parse_field_path("codec") == ("codec",)

    def test_nested(self):
        assert parse_field_path("codec.encoding.crf") == ("codec", "encoding", "crf")

    def test_escaped_dot(self):
        assert parse_field_path(r"a\.b.c") == ("a.b", "c")

    def test_escaped_backslash(self):
        assert parse_field_path("a\\\\b") == ("a\\b",)

    def test_round_trip(self):
        for path in [("codec", "encoding", "crf"), ("a.b", "c"), ("x\\y",)]:
            assert parse_field_path(join_field_path(path)) == path

    def test_tuple_passthrough(self):
        assert parse_field_path(("a", "b")) == ("a", "b")

    def test_empty_segment_rejected(self):
        for bad in ["", ".a", "a.", "a..b"]:
            with pytest.raises(GraphAddressError):
                parse_field_path(bad)

    def test_dangling_escape_rejected(self):
        with pytest.raises(GraphAddressError):
            parse_field_path("a\\")

    def test_non_string_rejected(self):
        with pytest.raises(GraphAddressError):
            parse_field_path(None)


class TestNodeInputAccess:
    def test_set_writes_flattened_key(self):
        workflow = {"7": {"class_type": "SaveVideo", "inputs": {}}}
        set_node_input(workflow, "7", "codec.encoding.crf", 20)
        assert workflow["7"]["inputs"]["codec.encoding.crf"] == 20

    def test_set_never_creates_nodes(self):
        """No auto-vivification -- the lodash CVE-2020-8203 lesson."""
        workflow = {}
        with pytest.raises(GraphAddressError):
            set_node_input(workflow, "99", "codec", "auto")
        assert workflow == {}

    def test_get_reads_flattened_key(self):
        workflow = {"7": {"class_type": "SaveVideo", "inputs": {"codec.encoding": "auto"}}}
        assert get_node_input(workflow, "7", "codec.encoding") == "auto"
        assert get_node_input(workflow, "7", "missing", default="d") == "d"

    def test_get_missing_node_raises(self):
        with pytest.raises(GraphAddressError):
            get_node_input({}, "1", "x")


# =============================================================================
# Presence-aware dynamic combos
# =============================================================================


class TestDynamicCombo:
    def test_flac_emits_no_quality(self):
        assert SAVE_AUDIO_FORMAT.build("flac") == {"format": "flac"}

    def test_mp3_emits_dotted_quality(self):
        assert SAVE_AUDIO_FORMAT.build("mp3", quality="320k") == {
            "format": "mp3",
            "format.quality": "320k",
        }

    def test_inactive_branch_rejected_at_construction(self):
        """quality under flac is the inactive-branch bug class."""
        with pytest.raises(GraphAddressError):
            SAVE_AUDIO_FORMAT.build("flac", quality="320k")

    def test_invalid_choice_rejected(self):
        with pytest.raises(InvalidParameterError):
            SAVE_AUDIO_FORMAT.build("wav")

    def test_nested_codec_chain(self):
        assert SAVE_VIDEO_CODEC.build("h264", {"encoding": "re-encode", "encoding.crf": 20}) == {
            "codec": "h264",
            "codec.encoding": "re-encode",
            "codec.encoding.crf": 20,
        }

    def test_nested_optional_selector_can_be_omitted(self):
        assert SAVE_VIDEO_CODEC.build("h264") == {"codec": "h264"}
        assert SAVE_VIDEO_CODEC.build("auto") == {"codec": "auto"}

    def test_child_without_parent_selection_rejected(self):
        with pytest.raises(GraphAddressError, match="encoding"):
            SAVE_VIDEO_CODEC.build("h264", {"encoding.crf": 20})

    def test_crf_under_auto_encoding_rejected(self):
        with pytest.raises(GraphAddressError):
            SAVE_VIDEO_CODEC.build("h264", {"encoding": "auto", "encoding.crf": 20})

    def test_encoding_under_auto_codec_rejected(self):
        with pytest.raises(GraphAddressError):
            SAVE_VIDEO_CODEC.build("auto", {"encoding": "auto"})

    def test_invalid_nested_choice_rejected(self):
        with pytest.raises(InvalidParameterError):
            SAVE_VIDEO_CODEC.build("h264", {"encoding": "vp9"})

    def test_stale_sibling_cannot_survive_tag_change(self):
        """
        The typestate/clear-siblings property: the fragment is built fresh
        from the tag, so values from a previous choice cannot leak through.
        """
        lossy = SAVE_AUDIO_FORMAT.build("mp3", quality="320k")
        assert "format.quality" in lossy
        lossless = SAVE_AUDIO_FORMAT.build("flac")
        assert "format.quality" not in lossless

    def test_unknown_field_names_active_set(self):
        combo = DynamicCombo(name="mode", branches={"a": {"x": None}, "b": {}})
        with pytest.raises(GraphAddressError) as excinfo:
            combo.build("b", x=1)
        assert "not active" in str(excinfo.value)


# =============================================================================
# Output-node guard
# =============================================================================


class TestOutputNodeGuard:
    def test_graph_with_save_node_passes(self):
        workflow = {"1": {"class_type": "SaveText", "inputs": {}}}
        assert has_output_node(workflow) is True
        require_output_node(workflow)  # no raise

    def test_bare_captioner_graph_rejected(self):
        """The run-green-return-nothing failure mode."""
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {}},
            "2": {"class_type": "Florence2Run", "inputs": {}},
        }
        assert has_output_node(workflow) is False
        with pytest.raises(ValidationError):
            require_output_node(workflow)

    def test_empty_graph_rejected(self):
        with pytest.raises(ValidationError):
            require_output_node({})


# =============================================================================
# extract_object_info_types -- tolerant /object_info parsing
# =============================================================================


class TestExtractObjectInfoTypes:
    def test_normalizes_required_and_optional(self):
        raw = {
            "Foo": {
                "input": {
                    "required": {"a": ["IMAGE"], "b": [["x", "y"], {"default": "x"}]},
                    "optional": {"c": ["VAE", {}]},
                },
                "output": ["IMAGE", "MASK"],
            }
        }
        catalog = extract_object_info_types(raw)
        assert catalog["Foo"]["inputs"] == {"a": "IMAGE", "b": "COMBO", "c": "VAE"}
        assert catalog["Foo"]["outputs"] == ["IMAGE", "MASK"]

    def test_tolerates_malformed_entries(self):
        raw = {
            "Junk1": "not a dict",
            "Junk2": {"input": "nope", "output": "nope"},
            "Junk3": {"input": {"required": {"x": None}}, "output": [None, 3]},
        }
        catalog = extract_object_info_types(raw)
        assert "Junk1" not in catalog
        assert catalog["Junk2"] == {"inputs": {}, "outputs": []}
        # Non-string junk outputs degrade to the Any type, never crash.
        assert catalog["Junk3"]["outputs"] == ["*", "*"]

    def test_legacy_list_output_preserved_for_combo_edges(self):
        raw = {"Foo": {"input": {"required": {}}, "output": [["opt1", "opt2"]]}}
        catalog = extract_object_info_types(raw)
        assert catalog["Foo"]["outputs"] == [["opt1", "opt2"]]


# =============================================================================
# THE ZERO-REJECTIONS CORPUS GATE
# =============================================================================
#
# Frozen catalog snapshot (types only), transcribed from the live /object_info
# schemas on 2026-08-21. This is a test fixture, not shipped truth -- the
# runtime checker always consumes a live /object_info.

_T = {  # class_type -> (inputs {name: type}, outputs [type, ...])
    # --- shared core ---
    "LoadImage": ({"image": "COMBO"}, ["IMAGE", "MASK"]),
    "LoadAudio": ({"audio": "COMBO"}, ["AUDIO"]),
    "SaveImage": ({"images": "IMAGE", "filename_prefix": "STRING"}, ["IMAGE"]),
    "KSampler": (
        {
            "model": "MODEL",
            "seed": "INT",
            "steps": "INT",
            "cfg": "FLOAT",
            "sampler_name": "COMBO",
            "scheduler": "COMBO",
            "positive": "CONDITIONING",
            "negative": "CONDITIONING",
            "latent_image": "LATENT",
            "denoise": "FLOAT",
        },
        ["LATENT"],
    ),
    "CheckpointLoaderSimple": ({"ckpt_name": "COMBO"}, ["MODEL", "CLIP", "VAE"]),
    "CLIPTextEncode": ({"clip": "CLIP", "text": "STRING"}, ["CONDITIONING"]),
    "VAELoader": ({"vae_name": "COMBO"}, ["VAE"]),
    "VAEDecode": ({"samples": "LATENT", "vae": "VAE"}, ["IMAGE"]),
    "UNETLoader": ({"unet_name": "COMBO", "weight_dtype": "COMBO"}, ["MODEL"]),
    "CLIPLoader": ({"clip_name": "COMBO", "type": "COMBO", "device": "COMBO"}, ["CLIP"]),
    "DualCLIPLoader": (
        {"clip_name1": "COMBO", "clip_name2": "COMBO", "type": "COMBO", "device": "COMBO"},
        ["CLIP"],
    ),
    "CLIPVisionLoader": ({"clip_name": "COMBO"}, ["CLIP_VISION"]),
    "CLIPVisionEncode": (
        {"clip_vision": "CLIP_VISION", "image": "IMAGE", "crop": "COMBO"},
        ["CLIP_VISION_OUTPUT"],
    ),
    "MaskToImage": ({"mask": "MASK"}, ["IMAGE"]),
    "Canny": ({"image": "IMAGE", "low_threshold": "FLOAT", "high_threshold": "FLOAT"}, ["IMAGE"]),
    "EmptyLatentImage": ({"width": "INT", "height": "INT", "batch_size": "INT"}, ["LATENT"]),
    "EmptySD3LatentImage": ({"width": "INT", "height": "INT", "batch_size": "INT"}, ["LATENT"]),
    "ModelSamplingAuraFlow": ({"model": "MODEL", "shift": "FLOAT"}, ["MODEL"]),
    "ModelSamplingSD3": ({"model": "MODEL", "shift": "FLOAT"}, ["MODEL"]),
    # --- 3D profile ---
    "ImageOnlyCheckpointLoader": ({"ckpt_name": "COMBO"}, ["MODEL", "CLIP_VISION", "VAE"]),
    "Hunyuan3Dv2Conditioning": (
        {"clip_vision_output": "CLIP_VISION_OUTPUT"},
        ["CONDITIONING", "CONDITIONING"],
    ),
    "EmptyLatentHunyuan3Dv2": ({"resolution": "INT", "batch_size": "INT"}, ["LATENT"]),
    "VAEDecodeHunyuan3D": (
        {"samples": "LATENT", "vae": "VAE", "num_chunks": "INT", "octree_resolution": "INT"},
        ["VOXEL"],
    ),
    "VoxelToMesh": ({"voxel": "VOXEL", "algorithm": "COMBO", "threshold": "FLOAT"}, ["MESH"]),
    "SaveGLB": (
        {
            "mesh": (
                "MESH,FILE_3D_GLB,FILE_3D_GLTF,FILE_3D_OBJ,FILE_3D_FBX,FILE_3D_STL,"
                "FILE_3D_USDZ,FILE_3D_PLY,FILE_3D_SPLAT,FILE_3D_SPZ,FILE_3D_KSPLAT,"
                "FILE_3D_SPLAT_ANY,FILE_3D_POINT_CLOUD_ANY,FILE_3D"
            ),
            "filename_prefix": "STRING",
        },
        [],
    ),
    # --- audio profile ---
    "TextEncodeAceStepAudio1.5": (
        {
            "clip": "CLIP",
            "tags": "STRING",
            "lyrics": "STRING",
            "seed": "INT",
            "bpm": "INT",
            "duration": "FLOAT",
            "timesignature": "COMBO",
            "language": "COMBO",
            "keyscale": "COMBO",
            "generate_audio_codes": "BOOLEAN",
            "cfg_scale": "FLOAT",
            "temperature": "FLOAT",
            "top_p": "FLOAT",
            "top_k": "INT",
            "min_p": "FLOAT",
        },
        ["CONDITIONING"],
    ),
    "EmptyAceStep1.5LatentAudio": ({"seconds": "FLOAT", "batch_size": "INT"}, ["LATENT"]),
    "VAEDecodeAudio": ({"samples": "LATENT", "vae": "VAE"}, ["AUDIO"]),
    "SaveAudioAdvanced": (
        {"audio": "AUDIO", "filename_prefix": "STRING", "format": "COMFY_DYNAMICCOMBO_V3"},
        ["AUDIO"],
    ),
    "AudioSeparation": (
        {
            "audio": "AUDIO",
            "chunk_fade_shape": "COMBO",
            "chunk_length": "FLOAT",
            "chunk_overlap": "FLOAT",
        },
        ["AUDIO", "AUDIO", "AUDIO", "AUDIO"],
    ),
    # --- inference profile ---
    "DownloadAndLoadFlorence2Model": (
        {"model": "COMBO", "precision": "COMBO", "attention": "COMBO"},
        ["FL2MODEL"],
    ),
    "Florence2Run": (
        {
            "image": "IMAGE",
            "florence2_model": "FL2MODEL",
            "text_input": "STRING",
            "task": "COMBO",
            "fill_mask": "BOOLEAN",
            "keep_model_loaded": "BOOLEAN",
            "max_new_tokens": "INT",
            "num_beams": "INT",
            "do_sample": "BOOLEAN",
            "output_mask_select": "STRING",
            "seed": "INT",
        },
        ["IMAGE", "MASK", "STRING", "JSON"],
    ),
    "Florence2toCoordinates": (
        {"data": "JSON", "index": "STRING", "batch": "BOOLEAN"},
        ["STRING", "BBOX"],
    ),
    "SaveText": (
        {"text": "STRING", "filename_prefix": "STRING", "format": "COMBO"},
        ["STRING"],
    ),
    # --- image profile (ControlNet / Edit) ---
    "TextEncodeQwenImageEditPlus": (
        {
            "clip": "CLIP",
            "prompt": "STRING",
            "vae": "VAE",
            "image1": "IMAGE",
            "image2": "IMAGE",
            "image3": "IMAGE",
        },
        ["CONDITIONING"],
    ),
    "ControlNetLoader": ({"control_net_name": "COMBO"}, ["CONTROL_NET"]),
    "SetUnionControlNetType": (
        {"control_net": "CONTROL_NET", "type": "COMBO"},
        ["CONTROL_NET"],
    ),
    "ControlNetApplyAdvanced": (
        {
            "positive": "CONDITIONING",
            "negative": "CONDITIONING",
            "control_net": "CONTROL_NET",
            "image": "IMAGE",
            "strength": "FLOAT",
            "start_percent": "FLOAT",
            "end_percent": "FLOAT",
            "vae": "VAE",
        },
        ["CONDITIONING", "CONDITIONING"],
    ),
    # --- video profile (hunyuan 1.5 + core output) ---
    "EmptyHunyuanVideo15Latent": (
        {"width": "INT", "height": "INT", "length": "INT", "batch_size": "INT"},
        ["LATENT"],
    ),
    "HunyuanVideo15ImageToVideo": (
        {
            "positive": "CONDITIONING",
            "negative": "CONDITIONING",
            "vae": "VAE",
            "width": "INT",
            "height": "INT",
            "length": "INT",
            "batch_size": "INT",
            "start_image": "IMAGE",
            "clip_vision_output": "CLIP_VISION_OUTPUT",
        },
        ["CONDITIONING", "CONDITIONING", "LATENT"],
    ),
    "CFGGuider": (
        {"model": "MODEL", "positive": "CONDITIONING", "negative": "CONDITIONING", "cfg": "FLOAT"},
        ["GUIDER"],
    ),
    "BasicScheduler": (
        {"model": "MODEL", "scheduler": "COMBO", "steps": "INT", "denoise": "FLOAT"},
        ["SIGMAS"],
    ),
    "RandomNoise": ({"noise_seed": "INT"}, ["NOISE"]),
    "KSamplerSelect": ({"sampler_name": "COMBO"}, ["SAMPLER"]),
    "SamplerCustomAdvanced": (
        {
            "noise": "NOISE",
            "guider": "GUIDER",
            "sampler": "SAMPLER",
            "sigmas": "SIGMAS",
            "latent_image": "LATENT",
        },
        ["LATENT", "LATENT"],
    ),
    "CreateVideo": (
        {"images": "IMAGE", "fps": "FLOAT", "audio": "AUDIO", "bit_depth": "INT"},
        ["VIDEO"],
    ),
    "SaveVideo": (
        {
            "video": "VIDEO",
            "filename_prefix": "STRING",
            "format": "COMBO",
            "codec": "COMFY_DYNAMICCOMBO_V3",
        },
        ["VIDEO"],
    ),
    # --- video profile (animatediff path, pack nodes) ---
    "ADE_LoadAnimateDiffModel": ({"model_name": "COMBO"}, ["MOTION_MODEL_ADE"]),
    "ADE_ApplyAnimateDiffModel": (
        {"model": "MODEL", "motion_model": "MOTION_MODEL_ADE", "scale_multival": "FLOAT"},
        ["MODEL"],
    ),
    "ADE_EmptyLatentImageLarge": (
        {"width": "INT", "height": "INT", "batch_size": "INT"},
        ["LATENT"],
    ),
    "VHS_VideoCombine": (
        {"images": "IMAGE", "frame_rate": "FLOAT", "filename_prefix": "STRING"},
        ["VHS_FILENAMES"],
    ),
}

FROZEN_CATALOG = {name: {"inputs": spec[0], "outputs": spec[1]} for name, spec in _T.items()}


def _corpus():
    """Every known-good graph the profile builders can emit."""
    import copy

    from comfy_headless.audio import build_audio_separation_workflow, build_audio_workflow
    from comfy_headless.inference import build_inference_workflow
    from comfy_headless.three_d import build_3d_workflow
    from comfy_headless.video import VIDEO_PRESETS, VideoWorkflowBuilder
    from comfy_headless.workflows import (
        build_controlnet_workflow,
        build_qwen_edit_workflow,
        compile_workflow,
    )

    ref = "uploaded_00001.png"
    yield "3d_standard", build_3d_workflow(ref)
    yield "3d_detail", build_3d_workflow(ref, preset="detail")
    yield "audio_music", build_audio_workflow("lo-fi, jazz")
    yield "audio_mp3", build_audio_workflow("rock", preset="music_mp3")
    yield "audio_separation", build_audio_separation_workflow("song_00001.flac")
    for task in ("caption", "tag", "ocr", "more_detailed_caption"):
        yield f"inference_{task}", build_inference_workflow(ref, task=task)
    yield "inference_detect", build_inference_workflow(ref, task="detect", text_input="a car")
    yield (
        "inference_segment",
        build_inference_workflow(ref, task="segment", text_input="the person"),
    )
    compiled = compile_workflow(prompt="a castle", template_id="qwen_txt2img", preset="")
    assert compiled.is_valid, compiled.errors
    yield "qwen_txt2img", compiled.workflow
    yield "qwen_edit", build_qwen_edit_workflow("make it night", [ref, ref])
    yield "controlnet_qwen", build_controlnet_workflow("a fortress", ref, control_type="depth")
    yield (
        "controlnet_qwen_canny",
        build_controlnet_workflow(
            "a fortress", ref, control_type="canny/lineart/anime_lineart/mlsd", preprocess="canny"
        ),
    )
    yield (
        "controlnet_sdxl",
        build_controlnet_workflow("a fortress", ref, base="sdxl", control_type="depth"),
    )

    builder = VideoWorkflowBuilder()
    hy = copy.deepcopy(VIDEO_PRESETS["hunyuan15_720p"])
    yield "video_hunyuan15_t2v", builder.build("a cat", "blurry", hy)
    hy_i2v = copy.deepcopy(VIDEO_PRESETS["hunyuan15_i2v"])
    yield "video_hunyuan15_i2v", builder.build("a cat", "blurry", hy_i2v, init_image=ref)
    std = copy.deepcopy(VIDEO_PRESETS["standard"])
    yield "video_standard_vhs", builder.build("a cat", "blurry", std)
    std_core = copy.deepcopy(VIDEO_PRESETS["standard"])
    std_core.output = "core"
    yield "video_standard_core", builder.build("a cat", "blurry", std_core)


class TestZeroRejectionsCorpusGate:
    """
    RELEASE GATE: the client-side type checker must accept every known-good
    graph with zero errors. A failure here means the checker became stricter
    than the server -- fix the checker, never the graphs.
    """

    def test_catalog_covers_every_corpus_class(self):
        """No edge may escape the gate by falling into skip-unknown."""
        missing = set()
        for _name, workflow in _corpus():
            for node in workflow.values():
                if node["class_type"] not in FROZEN_CATALOG:
                    missing.add(node["class_type"])
        assert not missing, f"extend FROZEN_CATALOG with: {sorted(missing)}"

    def test_zero_rejections_on_known_good_corpus(self):
        checker = GraphTypeChecker(FROZEN_CATALOG)
        rejections = {}
        for name, workflow in _corpus():
            errors = checker.errors(workflow)
            if errors:
                rejections[name] = [e.message for e in errors]
        assert not rejections, f"false rejections on known-good graphs: {rejections}"

    def test_zero_warnings_on_known_good_corpus(self):
        """Our own emitted graphs should not even warrant overlap warnings."""
        checker = GraphTypeChecker(FROZEN_CATALOG)
        warned = {}
        for name, workflow in _corpus():
            warnings = [i for i in checker.check(workflow) if i.severity == "warning"]
            if warnings:
                warned[name] = [w.message for w in warnings]
        assert not warned, f"unexpected type warnings: {warned}"

    def test_checker_still_catches_a_real_error(self):
        """The gate must not pass because the checker is toothless."""
        checker = GraphTypeChecker(FROZEN_CATALOG)
        bad = {
            "1": {"class_type": "Florence2Run", "inputs": {}},
            # JSON output wired straight into SaveText's STRING input:
            # exactly the invalid edge the detect leg must bridge.
            "2": {
                "class_type": "SaveText",
                "inputs": {"text": ["1", 3], "filename_prefix": "x", "format": "json"},
            },
        }
        errors = checker.errors(bad)
        assert len(errors) == 1
        assert errors[0].received == "JSON"
        assert errors[0].declared == "STRING"

    def test_every_corpus_graph_has_an_output_node(self):
        for name, workflow in _corpus():
            assert has_output_node(workflow), f"{name} has no output node"

    def test_corpus_has_no_dangling_links(self):
        for name, workflow in _corpus():
            ids = set(workflow)
            for node_id, node in workflow.items():
                for key, value in node.get("inputs", {}).items():
                    if isinstance(value, list) and len(value) == 2:
                        assert str(value[0]) in ids, f"{name}: {node_id}.{key} -> {value[0]}"
