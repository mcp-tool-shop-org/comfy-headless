"""
Comfy Headless - Inference Module
=================================

v3.1.0: the inference profile -- non-generative model calls through ComfyUI:
caption, tag, detect, segment, OCR.

The load-bearing mechanic: a STRING/JSON result reaches ``/history`` ONLY if
it terminates in a node with ``OUTPUT_NODE=True``. A bare captioner's output
is invisible to a headless caller -- the graph runs green and returns
nothing. Every builder here therefore terminates in core ``SaveText``
(category ``text``, ``format: txt|csv|md|json``) or, for masks, core
``SaveImage`` -- and every built graph passes the
:func:`comfy_headless.addressing.require_output_node` guard before it is
returned.

``SaveText`` reports BOTH the inline text (history outputs key ``"text"``)
and the saved file (key ``"files"``), so callers usually need no second
round-trip to read a caption.

This profile is custom-pack territory -- there is no core captioner, tagger
or detector. Verified against the live catalog (2026-08-21):

* Caption / tag / OCR / segment: ``DownloadAndLoadFlorence2Model`` +
  ``Florence2Run`` (pack ``comfyui-florence2``). NOTE: the local-path loader
  ``Florence2ModelLoader`` was NOT present in the catalog, so only the
  auto-downloading loader is emitted.
* Tagging uses ``Florence2Run(task="prompt_gen_tags")`` with the PromptGen
  checkpoint -- the WD14 tagger pack could not be verified in the catalog
  (zero hits) and is deliberately NOT emitted; a class we have not seen in
  ``/object_info`` does not ship.
* Detect: Florence2Run's coordinates leave on its JSON output, and
  JSON -> STRING is not a valid edge, so the ``Florence2toCoordinates``
  converter (pack ``comfyui-segment-anything-2``) bridges into SaveText.
* Segment: ``referring_expression_segmentation`` -> MASK -> core
  ``MaskToImage`` -> core ``SaveImage`` (a PNG the consumer thresholds).

Embed/score surfaces are intentionally absent: nothing verified in the
catalog earns them yet.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .addressing import require_output_node

__all__ = [
    "InferenceTask",
    "InferenceSettings",
    "InferenceModelInfo",
    "INFERENCE_MODEL_INFO",
    "FLORENCE2_TASKS",
    "InferenceWorkflowBuilder",
    "get_inference_builder",
    "build_inference_workflow",
]


class InferenceTask(str, Enum):
    """High-level inference tasks."""

    CAPTION = "caption"
    DETAILED_CAPTION = "detailed_caption"
    MORE_DETAILED_CAPTION = "more_detailed_caption"
    TAG = "tag"
    DETECT = "detect"
    SEGMENT = "segment"
    OCR = "ocr"


# InferenceTask -> Florence2Run task value (verified option list).
FLORENCE2_TASKS: dict[InferenceTask, str] = {
    InferenceTask.CAPTION: "caption",
    InferenceTask.DETAILED_CAPTION: "detailed_caption",
    InferenceTask.MORE_DETAILED_CAPTION: "more_detailed_caption",
    InferenceTask.TAG: "prompt_gen_tags",
    InferenceTask.DETECT: "caption_to_phrase_grounding",
    InferenceTask.SEGMENT: "referring_expression_segmentation",
    InferenceTask.OCR: "ocr",
}

# Tasks whose result is text saved via SaveText.
_TEXT_TASKS = {
    InferenceTask.CAPTION,
    InferenceTask.DETAILED_CAPTION,
    InferenceTask.MORE_DETAILED_CAPTION,
    InferenceTask.TAG,
    InferenceTask.OCR,
}

# Tasks that require a text query (what to find in the image).
_QUERY_TASKS = {InferenceTask.DETECT, InferenceTask.SEGMENT}

# Default Florence-2 checkpoint per task family. The PromptGen fine-tune is
# the one that produces booru-style tags; the base models do captions.
_DEFAULT_MODELS: dict[InferenceTask, str] = {
    InferenceTask.TAG: "MiaoshouAI/Florence-2-base-PromptGen-v1.5",
}
_DEFAULT_MODEL = "microsoft/Florence-2-large"


@dataclass
class InferenceSettings:
    """Settings for inference workflows."""

    task: InferenceTask = InferenceTask.CAPTION
    # Florence-2 checkpoint repo id; None -> per-task default.
    model: str | None = None
    precision: str = "fp16"  # fp16 | bf16 | fp32
    attention: str = "sdpa"  # flash_attention_2 | sdpa | eager
    # Query text for detect/segment (what to look for).
    text_input: str = ""
    max_new_tokens: int = 1024
    num_beams: int = 3
    do_sample: bool = True
    keep_model_loaded: bool = False
    seed: int = 1
    # SaveText format for text results; detect coordinates always use json.
    format: str = "txt"
    # Which detection box Florence2toCoordinates selects ("0" = first;
    # the node's schema default).
    detect_index: str = "0"
    filename_prefix: str = "inference/ComfyUI"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task.value,
            "model": self.model,
            "precision": self.precision,
            "attention": self.attention,
            "text_input": self.text_input,
            "max_new_tokens": self.max_new_tokens,
            "num_beams": self.num_beams,
            "do_sample": self.do_sample,
            "keep_model_loaded": self.keep_model_loaded,
            "seed": self.seed,
            "format": self.format,
            "detect_index": self.detect_index,
            "filename_prefix": self.filename_prefix,
        }


@dataclass
class InferenceModelInfo:
    """Information about an inference model family."""

    id: str
    name: str
    description: str
    tasks: list[InferenceTask] = field(default_factory=list)
    min_vram_gb: int = 4
    estimated_time_seconds: int = 10
    # Custom node packs this family's workflows depend on.
    requires_packs: list[str] = field(default_factory=list)


INFERENCE_MODEL_INFO: dict[str, InferenceModelInfo] = {
    "florence2": InferenceModelInfo(
        id="florence2",
        name="Florence-2",
        description=(
            "Microsoft's compact vision-language model: captioning at three "
            "detail levels, booru-style tagging (PromptGen fine-tune), "
            "phrase-grounded detection, referring-expression segmentation, "
            "and OCR -- one pack covers the whole inference profile."
        ),
        tasks=list(InferenceTask),
        min_vram_gb=4,
        estimated_time_seconds=10,
        requires_packs=["comfyui-florence2"],
    ),
    "florence2_coordinates": InferenceModelInfo(
        id="florence2_coordinates",
        name="Florence2 Coordinates bridge",
        description=(
            "Converts Florence2Run's JSON detection data into a coordinates "
            "STRING that core SaveText can persist (JSON -> STRING is not a "
            "valid edge). Used only by the detect task."
        ),
        tasks=[InferenceTask.DETECT],
        min_vram_gb=0,
        estimated_time_seconds=0,
        requires_packs=["comfyui-segment-anything-2"],
    ),
}


class InferenceWorkflowBuilder:
    """
    Builds ComfyUI workflows for non-generative inference.

    The input image must already be on the ComfyUI server -- upload it with
    ``ComfyClient.upload_image()`` and pass the returned ``"ref"``.
    """

    def build(self, image_ref: str, settings: InferenceSettings) -> dict[str, Any]:
        """
        Build an inference workflow for the given task.

        Returns:
            ComfyUI API-format workflow JSON, guaranteed to terminate in an
            OUTPUT_NODE (guarded by ``require_output_node``).

        Raises:
            ValueError: If the task needs ``text_input`` and none was given,
                or ``image_ref`` is missing.
            ValidationError: If (through a future bug) the built graph lost
                its output node -- the guard that prevents run-green-return-
                nothing.
        """
        if not image_ref:
            raise ValueError("Inference requires an input image (image_ref)")

        task = settings.task
        if task in _QUERY_TASKS and not settings.text_input:
            raise ValueError(f"Task '{task.value}' needs text_input (what to find in the image)")

        model = settings.model or _DEFAULT_MODELS.get(task, _DEFAULT_MODEL)
        florence_task = FLORENCE2_TASKS[task]

        workflow: dict[str, Any] = {
            "1": {"class_type": "LoadImage", "inputs": {"image": image_ref}},
            "2": {
                "class_type": "DownloadAndLoadFlorence2Model",
                "inputs": {
                    "model": model,
                    "precision": settings.precision,
                    "attention": settings.attention,
                },
            },
            "3": {
                "class_type": "Florence2Run",
                "inputs": {
                    "image": ["1", 0],
                    "florence2_model": ["2", 0],
                    "text_input": settings.text_input,
                    "task": florence_task,
                    # Mask filling only matters for segmentation output.
                    "fill_mask": task is InferenceTask.SEGMENT,
                    "keep_model_loaded": settings.keep_model_loaded,
                    "max_new_tokens": settings.max_new_tokens,
                    "num_beams": settings.num_beams,
                    "do_sample": settings.do_sample,
                    "output_mask_select": "",
                    "seed": settings.seed,
                },
            },
        }

        if task in _TEXT_TASKS:
            # Florence2Run outputs: IMAGE, MASK, STRING (caption), JSON (data)
            workflow["4"] = {
                "class_type": "SaveText",
                "inputs": {
                    "text": ["3", 2],
                    "filename_prefix": settings.filename_prefix,
                    "format": settings.format,
                },
            }
        elif task is InferenceTask.DETECT:
            # JSON -> STRING is not a valid edge; bridge through the
            # coordinates converter, then persist as json.
            workflow["4"] = {
                "class_type": "Florence2toCoordinates",
                "inputs": {
                    "data": ["3", 3],
                    "index": settings.detect_index,
                    "batch": False,
                },
            }
            workflow["5"] = {
                "class_type": "SaveText",
                "inputs": {
                    "text": ["4", 0],
                    "filename_prefix": settings.filename_prefix,
                    "format": "json",
                },
            }
        elif task is InferenceTask.SEGMENT:
            # MASK -> IMAGE -> SaveImage: a PNG the consumer thresholds.
            workflow["4"] = {
                "class_type": "MaskToImage",
                "inputs": {"mask": ["3", 1]},
            }
            workflow["5"] = {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["4", 0],
                    "filename_prefix": settings.filename_prefix,
                },
            }
        else:  # pragma: no cover - every InferenceTask is handled above
            raise ValueError(f"Unhandled inference task: {task}")

        # The profile's most likely silent failure: a graph that runs green
        # and returns nothing. Refuse to hand one out.
        require_output_node(workflow)
        return workflow


_builder: InferenceWorkflowBuilder | None = None


def get_inference_builder() -> InferenceWorkflowBuilder:
    """Get singleton inference workflow builder."""
    global _builder
    if _builder is None:
        _builder = InferenceWorkflowBuilder()
    return _builder


def build_inference_workflow(
    image_ref: str,
    task: "InferenceTask | str" = InferenceTask.CAPTION,
    text_input: str = "",
    **overrides: Any,
) -> dict[str, Any]:
    """
    Build an inference workflow.

    Simple usage::

        uploaded = client.upload_image("screenshot.png")
        workflow = build_inference_workflow(uploaded["ref"], task="caption")
        workflow = build_inference_workflow(
            uploaded["ref"], task="detect", text_input="the red car"
        )
    """
    task_enum = InferenceTask(task)
    base = InferenceSettings(task=task_enum, text_input=text_input)
    merged = base.to_dict()
    merged.update(overrides)
    settings = InferenceSettings(
        task=task_enum,
        model=merged.get("model"),
        precision=merged.get("precision", base.precision),
        attention=merged.get("attention", base.attention),
        text_input=merged.get("text_input", text_input),
        max_new_tokens=int(merged.get("max_new_tokens", base.max_new_tokens)),
        num_beams=int(merged.get("num_beams", base.num_beams)),
        do_sample=bool(merged.get("do_sample", base.do_sample)),
        keep_model_loaded=bool(merged.get("keep_model_loaded", base.keep_model_loaded)),
        seed=int(merged.get("seed", base.seed)),
        format=merged.get("format", base.format),
        detect_index=str(merged.get("detect_index", base.detect_index)),
        filename_prefix=merged.get("filename_prefix", base.filename_prefix),
    )
    return get_inference_builder().build(image_ref, settings)
