<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

**让 ComfyUI 的强大功能触手可及，同时避免其复杂性**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## 为什么选择 Comfy Headless？

| 问题 | 解决方案 |
|---------|----------|
| ComfyUI 的节点界面过于复杂。 | 简单的预设和简洁的 Python API。 |
| 提示词工程很困难。 | 基于 AI 的提示词增强。 |
| 视频生成很复杂。 | 一键视频生成，带有模型预设。 |
| 不知道该使用哪些设置。 | 根据您的意图，自动选择最佳设置。 |

## 快速入门

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

- **面向用户：** 简单的预设和基于 AI 的提示词增强。
- **面向开发者：** 简洁的 API 和基于模板的工作流程编译。
- **面向所有人：** 根据您的意图，自动选择最佳设置。

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

### 可用的附加组件

| 附加组件 | 依赖项 | 特性 |
|-------|--------------|----------|
| `ai` | httpx | Ollama 提示词智能 |
| `websocket` | websockets | 实时进度更新 |
| `health` | psutil | 系统健康状况监控 |
| `ui` | gradio | Web 界面 |
| `validation` | pydantic | 配置验证 |
| `observability` | opentelemetry | 分布式追踪 |
| `standard` | AI + WebSocket | 推荐的组件包 |
| `full` | 以上所有 | 全部 |

### 要求

- Python 3.10+
- ComfyUI 运行在本地 (默认: `http://localhost:8188`)
- 可选: Ollama 用于 AI 提示词增强

## 使用方法

### 作为库使用

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### 带有 AI 增强

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

或者通过命令行：
```bash
python -m comfy_headless.ui
```

**UI 特性 (v2.5.1):**
- **图像生成** - txt2img，带有预设和 AI 提示词增强
- **视频生成** - 支持 AnimateDiff、LTX、Hunyuan、Wan
- **队列 & 历史** - 实时队列管理，任务历史
- **工作流程** - 浏览、导入和创建工作流程模板
- **模型浏览器** - 查看检查点、LoRA、运动模型
- **设置** - 连接管理、超时、系统信息

**主题：** 海洋薄雾 - 柔和的薄荷绿点缀在温暖的中性背景上。

## 视频模型 (v2.5.0)

### 支持的模型

| 模型 | 显存 (VRAM) | 质量 | 速度 | 最适合 |
|-------|------|---------|-------|----------|
| **LTX-Video 2** | 12GB+ | 优秀 | 快速 | 通用用途，RTX 3080+ |
| **Hunyuan 1.5** | 14GB+ | 最佳 | 缓慢 | 高质量，RTX 4080+ |
| **Wan 2.1/2.2** | 6-16GB | 良好 | 中等 | 入门级显卡，效率 |
| **Mochi** | 12GB+ | 优秀 | 缓慢 | 文本一致性 |
| AnimateDiff | 6GB+ | 良好 | 快速 | 快速预览 |
| SVD | 8GB+ | 良好 | 中等 | 图像转视频 |
| CogVideoX | 10GB+ | 良好 | 缓慢 | 旧版本支持 |

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

## 安全与数据范围

- **涉及的数据：** 通过 HTTP/WebSocket 连接到本地/远程 ComfyUI 实例。发送工作流程 JSON，接收生成的图像。可选地连接到本地 Ollama，用于 AI 提示智能。将生成的图像存储在临时目录中，并自动清理。
- **未涉及的数据：** 不收集任何遥测数据，不进行任何分析，不使用任何外部 API，除非用户配置了 ComfyUI 和可选的 Ollama。所有日志输出中的敏感信息都通过 `SecretValue` 进行屏蔽。
- **所需权限：** 访问 ComfyUI 服务器的网络权限，可选的 Ollama 服务器。 写入文件权限，用于图像输出和临时目录。

请参阅 [SECURITY.md](SECURITY.md)，了解漏洞报告和安全最佳实践。

## 评估指标

| 类别 | 评分 |
|----------|-------|
| A. 安全性 | 10/10 |
| B. 错误处理 | 10/10 |
| C. 操作文档 | 10/10 |
| D. 发布质量 | 10/10 |
| E. 身份验证（软） | 10/10 |
| **Overall** | **50/50** |

> 使用 [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck) 进行评估

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

由 [MCP Tool Shop](https://mcp-tool-shop.github.io/) 构建。
