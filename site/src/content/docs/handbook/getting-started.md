---
title: Getting Started
description: Install Comfy Headless, configure prerequisites, and generate your first image in under a minute.
sidebar:
  order: 1
---

This page walks you through installing Comfy Headless, setting up prerequisites, and running your first generation.

## Prerequisites

Before installing Comfy Headless, make sure you have:

- **Python 3.10 or later** — check with `python --version`
- **ComfyUI running locally** — by default Comfy Headless connects to `http://localhost:8188`
- **Optional: Ollama** — required only if you want AI-powered prompt enhancement (the `[ai]` extra)

## Modular installation

Comfy Headless uses Python extras so you install only the dependencies you actually need. The core package is approximately 2 MB with zero heavy dependencies.

### Install options

```bash
# Core only (minimal, ~2MB)
pip install comfy-headless

# With AI prompt enhancement (Ollama)
pip install comfy-headless[ai]

# With WebSocket real-time progress
pip install comfy-headless[websocket]

# Recommended for most users
pip install comfy-headless[standard]

# Everything (UI, health monitoring, observability)
pip install comfy-headless[full]
```

### Available extras

| Extra | Dependencies | What it adds |
|-------|-------------|--------------|
| `ai` | httpx | Ollama-powered prompt analysis and enhancement |
| `websocket` | websockets | Real-time generation progress updates over WebSocket |
| `health` | psutil | System health monitoring and circuit-breaker retry logic |
| `ui` | gradio | Gradio 6.0 web interface with the Ocean Mist theme |
| `validation` | pydantic | Configuration validation with Pydantic models |
| `observability` | opentelemetry | Distributed tracing for production deployments |
| `standard` | ai + websocket | The recommended bundle for most users |
| `full` | All of the above | Everything in one install |

### Choosing the right extra

- **Experimenting locally?** Start with `comfy-headless[standard]`. It gives you AI enhancement and WebSocket progress without pulling in heavy UI or tracing deps.
- **Building a production pipeline?** Use `comfy-headless[health]` or `comfy-headless[full]` for circuit-breaker retry logic and observability.
- **Just need the API?** Plain `comfy-headless` (no extras) is enough for basic image generation.

## First generation

Once installed, generating an image is three lines:

```python
from comfy_headless import ComfyClient

client = ComfyClient()  # connects to localhost:8188 by default
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

The `ComfyClient` handles workflow compilation, prompt submission, and result retrieval. You get back a dictionary with an `images` key containing the paths to your generated files.

## Verifying the installation

You can check which extras are active in your environment:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

`FEATURES` is a dictionary mapping extra names to booleans. `list_missing_features()` returns install commands for any extras that are not currently available.

## Next steps

- Learn how to use the library API, AI enhancement, and video generation in [Usage](../usage/).
- Explore video model presets and VRAM requirements in [Video Models](../video-models/).
- Configure feature flags and WebSocket progress in [Configuration](../configuration/).
