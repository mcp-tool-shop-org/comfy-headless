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
takes no `batch_size` — use `generate_batch`.
:::

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
```

Returns `{"name", "subfolder", "type", "ref"}`. **`name` is the server's stored filename
and is authoritative** — ComfyUI renames on collision. `ref` is `name` joined with
`subfolder`, ready to use as a `LoadImage` node's `image` input.

`original_ref` accepts either the dict returned by `upload_image` or a bare filename.

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

queue_prompt(workflow) -> str | None
wait_for_completion(prompt_id, timeout=None, poll_interval=0.5, on_progress=None) -> dict | None
```

### Dependency checking

```python
check_workflow_dependencies(workflow) -> dict     # reports; never raises
require_workflow_dependencies(workflow) -> dict   # raises MissingNodePackError
```

The report includes `missing_packs` and `required_packs`. This validates against the
target server's live `/object_info`, so the answer is specific to the machine you are
pointed at.

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
close()
```

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

## Node provenance

```python
from comfy_headless import video

video.NODE_PACKS          # class_type -> pack id, for every non-core node
video.NODE_PACK_INFO      # pack id -> name, URL, install hint
video.get_node_pack("VHS_VideoCombine")   # "comfyui-videohelpersuite"
```

A `class_type` absent from `NODE_PACKS` is a core ComfyUI node.

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
