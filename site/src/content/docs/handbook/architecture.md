---
title: Architecture
description: How Comfy Headless works internally — the graph emitter model, the ComfyUI routes it uses, node provenance and validation, resilience, and the module map.
sidebar:
  order: 6
---

## The one idea

Comfy Headless is a **graph emitter and poller**.

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

It does not wrap ComfyUI's Python internals, does not load models, and does not render
anything. It composes a JSON node graph and hands it to a ComfyUI server.

Almost every design decision follows from that. The library's correctness is exactly the
correctness of the node names and input keys it emits.

## API format

ComfyUI's `/prompt` endpoint accepts a flat map of node id to node:

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "model": ["4", 0],
      "positive": ["6", 0],
      "latent_image": ["5", 0],
      "seed": 42, "steps": 20, "cfg": 7.0,
      "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0
    }
  },
  "4": { "class_type": "CheckpointLoaderSimple", "inputs": { "ckpt_name": "..." } }
}
```

A value is either a **literal** or a **link** — `["<upstream_node_id>", <output_index>]`.
That envelope has been stable for years and is what output PNGs embed, so it is safe to
build on. What moves is *inside* `inputs`: individual node input keys and enum values
change with the nodes themselves.

`build_txt2img_workflow()` and `build_video_workflow()` return exactly this structure, so
you can inspect, diff or hand-edit a graph before submitting it.

## Routes used

| Route | Purpose |
|-------|---------|
| `GET /object_info` | The server's live node catalog — what it can actually run |
| `GET /system_stats` | VRAM and device info |
| `POST /prompt` | Submit a graph |
| `GET /history` | Poll for completion, read outputs |
| `GET /view` | Fetch a generated file |
| `GET /queue` | Inspect pending and running jobs |
| `POST /interrupt` | Cancel the running job |
| `POST /upload/image` | Put a source image into the input folder |
| `POST /upload/mask` | Composite a mask into an existing image |

That is the whole surface. There is no private API and no plugin protocol.

## Why `/object_info` is load-bearing

There is no published core-node registry to pin a version against. `/object_info` is a
**live endpoint, not a versioned artifact**, and ComfyUI ships no deprecation or alias
mechanism — when a node is renamed or dropped, graphs referencing the old name simply fail
at submit with a validation error naming the missing class. That is the only signal.

This is not hypothetical. In August 2026 an audit of every node type this library emits
found **nine that no longer existed**:

```
MochiSampler            MochiModelLoader          MochiVAEDecode
HunyuanVideoSampler     HunyuanVideoModelLoader   HunyuanVideoTextEncode
HunyuanVideoVAEDecode   CogVideoModelLoader       CogVideoVAEDecode
```

The pattern is instructive. All nine were **per-family pipeline nodes** that took
pipe-style inputs. ComfyUI kept the generic path — `UNETLoader` → `KSampler` →
`VAEDecode` — and the per-family *latent* nodes such as `EmptyMochiLatentVideo`, and
dropped the family pipelines. The survivors are the pieces with no model dependency.

So the strategy is: **prefer core nodes, and validate against the live catalog rather than
assuming a fixed node set.** `check_workflow_dependencies()` is that check, and it is
infrastructure rather than a preflight convenience.

## Node provenance

Every non-core node the library emits is recorded with the pack that supplies it:

```python
from comfy_headless import video

video.NODE_PACKS["VHS_VideoCombine"]     # "comfyui-videohelpersuite"
video.NODE_PACK_INFO["comfyui-videohelpersuite"].url
video.get_node_pack("KSampler")          # None -> core
```

`VideoModelInfo.requires_packs` declares this per family, which is what lets
`MissingNodePackError` name both the class and how to install its pack rather than
surfacing a bare validation failure.

Declared packs:

| Pack | Supplies |
|------|----------|
| `comfyui-videohelpersuite` | `VHS_VideoCombine` — video encoding, used by every family |
| `comfyui-animatediff-evolved` | The three `ADE_*` nodes |
| `comfyui-cogvideoxwrapper` | The whole CogVideoX family |
| `comfyui-frame-interpolation` | `RIFE VFI` frame interpolation |

## Resilience

Between your call and ComfyUI sit several layers, all configurable
(see [Configuration](../configuration/)):

- **Connection pooling** — a reused session rather than a socket per request
- **Retry with exponential backoff and jitter** via `tenacity`
- **A circuit breaker** — after repeated failures the circuit opens and calls fail fast
  with `CircuitOpenError` instead of piling onto a struggling server
- **Rate limiting** — optional, set on the client constructor
- **Structured logging** with secret masking, so credentials embedded in a URL never
  reach a log line

## Module map

```
comfy_headless/
├── __init__.py           # public exports, lazy loading of optional features
├── _version.py           # single source of truth for the version
├── client.py             # ComfyClient — HTTP, uploads, polling, graph builders
├── video.py              # video graph builders, presets, node provenance
├── workflows.py          # template compiler, DAG validation, snapshots, caching
├── websocket_client.py   # ComfyWSClient          [websocket]
├── intelligence.py       # prompt analysis + enhancement  [ai]
├── ui.py                 # Gradio interface       [ui]
├── theme.py              # Ocean Mist theme
├── health.py             # health checks          [health]
├── config.py             # settings, env resolution
├── exceptions.py         # structured error taxonomy
├── retry.py              # circuit breaker, rate limiter, backoff
├── http_client.py        # pooled transport
├── logging_config.py     # structured logging, OTel hooks
├── secrets.py            # SecretValue masking
├── secrets_manager.py    # secret storage helpers
├── cleanup.py            # temp file lifecycle
├── feature_flags.py      # optional dependency detection
├── validation.py         # input validation
├── help_system.py        # in-library help topics
└── __main__.py           # CLI entry point

tests/                    # test suite (repo root, not inside the package)
site/                     # landing page + this handbook
```

## Lazy loading

Optional features are resolved through a module-level `__getattr__`. Importing
`comfy_headless` does not import `gradio`, `websockets` or `httpx` — those load on first
use of the symbol that needs them.

The practical effect: the core install stays around 2MB, and a missing extra surfaces as
`FeatureNotAvailable` with the exact `pip install` line rather than a bare `ImportError`
from a dependency you have never heard of.

## Validation layers

Three checks run before a job reaches the server:

1. **Parameter validation** — dimensions, steps and CFG against the `generation.max_*`
   guard rails
2. **DAG validation** — `validate_workflow_dag()` checks the graph is well-formed and has
   no dangling references
3. **Dependency validation** — `check_workflow_dependencies()` confirms every emitted
   `class_type` exists on the target server

Each is cheaper than the failure it prevents, and the third is the one that catches
ecosystem drift.

## Testing

The suite includes a **node-catalog contract test** that builds every preset across every
option combination and asserts that no removed node is emitted, every `class_type` is
either core or declared with a pack, no reference dangles, an output node is present, and
the seed is recoverable.

That test is the regression barrier for the class of bug v3.0 fixed. If you add a model
family, it will fail until the new nodes are verified and declared.
