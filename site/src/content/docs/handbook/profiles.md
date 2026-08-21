---
title: The Six Profiles
description: Image, Video, 3D, Inference, Metadata, Audio — what each profile does, the graphs it emits, and the traps it protects you from.
sidebar:
  order: 3
---

v3.1 organizes comfy-headless around **six workflow profiles**. Each profile is a set of
verified graph builders plus a high-level client method; all six share one retrieval path
(`/history` + `/view`) and one dependency story (`check_workflow_dependencies` names any
missing pack).

| Profile | What it does | Client surface |
|---------|--------------|----------------|
| Image | txt2img (SDXL, Qwen-Image-2512), instruction edit, ControlNet | `generate_image`, `edit_image`, `compile_workflow`, `build_controlnet_workflow` |
| Video | 26 presets, 9 families, t2v + i2v | `generate_video` |
| 3D | image → GLB mesh (Hunyuan3D-2) | `generate_3d` |
| Inference | caption, tag, detect, segment, OCR | `run_inference` |
| Metadata | provenance round-trip on output PNGs | `rerun_from_png`, `read_workflow_metadata` |
| Audio | text-to-music, stem separation | `generate_audio`, `separate_audio` |

## The layer underneath

All six profiles sit on a shared **addressing/typing layer**
(`comfy_headless.addressing`) that speaks ComfyUI's own validation rules:

- **Union type matching, transcribed from the server.** ComfyUI accepts an edge when the
  source and declared type sets intersect — so `VoxelToMesh`'s `MESH` output legitimately
  feeds `SaveGLB`'s 14-member `FILE_3D_*` union input. `validate_node_input()` is a
  line-for-line transcription of the server's validator, and
  `client.check_workflow_types()` applies it per edge against the live `/object_info`.
  A client stricter than the server manufactures false rejections; a corpus test asserts
  zero rejections across every graph the builders emit.
- **Dotted dynamic-combo fields.** `SaveVideo.codec` and `SaveAudioAdvanced.format` are
  dynamic combos whose sub-fields serialize as flattened dotted keys
  (`codec.encoding.crf`, `format.quality`). Sent flat, they fail with
  `required_input_missing`.
- **Presence-aware conditionals.** `format.quality` exists only under `mp3`/`opus`;
  writing it under `flac` is a bug even when tolerated. `DynamicCombo.build()` refuses
  inactive-branch fields at construction time — a stale value cannot survive a tag
  change.
- **The output-node guard.** A result reaches `/history` only through a node with
  `OUTPUT_NODE=True`; a graph without one runs green and returns nothing.
  `require_output_node()` makes that failure impossible to ship.

## 3D

```python
result = client.generate_3d("character.png", preset="detail")
glb = client.get_file(**result["meshes"][0])
```

Hunyuan3D-2 image-to-mesh, **entirely core nodes** — the chain is
`ImageOnlyCheckpointLoader → Hunyuan3Dv2Conditioning → KSampler →
VAEDecodeHunyuan3D → VoxelToMesh → SaveGLB`. It is pure image conditioning: there is no
text prompt in the graph. The GLB registers in `/history` under the `3d` key and
downloads through `/view` like any image — no new routes.

Presets: `standard` (steps 30, cfg 5.5, octree 256), `draft` (faster, coarser),
`detail` (steps 50, octree 384). Wrapper-pack models (TRELLIS, TripoSG, ...) are
deliberately not emitted; ComfyUI-3D-Pack's native dependencies are the least stable in
the ecosystem.

## Audio

```python
result = client.generate_audio(
    tags="orchestral, epic, battle theme",
    lyrics="",            # empty = instrumental
    preset="music",       # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
```

ACE-Step 1.5 — MIT-licensed code *and* weights, native core, zero packs. The turbo AIO
checkpoint runs at 8 steps / cfg 1. Two invariants are enforced by the builder rather
than left as user knobs:

1. The encoder's `duration` and the latent's `seconds` are one logical parameter split
   across two nodes; the runtime does not cross-validate them, and a mismatch completes
   "successfully" with silently drifted output. Both come from `seconds`.
