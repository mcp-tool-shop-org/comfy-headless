---
title: API Reference
description: Core classes, video types, workflow compilation, intelligence functions, and the full error taxonomy for Comfy Headless.
sidebar:
  order: 5
---

This page documents the public API surface of Comfy Headless — the classes, functions, and types you import and use in your code.

## Core clients

### ComfyClient

The main HTTP client for interacting with ComfyUI.

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
```

- Connects to `http://localhost:8188` by default.
- Handles workflow compilation, prompt submission, and result retrieval.
- Returns a dictionary with an `images` key for image generation and a `video` key for video generation.

### ComfyWSClient

The WebSocket client for real-time progress tracking. Requires the `[websocket]` extra.

```python
from comfy_headless import ComfyWSClient

async with ComfyWSClient() as ws:
    prompt_id = await ws.queue_prompt(workflow)
    result = await ws.wait_for_completion(
        prompt_id,
        on_progress=lambda p: print(f"Progress: {p.progress}%")
    )
```

- Opens a persistent WebSocket connection to ComfyUI.
- Supports an `on_progress` callback for real-time progress updates.
- Use this for long-running operations like video generation.

## Video types

### VideoSettings

A configuration object for video generation parameters.

```python
from comfy_headless import VideoSettings
```

Holds resolution, frame count, step count, and model-specific settings for a video generation request.

### VideoModel

An enum of supported video generation models.

```python
from comfy_headless import VideoModel

# Available models:
# VideoModel.LTXV        - LTX-Video 2
# VideoModel.HUNYUAN_15  - Hunyuan 1.5
# VideoModel.WAN         - Wan 2.1/2.2
# VideoModel.MOCHI       - Mochi
# VideoModel.ANIMATEDIFF - AnimateDiff
# VideoModel.SVD         - Stable Video Diffusion
# VideoModel.COGVIDEOX   - CogVideoX
```

### VIDEO_PRESETS

A dictionary mapping preset names to their full configuration.

```python
from comfy_headless import VIDEO_PRESETS

for name, preset in VIDEO_PRESETS.items():
    print(f"{name}: {preset}")
```

### get_recommended_preset

Returns the best preset for a given amount of VRAM.

```python
from comfy_headless import get_recommended_preset

preset = get_recommended_preset(vram_gb=16)  # "hunyuan15_720p"
```

## Workflow compilation

### compile_workflow

Compiles a generation workflow from a preset name.

```python
from comfy_headless import compile_workflow

workflow = compile_workflow(preset="ltx_standard", prompt="a sunset")
```

### WorkflowCompiler

The low-level compiler class for custom workflow construction.

```python
from comfy_headless import WorkflowCompiler

compiler = WorkflowCompiler()
```

Use this when you need more control over workflow construction than `compile_workflow` provides.

## Intelligence functions

These require the `[ai]` extra.

### analyze_prompt

Analyzes a prompt to detect intent, style, and a suggested preset.

```python
from comfy_headless import analyze_prompt

analysis = analyze_prompt("a cyberpunk city at night with neon lights")
print(analysis.intent)           # "scene"
print(analysis.styles)           # ["scifi", "cinematic"]
print(analysis.suggested_preset) # "cinematic"
```

### enhance_prompt

Enhances a prompt with quality tags, style modifiers, and a matching negative prompt.

```python
from comfy_headless import enhance_prompt

enhanced = enhance_prompt("a cat", style="detailed")
print(enhanced.enhanced)  # "a cat, masterpiece, best quality, highly detailed..."
print(enhanced.negative)  # Style-aware negative prompt
```

### PromptAnalysis

The return type of `analyze_prompt`. Contains:

- `intent` — detected intent (portrait, scene, object, etc.)
- `styles` — list of detected style tags
- `suggested_preset` — the ComfyUI preset that best matches the prompt

## Error handling

Comfy Headless provides a structured error hierarchy. All exceptions inherit from `ComfyHeadlessError`.

```python
from comfy_headless import (
    ComfyHeadlessError,      # Base exception
    ComfyUIConnectionError,  # Cannot reach ComfyUI server
    ComfyUIOfflineError,     # ComfyUI is not responding
    GenerationTimeoutError,  # Generation exceeded the timeout
    GenerationFailedError,   # Generation failed during execution
    ValidationError,         # Invalid parameters
)
```

### Error handling pattern

```python
from comfy_headless import (
    ComfyClient,
    ComfyUIOfflineError,
    GenerationTimeoutError,
    GenerationFailedError,
)

client = ComfyClient()

try:
    result = client.generate_image("test prompt")
except ComfyUIOfflineError:
    print("ComfyUI is not running. Start it first.")
except GenerationTimeoutError:
    print("Generation timed out. Try a simpler prompt or lower settings.")
except GenerationFailedError as e:
    print(f"Generation failed: {e}")
```

### Exception hierarchy

```
ComfyHeadlessError
├── ComfyUIConnectionError    # Network-level connection failure
├── ComfyUIOfflineError       # Server reachable but not responding
├── GenerationTimeoutError    # Generation exceeded timeout
├── GenerationFailedError     # ComfyUI reported failure
└── ValidationError           # Invalid parameters passed to the API
```

Catch `ComfyHeadlessError` to handle all library exceptions in a single block. Catch specific subclasses when you need different recovery strategies for different failure modes.

## Feature detection

### FEATURES

A dictionary mapping extra names to availability booleans.

```python
from comfy_headless import FEATURES
# {'ai': True, 'websocket': True, 'health': False, ...}
```

### list_missing_features

Returns a dictionary of unavailable extras with their install commands.

```python
from comfy_headless import list_missing_features
# {'health': 'pip install comfy-headless[health]', ...}
```

## Next steps

- Understand the project structure and ComfyUI node requirements in [Architecture](../architecture/).
- Return to the [Handbook index](../) for a complete overview.
