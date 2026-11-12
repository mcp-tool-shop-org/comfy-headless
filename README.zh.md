<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="600">
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

comfy-headless 构建 **ComfyUI API 格式的图表**，并运行这些图表。 您调用一个 Python 函数，该函数会生成 JSON 节点图，然后将其通过 POST 方法发送到 ComfyUI，并轮询以检查是否完成，最后将结果路径返回给您。

这种框架很重要，因为它告诉你可能出现什么问题。该库的全部工作是输出目标 ComfyUI 实际拥有的节点名称和输入键。当 ComfyUI 重命名或删除一个节点时，引用旧名称的图将在提交时被拒绝，并显示一个不透明的错误——并且没有任何内容会提前警告你。

**v3.0 是认真对待这一点的发布版本。**该库输出的每个节点类型都经过审核，以确保与实时的 ComfyUI 目录一致。其中九个不再存在。它们已被删除，使用它们的图已在经过验证的节点上重新构建，并且该库现在可以告诉你服务器缺少什么，*然后再*你开始运行它。

**v3.1 将这种方法扩展到六个工作流程配置文件**——**图像、视频、3D、推理、元数据、音频**——在一个共享的寻址/类型化层上，该层使用 ComfyUI 自己的验证规则：从服务器验证器转录的联合类型匹配、点状动态组合字段（`codec.encoding.crf`）以及在构建时拒绝非活动分支值的条件输入。与之前相同的路由表面——网格、音乐和字幕通过 `/history` + `/view` 返回，就像其他内容一样。

| 问题 | comfy-headless 的作用 |
|---------|--------------------------|
| 节点界面有很多 | 预设和简洁的 Python API |
| 提示工程很困难 | 通过本地 Ollama 进行可选的 AI 增强 |
| 视频生成很复杂 | 9 个模型系列中的 26 个预设 |
| “我需要从这张图像中提取一个网格” | `generate_3d()` — Hunyuan3D-2，所有核心节点 |
| “我需要音乐/音轨” | `generate_audio()`（ACE-Step 1.5），`separate_audio()` |
| “这张图像里有什么？” | `run_inference()` — 标题、标签、检测、分割、OCR |
| “哪个图生成了这个 PNG？” | `extract_prompt_graph()` / `rerun_from_png()` |
| “我应该使用哪些设置？” | 根据你的 VRAM 调整推荐设置 |
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

`generate_image` 返回一个包含 `success`、`prompt_id`、`images`、`error`、`seed` 和 `preset` 的 `dict`。此库中的每次生成调用都会返回一个字典，因此无需解包结果对象。

## 安装

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| 附加功能 | 添加 |
|-------|------|
| `ai` | 通过本地 Ollama 进行提示分析和增强 |
| `websocket` | 通过 WebSocket 进行实时进度显示 |
| `ui` | Gradio Web 界面 |
| `health` | 系统健康状况监控 |
| `validation` | Pydantic 配置验证 |
| `observability` | OpenTelemetry 跟踪 |
| `standard` | `ai` + `websocket` |
| `full` | 以上所有功能 |

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

需要 `[ai]` 附加组件和本地 Ollama。这些是**模块级别的函数**，而不是客户端方法：

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image（3.1 版本的新功能）

Qwen-Image-2512 文本到图像生成作为 `qwen_txt2img` 模板提供，其中包含模型实际需要的配方：`UNETLoader` 路径、16 频道 `EmptySD3LatentImage`（SDXL 潜在图像在 DiT 模型上产生垃圾），步骤 20，**cfg 2.5**，偏移 3.1，原生 1328×1328 桶：

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

参考图像作为离散的 `image1..image3` 输入提供给 `TextEncodeQwenImageEditPlus`，并且不通过 VAEEncode——这是节点实际期望的图的形状。

### ControlNet（3.1 版本的新功能）

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

仅输出核心 `Canny` 预处理器（`preprocess="canny"`）；其他提示类型需要预先制作好的控制图像，因为它们的预处理器位于自定义包中，而该库不会静默地要求安装该包。

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

选择**通过预设**进行，而不是通过模型进行——`generate_video` 没有 `model` 参数。可以将任何 `frames`、`fps`、`steps`、`cfg`、`width`、`height` 传递给预设以进行覆盖。

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

从响应中读取 `name`，而不是重用你发送的文件名——ComfyUI 在发生冲突时会重命名，因此两者并不总是相等。`ref` 是与任何子文件夹连接在一起的相同值，这正是图所需要的。

> **3.0 版本中的更改：** `init_image` 是服务器端的文件名。早期版本接受 base64 数据并通过不存在于标准 ComfyUI 安装中的第三方节点将其传递。请参阅 [CHANGELOG](CHANGELOG.md)。

