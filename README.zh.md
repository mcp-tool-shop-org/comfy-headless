<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>用Python轻松掌控ComfyUI，告别复杂的节点图。</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## 这是什么

comfy-headless **构建 ComfyUI API 格式的图**并运行它们。你调用一个 Python 函数；它会输出 JSON 节点图，将其 POST 到 ComfyUI，轮询以获取完成状态，并将输出路径提供给你。

这种框架很重要，因为它告诉你可能出现什么问题。该库的全部工作是输出目标 ComfyUI 实际拥有的节点名称和输入键。当 ComfyUI 重命名或删除一个节点时，引用旧名称的图将在提交时被拒绝，并显示一个不透明的错误——并且没有任何内容会提前警告你。

**v3.0 是认真对待这一点的版本。**该库输出的每个节点类型都经过审核，以确保与当前的 ComfyUI 目录一致。其中九个不再存在。它们已被删除，使用它们的图已在经过验证的节点上重新构建，并且该库现在可以告诉你服务器缺少什么*在你*运行它之前。

| 问题 | comfy-headless 的作用 |
|---------|--------------------------|
| 节点接口有很多 | 预设和简洁的 Python API |
| 提示工程很困难 | 可选的本地 Ollama AI 增强功能 |
| 视频生成比较复杂 | 9 个模型系列中的 24 个预设 |
| “我应该使用哪些设置？” | 根据你的 VRAM 进行调整的推荐配置 |
| 图因神秘错误而失败 | 依赖项检查会命名节点*和*包 |

## 快速入门

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` 返回一个包含 `success`、`prompt_id`、`images`、`error`、`seed` 和 `preset` 的 `dict`。此库中的每个生成调用都返回一个字典——没有需要解包的结果对象。

## 安装

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| 附加功能 | 添加 |
|-------|------|
| `ai` | 通过本地 Ollama 进行提示分析和增强 |
| `websocket` | 通过 WebSocket 实现实时进度显示 |
| `ui` | Gradio Web 界面 |
| `health` | 系统健康状况监控 |
| `validation` | Pydantic 配置验证 |
| `observability` | OpenTelemetry 跟踪 |
| `standard` | `ai` + `websocket` |
| `full` | 以上所有内容 |

需要 **Python 3.10+** 和正在运行的 ComfyUI 实例。

检查运行时激活的内容：

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## 图像

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

八个图像预设：`draft`、`fast`、`quality`、`hd`、`portrait`、`landscape`、`cinematic`、`square`。

批量处理提示列表：

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### AI 提示增强

需要 `[ai]` 附加组件和本地 Ollama。这些是**模块级别函数**，而不是客户端方法：

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

## 视频

```python
from comfy_headless import list_video_presets, get_recommended_preset

print(list_video_presets())                  # 24 presets
print(get_recommended_preset(vram_gb=16))    # picks one that fits

