---
title: Video Models
description: The nine video model families, all 26 presets with real resolutions and frame counts, VRAM floors, and which families need custom node packs.
sidebar:
  order: 4
---

Comfy Headless ships **26 curated presets across 9 model families**. You pick a preset;
the preset picks the model, resolution, frame count, step count and CFG.

There is no `model` argument on `generate_video` — selection is by preset name.

## Choosing by VRAM

```python
from comfy_headless import get_recommended_preset

get_recommended_preset(vram_gb=8)
get_recommended_preset(vram_gb=16, quality="high")
get_recommended_preset(intent="cinematic", vram_gb=24)
```

The VRAM figures below are the **floor for that family's default resolution**, read from
`VIDEO_MODEL_INFO`. More memory buys longer clips and higher resolutions from the same
family — they are not ceilings.

| Family | Min VRAM | Node packs needed |
|--------|----------|-------------------|
| Wan | 6 GB | — |
| AnimateDiff Lightning | 6 GB | AnimateDiff-Evolved |
| AnimateDiff | 8 GB | AnimateDiff-Evolved, Frame Interpolation |
| LTX-Video | 12 GB | — |
| Mochi | 12 GB | — |
| SVD | 12 GB | — |
| Hunyuan 1.5 | 14 GB | — |
| CogVideoX | 16 GB | CogVideoX Wrapper |
| Hunyuan 1.0 | 24 GB | Frame Interpolation |

Every family uses **Video Helper Suite** for encoding the final file by default — or
none at all: pass `output="core"` to swap the terminator for core
`CreateVideo → SaveVideo` and drop that pack entirely (new in 3.1):

```python
result = client.generate_video("a cat walking", preset="ltx_standard", output="core")
```

Six of the nine families run entirely on **stock ComfyUI core nodes**. Only AnimateDiff
(both variants) and CogVideoX depend on a wrapper pack for the model itself — so with
`output="core"`, six families need zero custom packs end to end.

## The presets

### Wan 2.1 / 2.2 — the low-VRAM workhorse

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `wan_1.3b` | 832×480 | 33 | 16 | 30 | 6.0 |
| `wan_14b` | 640×640 | 81 | 16 | 20 | 3.5 |
| `wan_quality` | 1280×720 | 81 | 24 | 30 | 3.5 |
| `wan_fast` | 640×640 | 81 | 16 | 4 | 1.0 |

`wan_fast` uses the LightX2V 4-step distillation, which is why CFG is 1.0 — the guidance
is baked into the weights and raising CFG reintroduces the artifacts the LoRA removes.

### LTX-Video — the best all-rounder

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `ltx_quick` | 768×512 | 97 | 24 | 20 | 3.0 |
| `ltx_standard` | 768×512 | 97 | 24 | 30 | 3.0 |
| `ltx_quality` | 1280×720 | 97 | 24 | 30 | 3.0 |

97 frames at 24fps is roughly four seconds. Fully core-node, fast, and forgiving — the
default recommendation if your card clears 12 GB.

### Hunyuan Video 1.5 — highest quality

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `hunyuan15_720p` | 1280×720 | 121 | 24 | 20 | 6.0 |
| `hunyuan15_quality` | 1280×720 | 121 | 24 | 50 | 6.0 |
| `hunyuan15_1080p` | 1920×1080 | 121 | 24 | 20 | 6.0 |
| `hunyuan15_fast` | 848×480 | 81 | 24 | 6 | 1.0 |
| `hunyuan15_i2v` | 848×480 | 81 | 24 | 20 | 6.0 |
| `hunyuan15_i2v_fast` | 848×480 | 81 | 24 | 6 | 1.0 |

`hunyuan15_fast` is the step-distilled variant — 6 steps at CFG 1.0. Note the distilled
text-to-video weights are published at 480p only, which is why this preset is not offered
at 720p. (The **image-to-video** distillation exists at both 480p and 720p.)

The two `_i2v` presets (new in 3.1) are **true image-to-video** on the core
`HunyuanVideo15ImageToVideo` node, and require an `init_image`:

