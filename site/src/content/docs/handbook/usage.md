---
title: Usage
description: Day-to-day patterns — images, batches, AI prompt enhancement, video, image input, progress tracking, and the web UI.
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

print(list_video_presets())                    # 24 presets
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

`build_video_workflow()` does the same for video. Both return a plain dict in ComfyUI
API format — `{"<node_id>": {"class_type": ..., "inputs": {...}}}` — which you can save,
diff or hand to ComfyUI yourself.

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
