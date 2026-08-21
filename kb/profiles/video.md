# Video profile

Summary: 26 presets across 9 model families (AnimateDiff, SVD, CogVideoX, Hunyuan 1.0/1.5, LTXV, Wan, Mochi) with t2v/i2v legs and a pack-free core terminator option.
Keywords: video, animatediff, svd, hunyuan, ltxv, wan, mochi, i2v, vhs, savevideo

## Surfaces

- `build_video_workflow(prompt, preset=..., init_image=..., **overrides)`
- `ComfyClient.generate_video(prompt, preset=..., init_image=...)`
- Registries: `VIDEO_PRESETS` (26), `VIDEO_MODEL_INFO` (9 families, each
  declaring `requires_packs`).

## Family facts that are easy to get wrong

- **LTXV sampler leg is deliberate**: `LTXVScheduler → KSamplerSelect →
  SamplerCustom`. `LTXVScheduler` emits SIGMAS; a plain `KSampler` silently
  drops its entire config. Do not "fix" this to KSampler.
- **Hunyuan 1.0 t2v is guidance-distilled**: steered by `FluxGuidance →
  BasicGuider`, takes NO negative prompt. Encoders load via `DualCLIPLoader`
  with `type="hunyuan_video"` — `CLIPLoader` does NOT have that type
  (only `DualCLIPLoader` carries `hunyuan_video` and `hunyuan_video_15`).
- **Hunyuan 1.5**: `DualCLIPLoader(qwen_2.5_vl_7b_fp8_scaled + 
  byt5_small_glyphxl_fp16, type="hunyuan_video_15")`, `CFGGuider` +
  `SamplerCustomAdvanced`, VAE `hunyuanvideo15_vae_fp16.safetensors`.
  t2v cfg-distilled exists at 480p ONLY; **i2v cfg-distilled exists at both
  480p and 720p** (verified 2026-08-21).
- **Hunyuan 1.5 i2v (repaired v3.1.0)**: `HunyuanVideo15ImageToVideo`
  (positive, negative, vae, width d848, height d480, length d33, batch,
  optional start_image + clip_vision_output) replaces the empty latent; its
  CONDITIONING/CONDITIONING/LATENT outputs rewire the guider and sampler.
  Presets `hunyuan15_i2v`, `hunyuan15_i2v_fast`; both REQUIRE `init_image`.
- **hunyuan15_1080p is an upsample**, not the official two-stage
  `HunyuanVideo15SuperResolution` refinement — valid, but a clean upscale
  rather than a re-detailed render (documented limitation).
- **Wan i2v** needs `CLIPVisionLoader(clip_vision_h.safetensors)` →
  `CLIPVisionEncode` → `WanImageToVideo`.
- **Mochi** loads via `UNETLoader` (diffusion_models), not checkpoints.

## Terminators and retrieval

- Default: `VHS_VideoCombine` (pack `comfyui-videohelpersuite`); history
  outputs key **`gifs`**.
- `VideoSettings(output="core")` (v3.1.0): swaps to core
  `CreateVideo → SaveVideo` — zero pack dependencies. `SaveVideo.codec` is a
  dynamic combo (`auto | h264`, with nested `codec.encoding` and
  `codec.encoding.crf`), emitted through the addressing layer. History
  outputs key: **`images` with an `animated` flag** (NOT `gifs`);
  `generate_video` handles both.

## i2v triggering

Passing `init_image` (a server-side ref from `upload_image()["ref"]`) flips
families that support it (SVD, LTXV, Wan, Hunyuan 1.5) onto their i2v leg.
SVD and the hunyuan15_i2v presets raise if `init_image` is missing.

## Fixed in v3.1.0

`build_video_workflow` overrides previously dropped `variant`, `upscale`,
`shift`, and `precision` — e.g. `preset="hunyuan15_fast"` plus any override
silently lost `variant="distilled"` and built the wrong graph. All settings
fields now survive the override path.
