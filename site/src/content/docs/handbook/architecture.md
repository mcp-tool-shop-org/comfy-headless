---
title: Architecture
description: Project structure, module responsibilities, ComfyUI node requirements, and how the pieces fit together.
sidebar:
  order: 6
---

This page explains how Comfy Headless is structured internally, what each module does, and what custom nodes your ComfyUI instance needs for different features.

## Directory structure

```
comfy_headless/
├── __init__.py          # Package exports, lazy loading
├── feature_flags.py     # Optional dependency detection
├── client.py            # ComfyUI HTTP client
├── websocket_client.py  # WebSocket client
├── intelligence.py      # AI prompt analysis (requires [ai])
├── workflows.py         # Template compiler & presets
├── video.py             # Video models & presets
├── ui.py                # Gradio 6.0 interface (requires [ui])
├── theme.py             # Ocean Mist theme
├── config.py            # Settings management
├── exceptions.py        # Error types
├── retry.py             # Circuit breaker, rate limiting
├── health.py            # Health checks (requires [health])
└── tests/               # Test suite
```

## Module responsibilities

### Core (always available)

| Module | Responsibility |
|--------|---------------|
| `__init__.py` | Package-level exports with lazy loading. Imports are deferred so the package loads fast even when extras are installed. |
| `feature_flags.py` | Detects which optional extras are installed and exposes the `FEATURES` dictionary. |
| `client.py` | The `ComfyClient` HTTP client. Handles connection, workflow submission, polling, and result retrieval. |
| `workflows.py` | Template-based workflow compiler. Translates presets and prompts into ComfyUI workflow JSON. |
| `video.py` | Video model definitions, preset configurations, and the VRAM-aware recommendation engine. |
| `config.py` | Settings management — connection URLs, timeouts, and other runtime configuration. |
| `exceptions.py` | The structured error hierarchy (`ComfyHeadlessError` and its subclasses). |
| `retry.py` | Circuit-breaker logic and rate limiting for resilient ComfyUI communication. |

### Optional (requires extras)

| Module | Extra | Responsibility |
|--------|-------|---------------|
| `websocket_client.py` | `[websocket]` | The `ComfyWSClient` for real-time progress tracking over WebSocket. |
| `intelligence.py` | `[ai]` | AI prompt analysis and enhancement via a local Ollama model. |
| `health.py` | `[health]` | System health monitoring using psutil. |
| `ui.py` | `[ui]` | The Gradio 6.0 web interface. |
| `theme.py` | `[ui]` | Ocean Mist theme definition for the Gradio interface. |

## How workflow compilation works

When you call `client.generate_image("a sunset")`, the following happens:

1. **Prompt analysis** (optional) — if the `[ai]` extra is installed and configured, the prompt is sent to Ollama for analysis and enhancement.
2. **Template selection** — the workflow compiler selects a workflow template based on the generation type (image, video) and any preset you specified.
3. **Template compilation** — the compiler fills in the template with your prompt, settings, and model-specific parameters, producing a ComfyUI-compatible workflow JSON.
4. **Submission** — the compiled workflow is submitted to ComfyUI via HTTP POST.
5. **Polling or WebSocket** — depending on which client you use, the library either polls for completion (HTTP) or listens for progress events (WebSocket).
6. **Result retrieval** — once ComfyUI reports completion, the generated files are retrieved and returned.

## ComfyUI node requirements

Comfy Headless generates workflow JSON that references specific ComfyUI nodes. Your ComfyUI instance must have these nodes installed for the corresponding features to work.

### Core (required for all generation)

The standard ComfyUI installation includes all nodes needed for basic image generation. No additional custom nodes are required for text-to-image workflows.

### Video generation nodes

Each video model requires specific custom nodes:

| Model | Required custom nodes |
|-------|-----------------------|
| **All video models** | [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) — video encoding and output |
| **LTX-Video 2** | Built-in ComfyUI support (recent versions include LTX nodes natively) |
| **Hunyuan 1.5** | [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper) |
| **Wan** | [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper) |
| **AnimateDiff** | [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved) |

### Installing custom nodes

Most custom nodes can be installed through ComfyUI Manager or by cloning the repository into your ComfyUI `custom_nodes` directory:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
```

After installing, restart ComfyUI for the new nodes to be detected.

## Security and data scope

Comfy Headless is designed to be transparent about what it touches:

- **Data touched:** connects to a local or remote ComfyUI instance via HTTP/WebSocket. Sends workflow JSON, receives generated images. Optionally connects to local Ollama for AI prompt intelligence. Stores generated images in temp directories with automatic cleanup.
- **Data not touched:** no telemetry, no analytics, no external API calls beyond user-configured ComfyUI and optional Ollama. Secrets are masked in all log output via `SecretValue`.
- **Permissions required:** network access to the ComfyUI server, optional Ollama server. File write access for image output and temp directories.

## Related projects

Comfy Headless is part of the [MCP Tool Shop](https://mcp-tool-shop.github.io/) ecosystem — open-source ML tooling for local hardware. Related projects include:

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) — ML development toolkit
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) — browse all tools

## Next steps

- Return to the [Handbook index](../) for a complete overview.
- Visit the [Getting Started](../getting-started/) page if you have not installed Comfy Headless yet.
