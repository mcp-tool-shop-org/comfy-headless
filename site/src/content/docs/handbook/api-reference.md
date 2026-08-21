---
title: API Reference
description: Verified signatures for the ComfyClient methods, module-level functions, data types, and the full error taxonomy.
sidebar:
  order: 6
---

Every signature on this page is taken from the installed package by introspection, not
from memory.

## ComfyClient

```python
from comfy_headless import ComfyClient

ComfyClient(base_url=None, rate_limit=None, rate_limit_per_seconds=1.0)
```

`base_url` falls back to `settings.comfyui.url` when omitted. There is no `timeout`
constructor argument — timeouts are configured per operation (see
[Configuration](../configuration/)).

### Generation

```python
generate_image(
    prompt, negative_prompt="", preset="", checkpoint="",
    width=1024, height=1024, steps=20, cfg=7.0,
    sampler="euler", scheduler="normal", seed=-1,
    wait=True, timeout=None, on_progress=None,
) -> dict
```

```python
generate_video(
    prompt, negative_prompt="", preset="standard", init_image=None,
    wait=True, timeout=None, on_progress=None,
    checkpoint="", motion_model="",
    width=None, height=None, frames=None, fps=None,
    steps=None, cfg=None, seed=-1, motion_scale=None,
) -> dict
```

```python
generate_batch(
    prompts, negative_prompt="", preset="fast", checkpoint="",
    width=1024, height=1024, steps=20, cfg=7.0,
    sampler="euler", scheduler="normal", seeds=None,
    max_concurrent=1, check_vram=True, on_progress=None,
) -> dict
```

All three return a **dict**: `success`, `prompt_id`, `images` (or `videos`), `error`,
`seed`, `preset`.

:::note
`generate_video` takes no `model` argument — selection is by `preset`. `generate_image`
takes no `batch_size` — use `generate_batch`. `generate_video` also accepts any
`VideoSettings` field as an override, including `variant`, `precision` and
`output` (`"vhs"` | `"core"`).
:::

### Profiles (new in 3.1)

The `image`/`audio` arguments below accept a local path, raw bytes, an
`upload_image()`/`upload_audio()` dict, or a server-side ref string — local sources are
uploaded automatically.

```python
generate_3d(
    image, preset="standard",
    wait=True, timeout=None, on_progress=None,
    **overrides,                    # steps, cfg, seed, octree_resolution, threshold, ...
) -> dict                           # success, prompt_id, meshes, error, seed, preset

generate_audio(
    tags, lyrics="", negative_tags="", preset="music",
    wait=True, timeout=None, on_progress=None,
    **overrides,                    # seconds, bpm, keyscale, format, quality, seed, ...
) -> dict                           # success, prompt_id, audios, error, seed, preset

separate_audio(
    audio, stems=None,              # default: ("bass", "drums", "other", "vocals")
    wait=True, timeout=None, on_progress=None,
    **kwargs,                       # chunk_fade_shape, chunk_length, chunk_overlap
) -> dict                           # success, prompt_id, audios (each with "stem"), error

run_inference(
    image, task="caption", text_input="",
    wait=True, timeout=None, on_progress=None,
    **overrides,                    # model, precision, format, detect_index, ...
) -> dict                           # success, prompt_id, task, text, texts, files, images, error

edit_image(
    prompt, images,                 # 1-3 references
    negative="", wait=True, timeout=None, on_progress=None,
    **kwargs,                       # unet, width, height, steps, cfg, shift, seed
) -> dict                           # success, prompt_id, images, error, seed

rerun_from_png(
    source,                         # PNG path or bytes
    wait=True, timeout=None, on_progress=None, extra_pnginfo=None,
) -> dict                           # success, prompt_id, seed, images, videos, audios,
                                    # meshes, files, texts, error
```

Inference tasks: `caption`, `detailed_caption`, `more_detailed_caption`, `tag`,
`detect`, `segment`, `ocr` — `detect`/`segment` require `text_input`.

