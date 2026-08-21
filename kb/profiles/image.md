# Image profile

Summary: Text-to-image (SD1.5/SDXL templates + Qwen-Image-2512), instruction editing (Qwen-Edit-2511), and union ControlNet on one code path.
Keywords: image, txt2img, qwen, sdxl, edit, controlnet, inpaint, upscale

## Surfaces

| Capability | Entry point | Client method |
|---|---|---|
| SD1.5/SDXL txt2img | `compile_workflow(prompt, template_id="txt2img_standard")` | `ComfyClient.generate_image()` |
| Hi-res fix / upscale / inpaint | templates `txt2img_hires`, `upscale`, `inpaint` | `compile_workflow` + `queue_prompt` |
| Qwen-Image-2512 txt2img | template `qwen_txt2img` | `compile_workflow` + `queue_prompt` |
| Qwen-Image-Edit-2511 | `build_qwen_edit_workflow(prompt, image_refs)` | `ComfyClient.edit_image()` |
| Union ControlNet (qwen/sdxl) | `build_controlnet_workflow(...)` | `queue_prompt` |

## Qwen family — verified facts (2026-08-21)

- Qwen models live in `models/diffusion_models` and load through
  **`UNETLoader`**, NOT `CheckpointLoaderSimple`. Searching the checkpoint
  namespace and concluding "Qwen doesn't exist" is a known trap.
- Text encoder: `CLIPLoader(clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors",
  type="qwen_image")`. The `type` enum has `qwen_image`; FLUX.2's value is
  `flux2` — there is **no plain `flux`** value.
- Latent: **`EmptySD3LatentImage`** (16-channel DiT latent).
  `EmptyLatentImage` is the 4-channel SD1.5/SDXL latent and produces garbage.
- VAE: `qwen_image_vae.safetensors` via `VAELoader`.
- Sampling defaults: steps 20, **cfg 2.5** (not 7.0), euler, simple,
  `ModelSamplingAuraFlow` shift **3.1**, native bucket 1328×1328
  (portrait 768×1344, landscape 1344×768).
- txt2img weights: `qwen_image_2512_fp8_e4m3fn.safetensors` (default) /
  `qwen_image_2512_bf16.safetensors`.

## Qwen-Edit reference mechanism (verbatim from the live schema)

`TextEncodeQwenImageEditPlus` — core, category `model/conditioning/qwen image`:

- inputs: `clip` (CLIP, required), `prompt` (STRING, required),
  `vae` (VAE, optional), `image1`/`image2`/`image3` (IMAGE, optional)
- output: CONDITIONING

Reference images go in as up to **three discrete inputs** `image1..image3`,
NOT a batched list. They do **not** pass through `VAEEncode` — the VAE wires
into the encoder's own `vae` input and raw IMAGE goes into `image1..3`.
This node replaces the positive `CLIPTextEncode`; the negative stays a plain
`CLIPTextEncode`. Edit weights: `qwen_image_edit_2511_fp8mixed.safetensors`
(default), `qwen_image_edit_2511_int8_convrot`, `qwen_image_edit_2509_bf16`.

## Union ControlNet (Qwen and SDXL share one path)

`ControlNetLoader → SetUnionControlNetType → ControlNetApplyAdvanced`.

- `SetUnionControlNetType.type` enum, **verbatim**: `auto`, `openpose`,
  `depth`, `hed/pidi/scribble/ted`, `canny/lineart/anime_lineart/mlsd`,
  `normal`, `segment`, `tile`, `repaint`. Slash-grouped values are SINGLE
  literal choices. Prefer an explicit type; `auto` makes the model infer the
  hint kind.
- `ControlNetApplyAdvanced`: `positive`, `negative`, `control_net`, `image`,
  `strength`, `start_percent`, `end_percent` + optional `vae`. The Qwen path
  wires the VAE; the SDXL path does not need it.
- ControlNet weights: `Qwen-Image-2512-Fun-Controlnet-Union-2602.safetensors`
  (qwen) / `controlnet-union-sdxl-1.0.safetensors` (sdxl).
- Preprocessors: only core `Canny` is emitted (`preprocess="canny"`). All
  others (openpose, depth, lineart, HED, MLSD, normal, tile) live in
  `comfyui_controlnet_aux`, which this library deliberately does not emit —
  supply a pre-made hint image.

## Not built (known gap, deliberate)

Segmentation/detection as an in-image editing stage (detect → mask →
inpaint composite). The inference profile provides the detection/segmentation
primitives; the composite pipeline is future work.
