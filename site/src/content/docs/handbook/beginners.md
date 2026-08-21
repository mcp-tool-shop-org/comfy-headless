---
title: For Beginners
description: New to ComfyUI or to generating images from code? Start here — what this tool is, what you need, and your first picture.
sidebar:
  order: 99
---

This page assumes nothing. If you already know what ComfyUI is, go to
[Getting Started](../getting-started/) instead.

## What is ComfyUI?

ComfyUI is a program that runs image and video AI models on your own computer. You build a
**workflow** by dragging boxes onto a canvas and connecting them with wires — one box
loads a model, another holds your prompt, another does the actual generating, another
saves the picture.

It is enormously capable and completely in your control. It is also a lot of boxes.

## What is Comfy Headless, then?

The same power, from Python, with no canvas.

"Headless" means "without a graphical interface". You write a line of code; Comfy Headless
builds the box-and-wire workflow for you behind the scenes, sends it to ComfyUI, waits for
the picture, and hands you the file path.

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a lighthouse in a storm")
print(result["images"])
```

Those four lines replace roughly seven boxes and a dozen wires.

### It is a remote control, not an engine

This trips people up, so it is worth being blunt: **Comfy Headless does not generate
anything itself.** It tells ComfyUI what to do. ComfyUI must already be installed and
running, on your machine or one you can reach over the network.

If ComfyUI is not running, nothing here works — and the error you will see is
`ComfyUIOfflineError`.

## What you need

1. **ComfyUI, installed and running.** Follow the
   [official install guide](https://docs.comfy.org/). Start it and leave it running. By
   default it listens on `http://localhost:8188`.
2. **At least one model** (a "checkpoint") downloaded into ComfyUI's `models/checkpoints`
   folder. ComfyUI cannot generate without one.
3. **Python 3.10 or newer.**
4. *(Optional)* **[Ollama](https://ollama.com/)**, only if you want the AI prompt
   enhancement feature.

## Install

```bash
pip install comfy-headless[standard]
```

Check it worked:

```bash
comfy-headless --diagnose
```

That prints the version, which optional features are active, and — importantly — which
ComfyUI address it is going to talk to.

## Your first picture

Create a file called `first.py`:

```python
from comfy_headless import ComfyClient

client = ComfyClient()

if not client.is_online():
    raise SystemExit("ComfyUI isn't running — start it first")

result = client.generate_image("a lighthouse in a storm, dramatic lighting")

if result["success"]:
    print("Saved:", result["images"])
    print("Seed was:", result["seed"])
else:
    print("Failed:", result["error"])
```

Run it:

```bash
python first.py
```

The first run may take a while — ComfyUI has to load the model into your graphics card's
memory. Later runs are much faster.

## Understanding what came back

Every generation returns a **dictionary** — a labelled bag of values:

| Key | What it is |
|-----|------------|
| `success` | Did it work? |
| `images` | List of file paths to your pictures |
| `seed` | The random number used. Reuse it to get the same picture again |
| `error` | What went wrong, if anything |
| `prompt_id` | ComfyUI's job id |
| `preset` | Which preset was applied |

Saving the seed is how you reproduce a result you liked:

```python
again = client.generate_image("a lighthouse in a storm", seed=result["seed"])
```

## Presets

Rather than learning what "steps" and "CFG" mean before you can make anything, use a
preset:

```python
client.generate_image("a fox in snow", preset="quality")
```

| Preset | Use it for |
|--------|-----------|
| `draft` | Fastest, roughest — checking an idea |
| `fast` | Quick results |
| `quality` | A good balance |
| `hd` | Higher resolution, slower |
| `portrait` | Tall — people, characters |
| `landscape` | Wide — scenery |
| `cinematic` | Widescreen, film-like |
| `square` | Equal sides — avatars, icons |

## Writing better prompts

Two habits carry most of the improvement:

**Describe, don't command.** "A red fox sitting in deep snow at sunset, soft golden light"
works better than "make me a nice fox picture".

**Say what you don't want**, using the negative prompt:

```python
client.generate_image(
    "a red fox in deep snow at sunset",
    negative_prompt="blurry, low quality, extra limbs, watermark",
)
```

If you installed the `[ai]` extra and have Ollama running, the library can do this for
you:

```python
from comfy_headless import enhance_prompt

better = enhance_prompt("a fox")
print(better.enhanced)     # a much richer prompt
print(better.negative)     # a matching negative prompt
```

## Making video

Video works the same way, but you choose a **preset** rather than a model name:

```python
result = client.generate_video("clouds moving over a mountain", preset="ltx_quality")
print(result["videos"])
```

Video is far heavier than images. If you are unsure what your graphics card can manage:

```python
from comfy_headless import get_recommended_preset
print(get_recommended_preset(vram_gb=8))
```

Some video families also need extra ComfyUI add-ons. Check before committing to a long
run:

```python
workflow = client.build_video_workflow("clouds moving")
report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # empty list means you're ready
```

See [Video Models](../video-models/) for what each family needs.

## It makes more than pictures

The same four-line pattern covers 3D models, music, and asking questions about images:

```python
result = client.generate_3d("character.png")          # image -> 3D model (.glb)
result = client.generate_audio(tags="calm piano")     # text -> music (.flac)
result = client.run_inference("photo.png", task="caption")
print(result["text"])                                 # "a lighthouse on a rocky coast..."
```

3D and music run entirely on ComfyUI's built-in nodes (you just need the models
downloaded); captioning needs one add-on, and the error message names it if it is
missing. See [The Six Profiles](../profiles/) when you are ready for the full picture.

## A web interface, if you prefer clicking

```bash
comfy-headless
```

That opens a browser page at `http://localhost:7861` with tabs for images, video, the
queue, workflows, models and settings.

## When things go wrong

| Message | What to do |
|---------|-----------|
| `ComfyUIOfflineError` | Start ComfyUI. Check the address with `--diagnose` |
| `MissingNodePackError` | Install the add-on it names, or pick a different preset |
| `GenerationTimeoutError` | Usually a slow first load — try again, or raise `timeout` |
| `FeatureNotAvailable` | Run the `pip install` line in the error message |
| Empty `images` list | Check `result["error"]`, and look at ComfyUI's own console |

ComfyUI's terminal window is worth watching. When a generation fails, the real reason is
usually printed there.

## Where next

- [Getting Started](../getting-started/) — the same ground, faster
- [Usage](../usage/) — batches, progress callbacks, working with graphs directly
- [Video Models](../video-models/) — every preset with real numbers