### Uploads

```python
upload_image(
    path_or_bytes, *, filename=None, subfolder="",
    overwrite=False, type="input",
) -> dict

upload_mask(
    path_or_bytes, original_ref, *, filename=None, subfolder="",
    overwrite=False, type="input",
) -> dict

upload_audio(
    path_or_bytes, *, filename=None, subfolder="",
    overwrite=False, type="input",
) -> dict
```

Returns `{"name", "subfolder", "type", "ref"}`. **`name` is the server's stored filename
and is authoritative** — ComfyUI renames on collision. `ref` is `name` joined with
`subfolder`, ready to use as a `LoadImage` (or `LoadAudio`) node's input.

`original_ref` accepts either the dict returned by `upload_image` or a bare filename.
`upload_audio` rides the same `POST /upload/image` route — ComfyUI has no audio-specific
upload endpoint — and sniffs a proper audio extension for raw bytes.

### Workflow building and submission

```python
build_txt2img_workflow(
    prompt, negative_prompt="", checkpoint="",
    width=1024, height=1024, steps=20, cfg=7.0,
    sampler="euler", scheduler="normal", seed=-1, batch_size=1,
) -> dict

build_video_workflow(
    prompt, negative_prompt="", checkpoint="", motion_model="",
    width=512, height=512, frames=16, fps=8,
    steps=20, cfg=7.0, seed=-1, motion_scale=1.0,
) -> dict

queue_prompt(workflow, extra_pnginfo=None) -> str | None
wait_for_completion(prompt_id, timeout=None, poll_interval=0.5, on_progress=None) -> dict | None
```

`extra_pnginfo` embeds custom provenance: every key becomes a PNG text chunk in the
job's outputs (payload shape `extra_data.extra_pnginfo`, verified against the server).

Module-level graph builders (all return the same API-format dict):

```python
from comfy_headless import (
    build_3d_workflow,               # (image_ref, preset="standard", **overrides)
    build_audio_workflow,            # (tags, lyrics="", negative_tags="", preset="music", **overrides)
    build_audio_separation_workflow, # (audio_ref, stems=..., **kwargs)
    build_inference_workflow,        # (image_ref, task="caption", text_input="", **overrides)
    build_qwen_edit_workflow,        # (prompt, image_refs, negative="", ...)
    build_controlnet_workflow,       # (prompt, control_image_ref, control_type="auto", base="qwen", ...)
    build_video_workflow,            # (prompt, negative="...", preset="standard", init_image=None, **overrides)
    compile_workflow,                # (prompt, ..., template_id="txt2img_standard" | "qwen_txt2img" | ...)
)
```

### Dependency and type checking

```python
check_workflow_dependencies(workflow) -> dict     # reports; never raises
require_workflow_dependencies(workflow) -> dict   # raises MissingNodePackError
check_workflow_types(workflow) -> dict            # {"checked", "errors", "warnings"}
```

The dependency report includes `missing_packs` and `required_packs`. Both checks
validate against the target server's live `/object_info`, so the answer is specific to
the machine you are pointed at. `check_workflow_types` applies the server's own
union-matching acceptance rule per edge — only edges the server would provably reject
are errors; partial type overlaps are warnings; `checked: False` means `/object_info`
was unreachable and nothing was validated.

### Server introspection

```python
is_online() -> bool
ensure_online()                     # raises ComfyUIOfflineError
get_system_stats() -> dict | None
get_vram_gb() -> float
get_free_vram_gb() -> float
check_vram_available(required_gb, raise_on_insufficient=False) -> bool
estimate_vram_for_image(width=1024, height=1024, batch_size=1) -> float
estimate_vram_for_video(width=512, height=512, frames=16, model="animatediff") -> float
```

```python
get_checkpoints() -> list[str]
get_loras() -> list[str]
get_samplers() -> list[str]
get_schedulers() -> list[str]
get_motion_models() -> list[str]
get_all_installed_nodes() -> list[str]
```

