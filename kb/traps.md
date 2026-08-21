# Traps — already paid for, do not rediscover

Summary: The mistakes that already cost sessions — wrong loaders, wrong latents, deprecated terminators, silent i2v downgrades, environment and release traps.
Keywords: traps, pitfalls, deprecated, latent, namespace, python-3.14, lifecycle

## Graph-construction traps

| Trap | Detail |
|---|---|
| Qwen "doesn't exist" | Qwen models live in `models/diffusion_models` → `UNETLoader`. Searching `CheckpointLoaderSimple.ckpt_name` finds nothing and misleads. |
| Wrong latent for DiT models | Qwen needs `EmptySD3LatentImage` (16-channel). `EmptyLatentImage` is 4-channel SD1.5/SDXL and produces garbage — no error, just noise. |
| `CLIPLoader.type` guessing | The enum has `qwen_image` and `flux2` — there is NO plain `flux`. Guessing from FLUX.1 convention silently fails. |
| Hunyuan CLIP types | `hunyuan_video` / `hunyuan_video_15` exist ONLY on `DualCLIPLoader.type`, not `CLIPLoader`. |
| Deprecated audio savers | `SaveAudio`, `SaveAudioMP3`, `SaveAudioOpus` all carry `deprecated=true`. `SaveAudioAdvanced` is the only survivor. Contract test forbids the dead three. |
| Flat dynamic-combo fields | `{"crf": 23}` on SaveVideo fails `required_input_missing`; the key is `codec.encoding.crf` — and only under `codec=h264, encoding=re-encode`. Use the addressing layer. |
| Inactive-branch fields | `format.quality` under `format=flac` is a bug even when the server tolerates it. `DynamicCombo.build` raises at construction time. |
| LTXV sampler "fix" | `LTXVScheduler` emits SIGMAS; replacing its `KSamplerSelect → SamplerCustom` leg with a plain KSampler silently drops the whole schedule. |
| No output node | A graph whose result doesn't terminate in `OUTPUT_NODE=True` runs green and returns nothing. `require_output_node()`. |
| JSON → STRING edge | Disjoint types; the server rejects it. Florence2Run's detection JSON must bridge through `Florence2toCoordinates` before `SaveText`. |
| ACE-Step duration split | Encoder `duration` and latent `seconds` are one parameter in two nodes; the runtime does not cross-validate. Drive both from one source. |
| Upload name trust | The server renames on collision and reports the stored name. Using the sent filename points the workflow at the wrong file. |

## Lifecycle vs shape (the consult calibration)

Schema SHAPE (inputs, types, unions, output_node flags) is stable and
reliably reported. LIFECYCLE (deprecated flags, pack-vs-core membership,
what superseded what) moves fast and MUST be pulled live. All three known
consult misses were lifecycle: SaveText assumed pack (it's core),
AudioSeparation assumed core (it's a pack), SaveAudio repair swapped to
another deprecated node. The catalog-verification rule exists for this:
**no class ships unless seen in the live catalog** — which is also why
`Florence2ModelLoader` and the WD14 tagger are not emitted (absent from the
catalog on the verification date).

## Environment / release traps

| Trap | Detail |
|---|---|
| Python 3.14 masks import bugs | PEP 649 defers annotation evaluation: a core-only install can import on 3.14 while failing on 3.11/3.12. Verify core-only installs on Python 3.12 (CI tests 3.11 + 3.12). This shipped a broken v3.0.0 once. |
| Version single-source | `comfy_headless/_version.py` only. Never hardcode a version elsewhere or assert a literal version in a test — an old test asserted "2.5.1" and enforced drift for two releases. |
| Docs-PR CI deadlock | `pull_request` in ci.yml is deliberately ungated: a required check that never runs never reports, and docs PRs block forever. Do not re-add paths there. |
| KB drift | `kb/workflows/*.json`, `kb/nodes.json`, `kb/index.json` are generated. Hand-editing them fails `tests/test_kb.py`; regenerate with `python scripts/gen_kb.py`. |
