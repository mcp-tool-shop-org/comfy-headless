<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## What this is

comfy-headless builds **ComfyUI API-format graphs** and runs them. You call a Python
function; it emits the JSON node graph, POSTs it to ComfyUI, polls for completion, and
hands you the output paths.

That framing matters, because it tells you what can go wrong. The library's entire job is
emitting node names and input keys that the target ComfyUI actually has. When ComfyUI
renames or drops a node, a graph referencing the old name is rejected at submit with an
opaque error — and nothing warns you first.

**v3.0 is the release that took that seriously.** Every node type this library emits was
audited against the live ComfyUI catalog. Nine no longer existed. They're gone, the graphs
that used them are rebuilt on verified nodes, and the library can now tell you what a
server is missing *before* you spend a run on it.

| Problem | What comfy-headless does |
|---------|--------------------------|
| The node interface is a lot | Presets and a clean Python API |
| Prompt engineering is hard | Optional AI enhancement via local Ollama |
| Video generation is fiddly | 24 presets across 9 model families |
| "Which settings do I use?" | Recommendations sized to your VRAM |
| Graphs fail with cryptic errors | Dependency check names the node *and* the pack |

## Quick start

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` returns a `dict` with `success`, `prompt_id`, `images`, `error`, `seed`
and `preset`. Every generation call in this library returns a dict — there is no result
object to unwrap.

## Install

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| Extra | Adds |
|-------|------|
| `ai` | Prompt analysis and enhancement via local Ollama |
| `websocket` | Real-time progress over WebSocket |
| `ui` | Gradio web interface |
| `health` | System health monitoring |
| `validation` | Pydantic config validation |
| `observability` | OpenTelemetry tracing |
| `standard` | `ai` + `websocket` |
| `full` | All of the above |

Requires **Python 3.10+** and a running ComfyUI instance.

Check what's active at runtime:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## Images

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

Eight image presets: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`,
`cinematic`, `square`.

Batch a list of prompts:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### AI prompt enhancement

Requires the `[ai]` extra and a local Ollama. These are **module-level functions**, not
client methods:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

## Video

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

Selection is **by preset**, not by model — `generate_video` has no `model` argument. Any
of `frames`, `fps`, `steps`, `cfg`, `width`, `height` can be passed to override the preset.

### Image input

Image-to-video, and anything else taking a source image, needs that image to exist inside
ComfyUI first. Upload it, then pass the name the server gives back:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Read `name` back from the response rather than reusing the filename you sent — ComfyUI
renames on collision, so the two are not always equal. `ref` is the same value already
joined with any subfolder, which is exactly what the graph needs.

> **Changed in 3.0:** `init_image` is a server-side filename. Earlier versions accepted
> base64 data and smuggled it through a third-party node that does not exist on a stock
> ComfyUI install. See the [CHANGELOG](CHANGELOG.md).

### Model families

| Family | Min VRAM | Quality | Speed | Extra nodes | Best for |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Great | Medium | — | Low VRAM, efficiency |
| AnimateDiff Lightning | 6 GB | Fair | Fastest | AnimateDiff-Evolved | 4-step drafts |
| AnimateDiff | 8 GB | Good | Fast | AnimateDiff-Evolved, Frame Interp. | Quick previews |
| **LTX-Video** | 12 GB | Excellent | Fast | — | The safe default |
| **Mochi** | 12 GB | Excellent | Slow | — | Text adherence, long clips |
| **SVD** | 12 GB | Good | Medium | — | Animating a still |
| **Hunyuan 1.5** | 14 GB | Best | Slow | — | Highest quality |
| CogVideoX | 16 GB | Good | Slow | CogVideoX Wrapper | Legacy |
| **Hunyuan 1.0** | 24 GB | Great | Slow | Frame Interpolation | Superseded by 1.5 |

Six of the nine families run on **stock ComfyUI core nodes** — no wrapper pack for the
model itself. Only AnimateDiff (both variants) and CogVideoX need one. Video output uses
[Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); frame
interpolation uses
[Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

VRAM figures are the floor for that family's default resolution, read from
`VIDEO_MODEL_INFO` — not ceilings. More memory buys longer clips and higher resolutions
from the same family.

### Check before you run

Rather than discovering a missing node at submit time:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

## Configuration

Environment variables use the `COMFY_HEADLESS_` prefix with `__` section delimiters:

| Variable | Default |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | read timeout, seconds |
| `COMFY_HEADLESS_LOGGING__LEVEL` | log level |

Or pass the URL directly: `ComfyClient("http://192.168.1.50:8188")`.

## Web UI

```bash
comfy-headless                 # launching the UI is the default action
```

| Flag | Meaning |
|------|---------|
| `--port` / `-p` | UI port (default `7861`) |
| `--share` | Public Gradio share link |
| `--url` | ComfyUI server URL |
| `--version` / `-v` | Print version |
| `--check` | Feature availability |
| `--diagnose` | Full diagnostics |

Six tabs: Image, Video, Queue & History, Workflows, Models, Settings. Theme is Ocean Mist —
soft teal accents on warm neutral backgrounds.

Programmatically (requires `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progress

Blocking calls take an `on_progress` callback:

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

For real-time updates over WebSocket (requires `[websocket]`):

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## Errors

Every exception carries a structured code, message and hint:

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

## How it works

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

The library talks to seven ComfyUI routes — `/system_stats`, `/object_info`, `/queue`,
`/history`, `/prompt`, `/interrupt`, `/view` — plus `/upload/image` and `/upload/mask` for
binary input.

`/object_info` is the authority on what a given server can run. It is a live endpoint, not
a versioned artifact: there is no core-node registry to pin against. So the library
validates emitted graphs against the target server's actual catalog rather than assuming a
fixed node set. `check_workflow_dependencies()` is that check, and it is load-bearing
infrastructure rather than a convenience.

Useful escape hatches when you want the graph itself:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Docs

Full handbook:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**
— getting started, usage, configuration, API reference, video models, architecture.

## Security & data scope

- **Data touched:** connects to a local or remote ComfyUI instance over HTTP/WebSocket.
  Sends workflow JSON and uploaded images, receives generated media. Optionally connects
  to a local Ollama for prompt intelligence. Writes output to temp directories with
  automatic cleanup.
- **Data NOT touched:** no telemetry, no analytics, no external APIs beyond the ComfyUI
  and Ollama endpoints you configure. Secrets are masked in all log output via
  `SecretValue`.
- **Permissions required:** network access to your ComfyUI server and optional Ollama
  server; file write for output and temp directories.
- **Uploads:** `upload_image` rejects subfolder traversal attempts. Uploaded files land in
  ComfyUI's input directory on whichever server you point at — treat that server as
  trusted.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Scorecard

| Category | Score |
|----------|-------|
| A. Security | 10/10 |
| B. Error Handling | 10/10 |
| C. Operator Docs | 10/10 |
| D. Shipping Hygiene | 10/10 |
| E. Identity (soft) | 10/10 |
| **Overall** | **50/50** |

> Assessed with [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Related

Part of [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — open-source ML tooling for
local hardware.

## Contributing

Issues and pull requests welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Useful areas:
additional model families, workflow templates, docs, bug fixes.

If you add a node type, verify it exists in the live ComfyUI catalog first, and declare its
pack if it isn't core. That rule is why this release exists.

## License

MIT — see [LICENSE](LICENSE).

---

Built by [MCP Tool Shop](https://mcp-tool-shop.github.io/)