### Queue and results

```python
get_queue() -> dict
get_history(prompt_id=None) -> dict
cancel_current() -> bool
clear_queue() -> bool
get_image(filename, subfolder="", folder_type="output") -> bytes | None
get_video(filename, subfolder="", folder_type="output") -> bytes | None
get_file(filename, subfolder="", folder_type="output") -> bytes | None
close()
```

`get_file` is the generic fetch — meshes, audio and text files come back through the
same `GET /view` route as images. Pass a result entry directly:
`client.get_file(**result["meshes"][0])`.

### Recommendations

```python
recommend_image_preset(intent="general") -> str
recommend_video_preset(intent="general") -> str
```

## Module-level functions

These are **not** client methods — importing them from the package is the only correct
usage.

### Prompt intelligence — requires `[ai]`

```python
from comfy_headless import enhance_prompt, analyze_prompt, quick_enhance

enhance_prompt(prompt, style="balanced") -> EnhancedPrompt
analyze_prompt(prompt) -> PromptAnalysis
```

### Presets

```python
from comfy_headless import list_presets, list_video_presets, get_recommended_preset

list_presets() -> list[str]
list_video_presets() -> list[str]
get_recommended_preset(intent="general", quality="standard", vram_gb=8.0) -> str
```

### Features and settings

```python
from comfy_headless import (
    FEATURES, check_feature, list_available_features, list_missing_features,
    get_settings, reload_settings, set_log_level,
)
```

### UI — requires `[ui]`

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Data types

### `EnhancedPrompt`

`original`, `enhanced`, `negative`, `additions`, `reasoning`, `version`, `prompt_hash`,
`created_at`

### `PromptAnalysis`

`original`, `intent`, `subjects`, `styles`, `mood`, `complexity`, `suggested_aspect`,
`suggested_workflow`, `suggested_preset`, `confidence`

### `VideoSettings`

`model`, `width`, `height`, `frames`, `fps`, `steps`, `cfg`, `motion_style`, and related
fields. Read them from `VIDEO_PRESETS[name]`.

### `VideoModelInfo`

`id`, `name`, `description`, `model`, `text_to_video`, `image_to_video`, `min_vram_gb`,
`estimated_time_seconds`, `max_frames`, `max_width`, `max_height`, `presets`,
`requires_packs`. Read them from `VIDEO_MODEL_INFO[family]`.

```python
from comfy_headless import VIDEO_PRESETS, VIDEO_MODEL_INFO, VideoModel

VIDEO_PRESETS["ltx_quality"].frames        # 97
VIDEO_MODEL_INFO["ltxv"].min_vram_gb       # 12
VIDEO_MODEL_INFO["cogvideo"].requires_packs
```

`VideoModel` is an enum of family identifiers used *inside* `VideoSettings`. It is not
accepted by `generate_video` — that takes a preset name.

### Profile settings and registries (new in 3.1)

```python
from comfy_headless import (
    ThreeDSettings, THREE_D_PRESETS, THREE_D_MODEL_INFO,       # 3D
    AudioSettings, AudioFormat, AUDIO_PRESETS, AUDIO_MODEL_INFO,
    SEPARATION_STEMS,                                           # audio
    InferenceTask, InferenceSettings, INFERENCE_MODEL_INFO,
    FLORENCE2_TASKS,                                            # inference
    ProvenanceRecord,                                           # metadata
)
```

- `ThreeDSettings`: `checkpoint`, `resolution`, `steps`, `cfg`, `seed`, `num_chunks`,
  `octree_resolution`, `algorithm`, `threshold`, `filename_prefix`
- `AudioSettings`: `seconds` (drives both encoder duration and latent length), `bpm`,
  `timesignature`, `language`, `keyscale`, `steps`, `cfg`, `generate_audio_codes`,
  `format`, `quality`, `filename_prefix`