> **3.1 版本的新功能：** Hunyuan 1.5 图像到视频是真正的 i2v——预设 `hunyuan15_i2v` 和 `hunyuan15_i2v_fast` 基于核心 `HunyuanVideo15ImageToVideo` 节点构建，并且需要 `init_image`（v3.0 默默地构建了一个文本到视频图）。此外，`output="core"` 交换了 `VHS_VideoCombine` 终止符，以使用核心 `CreateVideo → SaveVideo`，从而完全取消了 Video Helper Suite 依赖项。

### 模型系列

| 系列 | 最小 VRAM | 质量 | 速度 | 附加节点 | 最适合 |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | 非常好 | 中等 | — | 低 VRAM，效率 |
| AnimateDiff Lightning | 6 GB | 还可以 | 最快 | AnimateDiff-Evolved | 4 步草稿 |
| AnimateDiff | 8 GB | 好 | 快 | AnimateDiff-Evolved，帧插值。 | 快速预览 |
| **LTX-Video** | 12 GB | 极佳 | 快 | — | 安全默认值 |
| **Mochi** | 12 GB | 极佳 | 慢 | — | 文本一致性，长片段 |
| **SVD** | 12 GB | 好 | 中等 | — | 对静态图像进行动画处理 |
| **Hunyuan 1.5** | 14 GB | 最佳 | 慢 | — | 最高质量 |
| CogVideoX | 16 GB | 好 | 慢 | CogVideoX 包装器 | 旧版 |
| **Hunyuan 1.0** | 24 GB | 非常好 | 慢 | 帧插值 | 已被 1.5 取代 |

九个模型中，有六个可以在**标准 ComfyUI 核心节点**上运行——模型本身不需要包装包。只有 AnimateDiff（两种变体）和 CogVideoX 需要。视频输出使用 [视频助手套件](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)；帧插值使用 [帧插值](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)。

VRAM 数据是该模型族默认分辨率的最小值，从 `VIDEO_MODEL_INFO` 读取——而不是最大值。更多的内存可以为同一模型族提供更长的片段和更高的分辨率。

### 运行前请检查

与其在提交时发现缺少节点：

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

您还可以使用服务器自身的接受规则，对图形的边进行类型检查，以验证其与实时服务器的兼容性（因此，将 `MESH` 馈送到 `FILE_3D_*` 联合输入绝不会导致错误的拒绝）：

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D（3.1 版本的新功能）

