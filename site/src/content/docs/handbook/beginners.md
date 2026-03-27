---
title: For Beginners
description: New to Comfy Headless? Start here for a gentle introduction.
sidebar:
  order: 99
---

## What is this tool?

Comfy Headless is a Python library that lets you generate images and videos using ComfyUI without touching ComfyUI's complex node-based interface. You write a few lines of Python, and the library handles all the workflow compilation, model selection, and prompt optimization behind the scenes.

Think of it as a remote control for ComfyUI — you tell it what you want to create, and it figures out the technical details.

## Who is this for?

- **Artists and creators** who want AI-generated images without learning node graphs — just launch the web UI and type a prompt
- **Python developers** who need programmatic image/video generation in their apps or scripts
- **Pipeline builders** who want headless, scriptable image generation for automation, batch processing, or CI workflows
- **Anyone with a GPU** who wants to experiment with AI image generation without the complexity

## Prerequisites

Before you start, you need:

- **Python 3.10 or later** — check with `python --version`
- **ComfyUI running locally** — Comfy Headless connects to ComfyUI as a backend. You need ComfyUI installed and running on `http://localhost:8188` (the default)
- **A GPU with at least 6 GB VRAM** — for basic image generation. Video generation needs 12+ GB depending on the model
- **pip** — Python's package manager, comes with Python
- **Optional: Ollama** — only needed if you want AI-powered prompt enhancement

## Your first 5 minutes

### 1. Install Comfy Headless

```bash
pip install comfy-headless[standard]
```

This installs the core library plus AI prompt enhancement and WebSocket progress tracking.

### 2. Make sure ComfyUI is running

Start your ComfyUI instance if it is not already running. By default, Comfy Headless looks for it at `http://localhost:8188`.

### 3. Generate your first image

Open a Python shell or create a script:

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a cat sitting on a windowsill, sunlight")
print(f"Generated: {result['images']}")
```

You should see the path to your generated image.

### 4. Check what features are available

```python
from comfy_headless import FEATURES
print(FEATURES)
```

This shows which optional extras are installed (AI, WebSocket, health monitoring, etc.).

### 5. Try the web UI (optional)

If you want a visual interface instead of code:

```bash
pip install comfy-headless[ui]
python -m comfy_headless --ui
```

This launches a Gradio web interface in your browser.

## Common mistakes

1. **Forgetting to start ComfyUI first.** Comfy Headless is a client that talks to ComfyUI — it does not include ComfyUI itself. If ComfyUI is not running, you will get connection errors. Make sure ComfyUI is running on port 8188 before using the library.

2. **Installing the wrong extra.** The bare `pip install comfy-headless` gives you the minimal core only. Most users want `pip install comfy-headless[standard]` which includes AI enhancement and WebSocket progress. Check with `FEATURES` to see what is active.

3. **Running out of VRAM on video generation.** Video models need significantly more VRAM than image models. Check the [Video Models](/comfy-headless/handbook/video-models/) page for VRAM requirements before trying video generation. Start with AnimateDiff (6 GB) if you have a smaller GPU.

4. **Expecting the AI enhancement to work without Ollama.** The `[ai]` extra requires a local Ollama instance running a language model. Install Ollama separately and pull a model before using prompt enhancement.

5. **Using synchronous code for long-running video generation.** Image generation completes in seconds, but video can take minutes. Use the WebSocket client (`ComfyWSClient`) with progress callbacks instead of the basic HTTP client for video generation, so you can see progress and avoid timeouts.

## Next steps

- [Getting Started](/comfy-headless/handbook/getting-started/) — detailed installation options and modular extras
- [Usage](/comfy-headless/handbook/usage/) — image generation, AI enhancement, video, and the web UI
- [Video Models](/comfy-headless/handbook/video-models/) — model presets and VRAM requirements

## Glossary

- **ComfyUI** — An open-source node-based interface for Stable Diffusion and other generative AI models. Comfy Headless uses it as a backend.
- **Workflow** — A ComfyUI node graph that defines how an image or video is generated. Comfy Headless compiles these from templates so you do not have to build them manually.
- **Preset** — A curated set of generation parameters (resolution, steps, model) optimized for specific hardware and use cases.
- **Prompt enhancement** — Using a local Ollama language model to rewrite your prompt for better generation results (e.g., adding style cues, quality tokens).
- **VRAM** — Video RAM on your GPU. Different models need different amounts. Running out of VRAM causes generation failures.
- **Ollama** — A local LLM runtime. Comfy Headless uses it (optionally) to analyze and improve your prompts before sending them to ComfyUI.
- **WebSocket** — A persistent network connection that lets Comfy Headless receive real-time progress updates from ComfyUI during generation.
- **Circuit breaker** — A retry pattern that stops sending requests to ComfyUI when it is unresponsive, then automatically resumes when it recovers.
- **Extras** — Python optional dependency groups (e.g., `[ai]`, `[websocket]`, `[full]`) that let you install only the features you need.