result = client.generate_video(
    "a slow pan across a mountain range",
    preset="ltx_quality",
)
print(result["videos"])
```

选择是**通过预设**进行，而不是通过模型——`generate_video` 没有 `model` 参数。任何 `frames`、`fps`、`steps`、`cfg`、`width` 或 `height` 都可以传递以覆盖预设。

### 图像输入

图像到视频，以及任何使用源图像的内容，都需要该图像首先存在于 ComfyUI 中。上传它，然后传递服务器返回的名称：

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

从响应中读取 `name`，而不是重用你发送的文件名——ComfyUI 在发生冲突时会更改文件名，因此两者并不总是相等。`ref` 是与任何子文件夹一起连接的相同值，这正是图所需的内容。

> **3.0 版本中的变更：** `init_image` 是服务器端的文件名。早期版本接受 base64 数据并通过不存在于标准 ComfyUI 安装中的第三方节点将其传递。请参阅 [CHANGELOG](CHANGELOG.md)。

### 模型系列

| 系列 | 最小 VRAM | 质量 | 速度 | 附加节点 | 最适合 |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | 非常好 | 中等 | — | 低 VRAM，效率 |
| AnimateDiff Lightning | 6 GB | 还可以 | 最快 | AnimateDiff-Evolved | 4 步草稿 |
| AnimateDiff | 8 GB | 良好 | 快 | AnimateDiff-Evolved，帧插值。 | 快速预览 |
| **LTX-Video** | 12 GB | 极佳 | 快 | — | 安全默认设置 |
| **Mochi** | 12 GB | 极佳 | 慢速 | — | 文本一致性，长片段 |
| **SVD** | 12 GB | 良好 | 中等 | — | 动画静止图像 |
| **Hunyuan 1.5** | 14 GB | 最佳 | 慢速 | — | 最高质量 |
| CogVideoX | 16 GB | 良好 | 慢速 | CogVideoX 包装器 | 旧版 |
| **Hunyuan 1.0** | 24 GB | 非常好 | 慢速 | 帧插值 | 已被 1.5 取代 |

九个系列中的六个在**标准 ComfyUI 核心节点**上运行——没有用于模型本身的包装包。只有 AnimateDiff（两个变体）和 CogVideoX 需要一个。视频输出使用 [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)；帧插值使用 [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)。

VRAM 数字是该系列默认分辨率的下限，从 `VIDEO_MODEL_INFO` 读取——而不是上限。更多的内存可以为同一系列带来更长的片段和更高的分辨率。

### 在运行之前检查

与其在提交时发现缺少节点：

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

## 配置

环境变量使用 `COMFY_HEADLESS_` 前缀，并带有 `__` 部分分隔符：

| 变量 | 默认值 |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | 读取超时时间（秒） |
| `COMFY_HEADLESS_LOGGING__LEVEL` | 日志级别 |

或者直接传递 URL：`ComfyClient("http://192.168.1.50:8188")`。

## Web UI

```bash
comfy-headless                 # launching the UI is the default action
```

| 标志 | 含义 |
|------|---------|
| `--port` / `-p` | UI 端口（默认 `7861`） |
| `--share` | 公共 Gradio 分享链接 |
| `--url` | ComfyUI 服务器 URL |
| `--version` / `-v` | 打印版本 |
| `--check` | 功能可用性 |
| `--diagnose` | 完整的诊断信息 |

六个选项卡：图像、视频、队列与历史记录、工作流程、模型、设置。主题为“海洋雾”，采用柔和的蓝绿色作为点缀，背景为温暖的中性色。

以编程方式（需要 `[ui]`）：

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## 进度

阻塞调用使用 `on_progress` 回调函数：

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

对于通过 WebSocket 进行的实时更新（需要 `[websocket]`）：

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## 错误

每个异常都包含一个结构化的代码、消息和提示：

```python
from comfy_headless import (
    ComfyHeadlessError,       # base
    ComfyUIConnectionError,   # cannot reach ComfyUI
    ComfyUIOfflineError,      # ComfyUI not responding
    GenerationTimeoutError,
    GenerationFailedError,
    ValidationError,
    UploadError,              # new in 3.0
    MissingNodePackError,     # new in 3.0
)

try:
    client.generate_image("test")
except ComfyUIOfflineError:
    print("Start ComfyUI first")
```

## 工作原理

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

该库与 ComfyUI 的七个路由进行通信——`/system_stats`、`/object_info`、`/queue`、
`/history`、`/prompt`、`/interrupt`、`/view`，以及 `/upload/image` 和 `/upload/mask` 用于
二进制输入。

`/object_info` 是确定给定服务器可以运行的内容的权威。它是一个实时端点，而不是
一个版本化的制品：没有核心节点注册表可供参考。因此，该库会根据目标服务器的实际目录来验证发出的图，而不是假设一个固定的节点集。`check_workflow_dependencies()` 就是这个检查，并且它是重要的基础设施，而不仅仅是便利功能。

当您需要访问图形本身时，以下是一些有用的方法：

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## 文档

完整手册：
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**——入门、使用方法、配置、API 参考、视频模型、架构。

## 安全性和数据范围

- **涉及的数据：**通过 HTTP/WebSocket 连接到本地或远程 ComfyUI 实例。发送工作流程 JSON 和上传的图像，接收生成的媒体。可选地连接到本地 Ollama 以进行提示智能处理。将输出写入临时目录并自动清理。
- **不涉及的数据：**没有遥测数据、分析数据，也没有超出您配置的 ComfyUI 和 Ollama 端点的外部 API。所有日志输出中的敏感信息都通过 `SecretValue` 进行屏蔽。
- **所需权限：**访问您的 ComfyUI 服务器和可选的 Ollama 服务器的网络连接；用于输出和临时目录的文件写入权限。
- **上传：**`upload_image` 会拒绝任何尝试遍历子文件夹的操作。上传的文件将存储在您指向的服务器上的 ComfyUI 的输入目录中——请将该服务器视为受信任的服务器。

有关漏洞报告，请参阅 [SECURITY.md](SECURITY.md)。

## 评估结果

| 类别 | 得分 |
|----------|-------|
| A. 安全性 | 10/10 |
| B. 错误处理 | 10/10 |
| C. 操作文档 | 10/10 |
| D. 发布规范 | 10/10 |
| E. 身份（软） | 10/10 |
| **Overall** | **50/50** |

> 使用 [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck) 进行评估。

## 相关内容

是 [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) 的一部分——用于本地硬件的开源机器学习工具。

## 贡献

欢迎提交问题和拉取请求——请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。有用的领域：额外的模型系列、工作流程模板、文档、错误修复。

如果您添加了一种节点类型，请首先验证它是否存在于 ComfyUI 的实时目录中，并声明其包（如果它不是核心组件）。这个规则就是本次发布的理由。

## 许可证

MIT——请参阅 [LICENSE](LICENSE)。

---

由 [MCP Tool Shop](https://mcp-tool-shop.github.io/) 构建
