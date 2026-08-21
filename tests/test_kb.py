"""
Tests for the in-repo knowledge base (kb/) and its generator.

The KB's generated half (workflows/*.json, nodes.json, index.json) is
derived from the package registries by scripts/gen_kb.py. These tests are
the freshness gate: if code and KB drift apart, the suite fails and the fix
is one command (python scripts/gen_kb.py).
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = REPO_ROOT / "kb"


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen_kb", REPO_ROOT / "scripts" / "gen_kb.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_kb"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen_kb():
    return _load_generator()


@pytest.fixture(scope="module")
def artifacts(gen_kb):
    return gen_kb.generate()


class TestKBFreshness:
    """The drift gate: kb/ on disk must match regeneration byte-for-byte."""

    def test_generated_files_match_disk(self, artifacts):
        stale = []
        for rel, content in artifacts.items():
            path = KB_DIR / rel
            if not path.exists():
                stale.append(f"missing: kb/{rel}")
            elif path.read_text(encoding="utf-8") != content:
                stale.append(f"stale: kb/{rel}")
        assert not stale, "KB drifted from the code. Run: python scripts/gen_kb.py\n" + "\n".join(
            stale
        )

    def test_no_orphaned_generated_files(self, artifacts):
        on_disk = {p.relative_to(KB_DIR).as_posix() for p in KB_DIR.rglob("*.json") if p.is_file()}
        orphans = sorted(on_disk - set(artifacts))
        assert not orphans, f"orphaned generated files (delete or regenerate): {orphans}"

    def test_generation_is_deterministic(self, gen_kb):
        """Two runs must be byte-identical (pinned seeds, sorted keys)."""
        assert gen_kb.generate() == gen_kb.generate()


@pytest.fixture(scope="module")
def index():
    return json.loads((KB_DIR / "index.json").read_text(encoding="utf-8"))


class TestKBIndex:
    def test_index_carries_version_and_date(self, index):
        import comfy_headless

        assert index["package_version"] == comfy_headless.__version__
        assert index["verified_against_catalog"]
        assert index["how_to_use"]

    def test_every_entry_resolves_to_a_file(self, index):
        for entry in index["entries"]:
            assert (KB_DIR / entry["path"]).is_file(), entry["path"]

    def test_every_entry_is_llm_addressable(self, index):
        """id, kind, profile, title, summary, keywords -- all present."""
        for entry in index["entries"]:
            for field in ("id", "path", "kind", "profile", "title", "summary", "keywords"):
                assert field in entry, f"{entry.get('id')}: missing {field}"
            assert entry["keywords"], f"{entry['id']}: empty keywords"
            assert entry["summary"], f"{entry['id']}: empty summary"

    def test_ids_are_unique(self, index):
        ids = [e["id"] for e in index["entries"]]
        assert len(ids) == len(set(ids))

    def test_all_six_profiles_have_a_guide(self, index):
        guides = {e["profile"] for e in index["entries"] if e["kind"] == "profile-guide"}
        assert {"image", "video", "three_d", "audio", "inference", "metadata"} <= guides

    def test_every_profile_has_workflows(self, index):
        with_workflows = {e["profile"] for e in index["entries"] if e["kind"] == "workflow"}
        # metadata is a utility surface with no graph of its own -- by design.
        assert {"image", "video", "3d", "audio", "inference"} <= with_workflows


class TestKBWorkflows:
    def test_workflow_documents_are_valid_and_annotated(self):
        from comfy_headless.node_packs import required_node_packs

        paths = sorted((KB_DIR / "workflows").glob("*.json"))
        assert len(paths) >= 20
        for path in paths:
            doc = json.loads(path.read_text(encoding="utf-8"))
            for field in (
                "id",
                "profile",
                "title",
                "python_entrypoint",
                "class_types",
                "required_packs",
                "history_output_keys",
                "graph",
                "notes",
                "verified_against_catalog",
            ):
                assert field in doc, f"{path.name}: missing {field}"
            graph = doc["graph"]
            assert graph, path.name
            # class_types annotation matches the graph
            assert doc["class_types"] == sorted({n["class_type"] for n in graph.values()}), (
                path.name
            )
            # pack annotation matches the registry
            assert doc["required_packs"] == required_node_packs(graph), path.name
            # every link resolves
            ids = set(graph)
            for node in graph.values():
                for value in node.get("inputs", {}).values():
                    if isinstance(value, list) and len(value) == 2:
                        assert str(value[0]) in ids, path.name

    def test_workflow_graphs_pass_the_output_node_guard(self):
        from comfy_headless.addressing import has_output_node

        for path in (KB_DIR / "workflows").glob("*.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            assert has_output_node(doc["graph"]), path.name

    def test_placeholders_are_declared(self):
        """Any placeholder token in a graph must be explained in the doc."""
        for path in (KB_DIR / "workflows").glob("*.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            raw = json.dumps(doc["graph"])
            for token in ("INPUT_IMAGE_REF.png", "INPUT_AUDIO_REF.flac"):
                if token in raw:
                    assert token in doc["placeholders"], f"{path.name}: {token}"


class TestKBNodeFacts:
    def test_nodes_json_mirrors_registries(self):
        from comfy_headless.addressing import HISTORY_OUTPUT_KEYS
        from comfy_headless.node_packs import NODE_PACK_INFO, NODE_PACKS

        doc = json.loads((KB_DIR / "nodes.json").read_text(encoding="utf-8"))
        assert doc["pack_nodes"] == dict(sorted(NODE_PACKS.items()))
        assert set(doc["packs"]) == set(NODE_PACK_INFO)
        assert doc["history_output_keys"] == {
            k: list(v) for k, v in sorted(HISTORY_OUTPUT_KEYS.items())
        }
