---
title: Video Models
description: Supported video models, curated presets, VRAM requirements, and recommendations for choosing the right model for your hardware.
sidebar:
  order: 3
---

Comfy Headless supports multiple video generation models, each with curated presets that configure resolution, frame count, and inference steps. This page covers what is available, what hardware each model needs, and how to choose the right one.

## Supported models

| Model | VRAM | Quality | Speed | Best for |
|-------|------|---------|-------|----------|
| **LTX-Video 2** | 12 GB+ | Excellent | Fast | General use, RTX 3080+ |
| **Hunyuan 1.5** | 14 GB+ | Best | Slow | High quality, RTX 4080+ |
| **Wan 2.1/2.2** | 6-16 GB | Great | Medium | Budget GPUs, efficiency |
| **Mochi** | 12 GB+ | Excellent | Slow | Text adherence |
| AnimateDiff | 6 GB+ | Good | Fast | Quick previews |
| SVD | 8 GB+ | Good | Medium | Image-to-video |
| CogVideoX | 10 GB+ | Good | Slow | Legacy support |

Models in **bold** are the recommended first choices for new users. The others remain fully supported for specific use cases.

## Video presets

Every model has one or more presets — pre-configured combinations of resolution, frame count, and inference steps that produce good results out of the box.

### LTX-Video 2

LTX-Video 2 is the best general-purpose choice. It balances quality and speed well and runs on any GPU with 12 GB or more of VRAM.

| Preset | Resolution | Frames | Steps | Use case |
|--------|-----------|--------|-------|----------|
| `ltx_quick` | 768x512 | 25 | 20 | Fast previews and iteration |
| `ltx_standard` | 1280x720 | 49 | 25 | General-purpose generation |
| `ltx_quality` | 1280x720 | 97 | 30 | High frame count, best quality |

### Hunyuan 1.5

Hunyuan 1.5 produces the highest visual quality but requires more VRAM and runs slower. Best suited for final renders rather than iteration.

| Preset | Resolution | Frames | Notes |
|--------|-----------|--------|-------|
| `hunyuan15_720p` | 1280x720 | 121 | High quality at 720p |
| `hunyuan15_1080p` | 1920x1080 | — | Uses super-resolution upscaling |

### Wan

The Wan family offers excellent efficiency. The 1.3B parameter variant runs on GPUs with as little as 6 GB of VRAM, making it the most accessible option for budget hardware.

| Preset | Resolution | Frames | VRAM | Notes |
|--------|-----------|--------|------|-------|
| `wan_1.3b` | 720x480 | 49 | 6 GB | Lightweight, budget GPUs |
| `wan_14b` | 1280x720 | 81 | 12 GB | Full quality Wan model |

## Choosing a model

Use the built-in recommendation function to let the library choose based on your GPU:

```python
from comfy_headless import get_recommended_preset

preset = get_recommended_preset(vram_gb=16)  # Returns "hunyuan15_720p"
preset = get_recommended_preset(vram_gb=8)   # Returns "wan_1.3b"
preset = get_recommended_preset(vram_gb=12)  # Returns "ltx_standard"
```

### Decision guide

- **6 GB VRAM** — Use Wan 1.3B (`wan_1.3b`). It is the only model that fits comfortably.
- **8-10 GB VRAM** — AnimateDiff for quick previews, Wan 1.3B for better quality.
- **12 GB VRAM** — LTX-Video 2 is the sweet spot. Fast and high quality.
- **14-16 GB VRAM** — Hunyuan 1.5 at 720p for the best visual quality, or LTX-Video 2 for faster iteration.
- **16 GB+ VRAM** — Hunyuan 1.5 at 1080p with super-resolution for production renders.

## Working with presets in code

```python
from comfy_headless import VIDEO_PRESETS, ComfyClient

# Inspect all presets
for name, preset in VIDEO_PRESETS.items():
    print(f"{name}: {preset}")

# Generate with a specific preset
client = ComfyClient()
result = client.generate_video(
    prompt="a timelapse of clouds over a valley",
    preset="ltx_quality"
)
```

The `VIDEO_PRESETS` dictionary maps preset names to their full configuration. You can inspect it to see exactly what settings each preset uses.

## ComfyUI node requirements

Each video model requires specific custom nodes installed in your ComfyUI instance. See the [Architecture](../architecture/) page for the full list of required nodes per model.

## Next steps

- Configure WebSocket progress tracking for long video generations in [Configuration](../configuration/).
- See the `VideoSettings` and `VideoModel` classes in [API Reference](../api-reference/).
