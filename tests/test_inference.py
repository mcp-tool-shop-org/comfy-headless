"""Tests for comfy_headless/inference.py -- the inference profile."""

import pytest

from comfy_headless.inference import (
    FLORENCE2_TASKS,
    INFERENCE_MODEL_INFO,
    InferenceSettings,
    InferenceTask,
    build_inference_workflow,
    get_inference_builder,
)

_REF = "uploaded_00001.png"


def _node_of_type(workflow, class_type):
    matches = [n for n in workflow.values() if n["class_type"] == class_type]
    assert len(matches) == 1, f"expected exactly one {class_type}, got {len(matches)}"
    return matches[0]


class TestTaskMapping:
    def test_every_task_maps_to_a_florence2_task(self):
        for task in InferenceTask:
            assert task in FLORENCE2_TASKS

    def test_tag_uses_prompt_gen(self):
        """WD14 is not in the catalog; tagging rides Florence-2 PromptGen."""
        assert FLORENCE2_TASKS[InferenceTask.TAG] == "prompt_gen_tags"
        workflow = build_inference_workflow(_REF, task="tag")
        loader = _node_of_type(workflow, "DownloadAndLoadFlorence2Model")
        assert "PromptGen" in loader["inputs"]["model"]


class TestTextTasks:
    @pytest.mark.parametrize(
        "task", ["caption", "detailed_caption", "more_detailed_caption", "tag", "ocr"]
    )
    def test_text_tasks_terminate_in_save_text(self, task):
        workflow = build_inference_workflow(_REF, task=task)
        run = _node_of_type(workflow, "Florence2Run")
        save = _node_of_type(workflow, "SaveText")
        # Florence2Run outputs: IMAGE, MASK, STRING, JSON -- text is index 2.
        run_id = next(nid for nid, n in workflow.items() if n is run)
        assert save["inputs"]["text"] == [run_id, 2]

    def test_caption_task_value(self):
        workflow = build_inference_workflow(_REF, task="caption")
        assert _node_of_type(workflow, "Florence2Run")["inputs"]["task"] == "caption"

    def test_format_override(self):
        workflow = build_inference_workflow(_REF, task="caption", format="md")
        assert _node_of_type(workflow, "SaveText")["inputs"]["format"] == "md"


class TestDetect:
    def test_detect_bridges_json_through_coordinates(self):
        """JSON -> STRING is not a valid edge; the bridge is mandatory."""
        workflow = build_inference_workflow(_REF, task="detect", text_input="the red car")
        run_id = next(nid for nid, n in workflow.items() if n["class_type"] == "Florence2Run")
        coords = _node_of_type(workflow, "Florence2toCoordinates")
        save = _node_of_type(workflow, "SaveText")
        # data comes from Florence2Run's JSON output (index 3)
        assert coords["inputs"]["data"] == [run_id, 3]
        coords_id = next(
            nid for nid, n in workflow.items() if n["class_type"] == "Florence2toCoordinates"
        )
        assert save["inputs"]["text"] == [coords_id, 0]
        assert save["inputs"]["format"] == "json"

    def test_detect_requires_query(self):
        with pytest.raises(ValueError, match="text_input"):
            build_inference_workflow(_REF, task="detect")

    def test_detect_passes_query(self):
        workflow = build_inference_workflow(_REF, task="detect", text_input="a dog")
        assert _node_of_type(workflow, "Florence2Run")["inputs"]["text_input"] == "a dog"


class TestSegment:
    def test_segment_terminates_in_save_image(self):
        workflow = build_inference_workflow(_REF, task="segment", text_input="the person")
        run_id = next(nid for nid, n in workflow.items() if n["class_type"] == "Florence2Run")
        mask_to_image = _node_of_type(workflow, "MaskToImage")
        save = _node_of_type(workflow, "SaveImage")
        # MASK is Florence2Run output index 1
        assert mask_to_image["inputs"]["mask"] == [run_id, 1]
        mti_id = next(nid for nid, n in workflow.items() if n["class_type"] == "MaskToImage")
        assert save["inputs"]["images"] == [mti_id, 0]

    def test_segment_fills_mask(self):
        workflow = build_inference_workflow(_REF, task="segment", text_input="x")
        assert _node_of_type(workflow, "Florence2Run")["inputs"]["fill_mask"] is True

    def test_non_segment_does_not_fill_mask(self):
        workflow = build_inference_workflow(_REF, task="caption")
        assert _node_of_type(workflow, "Florence2Run")["inputs"]["fill_mask"] is False

    def test_segment_requires_query(self):
        with pytest.raises(ValueError, match="text_input"):
            build_inference_workflow(_REF, task="segment")


class TestOutputNodeGuard:
    def test_every_task_graph_has_an_output_node(self):
        """The profile's most likely silent failure, structurally impossible."""
        from comfy_headless.addressing import has_output_node

        for task in InferenceTask:
            workflow = build_inference_workflow(
                _REF, task=task.value, text_input="query for grounding tasks"
            )
            assert has_output_node(workflow), task

    def test_builder_guard_rejects_terminatorless_graph(self):
        """The guard itself must bite when a graph loses its terminator."""
        from comfy_headless.addressing import require_output_node
        from comfy_headless.exceptions import ValidationError

        workflow = build_inference_workflow(_REF, task="caption")
        stripped = {nid: n for nid, n in workflow.items() if n["class_type"] != "SaveText"}
        with pytest.raises(ValidationError):
            require_output_node(stripped)


class TestSettingsAndInfo:
    def test_requires_image(self):
        with pytest.raises(ValueError, match="image"):
            build_inference_workflow("", task="caption")

    def test_default_model_for_captions(self):
        workflow = build_inference_workflow(_REF, task="caption")
        loader = _node_of_type(workflow, "DownloadAndLoadFlorence2Model")
        assert loader["inputs"]["model"] == "microsoft/Florence-2-large"

    def test_model_override(self):
        workflow = build_inference_workflow(_REF, task="caption", model="microsoft/Florence-2-base")
        loader = _node_of_type(workflow, "DownloadAndLoadFlorence2Model")
        assert loader["inputs"]["model"] == "microsoft/Florence-2-base"

    def test_florence_family_declares_its_pack(self):
        assert INFERENCE_MODEL_INFO["florence2"].requires_packs == ["comfyui-florence2"]
        assert INFERENCE_MODEL_INFO["florence2_coordinates"].requires_packs == [
            "comfyui-segment-anything-2"
        ]

    def test_settings_to_dict(self):
        d = InferenceSettings(task=InferenceTask.DETECT, text_input="x").to_dict()
        assert d["task"] == "detect"
        assert d["text_input"] == "x"

    def test_builder_singleton(self):
        assert get_inference_builder() is get_inference_builder()

    def test_detect_index_override(self):
        workflow = build_inference_workflow(
            _REF, task="detect", text_input="cars", detect_index="1"
        )
        coords = _node_of_type(workflow, "Florence2toCoordinates")
        assert coords["inputs"]["index"] == "1"
