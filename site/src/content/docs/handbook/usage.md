---
title: Usage
description: Library usage patterns for Comfy Headless — image generation, AI prompt enhancement, video generation, and the Gradio web UI.
sidebar:
  order: 2
---

This page covers the main ways to use Comfy Headless: as a Python library, with AI-powered prompt enhancement, for video generation, and through the built-in web UI.

## Image generation

The simplest usage is generating images through the `ComfyClient`:

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

`ComfyClient` connects to your local ComfyUI instance (default: `http://localhost:8188`), compiles a workflow from your prompt, submits it to the queue, and waits for the result. The returned dictionary contains an `images` key with the file paths to the generated output.

## AI prompt enhancement

When you install the `[ai]` extra, Comfy Headless can analyze and enhance your prompts using a local Ollama model before sending them to ComfyUI. This produces better results without requiring prompt engineering expertise.

### Analyzing a prompt

```python
from comfy_headless import analyze_prompt

analysis = analyze_prompt("a cyberpunk city at night with neon lights")
print(f"Intent: {analysis.intent}")           # "scene"
print(f"Styles: {analysis.styles}")           # ["scifi", "cinematic"]
print(f"Preset: {analysis.suggested_preset}") # "cinematic"
```

The `analyze_prompt` function returns a `PromptAnalysis` object with the detected intent (portrait, scene, object, etc.), style tags, and a suggested ComfyUI preset that matches the prompt's mood.

### Enhancing a prompt

```python
from comfy_headless import enhance_prompt

enhanced = enhance_prompt("a cat", style="detailed")
print(enhanced.enhanced)   # "a cat, masterpiece, best quality, highly detailed..."
print(enhanced.negative)   # Style-aware negative prompt
```

`enhance_prompt` takes a simple prompt and rewrites it with quality tags, style modifiers, and a matching negative prompt. The `style` parameter controls the enhancement direction — options include `"detailed"`, `"cinematic"`, `"anime"`, and more.

### How it works

The intelligence layer sends your prompt to a local Ollama model, which returns structured analysis and enhancement suggestions. This runs entirely on your machine — no data leaves your network.

## Video generation

Comfy Headless supports multiple video models through a preset system. Each preset configures resolution, frame count, and step count for a specific model.

```python
from comfy_headless import ComfyClient, list_video_presets

# See all available presets
print(list_video_presets())

# Generate video with a preset
client = ComfyClient()
result = client.generate_video(
    prompt="a cat walking through a garden",
    preset="ltx_quality"  # LTX-Video 2, 1280x720, 49 frames
)
```

For a full breakdown of supported models, presets, and VRAM requirements, see the [Video Models](../video-models/) page.

### VRAM-aware preset selection

If you are not sure which preset to use, let the library choose based on your available VRAM:

```python
from comfy_headless import get_recommended_preset

preset = get_recommended_preset(vram_gb=16)  # Returns "hunyuan15_720p"
```

This function picks the highest-quality preset that fits within your GPU memory budget.

## Web UI

Comfy Headless includes a built-in Gradio 6.0 interface for users who prefer a visual workflow. The UI uses the Ocean Mist theme — soft teal accents on warm neutral backgrounds.

### Launching the UI

From Python:

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

Or from the command line:

```bash
python -m comfy_headless.ui
```

### UI features

The web interface provides six main tabs:

| Tab | What it does |
|-----|-------------|
| **Image Generation** | Text-to-image with presets and AI prompt enhancement |
| **Video Generation** | AnimateDiff, LTX, Hunyuan, Wan support with preset selection |
| **Queue & History** | Real-time queue management and job history browser |
| **Workflows** | Browse, import, and create workflow templates |
| **Models Browser** | View installed checkpoints, LoRAs, and motion models |
| **Settings** | Connection management, timeouts, and system information |

The UI is optional — it requires the `[ui]` extra (`pip install comfy-headless[ui]`). Everything the UI does is also available through the Python API.

## Next steps

- Explore video model details and VRAM requirements in [Video Models](../video-models/).
- Configure feature flags and WebSocket progress in [Configuration](../configuration/).
- See the full public API surface in [API Reference](../api-reference/).
