---
title: Architecture
description: How Comfy Headless works internally — the graph emitter model, the ComfyUI routes it uses, node provenance and validation, resilience, and the module map.
sidebar:
  order: 7
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

Since 3.1 that one idea covers **six workflow profiles** — Image, Video, 3D, Inference,
Metadata, Audio — and the diagram above did not change: meshes, music, captions and
provenance ride the same five arrows. What did change is the layer that makes six
profiles safe to emit from one client, described next.

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

`build_txt2img_workflow()`, `build_video_workflow()` and every 3.1 profile builder
return exactly this structure, so you can inspect, diff or hand-edit a graph before
submitting it.

## The addressing/typing layer (3.1)

`comfy_headless/addressing.py` sits under all six profiles and encodes three server
behaviours that a naive emitter gets wrong:

**1. Union type matching, transcribed — not approximated.** ComfyUI accepts an edge when
the source type set and the declared type set intersect. `validate_node_input()` is a
line-for-line transcription of the server's own `comfy_execution/validation.py`, because
a client stricter than the server manufactures false rejections by construction — the
canonical case is `VoxelToMesh`'s `MESH` output feeding `SaveGLB`'s 14-member
`FILE_3D_*` union input, a perfectly valid edge that an equality check rejects.
`GraphTypeChecker` applies the rule per edge (`client.check_workflow_types()` runs it
against the live catalog), and a **zero-rejections corpus test** asserts every graph the
builders emit passes — if the checker ever gets stricter than the server, the suite
fails.

**2. Dotted dynamic-combo fields.** Some inputs are `COMFY_DYNAMICCOMBO_V3` selectors
whose conditional sub-fields serialize as flattened dotted keys:

```json
{ "codec": "h264", "codec.encoding": "re-encode", "codec.encoding.crf": 23 }
```

Sent flat (`{"crf": 23}`), the server rejects with `required_input_missing`. Field paths
parse to typed segments (escape-aware) and writes never auto-create structure.

**3. Presence-aware conditionals.** `format.quality` exists only when
`SaveAudioAdvanced.format` is `mp3`/`opus` — under `flac` it must not be sent at all.
`DynamicCombo.build()` constructs the input fragment fresh from the selected branch and
raises `GraphAddressError` for any field the branch does not activate, so a stale value
cannot survive a tag change.

**4. The output-node guard.** A result reaches `/history` only through a node flagged
`OUTPUT_NODE` — a bare captioner runs green and returns nothing. `require_output_node()`
makes that unshippable, and `HISTORY_OUTPUT_KEYS` records where each terminator reports:

| Terminator | `/history` outputs key |
|------------|------------------------|
| `SaveImage` | `images` |
| `SaveGLB` | `3d` |
| `SaveText` | `text` (inline) **and** `files` |
| `SaveAudioAdvanced` | `audio` |
| `SaveVideo` | `images` + `animated` flag |
| `VHS_VideoCombine` | `gifs` |

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
| `POST /upload/image` | Put a source file into the input folder (images **and** audio — the server has no audio-specific route) |
| `POST /upload/mask` | Composite a mask into an existing image |

That is the whole surface — and 3.1 added five output types without adding a single
route. Meshes (`SaveGLB`), audio (`SaveAudioAdvanced`) and text (`SaveText`) register in
`/history` exactly like images and download through the same `GET /view`. There is no
private API and no plugin protocol.

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
| `comfyui-videohelpersuite` | `VHS_VideoCombine` — the default video terminator (avoidable via `output="core"`) |
| `comfyui-animatediff-evolved` | The three `ADE_*` nodes |
| `comfyui-cogvideoxwrapper` | The whole CogVideoX family |
| `comfyui-frame-interpolation` | `RIFE VFI` frame interpolation |
| `comfyui-florence2` | `Florence2Run` + its loader — the whole inference profile |
| `comfyui-segment-anything-2` | `Florence2toCoordinates` — the detect leg's JSON→STRING bridge |
| `audio-separation-nodes-comfyui` | `AudioSeparation` — stem separation |

Since 3.1 the registry lives in `comfy_headless.node_packs`, shared by every profile;
`comfy_headless.video` re-exports it for older imports. Two classes are deliberately
**absent**: `Florence2ModelLoader` and any WD14 tagger — neither could be verified in
the live catalog, and this library does not emit classes it cannot verify (the contract
test enforces that).

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
├── client.py             # ComfyClient — HTTP, uploads, polling, profile methods
├── addressing.py         # union matching, dotted combos, output-node guard  (3.1)
├── node_packs.py         # shared custom-node-pack registry                  (3.1)
├── workflows.py          # image templates + Qwen edit/ControlNet builders
├── video.py              # video graph builders, 26 presets
├── three_d.py            # 3D profile — Hunyuan3D-2                          (3.1)
├── audio.py              # audio profile — ACE-Step 1.5 + separation         (3.1)
├── inference.py          # inference profile — Florence-2                    (3.1)
├── metadata.py           # provenance profile — PNG chunk round-trip         (3.1)
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
kb/                       # in-repo knowledge base — LLM-first index over
                          # profile facts, reference graphs, node provenance
scripts/gen_kb.py         # regenerates kb/ from the package registries
site/                     # landing page + this handbook
```

The `kb/` tree deserves a sentence: `kb/index.json` is a machine-readable index over
per-profile fact pages and runnable reference graphs, generated **from the package
registries themselves** with pinned seeds — `tests/test_kb.py` fails the suite if code
and KB drift. If you point an LLM at this repository, point it at `kb/index.json`
first.

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

Since 3.1 the contract covers **all six profiles** (`tests/test_profile_contract.py`)
and adds three more barriers:

- the **zero-rejections corpus gate** — the type checker must accept every known-good
  emitted graph (a checker stricter than the server is a bug in the checker);
- a **deprecated-terminator ban** — the three deprecated audio save nodes may never be
  emitted;
- an **unverified-class ban** — classes absent from the live catalog on the
  verification date (`Florence2ModelLoader`, the WD14 tagger) may never appear in a
  graph.

That battery is the regression barrier for the class of bug v3.0 fixed. If you add a
model family, it will fail until the new nodes are verified and declared.
