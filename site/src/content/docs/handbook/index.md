---
title: Comfy Headless Handbook
description: The complete guide to using Comfy Headless — a production-ready headless client for ComfyUI with AI-powered prompt intelligence, video generation, and a modern Gradio UI.
sidebar:
  order: 0
---

Welcome to the **Comfy Headless Handbook**. This guide covers everything you need to go from zero to generating images and videos programmatically through ComfyUI — without ever touching a node graph.

## What is Comfy Headless?

Comfy Headless is a Python library that wraps ComfyUI's full power behind a clean, developer-friendly API. Instead of wiring nodes together in a visual editor, you write a few lines of Python and let the library handle workflow compilation, model selection, and prompt optimization.

| Problem | How Comfy Headless Solves It |
|---------|------------------------------|
| ComfyUI's node interface is overwhelming | Simple presets and a clean Python API abstract the complexity away |
| Prompt engineering is hard | AI-powered prompt enhancement via Ollama rewrites prompts for better results |
| Video generation is complex | One-line video generation with curated model presets |
| No idea what settings to use | VRAM-aware recommendations pick the best settings automatically |

## Who is this for?

- **Users** who want great results without prompt engineering expertise. Launch the Gradio UI and start generating immediately.
- **Developers** who need a clean Python API with proper error handling, WebSocket progress hooks, and circuit-breaker retry logic for production integration.
- **Pipeline builders** who want headless operation, modular installs, and configurable settings for automation workflows, CI image testing, or batch generation.

## Handbook contents

| Page | What you will learn |
|------|---------------------|
| [Getting Started](./getting-started/) | Installation options, modular extras, and prerequisites |
| [Usage](./usage/) | Library usage, AI enhancement, video generation, and the web UI |
| [Video Models](./video-models/) | Supported video models, presets, and VRAM requirements |
| [Configuration](./configuration/) | Feature flags, WebSocket progress, and runtime settings |
| [API Reference](./api-reference/) | Core classes, error handling, and the full public API surface |
| [Architecture](./architecture/) | Project structure, module responsibilities, and ComfyUI node requirements |

## Philosophy

Comfy Headless follows three design principles:

1. **Output-first** — the library exists to produce images and videos. Every abstraction serves that goal.
2. **Modular by design** — the core is approximately 2 MB with zero heavy dependencies. Add extras only when you need them.
3. **Honest defaults** — preset recommendations are VRAM-aware and transparent. The library never hides trade-offs.

## Quick taste

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

That is all it takes. Read on to learn about modular installation, AI prompt enhancement, video model presets, and more.
