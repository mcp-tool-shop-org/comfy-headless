# comfy-headless Knowledge Base

Summary: Entry point for the in-repo KB — read index.json first, then the profile guide for the surface you are touching.
Keywords: knowledge-base, index, llm, workflows, profiles

This directory is the repo's knowledge base: everything an LLM (or a human)
needs to drive, extend, or debug comfy-headless without re-deriving facts
that were already verified against the live ComfyUI catalog.

## How to use it (LLM reading order)

1. **`index.json`** — the machine-readable index. Every KB entry with its
   `kind`, `profile`, `summary`, and `keywords`. Start here; pick entries by
   profile.
2. **`profiles/<profile>.md`** — the verified facts, defaults, and traps for
   one profile (image, video, three_d, audio, inference, metadata).
3. **`workflows/<id>.json`** — runnable API-format reference graphs, built by
   the package's own builders. Each carries `python_entrypoint`,
   `required_packs`, `history_output_keys`, `placeholders` (tokens to replace
   with real uploaded refs), and the `graph` itself.
4. **`nodes.json`** — node provenance: which emitted class_types come from
   custom packs (everything else is verified core), pack install metadata,
   and the /history retrieval contract per terminator.
5. **Cross-cutting pages** — `addressing.md` (type matching, dotted fields,
   presence-aware combos), `retrieval.md` (how results come back),
   `traps.md` (mistakes that already cost time; do not rediscover them).

## Generated vs curated

`workflows/*.json`, `nodes.json`, and `index.json` are **generated** by
`scripts/gen_kb.py` from the package registries — never hand-edit them;
regenerate with:

```bash
python scripts/gen_kb.py
```

`tests/test_kb.py` gates freshness: if code and KB drift apart, the suite
fails. The Markdown pages (this file, `profiles/`, the cross-cutting pages)
are **curated** — edit them directly; the generator only indexes them (it
reads each page's `# title`, `Summary:` and `Keywords:` lines).

## Trust model

Every `class_type` in every reference graph was verified present in the live
ComfyUI catalog on the date stamped in `index.json`
(`verified_against_catalog`). Facts older than that date are advisory until
re-verified — the same freshness rule the profile code follows. When a graph
here disagrees with a live `/object_info`, the live server wins; update the
code first, then regenerate the KB.
