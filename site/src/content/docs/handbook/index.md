---
title: Comfy Headless Handbook
description: The complete guide to driving ComfyUI from Python — image, video, 3D, audio, inference and provenance profiles, verified node graphs, and a clean API over the full ComfyUI feature set.
sidebar:
  order: 0
---

Welcome to the **Comfy Headless Handbook**. This guide takes you from zero to generating
images and video through ComfyUI programmatically, without ever opening a node graph.

## What Comfy Headless actually is

It is a **graph emitter and poller**. You call a Python function; it builds a ComfyUI
API-format JSON graph, POSTs it to `/prompt`, polls `/history` until the job finishes, and
returns the output paths.

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

Holding that model in your head explains most of the library's behaviour. It does not wrap
ComfyUI's Python internals and does not run models itself — it composes node graphs and
hands them to a ComfyUI server you point it at. Everything it can do is something ComfyUI
can do; the value is that you express it in a function call instead of a canvas.

## Why v3.0 exists

Because the library emits node names, a node that ComfyUI has renamed or removed becomes a
shipped bug. The graph is rejected at submit time with an opaque error, and nothing warns
you beforehand.

In August 2026 every node type this library emits was audited against the live ComfyUI
catalog. **Nine no longer existed.** They had been wrapper-pack nodes mislabelled as core;
ComfyUI kept the generic sampler path and the per-family latent nodes, and dropped the
family-specific pipelines.

v3.0 removes them, rebuilds the affected graphs on verified nodes, and adds the machinery
so the rot is visible next time:

- Every emitted node type is recorded with its provenance — core, or which pack supplies it
- `check_workflow_dependencies()` reports what a target server is missing
- `require_workflow_dependencies()` raises a named error instead of letting `/prompt` fail
  cryptically
- A contract test builds every preset and asserts no removed node, no undeclared node, no
  dangling reference

If you take one habit from this handbook: **check dependencies before you spend a run.**

## What v3.1 adds

v3.1 grows the library from two workflow surfaces to **six profiles** — Image, Video,
3D, Inference, Metadata, Audio — on a shared addressing/typing layer that speaks
ComfyUI's own validation rules. Meshes (Hunyuan3D-2), music (ACE-Step 1.5), captions and
detections (Florence-2), and PNG provenance round-trips all ride the same routes the
library already used; no new endpoints, the same dict-returning call shape. See
[The Six Profiles](../profiles/).

## Where to go next

| You want to | Read |
|-------------|------|
| Install and generate your first image | [Getting Started](../getting-started/) |
| Learn the day-to-day API | [Usage](../usage/) |
| Meshes, music, captions, provenance | [The Six Profiles](../profiles/) |
| Pick a video model for your GPU | [Video Models](../video-models/) |
| Configure URLs, timeouts, features | [Configuration](../configuration/) |
| Look up an exact signature | [API Reference](../api-reference/) |
| Understand the internals | [Architecture](../architecture/) |
| You are new to all of this | [For Beginners](../beginners/) |

## At a glance

- **Six profiles** — Image, Video, 3D, Inference, Metadata, Audio
- **8 image presets** — `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`,
  `cinematic`, `square` — plus Qwen-Image txt2img, edit and ControlNet
- **26 video presets** across **9 model families**, including true Hunyuan 1.5 i2v
- **3D** (Hunyuan3D-2 → GLB) and **audio** (ACE-Step 1.5 → flac/mp3/opus) on all-core
  graphs
- **Modular installs** — core is ~2MB; AI, WebSocket, UI, health, validation and tracing
  are opt-in extras
- **Structured errors** — every exception carries a code, a message and a hint
- **Python 3.10+**, MIT licensed

## Requirements

A running ComfyUI instance is required — Comfy Headless is a client, not a renderer. It
defaults to `http://localhost:8188`. Optional AI prompt enhancement needs a local
[Ollama](https://ollama.com/).
