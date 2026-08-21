<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>Drive ComfyUI from Python. No node graph.</strong>
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

**v3.1 将该方法扩展到六种工作流程配置**——图像、视频、3D、推理、元数据和音频——在一个共享的寻址/类型层上，该层支持 ComfyUI 的验证规则：从服务器验证器转录的联合类型匹配、点状动态组合字段（`codec.encoding.crf`）以及在构建时拒绝非活动分支值的条件输入。与之前相同的方式——网格、音乐和字幕通过 `/history` + `/view` 返回，就像其他内容一样。

| 问题 | comfy-headless 的作用 |
|---------|--------------------------|
| 节点接口有很多 | 预设和简洁的 Python API |
| 提示工程很困难 | 可选的本地 Ollama AI 增强功能 |
| 视频生成比较复杂 | 9 个模型系列中的 24 个预设 |
| “我需要从这张图像中提取一个网格。” | `generate_3d()` — Hunyuan3D-2，所有核心节点 |
| “我需要音乐/音轨。” | `generate_audio()` (ACE-Step 1.5)，`separate_audio()` |
| “这张图像里有什么？” | `run_inference()` — 标题、标签、检测、分割、OCR |
| “是哪个图生成了这张 PNG 图片？” | `extract_prompt_graph()` / `rerun_from_png()` |
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

### Qwen-Image（v3.1 中的新功能）

Qwen-Image-2512 文本到图像模型以 `qwen_txt2img` 模板的形式提供，其中包含模型实际需要的配方：`UNETLoader` 路径、16 通道的 `EmptySD3LatentImage`（SDXL 潜在层在 DiT 模型上会产生垃圾结果）、步数为 20，**cfg 为 2.5**，偏移量为 3.1，原生分辨率为 1328×1328：

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

使用最多三个参考图像进行指令编辑（Qwen-Image-Edit-2511）：

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

参考图像以离散的 `image1..image3` 输入形式输入到 `TextEncodeQwenImageEditPlus`，并且不通过 VAEEncode——这是该节点实际期望的图结构。

### ControlNet（v3.1 中的新功能）

一个代码路径涵盖 Qwen 和 SDXL 联合 ControlNets：

```python
from comfy_headless import build_controlnet_workflow

workflow = build_controlnet_workflow(
    "a stone fortress at dawn",
    control_image_ref=client.upload_image("depth.png")["ref"],
    control_type="depth",      # verbatim enum; "auto" makes the model infer
    base="qwen",               # or "sdxl"
)
client.queue_prompt(workflow)
```

仅发出核心 `Canny` 预处理器（`preprocess="canny"`）；其他提示类型需要一个预先准备好的控制图像，因为它们的预处理器位于自定义包中，而该库不会静默地要求安装这些包。

## 视频

```python
from comfy_headless import list_video_presets, get_recommended_preset

print(list_video_presets())                  # 26 presets
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

> **v3.1 中的新功能：** Hunyuan 1.5 图像到视频模型是一个真正的 i2v 模型——预设 `hunyuan15_i2v` 和 `hunyuan15_i2v_fast` 基于核心 `HunyuanVideo15ImageToVideo` 节点构建，并且需要一个 `init_image`（v3.0 静默地构建了一个文本到视频图）。此外，`output="core"` 将 `VHS_VideoCombine` 终止符替换为核心 `CreateVideo → SaveVideo`，完全取消了对 Video Helper Suite 的依赖。

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

您还可以使用服务器自己的接受规则来检查图的边缘是否与实时服务器兼容（因此，一个 `MESH` 输入到 `FILE_3D_*` 联合输入的组合永远不会导致错误的拒绝）：

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D（v3.1 中的新功能）

通过 **Hunyuan3D-2** 进行图像到网格的转换——完全使用 ComfyUI 核心节点，没有包装包，也没有新的路径。GLB 文件以与 PNG 文件相同的方式注册在 `/history` 中，并通过 `/view` 下载：

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` 接受本地路径、原始字节、一个 `upload_image()` 字典或服务器端引用，并在需要时自动上传。它是一种纯粹的图像条件设置——图中没有文本提示。可调参数：`steps`（30）、`cfg`（5.5）、`octree_resolution`（256）、`threshold`（0.6）、`seed`。