- `InferenceTask`: `CAPTION`, `DETAILED_CAPTION`, `MORE_DETAILED_CAPTION`, `TAG`,
  `DETECT`, `SEGMENT`, `OCR`
- `ProvenanceRecord`: `prompt` (the runnable graph), `workflow` (GUI graph), `extra`
  (custom chunk keys), `has_prompt`

### Metadata functions (no server needed)

```python
from comfy_headless import (
    read_png_text_chunks,       # (source) -> {keyword: text} — tEXt, zTXt, iTXt
    read_workflow_metadata,     # (source) -> ProvenanceRecord
    extract_prompt_graph,       # (source) -> dict — raises ValidationError if absent
)
```

### Addressing layer (new in 3.1)

```python
from comfy_headless import (
    validate_node_input,        # (received, declared, strict=False) -> bool — the server's rule
    match_types, TypeMatch,     # SUBSET / OVERLAP / DISJOINT resolution
    GraphTypeChecker,           # per-edge validation against a catalog
    extract_object_info_types,  # raw /object_info -> checker catalog
    parse_field_path, join_field_path, set_node_input, get_node_input,
    DynamicCombo, SAVE_AUDIO_FORMAT, SAVE_VIDEO_CODEC,
    has_output_node, require_output_node, KNOWN_OUTPUT_NODE_CLASSES,
    HISTORY_OUTPUT_KEYS,        # terminator class -> /history outputs key(s)
)
```

`SAVE_AUDIO_FORMAT.build("mp3", quality="320k")` returns
`{"format": "mp3", "format.quality": "320k"}` — the flattened dotted keys dynamic-combo
inputs need — and raises `GraphAddressError` for a field the selected branch does not
activate (e.g. `quality` under `flac`).

## Node provenance

```python
from comfy_headless import NODE_PACKS, NODE_PACK_INFO, get_node_pack, required_node_packs

NODE_PACKS                                # class_type -> pack id, for every non-core node
NODE_PACK_INFO                            # pack id -> name, URL, install hint
get_node_pack("VHS_VideoCombine")         # "comfyui-videohelpersuite"
get_node_pack("KSampler")                 # None -> core
required_node_packs(workflow)             # {pack_id: [class_types]} for one graph
```

A `class_type` absent from `NODE_PACKS` is a core ComfyUI node. The registry lives in
`comfy_headless.node_packs` (shared by all profiles since 3.1);
`comfy_headless.video` re-exports it for older imports.

## Errors

Every exception carries a structured `code`, `message` and `hint`.

| Exception | Raised when |
|-----------|-------------|
| `ComfyHeadlessError` | Base class for everything below |
| `ComfyUIConnectionError` | The server could not be reached |
| `ComfyUIOfflineError` | The server is not responding |
| `GenerationTimeoutError` | The job exceeded its timeout |
| `GenerationFailedError` | ComfyUI reported a failure |
| `InvalidPromptError` | The prompt failed validation |
| `InvalidParameterError` | A parameter was out of range or the wrong type |
| `ValidationError` | General validation failure |
| `SecurityError` | e.g. an upload subfolder traversal attempt |
| `UploadError` | An upload failed or returned an unusable response |
| `MissingNodePackError` | The graph needs a node pack the server lacks |
| `GraphAddressError` | A dotted field path is invalid, or a dynamic-combo field was set on an inactive branch *(new in 3.1)* |
| `CircuitOpenError` | The circuit breaker is open after repeated failures |
| `FeatureNotAvailable` | An optional extra is not installed |

```python
from comfy_headless import ComfyUIOfflineError, MissingNodePackError

try:
    client.require_workflow_dependencies(workflow)
    client.generate_video("a cat", preset="cogvideo")
except MissingNodePackError as e:
    print(e.code, e.message, e.hint)
except ComfyUIOfflineError:
    print("Start ComfyUI first")
```

`ErrorLevel` and `format_error_for_user` control how much detail is surfaced to end users
versus logged for operators.