通过 **Hunyuan3D-2** 将图像转换为网格——完全使用 ComfyUI 核心节点，没有包装包，没有新的路径。GLB 在 `/history` 中注册的方式与 PNG 相同，并通过 `/view` 下载：

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` 接受本地路径、原始字节、`upload_image()` 字典或服务器端引用，并在需要时自动上传。它是一种纯粹的图像条件处理——图中没有文本提示。可调参数：`steps`（30）、`cfg`（5.5）、`octree_resolution`（256）、`threshold`（0.6）、`seed`。

包装包 3D 模型（TRELLIS、TripoSG 等）不会被故意输出——ComfyUI-3D-Pack 的原生依赖项是生态系统中稳定性最低的。

## 音频（3.1 版本的新功能）

通过 **ACE-Step 1.5** 实现文本到音乐的转换——采用 MIT 许可的代码*和*权重，原生核心节点，零包装包。涡轮检查点以 8 步/cfg 1 运行：

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

构建器会强制执行模型的耦合不变性：编码器的 `duration` 和潜在的 `seconds` 是一个逻辑参数，由单个字段驱动——运行时不会对它们进行交叉验证，并且不匹配会导致“成功”完成，但输出会悄悄地出错。输出通过 `SaveAudioAdvanced`（唯一的非弃用的音频保存节点）；`flac` 输出根本不输出质量字段，`mp3`/`opus` 输出带点的 `format.quality` 子字段。

人声分离（需要 `audio-separation-nodes-comfyui` 包装包）：

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## 推理（3.1 版本的新功能）

非生成模型调用——询问有关图像的问题，而不是生成图像。在 Florence-2 上运行（包装包 `comfyui-florence2`；检测任务添加 `comfyui-segment-anything-2`）：

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

配置文件的负载规则：结果只能通过输出节点到达 `/history`。每个推理图都以核心 `SaveText` 结尾（该节点会内联报告文本——无需第二次往返）或 `SaveImage` 用于生成掩码，并且构建器会拒绝输出会运行并返回空结果的图。

## 溯源（3.1 版本的新功能）

ComfyUI 将**确切的 API 格式图**嵌入到每个输出 PNG 中。comfy-headless 会将其读回——纯粹的 stdlib，没有 Pillow——并且可以逐字地重新运行它：

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

无需任何自定义节点即可编写自定义溯源——`extra_pnginfo` 中的任何内容都将成为输出中的 PNG 文本块：

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

已知限制，记录而不是隐藏：WebP/JPEG 在 EXIF 中携带相同的数据（不同的读取路径，未实现）；视频输出不会嵌入图；加固的部署可能会删除未知的键；GUI 到 API 的转换没有服务器路由——使用 ComfyUI 的“工作流 → 导出（API）”。

## 配置

环境变量使用 `COMFY_HEADLESS_` 前缀和 `__` 分区分隔符：

| 变量 | 默认值 |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | 读取超时时间，秒 |
| `COMFY_HEADLESS_LOGGING__LEVEL` | 日志级别 |

或者直接传递 URL：`ComfyClient("http://192.168.1.50:8188")`。

## Web UI

```bash
comfy-headless                 # launching the UI is the default action
```

| 标志 | 含义 |
|------|---------|
| `--port` / `-p` | UI 端口（默认 `7861`） |
| `--share` | 公共 Gradio 共享链接 |
| `--url` | ComfyUI 服务器 URL |
| `--version` / `-v` | 打印版本 |
| `--check` | 功能可用性 |
| `--diagnose` | 完整诊断 |

六个选项卡：图像、视频、队列和历史记录、工作流、模型、设置。主题为海洋雾——在温暖的中性背景上使用柔和的青色强调色。

以编程方式（需要 `[ui]`）：

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## 进度

阻塞调用需要一个 `on_progress` 回调：

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

该库与七个 ComfyUI 路由进行通信——`/system_stats`、`/object_info`、`/queue`、`/history`、`/prompt`、`/interrupt`、`/view`——以及 `/upload/image` 和 `/upload/mask` 用于二进制输入（音频上传也使用 `/upload/image`；服务器没有音频专用路由）。所有六个配置文件都适合于该表面：v3.1 添加了网格、音乐、字幕和溯源，而无需添加任何路由。

`/object_info` 是关于给定服务器可以运行的内容的权威。它是一个实时端点，而不是一个版本化的工件：没有核心节点注册表可以固定。因此，该库会根据目标服务器的实际目录验证输出的图，而不是假设一组固定的节点。`check_workflow_dependencies()` 是该检查，并且它是重要的基础设施，而不是一个方便的功能。

当您想要图形本身时，有用的逃生通道：

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## 文档

完整手册：**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**——入门、用法、六个配置文件、视频模型、配置、API 参考、架构。

**存储库中的知识库**，供 LLM 和贡献者使用：[`kb/`](kb/README.md)——一个可读性强的 [`index.json`](kb/index.json)，包含每个配置文件的事实页面、可运行的参考图（`kb/workflows/*.json`，由构建器本身生成，因此不会发生漂移）和节点溯源（`kb/nodes.json`）。`python scripts/gen_kb.py` 会重新生成它；如果代码和知识库不一致，测试套件将失败。

## 安全与数据范围

- **涉及的数据：** 通过 HTTP/WebSocket 连接到本地或远程 ComfyUI 实例。
发送工作流 JSON 和上传的图像，接收生成的媒体。可以选择连接到本地 Ollama，以增强提示功能。将输出写入临时目录，并自动清理。
- **不涉及的数据：** 不收集遥测数据、分析数据，也不使用 ComfyUI 和您配置的 Ollama 端点之外的任何外部 API。所有日志输出中的敏感信息都通过 `SecretValue` 进行屏蔽。
- **所需权限：** 访问您的 ComfyUI 服务器和可选的 Ollama 服务器的网络权限；用于输出和临时目录的文件写入权限。
- **上传：** `upload_image` 会拒绝任何尝试访问子文件夹的操作。上传的文件会存储在您指定的服务器上的 ComfyUI 的输入目录中——请将该服务器视为受信任的服务器。

有关漏洞报告，请参阅 [SECURITY.md](SECURITY.md)。

## 评估

| 类别 | 得分 |
|----------|-------|
| A. 安全性 | 10/10 |
| B. 错误处理 | 10/10 |
| C. 操作文档 | 10/10 |
| D. 发布规范 | 10/10 |
| E. 身份验证（软身份验证） | 10/10 |
| **Overall** | **50/50** |

> 使用 [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck) 进行评估

## 相关

是 [**MCP 工具商店**](https://mcp-tool-shop.github.io/) 的一部分——用于本地硬件的开源机器学习工具。

## 贡献

欢迎提交问题和拉取请求——请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。有用的领域：
其他模型系列、工作流模板、文档、错误修复。

如果您添加了一种节点类型，请首先验证它是否已存在于实时的 ComfyUI 目录中，如果它不是核心组件，请声明其包。正是这条规则导致了这次发布。

## 许可证

MIT——请参阅 [LICENSE](LICENSE)。

---

由 [MCP 工具商店](https://mcp-tool-shop.github.io/) 构建
