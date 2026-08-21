# Metadata profile

Summary: Provenance round-trip — read the runnable graph back out of an output PNG, re-run it verbatim, and write custom provenance via extra_pnginfo.
Keywords: metadata, provenance, png, text-chunks, extra_pnginfo, rerun, workflow-export

## Surfaces

- `read_png_text_chunks(source)` — all three PNG text chunk flavors
  (tEXt, zTXt, iTXt), pure stdlib, no Pillow.
- `read_workflow_metadata(source)` → `ProvenanceRecord` (prompt graph,
  GUI graph, custom keys).
- `extract_prompt_graph(source)` — the machine-runnable API-format graph.
- `ComfyClient.rerun_from_png(source)` — re-POST the embedded graph verbatim.
- `ComfyClient.queue_prompt(workflow, extra_pnginfo={...})` — custom
  provenance on the write side.

## How ComfyUI embeds provenance (verified in server source)

`SaveImage` writes PNG **tEXt chunks** (not EXIF), two keys by default:

- `prompt` — the API-format graph: the exact `/prompt` payload,
  machine-runnable.
- `workflow` — the GUI/litegraph format (canvas layout; NOT runnable via
  `/prompt`).

The API graph is therefore recoverable from any output PNG independently of
the GUI. Custom provenance goes in through the submission payload:
`{"prompt": ..., "extra_data": {"extra_pnginfo": {...}}}` — every key in
that dict becomes an extra text chunk (verified against `execution.py`,
which reads `extra_data.get('extra_pnginfo')` into the save nodes' hidden
inputs). No custom node needed.

## Caveats (documented, not papered over)

- **WebP/JPEG** outputs carry the same data in EXIF — a different reader
  path this module does not implement; `read_png_text_chunks` raises a typed
  error naming the detected format.
- **Video terminators do not embed the graph** (`SaveVideo` writes container
  metadata, `VHS_VideoCombine` nothing by default) — provenance dies on
  video outputs unless carried externally.
- Some hardened deployments **strip unknown extra_pnginfo keys** —
  round-trip test against the real target before relying on custom keys.
- Servers running `--disable-metadata` embed nothing; `extract_prompt_graph`
  raises with that hint.
- Re-running needs the referenced **input files still on the server**
  (LoadImage refs etc. are names in the input folder, not embedded data).

## GUI → API conversion: the ruling

There is **no server route** for it — `graphToPrompt` is client-side
TypeScript in the ComfyUI frontend. The supported answer is ComfyUI's
"Workflow → Export (API)". This library reads the result of that export or
the `prompt` chunk; it deliberately does not attempt a best-effort
converter (reroutes, primitives and group nodes make the long tail wrong in
silent ways).

## Safety

zTXt/iTXt decompression is capped (64 MB) against zip-bomb chunks;
malformed individual chunks are skipped with a debug log rather than
failing the read.
