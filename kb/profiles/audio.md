# Audio profile

Summary: ACE-Step 1.5 text-to-music (all core, MIT weights) plus pack-based stem separation, with the two coupling invariants enforced in the builder.
Keywords: audio, music, ace-step, lyrics, stems, separation, flac, saveaudioadvanced

## Surfaces

- `build_audio_workflow(tags, lyrics=..., negative_tags=..., preset=...)` —
  presets `music` / `music_long` / `jingle` / `music_mp3` / `draft`.
- `build_audio_separation_workflow(audio_ref, stems=...)`.
- `ComfyClient.generate_audio(...)`, `ComfyClient.separate_audio(...)`,
  `ComfyClient.upload_audio(...)`.

## ACE-Step 1.5 — why it is the flagship

MIT for code AND weights, native core, zero packs — the only audio model
hitting all three. The turbo AIO checkpoint
(`ace_step_1.5_turbo_aio.safetensors`, via `CheckpointLoaderSimple`) is
built for **8 steps / cfg 1**.

`TextEncodeAceStepAudio1.5` inputs, verbatim: `clip`, `tags`, `lyrics`,
`seed`, `bpm` (d120), `duration` (FLOAT d120), `timesignature` (2|3|4|6),
`language` (51 options, d"en"), `keyscale` (34 options),
`generate_audio_codes` (BOOL dTrue), `cfg_scale` (d2.0), `temperature`
(d0.85), `top_p` (d0.9), `top_k` (d0), `min_p` (d0).

## The two coupling invariants (builder-enforced, NOT user knobs)

1. `TextEncodeAceStepAudio1.5.duration` and
   `EmptyAceStep1.5LatentAudio.seconds` are ONE logical parameter split
   across two nodes. The runtime does not cross-validate them — a mismatch
   completes "successfully" with silently drifted output. Both are driven
   from the single `AudioSettings.seconds` field.
2. `generate_audio_codes` must be False whenever reference audio is supplied
   (the node's own tooltip). v3.1.0 ships text-to-music only, so this is
   structural; the negative encoder always sets it False (the slow LLM stage
   is pointless there).

## Terminator — the deprecation trap

```
SaveAudio      "Save Audio (FLAC) (DEPRECATED)"  deprecated  DO NOT EMIT
SaveAudioMP3   deprecated                                    DO NOT EMIT
SaveAudioOpus  deprecated                                    DO NOT EMIT
SaveAudioAdvanced                                            the only survivor
```

`SaveAudioAdvanced` is core, `output_node: true`. Its `format` is a
**dynamic combo** (`flac | mp3 | opus`) with `format.quality` existing ONLY
under mp3/opus (options `V0|128k|320k|64k|96k|192k`) — emitted through the
presence-aware addressing layer. For lossless provenance: `format=flac` and
NO quality key at all.

## Stem separation

`AudioSeparation` is **NOT core** — pack `audio-separation-nodes-comfyui`.
Outputs 4× AUDIO in the documented order **bass, drums, other, vocals**;
the builder wires terminators by name from that order, never by slot guess.
Optional inputs: `chunk_fade_shape` (linear|half_sine|logarithmic|
exponential), `chunk_length` (d10), `chunk_overlap` (d0.1).

## Upload + retrieval

- No `/upload/audio` route exists: `POST /upload/image` is the server's
  general input-file uploader (no content-type validation) — this is how the
  GUI's LoadAudio uploads, and how `ComfyClient.upload_audio` works.
- Results register in `/history` under outputs key **`audio`**; fetch via
  `GET /view` (`ComfyClient.get_file`).

## Not shipped (catalog-verification rule)

Chatterbox TTS is pack-only; VibeVoice, DiffRhythm and Kokoro did not appear
in the catalog — no preset ships for a class not seen in `/object_info`.
