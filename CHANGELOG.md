# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-08-21

The six-profile release: **Image, Video, 3D, Inference, Metadata, Audio**, on a
shared addressing/typing layer. Every emitted `class_type` was verified against
the live ComfyUI catalog on 2026-08-21; non-core nodes are declared in the
shared pack registry so a missing dependency is reported by name before a run is
spent on it.

### Added

- **Addressing / typing layer** (`comfy_headless.addressing`) — the shared
  machinery under all six profiles:
  - `validate_node_input()` — a transcription of ComfyUI's own
    `comfy_execution/validation.py`, so the client can never be stricter than
    the server. `match_types()` adds SUBSET / OVERLAP / DISJOINT resolution and
    `GraphTypeChecker` applies it per edge; a union-superset edge (`MESH` into
    SaveGLB's 14-member `FILE_3D_*` union) is never a false rejection, gated by
    a zero-rejections corpus test over every graph the builders emit.
  - Dotted dynamic-combo addressing: escape-aware field paths, no
    auto-vivification, and presence-aware `DynamicCombo` specs
    (`SAVE_AUDIO_FORMAT`, `SAVE_VIDEO_CODEC`) that refuse inactive-branch
    fields at construction time (`format.quality` under `flac` raises;
    `codec.encoding.crf` requires `codec=h264, encoding=re-encode`).
  - The output-node guard (`require_output_node`) and the retrieval contract
    (`HISTORY_OUTPUT_KEYS`): a graph whose data does not terminate in an
    `OUTPUT_NODE` runs green and returns nothing.
  - New exception: `GraphAddressError`.
- **3D profile** (`comfy_headless.three_d`) — Hunyuan3D-2 image-to-mesh,
  entirely core nodes (`ImageOnlyCheckpointLoader` → `Hunyuan3Dv2Conditioning`
  → `KSampler` → `VAEDecodeHunyuan3D` → `VoxelToMesh` → `SaveGLB`). Presets
  `standard` / `draft` / `detail`; `ComfyClient.generate_3d()`; GLB retrieval
  through the existing `/history` + `/view` routes (outputs key `3d`).
- **Audio profile** (`comfy_headless.audio`) — ACE-Step 1.5 text-to-music
  (all core, MIT weights, 8 steps / cfg 1 turbo AIO), with the model's
  duration/seconds coupling invariant enforced from a single settings field,
  and terminating in `SaveAudioAdvanced` — the only non-deprecated audio save
  node (`SaveAudio`/`SaveAudioMP3`/`SaveAudioOpus` all carry
  `deprecated=true` and are never emitted). Stem separation via the
  `audio-separation-nodes-comfyui` pack, wired by the documented output order
  (bass, drums, other, vocals). `ComfyClient.generate_audio()`,
  `separate_audio()`, `upload_audio()`.
- **Inference profile** (`comfy_headless.inference`) — caption, tag, detect,
  segment, OCR through Florence-2 (`comfyui-florence2`). Tagging rides the
  PromptGen fine-tune (`prompt_gen_tags`) because no WD14 tagger class exists
  in the live catalog; the detect leg bridges Florence2Run's JSON output
  through `Florence2toCoordinates` because JSON → STRING is not a valid edge.
  Every graph passes the output-node guard; `SaveText` reports results inline
  (`text`) plus the written file (`files`), so `ComfyClient.run_inference()`
  returns the caption with no second round-trip.
- **Metadata profile** (`comfy_headless.metadata`) — provenance round-trip,
  pure stdlib: `read_png_text_chunks` (tEXt/zTXt/iTXt, zip-bomb-capped),
  `read_workflow_metadata`, `extract_prompt_graph`, and
  `ComfyClient.rerun_from_png()` which re-POSTs the embedded API-format graph
  verbatim. Custom provenance via
  `queue_prompt(workflow, extra_pnginfo={...})` (verified payload shape:
  `extra_data.extra_pnginfo`).
- **Image profile extensions** — `qwen_txt2img` template (Qwen-Image-2512:
  UNETLoader path, 16-channel `EmptySD3LatentImage`, steps 20 / cfg 2.5 /
  shift 3.1 / 1328×1328), `build_qwen_edit_workflow` +
  `ComfyClient.edit_image()` (Qwen-Image-Edit-2511, 1-3 discrete reference
  images into `TextEncodeQwenImageEditPlus`, no VAEEncode), and
  `build_controlnet_workflow` (union ControlNet, one code path for Qwen and
  SDXL, verbatim `SetUnionControlNetType` enum, optional core-Canny
  preprocess).
- **Video** — real Hunyuan 1.5 image-to-video: presets `hunyuan15_i2v` and
  `hunyuan15_i2v_fast` build on core `HunyuanVideo15ImageToVideo` and require
  an `init_image`. `VideoSettings(output="core")` swaps `VHS_VideoCombine`
  for core `CreateVideo` → `SaveVideo` (codec emitted through the dynamic-
  combo layer), dropping the Video Helper Suite dependency; `generate_video`
  understands SaveVideo's history shape (`images` + `animated`).
- **Client** — `generate_3d`, `generate_audio`, `separate_audio`,
  `run_inference`, `edit_image`, `rerun_from_png`, `upload_audio`,
  `get_file` (one `/view` route serves every output type), and
  `check_workflow_types` (edge type validation against the live
  `/object_info` using the server's own acceptance rule).
- **In-repo knowledge base** (`kb/`) — an LLM-first index (`kb/index.json`)
  over per-profile fact pages, runnable reference graphs
  (`kb/workflows/*.json`) and node provenance (`kb/nodes.json`), generated
  from the package registries by `scripts/gen_kb.py` with pinned seeds so
  regeneration is byte-identical; `tests/test_kb.py` fails the suite if code
  and KB drift.

### Fixed

- **`HUNYUAN_15_I2V` silently built a text-to-video graph** and ignored
  `init_image`. It now builds the real i2v shape and raises without an image.
- **`build_video_workflow` overrides dropped `variant`/`upscale`/`shift`/
  `precision`** — e.g. `preset="hunyuan15_fast"` plus any override silently
  lost `variant="distilled"` and built the wrong graph with the wrong cfg.

### Changed

- The custom-node pack registry moved to `comfy_headless.node_packs` (now
  shared by all profiles) and gained `comfyui-florence2`,
  `comfyui-segment-anything-2` and `audio-separation-nodes-comfyui`.
  `comfy_headless.video` re-exports it, so pre-3.1 imports keep working.

## [3.0.1] - 2026-08-21

Fixes a packaging defect in 3.0.0 that made a core-only install unimportable.
**3.0.0 was tagged on GitHub but never reached PyPI** — its publish run failed at
the build stage on exactly this bug, so no released artifact carries it.

### Fixed

- **A core-only `pip install comfy-headless` could not be imported on Python
  3.10-3.13.** `http_client.py` annotated a method as `-> httpx.Response` at class
  level. On a core install `httpx` is absent, so the module sets `httpx = None`, and
  evaluating that annotation at import time raised
  `AttributeError: 'NoneType' object has no attribute 'Response'`.

  `from __future__ import annotations` is now declared in every module that holds an
  optional dependency in a possibly-`None` name: `http_client`, `intelligence`,
  `retry`, `ui`, `websocket_client`.

  Two things hid this defect, and both are worth recording:

  1. The test suite runs in a dev environment where every extra **is** installed, so
     the annotation resolved fine and nothing failed.
  2. The maintainer's interpreter is Python 3.14, where [PEP 649][pep649] defers
     annotation evaluation. A manual core-only venv check therefore passed locally
     while CI on Python 3.11 failed. The package supports 3.10+, so most of the
     supported range was affected.

### Added

- `tests/test_optional_dep_annotations.py` — a static AST guard asserting that any
  module keeping an optional dependency in a possibly-`None` name declares
  `from __future__ import annotations`. It is deliberately static rather than an
  import test, so it cannot be masked by the interpreter version or by which extras
  happen to be installed. It includes a self-check that the scan is non-empty and a
  reconstruction of the original defect, so the guard cannot pass vacuously.

### Changed

- `publish.yml`: `test-install` now runs on `ubuntu-latest` only, and `publish-pypi`
  and `docker` declare `needs: [build, test-install]`. Previously they depended on
  `build` alone and were skipped only as a side effect of run cancellation — an
  accidental gate, now an explicit one.

[pep649]: https://peps.python.org/pep-0649/


## [3.0.0] - 2026-08-21

Correctness release. comfy-headless emits ComfyUI API-format graphs, so a node
name that no longer exists is a shipped bug — the graph is rejected at submit
with an opaque error. An audit against the live ComfyUI node catalog found nine
such names in the video builders, plus an image-input path that depended on an
unpublished third-party node. Both are fixed here.

### BREAKING

- **`init_image` is now a server-side filename, not base64 data.** Image input
  previously went through `LoadImageFromBase64`, a custom-pack node that is not
  published in the ComfyUI registry and does not resolve on a stock install.
  Video builders now emit the core `LoadImage` node, which takes the name of a
  file already in ComfyUI's input folder.

  Migration — upload first, then pass the returned name:

  ```python
  ref = client.upload_image("cat.png")
  result = client.generate_video("a cat walking", preset="wan_14b",
                                 init_image=ref["name"])
  ```

- Presets whose graphs were rebuilt now emit different node chains. If you
  depended on the exact JSON of `build_video_workflow()` output for
  `mochi`, `mochi_short`, `hunyuan`, `hunyuan_fast`, `cogvideo`,
  `hunyuan15_720p`, `hunyuan15_quality`, `hunyuan15_fast` or `hunyuan15_1080p`,
  re-capture it.

### Added

- `ComfyClient.upload_image()` and `ComfyClient.upload_mask()` — `POST /upload/image`
  and `POST /upload/mask`. The server's returned `name` is authoritative and is read
  back rather than assumed, because ComfyUI renames on filename collision. Returns
  `{"name", "subfolder", "type", "ref"}`, where `ref` is the exact string a
  `LoadImage` node expects.
- Node pack provenance: `NODE_PACKS`, `NODE_PACK_INFO` and
  `VideoModelInfo.requires_packs` record which custom node pack provides each
  non-core node, with name, URL and install hint.
- `check_workflow_dependencies()` now reports `missing_packs` and `required_packs`;
  new `require_workflow_dependencies()` raises `MissingNodePackError` naming the
  class and the pack that provides it, instead of letting `/prompt` reject cryptically.
- `UploadError` and `MissingNodePackError` exceptions, following the existing
  structured code/message/hint shape.
- A node-catalog contract test that builds every preset across every option
  combination and asserts no removed node, no undeclared node, no dangling
  reference, and a recoverable seed.

### Fixed

- **Nine node types that no longer exist in ComfyUI** were being emitted:
  `MochiSampler`, `MochiModelLoader`, `MochiVAEDecode`, `HunyuanVideoSampler`,
  `HunyuanVideoModelLoader`, `HunyuanVideoTextEncode`, `HunyuanVideoVAEDecode`,
  `CogVideoModelLoader`, `CogVideoVAEDecode`. These were wrapper-pack nodes
  mislabelled as core; ComfyUI kept the generic sampler path and the per-family
  latent nodes, and dropped the family pipelines.
- Mochi and Hunyuan Video 1.0 rebuilt on the native core path
  (`UNETLoader` / `CLIPLoader` / `DualCLIPLoader` → sampler → `VAEDecode`).
  Hunyuan Video is guidance-distilled, so it now uses `FluxGuidance` +
  `BasicGuider` rather than CFG with a negative prompt.
- CogVideoX rewired to the real wrapper-pack node names
  (`DownloadAndLoadCogVideoModel`, `CogVideoDecode`) and declared as
  pack-dependent — it has no native core path.
- Hunyuan 1.5 pointed at `hunyuanvideo1.5_720p_t2v_distilled_fp16.safetensors`,
  which does not exist; the distilled text-to-video weights are published at 480p
  only. The 1080p preset also sampled at 1920x1080 before "upscaling" to the same
  size, and passed `interpolation`/`extend_length` to a node whose inputs are
  `upscale_method`/`crop`.
- `EmptyMochiLatentVideo` was passed `frames`; the node's input is `length`.
- Mochi's `KSampler` negative conditioning was built but never wired.
- `_build_wan_fast` passed `seed` to `KSamplerAdvanced`, whose input is
  `noise_seed` — both sampler nodes in that graph would have been rejected.
- Seed recovery scanned for a hardcoded `HunyuanVideoSampler`, so every preset
  not built on plain `KSampler` returned `-1` instead of the resolved seed.

### Notes

- `HUNYUAN_15_I2V` still builds a text-to-video graph and ignores `init_image`;
  the core nodes to fix it exist and are verified, but that is a feature rather
  than part of this correctness pass.


## [2.5.7] - 2026-03-25

### Added
- `--diagnose` CLI flag — shows version, Python info, feature availability, and config
- 4 new tests for diagnose command

### Fixed
- Version alignment: `__init__.py` now matches `pyproject.toml` (was 2.5.1, now synced)

## [2.5.6] - 2026-02-27

### Added
- SHIP_GATE.md and SCORECARD.md (Shipcheck audit — 50/50)
- Security & Data Scope section in README
- Codecov badge in README

### Changed
- Standard report email in SECURITY.md
- Removed redundant h1 heading (logo contains product name)

## [2.5.1] - 2026-01-18

### Security
- **WebSocket DoS Protection**: Added `max_message_size` limit (1MB default) to prevent memory exhaustion
- **WebSocket Encryption Warning**: Now logs warning when using unencrypted `ws://` connections
- **Listener Limit**: Added `MAX_LISTENERS_PER_PROMPT` (100) to prevent memory exhaustion attacks
- **Gradio Minimum Version**: Updated to `>=5.6.0` to include fix for CVE-2025-23042 (path traversal)
- **Default Host Changed**: UI now defaults to `127.0.0.1` (localhost) instead of `0.0.0.0` to prevent accidental network exposure
- Added `SECURITY_AUDIT.md` documenting security review findings

### Fixed
- Version mismatch between pyproject.toml and code modules
- Updated WebSocket client to use modern `websockets.asyncio.client` API (fixes deprecation warnings)

### Added
- GitHub Actions CI/CD workflows for automated testing and PyPI publishing
- CHANGELOG.md for version history tracking
- CONTRIBUTING.md with contribution guidelines
- SECURITY.md with vulnerability reporting process
- `SECURITY_AUDIT.md` - Web UI security audit report
- `ERROR_HANDLING_AUDIT.md` - Exception handling audit report
- `GENERATION_AUDIT.md` - Image/Video/AI module audit report

### Improved
- Narrowed exception catches in `cleanup.py` from broad `Exception` to specific types

### Changed
- Moved archive folder outside main package directory
- WebSocket client constructor now accepts `max_message_size` parameter

## [2.5.0] - 2026-01-16

### Added
- Initial public release
- Modular architecture with feature-gating for optional dependencies
- Core client with connection pooling and retry logic
- WebSocket client for real-time progress updates
- AI-powered prompt intelligence via Ollama integration
- Video generation support with 11 preset models
- Gradio 5.0+ UI with 7 tabs and Ocean Mist theme
- Comprehensive exception hierarchy with user-friendly messages
- Circuit breaker pattern for resilience
- Structured logging with OpenTelemetry support
- Input validation and sanitization utilities
- Secrets management utilities
- Temporary file cleanup system
- Context-aware help system

### Features by Install Extra
- `[ai]` - Ollama prompt enhancement with A/B testing
- `[websocket]` - Real-time progress via WebSocket
- `[health]` - System health monitoring with psutil
- `[ui]` - Full Gradio web interface
- `[validation]` - Pydantic-based config validation
- `[observability]` - OpenTelemetry distributed tracing
- `[standard]` - ai + websocket bundle
- `[full]` - All features enabled

### Supported Video Models
- Wan 2.1 (14B, 1.3B variants)
- Hunyuan Video
- LTX Video
- Mochi
- CogVideoX (5B, 2B)
- AnimateDiff
- Stable Video Diffusion
- Custom workflow support

[Unreleased]: https://github.com/mcp-tool-shop/comfy-headless/compare/v2.5.1...HEAD
[2.5.1]: https://github.com/mcp-tool-shop/comfy-headless/compare/v2.5.0...v2.5.1
[2.5.0]: https://github.com/mcp-tool-shop/comfy-headless/releases/tag/v2.5.0
