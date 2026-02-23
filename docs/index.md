# Comfy Headless

**Production-ready headless client for ComfyUI with AI-powered prompt intelligence, video generation, and modular architecture.**

[![PyPI version](https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/comfy-headless/)
[![CI](https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg)](https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is Comfy Headless?

Comfy Headless gives you programmatic access to ComfyUI's image and video generation without the node-based GUI. It wraps ComfyUI's API into a clean Python interface with sensible defaults, AI-powered prompt enhancement, and one-line video generation.

## Features

- **Simple Python API** -- generate images and video in 3 lines of code
- **AI Prompt Intelligence** -- automatic prompt analysis and enhancement via Ollama
- **Video Generation** -- LTX-Video 2, Hunyuan 1.5, Wan 2.1/2.2, AnimateDiff, and more
- **Modular Extras** -- install only the features you need (`[ai]`, `[websocket]`, `[ui]`, `[health]`, `[full]`)
- **Web UI** -- built-in Gradio interface with Ocean Mist theme
- **WebSocket Progress** -- real-time generation progress tracking
- **Smart Presets** -- VRAM-aware model and parameter recommendations
- **Production Ready** -- circuit breaker, retry logic, health monitoring, OpenTelemetry tracing

## Quick Install

```bash
# Recommended for most users
pip install comfy-headless[standard]

# Core only (minimal)
pip install comfy-headless

# Everything
pip install comfy-headless[full]
```

## Quick Start

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## Requirements

- Python 3.10+
- ComfyUI running locally (default: `http://localhost:8188`)
- Optional: Ollama for AI prompt enhancement

## Links

- [GitHub Repository](https://github.com/mcp-tool-shop-org/comfy-headless)
- [PyPI Package](https://pypi.org/project/comfy-headless/)
- [Issue Tracker](https://github.com/mcp-tool-shop-org/comfy-headless/issues)
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) -- browse all tools

## License

MIT License