```python
ref = client.upload_image("first_frame.png")
result = client.generate_video(
    "the camera slowly pushes in",
    preset="hunyuan15_i2v",
    init_image=ref["name"],
)
```

:::caution[Upgrading from 3.0]
In 3.0, requesting Hunyuan 1.5 i2v silently built a **text-to-video** graph and ignored
the image. 3.1 builds the real i2v shape — and raises a clear error if `init_image` is
missing rather than quietly generating from text alone.
:::

### Mochi — strongest text adherence

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `mochi` | 848×480 | 162 | 30 | 64 | 4.5 |
| `mochi_short` | 848×480 | 81 | 30 | 50 | 4.5 |

162 frames at 30fps is the longest clip any preset produces. It is also the slowest — 64
steps on a 480p sequence is a long run.

### Hunyuan Video 1.0

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `hunyuan` | 1280×720 | 45 | 15 | 30 | 6.0 |
| `hunyuan_fast` | 848×480 | 33 | 15 | 20 | 6.0 |

The 24 GB floor makes this the most demanding family. On most cards Hunyuan 1.5 is the
better choice — it is newer, cheaper and higher quality.

### SVD — image-to-video

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `svd_short` | 1024×576 | 14 | 6 | 25 | 7.0 |
| `svd_long` | 1024×576 | 25 | 6 | 25 | 7.0 |

SVD animates a still rather than generating from text. Pair it with `upload_image`:

```python
ref = client.upload_image("photo.png")
client.generate_video("", preset="svd_long", init_image=ref["name"])
```

### AnimateDiff — fast previews

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `quick` | 512×512 | 16 | 8 | 4 | 2.0 |
| `standard` | 512×512 | 16 | 8 | 20 | 7.0 |
| `quality` | 768×768 | 24 | 12 | 25 | 7.0 |
| `cinematic` | 768×432 | 32 | 24 | 30 | 7.0 |
| `portrait` | 512×768 | 24 | 12 | 25 | 7.0 |
| `action` | 512×512 | 24 | 16 | 25 | 7.0 |

`quick` is the Lightning 4-step variant. The rest are AnimateDiff v3. All of them require
the **AnimateDiff-Evolved** pack — they were never core nodes.

### CogVideoX

| Preset | Resolution | Frames | FPS | Steps | CFG |
|--------|-----------|--------|-----|-------|-----|
| `cogvideo` | 720×480 | 48 | 8 | 50 | 7.0 |

CogVideoX has **no native ComfyUI path** — the entire family lives in the CogVideoX
Wrapper pack. If you cannot install that pack, this family is unavailable; there is no
core fallback.

## Checking a server can run it

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["required_packs"])   # what this graph needs
print(report["missing_packs"])    # what this server lacks

client.require_workflow_dependencies(workflow)   # raises MissingNodePackError
```

`MissingNodePackError` names the missing class, the pack that provides it, and how to
install it — rather than letting `/prompt` reject the job with a bare validation error.

## Inspecting presets in code

```python
from comfy_headless import VIDEO_PRESETS, VIDEO_MODEL_INFO, list_video_presets

print(list_video_presets())

s = VIDEO_PRESETS["ltx_quality"]
print(s.width, s.height, s.frames, s.fps, s.steps, s.cfg)

info = VIDEO_MODEL_INFO["ltxv"]
print(info.name, info.min_vram_gb, info.requires_packs)
print(info.text_to_video, info.image_to_video, info.max_frames)
```

## Estimating cost before you run

```python
gb = client.estimate_vram_for_video(width=1280, height=720, frames=97, model="ltxv")
if not client.check_vram_available(gb):
    print("Pick a smaller preset")
```

## Picking one

| If you want | Use |
|-------------|-----|
| The safe default | `ltx_quality` |
| To run on 6–8 GB | `wan_1.3b` or `wan_14b` |
| Fastest possible draft | `wan_fast` or `quick` |
| Best-looking output | `hunyuan15_quality` |
| The longest clip | `mochi` |
| To animate a photo | `svd_long` or `hunyuan15_i2v` |
| Zero custom node packs | Wan, LTX, Mochi, SVD, or Hunyuan 1.5 — with `output="core"` |
