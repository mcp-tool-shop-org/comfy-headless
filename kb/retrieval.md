# Retrieval contract

Summary: How every output type gets back to a headless caller — one route (/view), one discovery mechanism (/history outputs keys), per-terminator keys verified in server source.
Keywords: retrieval, history, view, outputs, download, images, audio, 3d, text

## The shape

1. `POST /prompt` → `prompt_id`.
2. Poll `GET /history/<prompt_id>` until `status.completed`
   (`ComfyClient.wait_for_completion`).
3. Results are announced at `history["outputs"][<node_id>][<key>]` — the key
   depends on the terminator class (below).
4. File entries (`{filename, subfolder, type}`) download via
   `GET /view?filename=...&subfolder=...&type=output` — ONE route serves
   every output type (`ComfyClient.get_file` / `get_image` / `get_video`).

## Per-terminator keys (verified in server source; `HISTORY_OUTPUT_KEYS`)

| Terminator | outputs key | Notes |
|---|---|---|
| `SaveImage` | `images` | file entries |
| `SaveGLB` | `3d` | registers exactly like SaveImage; GLB via /view |
| `SaveAudioAdvanced` | `audio` | file entries |
| `SaveText` | `text` **and** `files` | `text` is the raw string inline (tuple) — no second round-trip needed; `files` is the written file |
| `SaveVideo` (core) | `images` + `animated: (true,)` | the `animated` flag is what distinguishes it from stills |
| `VHS_VideoCombine` (pack) | `gifs` | historical key |

Client mapping: `generate_image → images`, `generate_video → gifs/videos` +
`images`-with-`animated`, `generate_3d → meshes` (from `3d`),
`generate_audio`/`separate_audio → audios` (from `audio`),
`run_inference → text/texts/files/images`, `rerun_from_png → all of them`.

## Inputs go in through one route too

`POST /upload/image` is the server's general input-file uploader — there is
no `/upload/audio`; audio files upload through the same route (no
content-type validation server-side; this is what the GUI does). The server
is authoritative about the stored name: on collision it renames and reports
the new name — ALWAYS use the returned `name`/`ref`, never assume the sent
one (`upload_image`/`upload_audio`/`upload_mask` handle this).

## The invisibility rule

A result reaches `/history` ONLY through a node with `OUTPUT_NODE=True`.
Any graph whose data terminates in a plain node executes green and returns
nothing — guard with `require_output_node()` (the inference builders do this
automatically).
