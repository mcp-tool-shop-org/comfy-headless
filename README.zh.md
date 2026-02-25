<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="comfy-headless" width="400">
</p>

# Comfy Headless

**让 ComfyUI 的强大功能触手可及，同时避免其复杂性**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## 为什么选择 Comfy Headless？

| 问题 | 解决方案 |
| --------- | ---------- |
| ComfyUI 的节点界面过于复杂 | 简单的预设和简洁的 Python API |
| 提示词工程很困难 | 基于 AI 的提示词增强 |
| 视频生成很复杂 | 一键视频生成，带模型预设 |
| 不知道该使用哪些设置 | 自动为您选择最佳设置，以满足您的需求 |

## 快速开始

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## 设计理念

- **面向用户：** 简单的预设和基于 AI 的提示词增强
- **面向开发者：** 干净的 API，基于模板的工作流程编译
- **面向所有人：** 自动为您选择最佳设置，以满足您的需求

## 安装

### 模块化安装 (v2.5.0+)

仅安装您需要的组件：

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

### 可选组件

| Extra | 依赖项 | 特性 |
| ------- | -------------- | ---------- |
| `ai` | httpx | Ollama 提示词智能 |
| `websocket` | WebSocket | 实时进度更新 |
| `health` | psutil | 系统健康状况监控 |
| `ui` | gradio | Web 界面 |
| `validation` | pydantic | 配置验证 |
| `observability` | opentelemetry | 分布式追踪 |
| `standard` | AI + WebSocket | 推荐套餐 |
| `full` | 以上所有组件 | 全部 |

### 系统要求

- Python 3.10+
- 必须在本地运行 ComfyUI (默认：`http://localhost:8188`)
- 可选：Ollama 用于 AI 提示词增强

## 使用方法

### 作为库使用

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### 带 AI 增强

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

### 视频生成

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

### 启动 Web 界面

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

或通过命令行：
```bash
python -m comfy_headless.ui
```

**UI 特性 (v2.5.1):**
- **图像生成** - txt2img，带预设和 AI 提示词增强
- **视频生成** - 支持 AnimateDiff、LTX、Hunyuan、Wan
- **队列和历史记录** - 实时队列管理，任务历史记录
- **工作流程** - 浏览、导入和创建工作流程模板
- **模型浏览器** - 查看检查点、LoRA、运动模型
- **设置** - 连接管理、超时设置、系统信息

**主题：** 海洋薄雾 - 柔和的薄荷绿点缀在温暖的中性背景上

## 视频模型 (v2.5.0)

### 支持的模型

| Model | VRAM | 质量 | Speed | 最适合 |
| ------- | ------ | --------- | ------- | ---------- |
| **LTX-Video 2** | 12GB+ | 优秀 | Fast | 通用用途，RTX 3080+ |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | 高质量，RTX 4080+ |
| **Wan 2.1/2.2** | 6-16GB | Great | 中等 | 入门级显卡，效率 |
| **Mochi** | 12GB+ | 优秀 | Slow | 文本一致性 |
| AnimateDiff | 6GB+ | Good | Fast | 快速预览 |
| SVD | 8GB+ | Good | 中等 | 图像转视频 |
| CogVideoX | 10GB+ | Good | Slow | 旧版本支持 |

### 视频预设

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

## 特性标志

检查哪些特性可用：

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## WebSocket 进度

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

## API 参考

### 核心类

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

### 错误处理

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

## 架构

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

## ComfyUI 节点要求

### 用于视频生成

安装以下自定义节点：

**核心功能：**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - 视频编码

**特定模型支持：**
- LTX-Video 2：内置 ComfyUI 支持（最新版本）
- Hunyuan 1.5：[ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan：[ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff：[ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## 相关项目

该项目是 [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) 的一部分，该项目提供用于本地硬件的开源机器学习工具。

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - 机器学习开发工具包
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - 浏览所有工具

## 许可证

MIT 许可证 - 参见 [LICENSE](LICENSE)

## 贡献

欢迎贡献！请提交问题或拉取请求。

感兴趣的领域：
- 更多视频模型支持
- 工作流程模板
- 文档
- 错误修复

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
