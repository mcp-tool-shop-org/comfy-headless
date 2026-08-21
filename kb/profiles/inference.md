# Inference profile

Summary: Non-generative model calls — caption, tag, detect, segment, OCR — through Florence-2, with every graph guaranteed to terminate in an output node.
Keywords: inference, caption, tag, detect, segment, ocr, florence2, savetext

## Surfaces

- `build_inference_workflow(image_ref, task=..., text_input=...)` — tasks
  `caption` / `detailed_caption` / `more_detailed_caption` / `tag` /
  `detect` / `segment` / `ocr`.
- `ComfyClient.run_inference(image, task=..., text_input=...)` — returns the
  inline text directly (`result["text"]`), no second round-trip.

## The load-bearing mechanic

A STRING/JSON result reaches `/history` ONLY if it terminates in a node with
`output_node: true`. A bare captioner's output is invisible to a headless
caller — the graph runs green and returns nothing. Every builder here
terminates in core `SaveText` (or `SaveImage` for masks) and passes
`require_output_node()` before the graph is returned. `SaveText` (core,
category `text`, `format: txt|csv|md|json`) reports BOTH the inline text
(outputs key `text`) and the written file (key `files`).

## Task → graph shapes (all verified 2026-08-21)

| Task | Graph | Result |
|---|---|---|
| caption / detailed / more_detailed / ocr | `DownloadAndLoadFlorence2Model → Florence2Run → SaveText` | inline text + file |
| tag | same, `task="prompt_gen_tags"`, model `MiaoshouAI/Florence-2-base-PromptGen-v1.5` | booru-style tags |
| detect | `Florence2Run(caption_to_phrase_grounding) → Florence2toCoordinates → SaveText(json)` | coordinates JSON |
| segment | `Florence2Run(referring_expression_segmentation, fill_mask) → MaskToImage → SaveImage` | mask PNG |

`Florence2Run` outputs, in order: IMAGE (0), MASK (1), STRING (2), JSON (3).
Detect/segment REQUIRE `text_input` (what to find).

## Why these vehicles (catalog rulings)

- **`Florence2ModelLoader` is NOT in the catalog** — only the
  auto-downloading `DownloadAndLoadFlorence2Model` is. Only the verified
  loader is emitted.
- **No WD14 tagger exists in the catalog** (zero hits for any tagger node),
  so tagging rides Florence-2 PromptGen instead — same pack, verified task
  value, and the contract test (`test_unverified_nodes_never_emitted`)
  forbids emitting `WD14Tagger|pysssss`.
- **JSON → STRING is not a valid edge** (disjoint types; the server rejects
  it). `Florence2toCoordinates` (pack `comfyui-segment-anything-2`) bridges
  Florence2Run's JSON detection data into a STRING SaveText can persist.

## Packs

Entirely custom-pack for the model legs (no core captioner/tagger/detector
exists): `comfyui-florence2` for everything, plus
`comfyui-segment-anything-2` for the detect bridge. Both declared in
`NODE_PACKS`, so `check_workflow_dependencies` names what to install.

## Deliberately thin

Embed and score surfaces are absent: nothing verified in the catalog earns
them yet.
