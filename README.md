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

**v3.1 extends that discipline to six workflow profiles** — **Image, Video, 3D,
Inference, Metadata, Audio** — on a shared addressing/typing layer that speaks ComfyUI's
own validation rules: union type matching transcribed from the server's validator, dotted
dynamic-combo fields (`codec.encoding.crf`), and conditional inputs that refuse
inactive-branch values at construction time. Same route surface as before — meshes, music
and captions come back through `/history` + `/view` like everything else.

| Problem | What comfy-headless does |
|---------|--------------------------|
| The node interface is a lot | Presets and a clean Python API |
| Prompt engineering is hard | Optional AI enhancement via local Ollama |
| Video generation is fiddly | 26 presets across 9 model families |
| "I need a mesh from this image" | `generate_3d()` — Hunyuan3D-2, all core nodes |
| "I need music / stems" | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "What's in this image?" | `run_inference()` — caption, tag, detect, segment, OCR |
| "Which graph made this PNG?" | `extract_prompt_graph()` / `rerun_from_png()` |
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

### Qwen-Image (new in 3.1)

Qwen-Image-2512 text-to-image ships as the `qwen_txt2img` template, with the recipe the
model actually wants baked in: `UNETLoader` path, 16-channel `EmptySD3LatentImage`
(the SDXL latent produces garbage on DiT models), steps 20, **cfg 2.5**, shift 3.1,
native 1328×1328 bucket:

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

Instruction editing with up to three reference images (Qwen-Image-Edit-2511):

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

References feed `TextEncodeQwenImageEditPlus` as discrete `image1..image3` inputs and do
not pass through VAEEncode — the graph shape the node actually expects.

### ControlNet (new in 3.1)

One code path covers Qwen and SDXL union ControlNets:

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

Only the core `Canny` preprocessor is emitted (`preprocess="canny"`); other hint types
expect a pre-made control image, because their preprocessors live in a custom pack this
library does not silently require.

## Video

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

> **New in 3.1:** Hunyuan 1.5 image-to-video is real i2v — presets `hunyuan15_i2v` and
> `hunyuan15_i2v_fast` build on the core `HunyuanVideo15ImageToVideo` node and require an
> `init_image` (v3.0 silently built a text-to-video graph instead). And
> `output="core"` swaps the `VHS_VideoCombine` terminator for core
> `CreateVideo → SaveVideo`, dropping the Video Helper Suite dependency entirely.

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

You can also type-check a graph's edges against the live server, using the server's own
acceptance rule (so a `MESH` feeding a `FILE_3D_*` union input is never a false
rejection):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (new in 3.1)

Image-to-mesh via **Hunyuan3D-2** — entirely ComfyUI core nodes, no wrapper packs, no new
routes. The GLB registers in `/history` exactly like a PNG does and downloads through
`/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` accepts a local path, raw bytes, an `upload_image()` dict, or a server-side
ref, and uploads automatically when needed. It is pure image-conditioning — there is no
text prompt in the graph. Tunables: `steps` (30), `cfg` (5.5), `octree_resolution` (256),
`threshold` (0.6), `seed`.

Wrapper-pack 3D models (TRELLIS, TripoSG, ...) are deliberately not emitted —
ComfyUI-3D-Pack's native dependencies are the least stable in the ecosystem.

## Audio (new in 3.1)

Text-to-music via **ACE-Step 1.5** — MIT-licensed code *and* weights, native core nodes,
zero packs. The turbo checkpoint runs at 8 steps / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

The builder enforces the model's coupling invariant for you: the encoder's `duration` and
the latent's `seconds` are one logical parameter, driven from a single field — the runtime
does not cross-validate them, and a mismatch completes "successfully" with silently wrong
output. Output goes through `SaveAudioAdvanced` (the only non-deprecated audio save node);
`flac` output emits no quality field at all, `mp3`/`opus` emit the dotted
`format.quality` sub-field.

Stem separation (requires the `audio-separation-nodes-comfyui` pack):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inference (new in 3.1)

Non-generative model calls — ask questions about an image instead of making one. Runs on
Florence-2 (pack `comfyui-florence2`; the detect task adds
`comfyui-segment-anything-2`):

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

The profile's load-bearing rule: a result reaches `/history` only through an output node.
Every inference graph terminates in core `SaveText` (which reports the text inline — no
second round-trip) or `SaveImage` for masks, and the builder refuses to emit a graph that
would run green and return nothing.

## Provenance (new in 3.1)

ComfyUI embeds the **exact API-format graph** in every output PNG. comfy-headless reads
it back — pure stdlib, no Pillow — and can re-run it verbatim:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Write custom provenance without any custom node — anything in `extra_pnginfo` becomes a
PNG text chunk in the outputs:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2024-077"})
```

Known limits, documented rather than hidden: WebP/JPEG carry the same data in EXIF (a
different reader path, not implemented); video outputs don't embed the graph; hardened
deployments may strip unknown keys; and GUI→API conversion has no server route — use
ComfyUI's "Workflow → Export (API)".

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
    GraphAddressError,        # new in 3.1 — bad dotted field / inactive combo branch
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

**In-repo knowledge base** for LLMs and contributors: [`kb/`](kb/README.md) — a
machine-readable [`index.json`](kb/index.json) over per-profile fact pages, runnable
reference graphs (`kb/workflows/*.json`, generated from the builders themselves so they
cannot drift), and node provenance (`kb/nodes.json`). `python scripts/gen_kb.py`
regenerates it; the test suite fails if code and KB disagree.

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
