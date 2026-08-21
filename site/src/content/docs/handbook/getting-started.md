---
title: Getting Started
description: Install Comfy Headless, point it at a ComfyUI server, and generate your first image.
sidebar:
  order: 1
---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | Checked at install time |
| A running ComfyUI | Comfy Headless is a client — it does not render anything itself |
| Ollama *(optional)* | Only for AI prompt enhancement |

Start ComfyUI first and note its address. The default assumption is
`http://localhost:8188`.

## Install

```bash
pip install comfy-headless[standard]
```

`[standard]` is the right default for most people: it adds AI prompt enhancement and
WebSocket progress on top of the core client.

If you want the smallest possible footprint:

```bash
pip install comfy-headless          # core only, ~2MB
```

Or everything, including the web UI:

```bash
pip install comfy-headless[full]
```

See [Configuration](../configuration/) for the full extras table.

## Verify the install

```bash
comfy-headless --version
comfy-headless --check       # which optional features are active
comfy-headless --diagnose    # version, Python, features, resolved config
```

`--diagnose` is the fastest way to answer "why isn't this working" — it prints the
resolved ComfyUI URL alongside feature availability.

## Your first image

```python
from comfy_headless import ComfyClient

client = ComfyClient()                  # http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")

print(result["success"])                # True
print(result["images"])                 # list of output paths
print(result["seed"])                   # the seed actually used
```

Every generation call returns a **dict**, not a result object. The keys are `success`,
`prompt_id`, `images` (or `videos`), `error`, `seed` and `preset`.

### Pointing at a different server

```python
client = ComfyClient("http://192.168.1.50:8188")
```

Or set it in the environment, which is usually better for anything scripted:

```bash
export COMFY_HEADLESS_COMFYUI__URL=http://192.168.1.50:8188
```

Note the `__` double underscore — it separates the config section from the key. See
[Configuration](../configuration/).

## Check the server is reachable

```python
if not client.is_online():
    raise SystemExit("ComfyUI is not responding")

print(client.get_vram_gb(), "GB total VRAM")
print(client.get_free_vram_gb(), "GB free")
```

`client.ensure_online()` does the same thing but raises `ComfyUIOfflineError` instead of
returning a boolean.

## Use a preset

Presets set resolution, steps and CFG together, and override any individual values you
also pass:

```python
result = client.generate_image("a mountain lake at dawn", preset="hd")
```

Available: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`,
`square`.

```python
from comfy_headless import list_presets
print(list_presets())
```

## Your first video

```python
result = client.generate_video(
    "a slow pan across a mountain range",
    preset="ltx_quality",
)
print(result["videos"])
```

Video is selected **by preset**, not by model name — there is no `model` argument. If you
are unsure which preset your GPU can handle:

```python
from comfy_headless import get_recommended_preset
print(get_recommended_preset(vram_gb=16))
```

See [Video Models](../video-models/) for the full list and what each family needs.

## Before you spend a long run

Video graphs can require custom node packs. Ask first rather than discovering it at submit
time:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
if report["missing_packs"]:
    print("Install these first:", report["missing_packs"])
```

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| `ComfyUIOfflineError` | ComfyUI isn't running, or the URL is wrong — check `--diagnose` |
| `MissingNodePackError` | The graph needs a custom node pack this server doesn't have |
| `GenerationTimeoutError` | Model still loading, or the job is genuinely slow — raise `timeout` |
| AI functions missing | Install `[ai]` and start Ollama |
| Import error on `launch` | Install `[ui]` |

## Next

- [Usage](../usage/) — the day-to-day API
- [For Beginners](../beginners/) — a gentler introduction if the above moved too fast
