#!/usr/bin/env python
"""
Knowledge-base generator for comfy-headless.

Regenerates the machine-derived half of kb/ from the installed package, so
the KB can never drift from the code:

* ``kb/workflows/*.json`` -- one reference graph per named workflow shape,
  built by the actual profile builders with a pinned seed (deterministic,
  byte-stable across runs).
* ``kb/nodes.json``       -- node provenance (core vs pack), pack metadata,
  and the /history retrieval contract, straight from the package registries.
* ``kb/index.json``       -- THE INDEX: every KB entry (generated workflow
  JSONs + curated Markdown pages found on disk) with kind, profile, summary
  and keywords, designed to be the first file an LLM reads.

Usage:
    python scripts/gen_kb.py           # regenerate in place
    python scripts/gen_kb.py --check   # exit 1 if regeneration would change
                                       # anything (CI/test freshness gate)

Curated pages (kb/profiles/*.md, kb/*.md) are hand-authored and only
*indexed* here, never rewritten. Their index summary comes from the page's
"Summary:" line and keywords from its "Keywords:" line.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

KB_DIR = REPO_ROOT / "kb"
WORKFLOWS_DIR = KB_DIR / "workflows"

# The catalog-verification date carried by every generated artifact. Bump it
# when the emitted node set is re-verified against a live /object_info.
VERIFIED_DATE = "2026-08-21"

# Deterministic seed for generated reference graphs: regeneration must be
# byte-identical, and builders resolve seed=-1 to a random value.
KB_SEED = 0

_REF_IMAGE = "INPUT_IMAGE_REF.png"
_REF_AUDIO = "INPUT_AUDIO_REF.flac"

_PLACEHOLDERS = {
    _REF_IMAGE: "server-side image name from ComfyClient.upload_image()['ref']",
    _REF_AUDIO: "server-side audio name from ComfyClient.upload_audio()['ref']",
}


def _workflow_specs() -> list[dict[str, Any]]:
    """Every named reference graph, built by the real profile builders."""
    from comfy_headless.audio import (
        AUDIO_PRESETS,
        build_audio_separation_workflow,
        build_audio_workflow,
    )
    from comfy_headless.inference import InferenceTask, build_inference_workflow
    from comfy_headless.three_d import THREE_D_PRESETS, build_3d_workflow
    from comfy_headless.video import build_video_workflow
    from comfy_headless.workflows import (
        build_controlnet_workflow,
        build_qwen_edit_workflow,
        compile_workflow,
    )

    specs: list[dict[str, Any]] = []

    for preset in THREE_D_PRESETS:
        specs.append(
            {
                "id": f"3d_hunyuan3d_v2_{preset}",
                "profile": "3d",
                "title": f"Hunyuan3D-2 image-to-mesh ({preset})",
                "entrypoint": f"build_3d_workflow(image_ref, preset={preset!r})",
                "client_method": "ComfyClient.generate_3d(image, preset=...)",
                "keywords": ["3d", "mesh", "glb", "hunyuan3d", "image-to-3d", preset],
                "graph": build_3d_workflow(_REF_IMAGE, preset=preset, seed=KB_SEED),
                "notes": [
                    "Pure image-conditioned: no text prompt anywhere in the graph.",
                    "MESH feeds SaveGLB's FILE_3D_* union input (union-superset edge).",
                    "Fetch the GLB from /history outputs key '3d' via GET /view.",
                ],
            }
        )

    for preset in AUDIO_PRESETS:
        specs.append(
            {
                "id": f"audio_ace_step_15_{preset}",
                "profile": "audio",
                "title": f"ACE-Step 1.5 text-to-music ({preset})",
                "entrypoint": f"build_audio_workflow(tags, preset={preset!r})",
                "client_method": "ComfyClient.generate_audio(tags, ...)",
                "keywords": ["audio", "music", "ace-step", "text-to-music", preset],
                "graph": build_audio_workflow("PROMPT_TAGS", preset=preset, seed=KB_SEED),
                "notes": [
                    "Encoder 'duration' and latent 'seconds' are ONE parameter, "
                    "driven from AudioSettings.seconds -- never set separately.",
                    "SaveAudioAdvanced is the only non-deprecated audio terminator; "
                    "flac emits no format.quality key at all.",
                    "Fetch audio from /history outputs key 'audio' via GET /view.",
                ],
            }
        )

    specs.append(
        {
            "id": "audio_separation_stems",
            "profile": "audio",
            "title": "Stem separation (bass / drums / other / vocals)",
            "entrypoint": "build_audio_separation_workflow(audio_ref)",
            "client_method": "ComfyClient.separate_audio(audio)",
            "keywords": ["audio", "stems", "separation", "vocals", "demucs-style"],
            "graph": build_audio_separation_workflow(_REF_AUDIO),
            "notes": [
                "AudioSeparation is pack audio-separation-nodes-comfyui, NOT core.",
                "Outputs are wired by the pack's documented order "
                "(bass, drums, other, vocals) -- never by slot guess.",
            ],
        }
    )

    for task in InferenceTask:
        specs.append(
            {
                "id": f"inference_florence2_{task.value}",
                "profile": "inference",
                "title": f"Florence-2 {task.value}",
                "entrypoint": (
                    f"build_inference_workflow(image_ref, task={task.value!r}"
                    + (", text_input=...)" if task.value in ("detect", "segment") else ")")
                ),
                "client_method": "ComfyClient.run_inference(image, task=...)",
                "keywords": ["inference", "florence2", task.value, "vision"],
                "graph": build_inference_workflow(
                    _REF_IMAGE, task=task.value, text_input="QUERY_TEXT"
                ),
                "notes": [
                    "Results reach /history ONLY through an OUTPUT_NODE terminator; "
                    "SaveText reports inline text under 'text' plus the file under 'files'.",
                ],
            }
        )

    compiled = compile_workflow(
        prompt="PROMPT_TEXT", template_id="qwen_txt2img", preset="", seed=KB_SEED
    )
    specs.append(
        {
            "id": "image_qwen_txt2img_2512",
            "profile": "image",
            "title": "Qwen-Image-2512 text-to-image",
            "entrypoint": "compile_workflow(prompt, template_id='qwen_txt2img')",
            "client_method": "ComfyClient.queue_prompt(compiled.workflow)",
            "keywords": ["image", "qwen", "txt2img", "dit", "unetloader"],
            "graph": compiled.workflow,
            "notes": [
                "Qwen loads via UNETLoader (diffusion_models), NOT CheckpointLoaderSimple.",
                "Latent is EmptySD3LatentImage (16-channel); EmptyLatentImage is garbage here.",
                "Defaults: steps 20, cfg 2.5 (not 7.0), shift 3.1, 1328x1328.",
            ],
        }
    )
    specs.append(
        {
            "id": "image_qwen_edit_2511",
            "profile": "image",
            "title": "Qwen-Image-Edit-2511 instruction edit (2 references)",
            "entrypoint": "build_qwen_edit_workflow(prompt, image_refs)",
            "client_method": "ComfyClient.edit_image(prompt, images)",
            "keywords": ["image", "qwen", "edit", "reference", "instruction"],
            "graph": build_qwen_edit_workflow(
                "EDIT_INSTRUCTION", [_REF_IMAGE, _REF_IMAGE], seed=KB_SEED
            ),
            "notes": [
                "References enter TextEncodeQwenImageEditPlus as discrete "
                "image1..image3 inputs (max 3), NOT a batched list.",
                "References do NOT pass through VAEEncode; the VAE wires into "
                "the encoder's own vae input.",
            ],
        }
    )
    for base in ("qwen", "sdxl"):
        specs.append(
            {
                "id": f"image_controlnet_union_{base}",
                "profile": "image",
                "title": f"Union ControlNet on {base}",
                "entrypoint": f"build_controlnet_workflow(prompt, control_image_ref, base={base!r})",
                "client_method": "ComfyClient.queue_prompt(workflow)",
                "keywords": ["image", "controlnet", "union", base, "depth", "canny"],
                "graph": build_controlnet_workflow(
                    "PROMPT_TEXT", _REF_IMAGE, base=base, control_type="depth", seed=KB_SEED
                ),
                "notes": [
                    "SetUnionControlNetType enum values are verbatim literals; "
                    "slash-grouped entries like 'canny/lineart/anime_lineart/mlsd' "
                    "are SINGLE choices.",
                    "Only the core Canny preprocessor is emitted; other hint types "
                    "expect a pre-made control image (aux pack not emitted).",
                ],
            }
        )

    for preset, extra in (
        ("standard", {}),
        ("hunyuan15_720p", {}),
        ("hunyuan15_i2v", {"init_image": _REF_IMAGE}),
        ("ltx_standard", {}),
        ("wan_14b", {}),
        ("mochi", {}),
    ):
        specs.append(
            {
                "id": f"video_{preset}",
                "profile": "video",
                "title": f"Video preset {preset}",
                "entrypoint": f"build_video_workflow(prompt, preset={preset!r})",
                "client_method": "ComfyClient.generate_video(prompt, preset=...)",
                "keywords": ["video", preset.split("_")[0], preset],
                "graph": build_video_workflow(
                    prompt="PROMPT_TEXT",
                    negative="NEGATIVE_TEXT",
                    preset=preset,
                    seed=KB_SEED,
                    **extra,
                ),
                "notes": [
                    "LTXV keeps its LTXVScheduler -> KSamplerSelect -> SamplerCustom "
                    "leg; a plain KSampler would silently drop the SIGMAS config."
                    if preset.startswith("ltx")
                    else "VHS_VideoCombine is the default terminator; "
                    "VideoSettings(output='core') swaps in CreateVideo -> SaveVideo.",
                ],
            }
        )

    # A core-terminator variant, showing the dotted dynamic-combo emission.
    specs.append(
        {
            "id": "video_standard_core_output",
            "profile": "video",
            "title": "Video with core CreateVideo -> SaveVideo terminator",
            "entrypoint": "build_video_workflow(prompt, preset='standard', output='core')",
            "client_method": "ComfyClient.generate_video(prompt, preset='standard')",
            "keywords": ["video", "savevideo", "core", "no-pack", "dynamic-combo"],
            "graph": build_video_workflow(
                prompt="PROMPT_TEXT",
                negative="NEGATIVE_TEXT",
                preset="standard",
                seed=KB_SEED,
                output="core",
            ),
            "notes": [
                "Drops the comfyui-videohelpersuite dependency.",
                "SaveVideo output registers in /history under 'images' with an "
                "'animated' flag, not under 'gifs'.",
            ],
        }
    )

    return specs


def _workflow_document(spec: dict[str, Any]) -> dict[str, Any]:
    from comfy_headless.addressing import HISTORY_OUTPUT_KEYS
    from comfy_headless.node_packs import required_node_packs

    graph = spec["graph"]
    class_types = sorted({n["class_type"] for n in graph.values()})
    output_keys = sorted({key for ct in class_types for key in HISTORY_OUTPUT_KEYS.get(ct, ())})
    used_placeholders = {
        token: meaning
        for token, meaning in _PLACEHOLDERS.items()
        if any(token in json.dumps(node) for node in graph.values())
    }
    return {
        "id": spec["id"],
        "profile": spec["profile"],
        "title": spec["title"],
        "verified_against_catalog": VERIFIED_DATE,
        "python_entrypoint": f"comfy_headless.{spec['entrypoint']}",
        "client_method": spec["client_method"],
        "class_types": class_types,
        "required_packs": required_node_packs(graph),
        "history_output_keys": output_keys,
        "placeholders": used_placeholders,
        "notes": spec["notes"],
        "graph": graph,
    }


def _nodes_document() -> dict[str, Any]:
    from comfy_headless.addressing import (
        HISTORY_OUTPUT_KEYS,
        KNOWN_OUTPUT_NODE_CLASSES,
    )
    from comfy_headless.node_packs import NODE_PACK_INFO, NODE_PACKS

    return {
        "verified_against_catalog": VERIFIED_DATE,
        "how_to_read": (
            "pack_nodes maps every NON-core class_type comfy-headless can emit "
            "to the custom node pack that provides it; anything a builder emits "
            "that is not listed here is a verified ComfyUI core node. "
            "history_output_keys is the retrieval contract: after a run, "
            "history['outputs'][node_id][key] holds the results for that "
            "terminator class."
        ),
        "pack_nodes": dict(sorted(NODE_PACKS.items())),
        "packs": {pid: pack.to_dict() for pid, pack in sorted(NODE_PACK_INFO.items())},
        "output_node_classes": sorted(KNOWN_OUTPUT_NODE_CLASSES),
        "history_output_keys": {k: list(v) for k, v in sorted(HISTORY_OUTPUT_KEYS.items())},
    }


_SUMMARY_RE = re.compile(r"^Summary:\s*(.+)$", re.MULTILINE)
_KEYWORDS_RE = re.compile(r"^Keywords:\s*(.+)$", re.MULTILINE)
_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _index_curated_pages() -> list[dict[str, Any]]:
    """Index every curated Markdown page under kb/ (never rewrites them)."""
    entries = []
    for path in sorted(KB_DIR.rglob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        title = _TITLE_RE.search(text)
        summary = _SUMMARY_RE.search(text)
        keywords = _KEYWORDS_RE.search(text)
        rel = path.relative_to(KB_DIR).as_posix()
        profile = path.stem if path.parent.name == "profiles" else "cross-cutting"
        entries.append(
            {
                "id": f"page-{path.stem}" if profile == "cross-cutting" else f"profile-{path.stem}",
                "path": rel,
                "kind": "profile-guide" if profile != "cross-cutting" else "knowledge-page",
                "profile": profile,
                "title": title.group(1).strip() if title else path.stem,
                "summary": summary.group(1).strip() if summary else "",
                "keywords": ([k.strip() for k in keywords.group(1).split(",")] if keywords else []),
            }
        )
    return entries


def generate() -> dict[str, str]:
    """Build every generated artifact; returns {relative_path: content}."""
    import comfy_headless

    artifacts: dict[str, str] = {}

    workflow_entries = []
    for spec in _workflow_specs():
        doc = _workflow_document(spec)
        rel = f"workflows/{doc['id']}.json"
        artifacts[rel] = json.dumps(doc, indent=2, sort_keys=True) + "\n"
        workflow_entries.append(
            {
                "id": f"wf-{doc['id']}",
                "path": rel,
                "kind": "workflow",
                "profile": doc["profile"],
                "title": doc["title"],
                "summary": doc["notes"][0] if doc["notes"] else "",
                "keywords": spec["keywords"],
                "python_entrypoint": doc["python_entrypoint"],
                "required_packs": sorted(doc["required_packs"]),
            }
        )

    artifacts["nodes.json"] = json.dumps(_nodes_document(), indent=2, sort_keys=True) + "\n"

    index = {
        "kb_version": 1,
        "package": "comfy-headless",
        "package_version": comfy_headless.__version__,
        "verified_against_catalog": VERIFIED_DATE,
        "generated_by": "scripts/gen_kb.py (do not hand-edit generated entries)",
        "how_to_use": (
            "This index is the entry point for the comfy-headless knowledge "
            "base. Pick entries by 'profile' (image, video, 3d, audio, "
            "inference, metadata) and 'kind': 'profile-guide' pages carry the "
            "verified facts and traps for one profile; 'workflow' entries are "
            "runnable API-format reference graphs with placeholder inputs "
            "(see each file's 'placeholders'); 'knowledge-page' entries are "
            "cross-cutting (addressing/typing rules, retrieval contract, "
            "traps); 'node-facts' is the machine-readable pack/provenance "
            "registry. Read the profile guide before editing a graph; every "
            "class_type in these graphs was verified against the live "
            "ComfyUI catalog on the date above."
        ),
        "entries": [
            {
                "id": "node-facts",
                "path": "nodes.json",
                "kind": "node-facts",
                "profile": "cross-cutting",
                "title": "Node provenance and retrieval contract",
                "summary": (
                    "Machine-readable: pack membership for every non-core "
                    "class_type, pack install metadata, output-node classes, "
                    "and /history output keys per terminator."
                ),
                "keywords": ["nodes", "packs", "provenance", "history", "retrieval"],
            },
            *_index_curated_pages(),
            *workflow_entries,
        ],
    }
    artifacts["index.json"] = json.dumps(index, indent=2, sort_keys=True) + "\n"
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the KB on disk matches regeneration (freshness gate)",
    )
    args = parser.parse_args()

    artifacts = generate()

    if args.check:
        stale = []
        for rel, content in artifacts.items():
            path = KB_DIR / rel
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(rel)
        expected_json = set(artifacts)
        on_disk_json = {
            p.relative_to(KB_DIR).as_posix() for p in KB_DIR.rglob("*.json") if p.is_file()
        }
        orphans = sorted(on_disk_json - expected_json)
        if stale or orphans:
            print("KB is stale. Regenerate with: python scripts/gen_kb.py")
            for rel in stale:
                print(f"  stale/missing: kb/{rel}")
            for rel in orphans:
                print(f"  orphaned:      kb/{rel}")
            return 1
        print(f"KB is fresh ({len(artifacts)} generated artifacts).")
        return 0

    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    for rel, content in artifacts.items():
        path = KB_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {len(artifacts)} generated artifacts under kb/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
