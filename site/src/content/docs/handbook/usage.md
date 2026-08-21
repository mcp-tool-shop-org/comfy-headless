---
title: Usage
description: Day-to-day patterns — images, video, 3D meshes, audio, inference, provenance, uploads, progress tracking, and the web UI.
sidebar:
  order: 2
---

Everything on this page assumes a client:

```python
from comfy_headless import ComfyClient
client = ComfyClient()
```

## Images

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality, watermark",
    preset="hd",
    seed=42,
)
```

Full parameter set: `prompt`, `negative_prompt`, `preset`, `checkpoint`, `width`,
`height`, `steps`, `cfg`, `sampler`, `scheduler`, `seed`, `wait`, `timeout`,
`on_progress`.

Two things worth knowing:

- **`preset` wins.** When set, it overrides `width`, `height`, `steps` and `cfg`. Leave it
  empty (`""`, the default) to control those yourself.
- **`seed=-1`** means random. The seed actually used comes back in `result["seed"]`, so a
  run is always reproducible after the fact.

### Fire and forget

```python
result = client.generate_image("a fox", wait=False)
prompt_id = result["prompt_id"]

# ... later
client.wait_for_completion(prompt_id)
```

### Batches

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
    seeds=[1, 2, 3],          # optional, one per prompt
    max_concurrent=1,
    check_vram=True,
)
```

`check_vram=True` estimates the job against available VRAM before queueing, which is
cheaper than discovering the problem halfway through a batch.

## AI prompt enhancement

Requires the `[ai]` extra and a running Ollama. These are **module-level functions**, not
methods on the client — a common source of confusion:

```python
from comfy_headless import enhance_prompt, analyze_prompt, quick_enhance

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)      # the rewritten prompt
print(result.negative)      # a style-aware negative prompt
print(result.additions)     # what was added
print(result.reasoning)     # why
```

`analyze_prompt` classifies without rewriting:

```python
analysis = analyze_prompt("a cyberpunk city at night with neon lights")
print(analysis.intent)              # e.g. "scene"
print(analysis.styles)              # e.g. ["scifi", "cinematic"]
print(analysis.suggested_preset)    # feed straight into generate_image(preset=...)
print(analysis.confidence)
```

A natural pairing:

```python
analysis = analyze_prompt(user_text)
enhanced = enhance_prompt(user_text)
client.generate_image(
    enhanced.enhanced,
    negative_prompt=enhanced.negative,
    preset=analysis.suggested_preset,
)
```

## Video

```python
from comfy_headless import list_video_presets, get_recommended_preset

print(list_video_presets())                    # 26 presets
print(get_recommended_preset(vram_gb=16))      # sized to your card

result = client.generate_video(
    "a slow pan across a mountain range",
    preset="ltx_quality",
)
print(result["videos"])
```

Selection is by **preset**, not model — `generate_video` has no `model` parameter. Any of
`frames`, `fps`, `steps`, `cfg`, `width`, `height`, `motion_scale` may be passed to
override the preset's defaults.

```python
result = client.generate_video(
    "ocean waves crashing",
    preset="wan_14b",
    frames=48,
    fps=24,
)
```

See [Video Models](../video-models/) for what each family needs.

## Image input

Image-to-video — and anything else taking a source image — needs that image to already
exist inside ComfyUI. Upload it first:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

**Always read `name` back from the response.** ComfyUI renames on filename collision, so
the stored name is not always what you sent. `ref` is the same value already joined with
any subfolder, which is exactly the string the graph needs.

```python
ref = client.upload_image(image_bytes, filename="frame.png", subfolder="refs")
print(ref["ref"])        # "refs/frame.png"
```

Masks work the same way, taking the image they apply to:

```python
base = client.upload_image("photo.png")
client.upload_mask("mask.png", original_ref=base)
```

:::caution[Changed in 3.0]
`init_image` is a **server-side filename**, not image data. Earlier versions accepted
base64 and smuggled it through a third-party node that does not exist on a stock ComfyUI
install. If you are upgrading, replace base64 payloads with an `upload_image` call.
:::

:::tip[New in 3.1]
The profile client methods below (`generate_3d`, `generate_audio`, `separate_audio`,
`run_inference`, `edit_image`) accept the image/audio in **any** spelling — a local path,
raw bytes, the dict from `upload_image()`/`upload_audio()`, or a bare server ref — and
upload automatically when the source is local.
:::

## Image editing (Qwen-Image-Edit)

Instruction-based editing with up to three reference images:

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],                 # 1–3 references
    negative="",
    seed=42,
)
print(result["images"])
```

Multiple references compose — e.g. put the subject of one image into the scene of
another:

```python
result = client.edit_image(
    "place the character from the first image into the second image's tavern",
    images=["character.png", "tavern.png"],
)
```

References feed `TextEncodeQwenImageEditPlus` as discrete `image1..image3` inputs — not a
batched list — and never pass through VAEEncode. That is the graph shape the node
expects, and getting it wrong is a silent quality bug, which is why the builder owns it.

## ControlNet

One code path covers the Qwen and SDXL union ControlNets:

```python
from comfy_headless import build_controlnet_workflow, UNION_CONTROL_TYPES

hint = client.upload_image("depth.png")
workflow = build_controlnet_workflow(
    "a stone fortress at dawn",
    control_image_ref=hint["ref"],
    control_type="depth",        # one of UNION_CONTROL_TYPES, verbatim
    base="qwen",                 # or "sdxl"
    strength=0.8,
    end_percent=0.45,            # release control early to free surface detail
)
prompt_id = client.queue_prompt(workflow)
```

The `control_type` enum is passed through verbatim — the slash-grouped entries such as
`"canny/lineart/anime_lineart/mlsd"` are single literal choices, not lists to split.
Supply a pre-made hint image; only the core `Canny` preprocessor can be emitted inline
(`preprocess="canny"`).

## 3D meshes

Image in, GLB out — Hunyuan3D-2 on all-core nodes:

```python
result = client.generate_3d("character.png", preset="standard")
# presets: standard / draft / detail

glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

It is pure image conditioning — there is no text prompt in a 3D graph. Useful overrides:
`steps` (30), `cfg` (5.5), `octree_resolution` (256 — mesh detail),
`threshold` (0.6 — surface extraction), `seed`.

The mesh registers in `/history` like any image and downloads through the same `/view`
route — `get_file()` is the generic fetch for every output type.

## Audio

Text-to-music via ACE-Step 1.5 (all core, MIT-licensed weights, 8 steps / cfg 1):

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",     # the main prompt
    lyrics="",                                   # empty = instrumental
    preset="music",       # music / music_long / jingle / music_mp3 / draft
    seconds=30,
    bpm=90,
    keyscale="A minor",
)
flac = client.get_file(**result["audios"][0])
```

`seconds` drives both halves of the model's split duration parameter — the encoder and
the latent — from one field, because the runtime does not cross-validate them and a
mismatch completes "successfully" with silently wrong output.

Formats: `flac` (default, lossless — no quality field emitted at all), `mp3`, `opus`
(both take `quality`, e.g. `"320k"`).

### Stem separation

```python
result = client.separate_audio("song.flac")                  # all four stems
result = client.separate_audio("song.flac", stems=["vocals"])

for entry in result["audios"]:
    print(entry["stem"], entry["filename"])
```

Requires the `audio-separation-nodes-comfyui` pack —
`check_workflow_dependencies` names it if missing. Audio uploads use
`client.upload_audio()`, which rides the same `/upload/image` route (ComfyUI has no
audio-specific upload endpoint; that route is the server's general input uploader).

## Inference — asking about an image

Non-generative model calls on Florence-2:

```python
r = client.run_inference("photo.png", task="caption")
print(r["text"])          # the caption, straight from /history

r = client.run_inference("photo.png", task="tag")             # booru-style tags
r = client.run_inference("photo.png", task="ocr")

r = client.run_inference("photo.png", task="detect", text_input="the red car")
print(r["text"])          # bounding-box coordinates as JSON

r = client.run_inference("photo.png", task="segment", text_input="the person")
mask_png = client.get_file(**r["images"][0])
```

Tasks: `caption`, `detailed_caption`, `more_detailed_caption`, `tag`, `detect`,
`segment`, `ocr`. The `detect` and `segment` tasks need `text_input` — what to look for.
Requires the `comfyui-florence2` pack (`detect` also needs
`comfyui-segment-anything-2`).

The result text comes back inline — `SaveText` reports it in the history entry itself,
so there is no second round-trip for a caption.

## Provenance

Every (metadata-enabled) ComfyUI output PNG embeds the exact API-format graph that made
it. Read it back, or re-run it verbatim:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)      # the runnable graph
print(record.extra)                   # custom keys land here

graph = extract_prompt_graph("output.png")     # raises, with a hint, if scrubbed
result = client.rerun_from_png("output.png")   # re-POSTs it as-is
```

Write your own provenance without any custom node — every key in `extra_pnginfo`
becomes a PNG text chunk in the outputs:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Limits worth knowing: WebP/JPEG carry the same data in EXIF (a different reader path,
not implemented here); video outputs do not embed the graph; and a re-run needs any
referenced input files to still exist on the server.

## Progress

Any blocking call takes a callback:

```python
def show(pct, msg):
    print(f"{pct:.0%}  {msg}")

client.generate_image("a fox", on_progress=show)
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

## Working with the graph directly

The preset API is a convenience over graph building. When you need the graph itself:

```python
workflow = client.build_txt2img_workflow("a fox", steps=30, cfg=6.5)

# inspect, mutate, validate
report = client.check_workflow_dependencies(workflow)

prompt_id = client.queue_prompt(workflow)
client.wait_for_completion(prompt_id)
```

Every profile has a module-level builder that returns the same plain dict in ComfyUI API
format — `{"<node_id>": {"class_type": ..., "inputs": {...}}}` — which you can save,
diff or hand to ComfyUI yourself:

```python
from comfy_headless import (
    build_video_workflow,            # 26 presets
    build_3d_workflow,               # Hunyuan3D-2
    build_audio_workflow,            # ACE-Step 1.5
    build_audio_separation_workflow,
    build_inference_workflow,        # caption/tag/detect/segment/ocr
    build_qwen_edit_workflow,
    build_controlnet_workflow,
    compile_workflow,                # image templates incl. "qwen_txt2img"
)
```

You can also type-check a graph's edges against the live server, using the server's own
union-matching acceptance rule (so a `MESH` output feeding a `FILE_3D_*` union input is
never a false rejection):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])      # edges the server would provably reject
print(report["warnings"])    # accepted edges with partial type overlap
```

## Queue control

```python
client.get_queue()          # what's pending and running
client.get_history()        # completed jobs
client.cancel_current()     # interrupt the running job
client.clear_queue()        # drop everything pending
```

## Discovering what the server has

```python
client.get_checkpoints()
client.get_loras()
client.get_samplers()
client.get_schedulers()
client.get_motion_models()
client.get_all_installed_nodes()
```

These read the target server's real catalog, so they are the honest answer to "what can
this machine actually run".

## The web UI

```bash
comfy-headless                    # launching the UI is the default action
comfy-headless --port 8080 --share
```

Six tabs: Image, Video, Queue & History, Workflows, Models, Settings.

Programmatically (requires `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Cleaning up

```python
client.close()
```

Or use it as a context manager where you want deterministic teardown of the connection
pool.