有目的地不发出包装包 3D 模型（TRELLIS、TripoSG……）——ComfyUI-3D-Pack 的原生依赖项是生态系统中稳定性最低的。

## 音频（v3.1 中的新功能）

通过 **ACE-Step 1.5** 进行文本到音乐的转换——MIT 许可的代码*和*权重、原生核心节点，零依赖包。涡轮检查点以 8 个步骤/cfg 1 的速度运行：

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

构建器会强制执行模型的耦合不变性：编码器的 `duration` 和潜在层的 `seconds` 是一个逻辑参数，由单个字段驱动——运行时不会对它们进行交叉验证，并且不匹配会导致“成功”完成，但输出结果会静默地出错。输出通过 `SaveAudioAdvanced`（唯一的非弃用的音频保存节点）；`flac` 输出根本不发出质量字段，`mp3`/`opus` 发出点状的 `format.quality` 子字段。

音轨分离（需要 `audio-separation-nodes-comfyui` 包）：

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## 推理（v3.1 中的新功能）

非生成模型调用——询问有关图像的问题，而不是生成一个图像。它运行在 Florence-2 上（包 `comfyui-florence2`；检测任务添加 `comfyui-segment-anything-2`）：

```python
r = client.run_inference("photo.png", task="caption")
print(r["text"])                     # the caption, read straight from /history

r = client.run_inference("photo.png", task="tag")               # booru-style tags
r = client.run_inference("photo.png", task="ocr")
r = client.run_inference("photo.png", task="detect", text_input="the red car")
print(r["text"])                     # bounding-box coordinates as JSON

r = client.run_inference("photo.png", task="segment", text_input="the person")
mask_png = client.get_file(**r["images"][0])
```

配置文件的关键规则：结果只能通过输出节点到达 `/history`。每个推理图都以核心 `SaveText` 结尾（该节点会内联报告文本——没有第二次往返），或者使用 `SaveImage` 进行掩码处理，并且构建器拒绝发出一个运行后不会返回任何内容的图。

## 来源（v3.1 中的新功能）

ComfyUI 将**确切的 API 格式图**嵌入到每个输出 PNG 中。comfy-headless 读取它——纯标准库，没有 Pillow——并且可以逐字地重新运行：

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

无需任何自定义节点即可编写自定义来源——`extra_pnginfo` 中的任何内容都将成为输出中的 PNG 文本块：

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

已知限制，已记录而不是隐藏：WebP/JPEG 在 EXIF 中携带相同的数据（不同的读取器路径，未实现）；视频输出不嵌入图；加固的部署可能会删除未知键；GUI 到 API 的转换没有服务器路由——使用 ComfyUI 的“工作流程 → 导出（API）”。

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
    GraphAddressError,        # new in 3.1 — bad dotted field / inactive combo branch
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

该库与七个 ComfyUI 路由进行通信——`/system_stats`、`/object_info`、`/queue`、`/history`、`/prompt`、`/interrupt`、`/view`——以及 `/upload/image` 和 `/upload/mask` 用于二进制输入（音频上传也使用 `/upload/image`；服务器没有特定于音频的路由）。所有六种配置都适合该表面：v3.1 添加了网格、音乐、标题和来源，而无需添加任何新的路由。

`/object_info` 是确定给定服务器可以运行的内容的权威。它是一个实时端点，而不是
一个版本化的制品：没有核心节点注册表可供参考。因此，该库会根据目标服务器的实际目录来验证发出的图，而不是假设一个固定的节点集。`check_workflow_dependencies()` 就是这个检查，并且它是重要的基础设施，而不仅仅是便利功能。

当您需要访问图形本身时，以下是一些有用的方法：

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## 文档

完整手册：**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**——入门、用法、六种配置、视频模型、配置、API 参考、架构。

**存储库中的知识库**，供 LLM 和贡献者使用：[`kb/`](kb/README.md)——一个机器可读的 [`index.json`](kb/index.json)，包含按配置分类的事实页面、可运行的参考图（`kb/workflows/*.json`，由构建器本身生成，因此不会发生漂移）和节点来源（`kb/nodes.json`）。`python scripts/gen_kb.py` 重新生成它；如果代码与知识库不一致，测试套件将失败。

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
