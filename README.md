<div align="center">

# Comfy Headless

**Making ComfyUI's power accessible without the complexity**

[![PyPI version](https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/comfy-headless/)
[![Downloads](https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white)](https://pypi.org/project/comfy-headless/)
[![Tests](https://github.com/mcp-tool-shop/comfy-headless/actions/workflows/test.yml/badge.svg)](https://github.com/mcp-tool-shop/comfy-headless/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/mcp-tool-shop/comfy-headless/graph/badge.svg)](https://codecov.io/gh/mcp-tool-shop/comfy-headless)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.5.1-green.svg)](https://github.com/mcp-tool-shop/comfy-headless/releases)
[![GitHub stars](https://img.shields.io/github/stars/mcp-tool-shop/comfy-headless?style=social)](https://github.com/mcp-tool-shop/comfy-headless)

*AI image & video generation in 3 lines of code*

[Installation](#installation) • [Quick Start](#quick-start) • [Video Models](#video-models-v250) • [Web UI](#launch-the-web-ui) • [Contributing](#contributing)

</div>

---

## Why Comfy Headless?

| Problem | Solution |
|---------|----------|
| ComfyUI's node interface is overwhelming | Simple presets and clean Python API |
| Prompt engineering is hard | AI-powered prompt enhancement |
| Video generation is complex | One-line video with model presets |
| No idea what settings to use | Best settings for your intent, automatically |

<!--
## Demo

<p align="center">
  <img src="docs/assets/demo.gif" alt="Comfy Headless Demo" width="600">
</p>
-->

## Quick Start

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## Philosophy

- **For Users**: Simple presets and AI-powered prompt enhancement
- **For Developers**: Clean API with template-based workflow compilation
- **For Everyone**: Best settings for your intent, automatically

## Installation

### Modular Installation (v2.5.0+)

Install only what you need:

```bash
# Core only (minimal - ~2MB)
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

### Available Extras

| Extra | Dependencies | Features |
|-------|--------------|----------|
| `ai` | httpx | Ollama prompt intelligence |
| `websocket` | websockets | Real-time progress updates |
| `health` | psutil | System health monitoring |
| `ui` | gradio | Web interface |
| `validation` | pydantic | Config validation |
| `observability` | opentelemetry | Distributed tracing |
| `standard` | ai + websocket | Recommended bundle |
| `full` | All of the above | Everything |

### Requirements

- Python 3.10+
- ComfyUI running locally (default: `http://localhost:8188`)
- Optional: Ollama for AI prompt enhancement

## Usage

### Use as a Library

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### With AI Enhancement

```python
from comfy_headless import analyze_prompt, enhance_prompt

# Analyze a prompt
analysis = analyze_prompt("a cyberpunk city at night with neon lights")
print(f"Intent: {analysis.intent}")        # "scene"
print(f"Styles: {analysis.styles}")        # ["scifi", "cinematic"]
print(f"Preset: {analysis.suggested_preset}")  # "cinematic"

# Enhance a prompt
enhanced = enhance_prompt("a cat", style="detailed")
print(enhanced.enhanced)   # "a cat, masterpiece, best quality, highly detailed..."
print(enhanced.negative)   # Style-aware negative prompt
```

### Video Generation

```python
from comfy_headless import ComfyClient, list_video_presets

# See available presets
print(list_video_presets())

# Generate video with preset
client = ComfyClient()
result = client.generate_video(
    prompt="a cat walking through a garden",
    preset="ltx_quality"  # LTX-Video 2, 1280x720, 49 frames
)
```

### Launch the Web UI

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

Or via command line:
```bash
python -m comfy_headless.ui
```

**UI Features (v2.5.1):**
- **Image Generation** - txt2img with presets, AI prompt enhancement
- **Video Generation** - AnimateDiff, LTX, Hunyuan, Wan support
- **Queue & History** - Real-time queue management, job history
- **Workflows** - Browse, import, and create workflow templates
- **Models Browser** - View checkpoints, LoRAs, motion models
- **Settings** - Connection management, timeouts, system info

**Theme:** Ocean Mist - soft teal accents on warm neutral backgrounds

## Video Models (v2.5.0)

### Supported Models

| Model | VRAM | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **LTX-Video 2** | 12GB+ | Excellent | Fast | General use, RTX 3080+ |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | High quality, RTX 4080+ |
| **Wan 2.1/2.2** | 6-16GB | Great | Medium | Budget GPUs, efficiency |
| **Mochi** | 12GB+ | Excellent | Slow | Text adherence |
| AnimateDiff | 6GB+ | Good | Fast | Quick previews |
| SVD | 8GB+ | Good | Medium | Image-to-video |
| CogVideoX | 10GB+ | Good | Slow | Legacy support |

### Video Presets

```python
from comfy_headless import VIDEO_PRESETS, get_recommended_preset

# Get preset recommendation based on your VRAM
preset = get_recommended_preset(vram_gb=16)  # Returns "hunyuan15_720p"

# LTX-Video 2 (Fast, great quality)
# "ltx_quick": 768x512, 25 frames, 20 steps
# "ltx_standard": 1280x720, 49 frames, 25 steps
# "ltx_quality": 1280x720, 97 frames, 30 steps

# Hunyuan 1.5 (Best quality)
# "hunyuan15_720p": 1280x720, 121 frames
# "hunyuan15_1080p": 1920x1080 with super-resolution

# Wan (Efficient)
# "wan_1.3b": 720x480, 49 frames (6GB VRAM)
# "wan_14b": 1280x720, 81 frames (12GB VRAM)
```

## Feature Flags

Check what features are available:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## WebSocket Progress

```python
import asyncio
from comfy_headless import ComfyWSClient

async def generate_with_progress():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        result = await ws.wait_for_completion(
            prompt_id,
            on_progress=lambda p: print(f"Progress: {p.progress}%")
        )
        return result

asyncio.run(generate_with_progress())
```

## API Reference

### Core Classes

```python
from comfy_headless import (
    # Client
    ComfyClient,           # Main HTTP client
    ComfyWSClient,         # WebSocket client (requires [websocket])

    # Video
    VideoSettings,         # Video generation settings
    VideoModel,            # Model enum (LTXV, HUNYUAN_15, WAN, etc.)
    VIDEO_PRESETS,         # Preset configurations
    get_recommended_preset, # VRAM-based recommendation

    # Workflows
    compile_workflow,      # Compile workflow from preset
    WorkflowCompiler,      # Low-level compiler

    # Intelligence (requires [ai])
    analyze_prompt,        # Analyze prompt intent/style
    enhance_prompt,        # AI-powered enhancement
    PromptAnalysis,        # Analysis result type
)
```

### Error Handling

```python
from comfy_headless import (
    ComfyHeadlessError,      # Base exception
    ComfyUIConnectionError,  # Can't reach ComfyUI
    ComfyUIOfflineError,     # ComfyUI not responding
    GenerationTimeoutError,  # Generation took too long
    GenerationFailedError,   # Generation failed
    ValidationError,         # Invalid parameters
)

try:
    result = client.generate_image("test")
except ComfyUIOfflineError:
    print("Start ComfyUI first!")
except GenerationTimeoutError:
    print("Generation timed out")
```

## Architecture

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

## ComfyUI Node Requirements

### For Video Generation

Install these custom nodes:

**Core:**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Video encoding

**Model-Specific:**
- LTX-Video 2: Built-in ComfyUI support (recent versions)
- Hunyuan 1.5: [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan: [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff: [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## Security

See [SECURITY.md](SECURITY.md) for full security documentation.

**Key defaults (v2.5.1+):**
- UI binds to `127.0.0.1` (localhost only) by default
- WebSocket requires `wss://` for non-localhost connections
- UI authentication support via environment variables

```bash
# To expose UI on network with auth:
export COMFY_HEADLESS_UI__HOST=0.0.0.0
export COMFY_HEADLESS_UI__USERNAME=admin
export COMFY_HEADLESS_UI__PASSWORD=your-password
```

## Troubleshooting

### Connection Refused / ComfyUI Offline

```python
ComfyUIOfflineError: Cannot connect to ComfyUI at http://localhost:8188
```

**Solutions:**
1. Start ComfyUI: `cd /path/to/ComfyUI && python main.py`
2. Check the port: `curl http://localhost:8188/system_stats`
3. If using custom port: `export COMFY_HEADLESS_COMFYUI__URL=http://localhost:YOUR_PORT`

### Generation Timeout

```python
GenerationTimeoutError: Generation timed out after 300s
```

**Solutions:**
1. Increase timeout: `export COMFY_HEADLESS_GENERATION__GENERATION_TIMEOUT=600`
2. For video: `export COMFY_HEADLESS_GENERATION__VIDEO_TIMEOUT=900`
3. Check VRAM - reduce resolution or use smaller model

### Missing Nodes / Workflow Error

```python
ValidationError: Node 'KSampler' not found
```

**Solutions:**
1. Install missing custom nodes via ComfyUI Manager
2. Check node name spelling in workflow JSON
3. Update ComfyUI to latest version

### WebSocket Connection Failed

```python
ValueError: Refusing unencrypted WebSocket connection to non-localhost host
```

**Solutions:**
1. Use HTTPS URL: `export COMFY_HEADLESS_COMFYUI__URL=https://your-host:8188`
2. Or allow insecure (not recommended): `export COMFY_HEADLESS_WEBSOCKET__ALLOW_INSECURE=true`

### Out of VRAM

**Solutions:**
1. Use smaller preset: `client.generate_video(prompt, preset="ltx_quick")`
2. Reduce resolution: `width=512, height=512`
3. Use VRAM-appropriate model: `get_recommended_preset(vram_gb=8)`

### Import Errors

```python
ImportError: 'analyze_prompt' requires the [ai] feature
```

**Solutions:**
```bash
# Install specific feature
pip install comfy-headless[ai]

# Or install standard bundle
pip install comfy-headless[standard]

# Or install everything
pip install comfy-headless[full]
```

## Related Projects

Part of the **Compass Suite** for AI-powered development:

- [Tool Compass](https://github.com/mcp-tool-shop/tool-compass) - Semantic MCP tool discovery
- [File Compass](https://github.com/mcp-tool-shop/file-compass) - Semantic file search
- [Integradio](https://github.com/mcp-tool-shop/integradio) - Vector-embedded Gradio components
- [Backpropagate](https://github.com/mcp-tool-shop/backpropagate) - Headless LLM fine-tuning

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please open an issue or pull request.

Areas of interest:
- Additional video model support
- Workflow templates
- Documentation
- Bug fixes

---

<div align="center">

**[Documentation](https://github.com/mcp-tool-shop/comfy-headless#readme)** • **[Issues](https://github.com/mcp-tool-shop/comfy-headless/issues)** • **[Discussions](https://github.com/mcp-tool-shop/comfy-headless/discussions)**

</div>
