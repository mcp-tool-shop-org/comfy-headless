"""
Comfy Headless - Audio Generation Module
========================================

v3.1.0: the audio profile. Audio comes back through ``/history`` + ``/view``
like everything else (outputs key ``"audio"``) -- no audio-specific route.

Text-to-music runs on **ACE-Step 1.5** (turbo AIO checkpoint): MIT for code
and weights, native core, zero packs -- the only audio model hitting all
three. Reference graph (validated against the live catalog, 2026-08-21)::

    CheckpointLoaderSimple(ace_step_1.5_turbo_aio.safetensors)
      |- CLIP -> TextEncodeAceStepAudio1.5 (tags + lyrics)  -> KSampler.positive
      |- CLIP -> TextEncodeAceStepAudio1.5 (negative)       -> KSampler.negative
      |- EmptyAceStep1.5LatentAudio(seconds)                -> KSampler.latent_image
      |- VAE  -> VAEDecodeAudio <- KSampler -> AUDIO -> SaveAudioAdvanced

    KSampler: steps 8, cfg 1, euler, simple (turbo AIO is built for
    low-step / cfg-1 operation).

Two coupling invariants this builder enforces (they are NOT user knobs):

1. ``TextEncodeAceStepAudio1.5.duration`` and
   ``EmptyAceStep1.5LatentAudio.seconds`` are one logical parameter split
   across two nodes. The runtime does not cross-validate them -- a mismatch
   completes "successfully" with silently drifted output. Both are driven
   from the single ``AudioSettings.seconds`` field here.
2. ``generate_audio_codes`` must be False whenever reference audio is
   supplied (per the node's own tooltip). v3.1.0 ships text-to-music only,
   so the flag is exposed but the invariant is documented for the reference-
   audio extension.

Terminator: **SaveAudioAdvanced is the only non-deprecated audio output
node** (SaveAudio / SaveAudioMP3 / SaveAudioOpus all carry
``deprecated=true``). Its ``format`` is a dynamic combo (flac|mp3|opus) with
``format.quality`` existing ONLY under mp3/opus -- built through the
presence-aware addressing layer, and for lossless output (flac) NO quality
key is emitted at all.

Stem separation uses the ``audio-separation-nodes-comfyui`` pack (NOT core):
``AudioSeparation`` outputs 4x AUDIO in documented order bass, drums, other,
vocals -- wired to four named terminators, never by slot guess.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .addressing import SAVE_AUDIO_FORMAT

__all__ = [
    "AudioModel",
    "AudioFormat",
    "AudioSettings",
    "AudioModelInfo",
    "AUDIO_PRESETS",
    "AUDIO_MODEL_INFO",
    "SEPARATION_STEMS",
    "AudioWorkflowBuilder",
    "get_audio_builder",
    "build_audio_workflow",
    "build_audio_separation_workflow",
    "list_audio_presets",
]


class AudioModel(str, Enum):
    """Available audio generation models."""

    ACE_STEP_15 = "ace_step_1.5"


class AudioFormat(str, Enum):
    """SaveAudioAdvanced output formats."""

    FLAC = "flac"  # lossless; emits NO quality field
    MP3 = "mp3"
    OPUS = "opus"


# AudioSeparation's four AUDIO outputs, in the pack's documented order.
# Wire by this order, never by guessing slots.
SEPARATION_STEMS: tuple[str, ...] = ("bass", "drums", "other", "vocals")


@dataclass
class AudioSettings:
    """Settings for text-to-music generation (ACE-Step 1.5)."""

    model: AudioModel = AudioModel.ACE_STEP_15
    checkpoint: str = "ace_step_1.5_turbo_aio.safetensors"
    # One logical duration: drives BOTH the encoder's `duration` and the
    # latent's `seconds`. Never split.
    seconds: float = 30.0
    bpm: int = 120
    timesignature: str = "4"  # COMBO: 2 | 3 | 4 | 6
    language: str = "en"
    keyscale: str = "C major"
    steps: int = 8  # turbo AIO is built for low-step
    cfg: float = 1.0  # ... and cfg-1
    sampler: str = "euler"
    scheduler: str = "simple"
    seed: int = -1
    # LLM audio-codes stage: slower, higher quality. MUST be False whenever
    # reference audio is supplied (no reference input in v3.1.0).
    generate_audio_codes: bool = True
    cfg_scale: float = 2.0  # encoder-side LLM cfg
    temperature: float = 0.85
    top_p: float = 0.9
    top_k: int = 0
    min_p: float = 0.0
    format: AudioFormat = AudioFormat.FLAC
    # Only meaningful for mp3/opus; ignored (and not emitted) for flac.
    # None -> the schema default "V0" when a lossy format is chosen.
    quality: str | None = None
    filename_prefix: str = "audio/ComfyUI"

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "checkpoint": self.checkpoint,
            "seconds": self.seconds,
            "bpm": self.bpm,
            "timesignature": self.timesignature,
            "language": self.language,
            "keyscale": self.keyscale,
            "steps": self.steps,
            "cfg": self.cfg,
            "sampler": self.sampler,
            "scheduler": self.scheduler,
            "seed": self.seed,
            "generate_audio_codes": self.generate_audio_codes,
            "cfg_scale": self.cfg_scale,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "min_p": self.min_p,
            "format": self.format.value,
            "quality": self.quality,
            "filename_prefix": self.filename_prefix,
        }


AUDIO_PRESETS: dict[str, AudioSettings] = {
    # 30s lossless piece -- the validated reference configuration.
    "music": AudioSettings(),
    # Full-length track (the model's native duration default).
    "music_long": AudioSettings(seconds=120.0),
    # Short sting for UI / transitions.
    "jingle": AudioSettings(seconds=10.0),
    # Distribution-friendly lossy output.
    "music_mp3": AudioSettings(format=AudioFormat.MP3, quality="320k"),
    # Faster draft: skip the LLM audio-codes stage.
    "draft": AudioSettings(seconds=15.0, generate_audio_codes=False),
}


@dataclass
class AudioModelInfo:
    """Information about an audio model family."""

    id: str
    name: str
    description: str
    model: AudioModel
    min_vram_gb: int = 8
    estimated_time_seconds: int = 30
    presets: list[str] = field(default_factory=list)
    # Custom node packs this family's workflows depend on. Empty == core only.
    requires_packs: list[str] = field(default_factory=list)


AUDIO_MODEL_INFO: dict[str, AudioModelInfo] = {
    "ace_step_1.5": AudioModelInfo(
        id="ace_step_1.5",
        name="ACE-Step 1.5",
        description=(
            "Text-to-music with tags + lyrics conditioning. MIT-licensed code "
            "and weights, native ComfyUI core path, zero custom packs. The "
            "turbo AIO checkpoint runs at 8 steps / cfg 1."
        ),
        model=AudioModel.ACE_STEP_15,
        min_vram_gb=8,
        estimated_time_seconds=30,
        presets=list(AUDIO_PRESETS),
        requires_packs=[],
    ),
}


class AudioWorkflowBuilder:
    """Builds ComfyUI workflows for audio generation and separation."""

    def _save_audio_inputs(self, settings: AudioSettings) -> dict[str, Any]:
        """
        SaveAudioAdvanced inputs via the presence-aware dynamic-combo layer.

        flac emits no quality key at all; mp3/opus emit the dotted
        ``format.quality`` (defaulting to the schema default "V0").
        """
        fmt = settings.format.value
        if fmt == AudioFormat.FLAC.value:
            return SAVE_AUDIO_FORMAT.build(fmt)
        return SAVE_AUDIO_FORMAT.build(fmt, quality=settings.quality or "V0")

    def build(
        self,
        tags: str,
        lyrics: str = "",
        negative_tags: str = "",
        settings: AudioSettings | None = None,
    ) -> dict[str, Any]:
        """
        Build an ACE-Step 1.5 text-to-music workflow.

        Args:
            tags: Style/genre tags -- the main prompt (e.g.
                "lo-fi, jazz, mellow, rainy night").
            lyrics: Optional lyrics; empty for instrumental.
            negative_tags: Tags to steer away from.
            settings: Audio settings (defaults to the "music" preset).

        Returns:
            ComfyUI API-format workflow JSON.
        """
        settings = settings or AUDIO_PRESETS["music"]

        seed = settings.seed
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        def _encoder(text_tags: str, text_lyrics: str) -> dict[str, Any]:
            return {
                "class_type": "TextEncodeAceStepAudio1.5",
                "inputs": {
                    "clip": ["1", 1],
                    "tags": text_tags,
                    "lyrics": text_lyrics,
                    "seed": seed,
                    "bpm": settings.bpm,
                    # Coupling invariant 1: same source as the latent's seconds.
                    "duration": float(settings.seconds),
                    "timesignature": settings.timesignature,
                    "language": settings.language,
                    "keyscale": settings.keyscale,
                    "generate_audio_codes": settings.generate_audio_codes,
                    "cfg_scale": settings.cfg_scale,
                    "temperature": settings.temperature,
                    "top_p": settings.top_p,
                    "top_k": settings.top_k,
                    "min_p": settings.min_p,
                },
            }

        save_inputs: dict[str, Any] = {
            "audio": ["6", 0],
            "filename_prefix": settings.filename_prefix,
        }
        save_inputs.update(self._save_audio_inputs(settings))

        negative = _encoder(negative_tags, "")
        # The negative encode never needs the (slow) LLM audio-codes stage.
        negative["inputs"]["generate_audio_codes"] = False

        return {
            # AIO checkpoint: MODEL + CLIP + VAE from one loader
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": settings.checkpoint},
            },
            "2": _encoder(tags, lyrics),
            "3": negative,
            "4": {
                "class_type": "EmptyAceStep1.5LatentAudio",
                # Coupling invariant 1: same source as the encoder's duration.
                "inputs": {"seconds": float(settings.seconds), "batch_size": 1},
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": settings.steps,
                    "cfg": settings.cfg,
                    "sampler_name": settings.sampler,
                    "scheduler": settings.scheduler,
                    "denoise": 1.0,
                },
            },
            "6": {
                "class_type": "VAEDecodeAudio",
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
            },
            "7": {
                "class_type": "SaveAudioAdvanced",
                "inputs": save_inputs,
            },
        }

    def build_separation(
        self,
        audio_ref: str,
        stems: "tuple[str, ...] | list[str]" = SEPARATION_STEMS,
        filename_prefix: str = "audio/stems",
        chunk_fade_shape: str = "linear",
        chunk_length: float = 10.0,
        chunk_overlap: float = 0.1,
    ) -> dict[str, Any]:
        """
        Build a stem-separation workflow (pack: audio-separation-nodes-comfyui).

        Args:
            audio_ref: Name of an audio file already in ComfyUI's input
                folder (see ``ComfyClient.upload_audio()``).
            stems: Which of ``SEPARATION_STEMS`` to save. Output wiring is by
                the pack's documented order (bass, drums, other, vocals) --
                never by slot guess.
            filename_prefix: Prefix for saved stems; the stem name is
                appended (e.g. ``audio/stems_vocals``).
            chunk_fade_shape: linear | half_sine | logarithmic | exponential.
            chunk_length: Segment length in seconds.
            chunk_overlap: Segment overlap in seconds.

        Returns:
            ComfyUI API-format workflow JSON with one flac SaveAudioAdvanced
            terminator per requested stem.
        """
        if not audio_ref:
            raise ValueError("Audio separation requires an input audio file (audio_ref)")

        unknown = [s for s in stems if s not in SEPARATION_STEMS]
        if unknown:
            raise ValueError(f"Unknown stems {unknown}; valid stems are {list(SEPARATION_STEMS)}")

        workflow: dict[str, Any] = {
            "1": {"class_type": "LoadAudio", "inputs": {"audio": audio_ref}},
            "2": {
                "class_type": "AudioSeparation",
                "inputs": {
                    "audio": ["1", 0],
                    "chunk_fade_shape": chunk_fade_shape,
                    "chunk_length": chunk_length,
                    "chunk_overlap": chunk_overlap,
                },
            },
        }

        next_id = 3
        for stem in stems:
            output_index = SEPARATION_STEMS.index(stem)
            inputs: dict[str, Any] = {
                "audio": ["2", output_index],
                "filename_prefix": f"{filename_prefix}_{stem}",
            }
            # Lossless stems: flac, and therefore no quality key at all.
            inputs.update(SAVE_AUDIO_FORMAT.build(AudioFormat.FLAC.value))
            workflow[str(next_id)] = {
                "class_type": "SaveAudioAdvanced",
                "inputs": inputs,
            }
            next_id += 1

        return workflow


_builder: AudioWorkflowBuilder | None = None


def get_audio_builder() -> AudioWorkflowBuilder:
    """Get singleton audio workflow builder."""
    global _builder
    if _builder is None:
        _builder = AudioWorkflowBuilder()
    return _builder


def build_audio_workflow(
    tags: str,
    lyrics: str = "",
    negative_tags: str = "",
    preset: str = "music",
    **overrides: Any,
) -> dict[str, Any]:
    """
    Build a text-to-music workflow with preset settings.

    Simple usage::

        workflow = build_audio_workflow(
            tags="orchestral, epic, battle theme",
            preset="music_long",
        )
    """
    base = AUDIO_PRESETS.get(preset, AUDIO_PRESETS["music"])
    if overrides:
        merged = base.to_dict()
        merged.update(overrides)
        quality = merged.get("quality", base.quality)
        settings = AudioSettings(
            model=AudioModel(merged.get("model", base.model.value)),
            checkpoint=merged.get("checkpoint", base.checkpoint),
            seconds=float(merged.get("seconds", base.seconds)),
            bpm=int(merged.get("bpm", base.bpm)),
            timesignature=str(merged.get("timesignature", base.timesignature)),
            language=merged.get("language", base.language),
            keyscale=merged.get("keyscale", base.keyscale),
            steps=int(merged.get("steps", base.steps)),
            cfg=float(merged.get("cfg", base.cfg)),
            sampler=merged.get("sampler", base.sampler),
            scheduler=merged.get("scheduler", base.scheduler),
            seed=int(merged.get("seed", base.seed)),
            generate_audio_codes=bool(
                merged.get("generate_audio_codes", base.generate_audio_codes)
            ),
            cfg_scale=float(merged.get("cfg_scale", base.cfg_scale)),
            temperature=float(merged.get("temperature", base.temperature)),
            top_p=float(merged.get("top_p", base.top_p)),
            top_k=int(merged.get("top_k", base.top_k)),
            min_p=float(merged.get("min_p", base.min_p)),
            format=AudioFormat(merged.get("format", base.format.value)),
            quality=quality,
            filename_prefix=merged.get("filename_prefix", base.filename_prefix),
        )
    else:
        settings = base

    return get_audio_builder().build(tags, lyrics, negative_tags, settings)


def build_audio_separation_workflow(audio_ref: str, **kwargs: Any) -> dict[str, Any]:
    """Convenience wrapper for :meth:`AudioWorkflowBuilder.build_separation`."""
    return get_audio_builder().build_separation(audio_ref, **kwargs)


def list_audio_presets() -> list[str]:
    """List available audio preset names."""
    return list(AUDIO_PRESETS.keys())
