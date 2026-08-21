# 3D profile

Summary: Image-to-mesh via Hunyuan3D-2, entirely core nodes, exporting GLB through SaveGLB and retrieved like any other output.
Keywords: 3d, mesh, glb, hunyuan3d, voxel, image-to-3d, savegLB

## Surfaces

- `build_3d_workflow(image_ref, preset=..., **overrides)` — presets
  `standard` / `draft` / `detail`.
- `ComfyClient.generate_3d(image, preset=...)` — accepts a local path, raw
  bytes, an upload dict, or a server ref; uploads automatically when needed.
- Registries: `THREE_D_PRESETS`, `THREE_D_MODEL_INFO`.

## The reference chain (validated, all core, zero packs)

```
LoadImage ─→ CLIPVisionEncode(crop=center) ←─ CLIPVisionLoader(clip_vision_g)
                    └→ Hunyuan3Dv2Conditioning → (positive, negative)
ImageOnlyCheckpointLoader(hunyuan3d-dit-v2_fp16) → MODEL, _, VAE
EmptyLatentHunyuan3Dv2(resolution 3072) → KSampler(steps 30, cfg 5.5, euler, simple)
  → VAEDecodeHunyuan3D(num_chunks 8000, octree_resolution 256) → VOXEL
  → VoxelToMesh(algorithm "surface net", threshold 0.6)        → MESH
  → SaveGLB(filename_prefix "3d/ComfyUI")
```

Facts that matter:

- **Pure image-conditioned** — no text prompt anywhere.
  `Hunyuan3Dv2Conditioning` turns one CLIP_VISION_OUTPUT into both positive
  and negative CONDITIONING.
- The VAE comes from the checkpoint loader's slot 2; the vision encoder is a
  **separate** `CLIPVisionLoader(clip_vision_g.safetensors)` (the official
  graph shape).
- `VoxelToMesh → SaveGLB` is the canonical **union-superset edge**: MESH into
  a 14-member `FILE_3D_*` union input. Correct; any validator rejecting it is
  wrong (covered by the corpus gate).
- `SaveGLB` is core, `output_node: true`, outputs `[]`. One node covers
  glb/obj/ply/stl and splat file inputs.

## Retrieval

`SaveGLB` registers in `/history` exactly like SaveImage does for PNGs —
outputs key **`"3d"`** — and the file comes back through
`GET /view?filename=...&type=output` (`ComfyClient.get_file`). No new route.

## Dependency policy

Hunyuan3D-2 (native core) is the ONLY default. TRELLIS.2, TripoSG, Hi3DGen,
PartCrafter, Step1X-3D are wrapper-pack territory, and ComfyUI-3D-Pack is
the least stable dependency in the ecosystem (nvdiffrast /
diff-gaussian-rasterization break across torch/CUDA versions) — deliberately
not emitted.

## Not built (verify before adding)

- Multi-view conditioning: the `-mv` checkpoints exist in the catalog
  (`hunyuan3d-dit-v2-mv_fp16`, `-mv-turbo_fp16`) but the 2mv conditioning
  class name and per-view input keys are UNVERIFIED — verify via the live
  catalog before emitting.
- Texture/PBR bake: a separate second graph that takes the finished mesh —
  not one chain.