2. Output terminates in `SaveAudioAdvanced` — the **only non-deprecated** audio save
   node. `flac` emits no quality field at all; `mp3`/`opus` emit the dotted
   `format.quality`.

Stem separation (`separate_audio`) uses the `audio-separation-nodes-comfyui` pack and
wires the four outputs by the documented order — bass, drums, other, vocals — never by
slot guess. Audio uploads go through `POST /upload/image` (`upload_audio`): ComfyUI has
no audio-specific upload route, and that route is the server's general input uploader.

## Inference

```python
r = client.run_inference("photo.png", task="caption")
print(r["text"])          # read straight from /history — no second round-trip
```

Tasks: `caption`, `detailed_caption`, `more_detailed_caption`, `tag`, `detect`,
`segment`, `ocr`. All run on Florence-2 (pack `comfyui-florence2`); `detect` and
`segment` need `text_input` (what to find).

Choices you should know about, because they were made against the live catalog:

- **Tagging rides Florence-2 PromptGen** (`task="prompt_gen_tags"`, checkpoint
  `MiaoshouAI/Florence-2-base-PromptGen-v1.5`). No WD14 tagger class exists in the live
  catalog, and this library does not emit classes it cannot verify.
- **Detect bridges through `Florence2toCoordinates`** (pack
  `comfyui-segment-anything-2`): Florence2Run's detection data leaves on a `JSON`
  output, and JSON → STRING is not a valid edge, so it cannot feed `SaveText` directly.
- **Segment** returns the mask as a PNG (`MaskToImage → SaveImage`) for the consumer to
  threshold.

Every inference graph terminates in an output node by construction — `SaveText` reports
the text inline (`text`) plus the written file (`files`).

## Metadata

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

graph = extract_prompt_graph("output.png")     # the exact /prompt payload
result = client.rerun_from_png("output.png")   # re-POST it verbatim
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-77"})
```

ComfyUI's save nodes embed the **API-format graph** in every output PNG (`prompt` text
chunk) alongside the GUI graph (`workflow` chunk). The reader is pure stdlib and parses
all three PNG text chunk flavors. Custom keys passed via `extra_pnginfo` become extra
chunks — no custom node needed.

Documented limits: WebP/JPEG carry the same data in EXIF (different reader path, not
implemented); video outputs don't embed the graph; hardened deployments may strip
unknown keys; GUI→API conversion has no server route — use ComfyUI's
"Workflow → Export (API)".

## Image additions in 3.1

- **`qwen_txt2img` template** — Qwen-Image-2512 with the recipe it actually wants:
  `UNETLoader` path, 16-channel `EmptySD3LatentImage`, steps 20, cfg 2.5, shift 3.1,
  1328×1328.
- **`edit_image` / `build_qwen_edit_workflow`** — Qwen-Image-Edit-2511; 1–3 reference
  images as discrete `image1..image3` inputs, no VAEEncode.
- **`build_controlnet_workflow`** — union ControlNet, one code path for Qwen
  (`Qwen-Image-2512-Fun-Controlnet-Union-2602`) and SDXL
  (`controlnet-union-sdxl-1.0`); the type enum is verbatim, and only the core `Canny`
  preprocessor is emitted.

## Video repairs in 3.1

- **Real Hunyuan 1.5 i2v** — presets `hunyuan15_i2v` / `hunyuan15_i2v_fast` build on
  core `HunyuanVideo15ImageToVideo` and require `init_image` (v3.0 silently built t2v).
- **Core terminator option** — `output="core"` swaps `VHS_VideoCombine` for
  `CreateVideo → SaveVideo`, dropping the Video Helper Suite pack.

## The knowledge base

The repo carries an LLM-first knowledge base at
[`kb/`](https://github.com/mcp-tool-shop-org/comfy-headless/tree/main/kb):
`index.json` (the dispatch table), per-profile fact pages, runnable reference graphs
generated from these builders, and node provenance. If you are pointing an LLM at this
library, point it at `kb/index.json` first.
