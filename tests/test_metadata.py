"""Tests for comfy_headless/metadata.py -- the provenance profile."""

import json
import struct
import zlib

import pytest

from comfy_headless.exceptions import ValidationError
from comfy_headless.metadata import (
    PNG_SIGNATURE,
    ProvenanceRecord,
    extract_prompt_graph,
    read_png_text_chunks,
    read_workflow_metadata,
)

# =============================================================================
# Synthetic PNG construction (stdlib only, mirrors what PIL/ComfyUI write)
# =============================================================================


def _chunk(ctype: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + ctype
        + payload
        + struct.pack(">I", zlib.crc32(ctype + payload) & 0xFFFFFFFF)
    )


def _text_chunk(keyword: str, text: str) -> bytes:
    return _chunk(b"tEXt", keyword.encode("latin-1") + b"\x00" + text.encode("latin-1"))


def _ztxt_chunk(keyword: str, text: str) -> bytes:
    return _chunk(
        b"zTXt",
        keyword.encode("latin-1") + b"\x00" + b"\x00" + zlib.compress(text.encode("latin-1")),
    )


def _itxt_chunk(keyword: str, text: str, compressed: bool = False) -> bytes:
    body = text.encode("utf-8")
    if compressed:
        body = zlib.compress(body)
    payload = (
        keyword.encode("latin-1")
        + b"\x00"
        + (b"\x01" if compressed else b"\x00")
        + b"\x00"  # compression method
        + b"\x00"  # empty language tag
        + b"\x00"  # empty translated keyword
        + body
    )
    return _chunk(b"iTXt", payload)


def _minimal_png(*chunks: bytes) -> bytes:
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    idat = _chunk(b"IDAT", zlib.compress(b"\x00\x00"))
    iend = _chunk(b"IEND", b"")
    return PNG_SIGNATURE + ihdr + b"".join(chunks) + idat + iend


SAMPLE_GRAPH = {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "m.safetensors"}},
    "2": {"class_type": "KSampler", "inputs": {"seed": 42, "model": ["1", 0]}},
}


class TestReadPngTextChunks:
    def test_text_chunk(self):
        png = _minimal_png(_text_chunk("prompt", "hello"))
        assert read_png_text_chunks(png) == {"prompt": "hello"}

    def test_ztxt_chunk(self):
        png = _minimal_png(_ztxt_chunk("workflow", "compressed data"))
        assert read_png_text_chunks(png) == {"workflow": "compressed data"}

    def test_itxt_chunk_plain_and_compressed(self):
        png = _minimal_png(
            _itxt_chunk("a", "unicode éè"),
            _itxt_chunk("b", "compressed unicode ✓", compressed=True),
        )
        chunks = read_png_text_chunks(png)
        assert chunks["a"] == "unicode éè"
        assert chunks["b"] == "compressed unicode ✓"

    def test_multiple_chunks(self):
        png = _minimal_png(
            _text_chunk("prompt", "{}"),
            _text_chunk("workflow", "{}"),
            _text_chunk("myapp:run_id", "abc-123"),
        )
        assert set(read_png_text_chunks(png)) == {"prompt", "workflow", "myapp:run_id"}

    def test_no_text_chunks(self):
        assert read_png_text_chunks(_minimal_png()) == {}

    def test_non_png_rejected_with_format_name(self):
        with pytest.raises(ValidationError) as excinfo:
            read_png_text_chunks(b"\xff\xd8\xff\xe0 jpeg-ish")
        assert "jpeg" in str(excinfo.value)

    def test_webp_named_in_rejection(self):
        webp = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 8
        with pytest.raises(ValidationError) as excinfo:
            read_png_text_chunks(webp)
        assert "webp" in str(excinfo.value)

    def test_truncated_chunk_does_not_crash(self):
        png = _minimal_png(_text_chunk("prompt", "ok"))
        # Chop mid-way through the IDAT chunk.
        assert read_png_text_chunks(png[:-8]).get("prompt") == "ok"

    def test_malformed_ztxt_skipped(self):
        bad = _chunk(b"zTXt", b"key\x00\x00not-zlib-data")
        png = _minimal_png(bad, _text_chunk("good", "still read"))
        assert read_png_text_chunks(png) == {"good": "still read"}

    def test_reads_from_file_path(self, tmp_path):
        path = tmp_path / "out.png"
        path.write_bytes(_minimal_png(_text_chunk("prompt", "from disk")))
        assert read_png_text_chunks(path)["prompt"] == "from disk"
        assert read_png_text_chunks(str(path))["prompt"] == "from disk"


class TestReadWorkflowMetadata:
    def test_parses_prompt_and_workflow(self):
        gui = {"nodes": [], "links": []}
        png = _minimal_png(
            _text_chunk("prompt", json.dumps(SAMPLE_GRAPH)),
            _text_chunk("workflow", json.dumps(gui)),
        )
        record = read_workflow_metadata(png)
        assert record.prompt == SAMPLE_GRAPH
        assert record.workflow == gui
        assert record.has_prompt is True
        assert record.extra == {}

    def test_custom_extra_pnginfo_keys_land_in_extra(self):
        png = _minimal_png(
            _text_chunk("prompt", json.dumps(SAMPLE_GRAPH)),
            _text_chunk("myapp:batch", "batch-77"),
        )
        record = read_workflow_metadata(png)
        assert record.extra["myapp:batch"] == "batch-77"

    def test_unparseable_prompt_kept_raw(self):
        png = _minimal_png(_text_chunk("prompt", "{not json"))
        record = read_workflow_metadata(png)
        assert record.prompt is None
        assert record.extra["prompt"] == "{not json"

    def test_empty_record(self):
        record = read_workflow_metadata(_minimal_png())
        assert record == ProvenanceRecord()
        assert record.has_prompt is False


class TestExtractPromptGraph:
    def test_round_trip(self):
        """The capability the profile exists for: PNG -> re-POSTable graph."""
        png = _minimal_png(_text_chunk("prompt", json.dumps(SAMPLE_GRAPH)))
        assert extract_prompt_graph(png) == SAMPLE_GRAPH

    def test_zip_compressed_round_trip(self):
        png = _minimal_png(_ztxt_chunk("prompt", json.dumps(SAMPLE_GRAPH)))
        assert extract_prompt_graph(png) == SAMPLE_GRAPH

    def test_missing_prompt_is_typed_error(self):
        png = _minimal_png(_text_chunk("workflow", json.dumps({"nodes": []})))
        with pytest.raises(ValidationError) as excinfo:
            extract_prompt_graph(png)
        # The error must steer callers away from the GUI chunk trap.
        assert "prompt" in str(excinfo.value)

    def test_scrubbed_png_is_typed_error(self):
        with pytest.raises(ValidationError):
            extract_prompt_graph(_minimal_png())


class TestClientQueuePayload:
    def test_extra_pnginfo_lands_in_extra_data(self):
        """The /prompt payload key verified against execution.py."""
        from unittest.mock import MagicMock, patch

        from comfy_headless.client import ComfyClient

        client = ComfyClient.__new__(ComfyClient)
        client.client_id = "test-client"
        response = MagicMock()
        response.ok = True
        response.json.return_value = {"prompt_id": "p-1"}
        response.headers = {"content-type": "application/json"}
        response.text = json.dumps({"prompt_id": "p-1"})
        with patch.object(ComfyClient, "_post", return_value=response) as post:
            prompt_id = client.queue_prompt(
                {"1": {"class_type": "SaveImage", "inputs": {}}},
                extra_pnginfo={"myapp:run": "r-9"},
            )
        assert prompt_id == "p-1"
        payload = post.call_args.kwargs["json"]
        assert payload["extra_data"] == {"extra_pnginfo": {"myapp:run": "r-9"}}

    def test_no_extra_data_key_without_extra_pnginfo(self):
        from unittest.mock import MagicMock, patch

        from comfy_headless.client import ComfyClient

        client = ComfyClient.__new__(ComfyClient)
        client.client_id = "test-client"
        response = MagicMock()
        response.ok = True
        response.json.return_value = {"prompt_id": "p-2"}
        response.headers = {"content-type": "application/json"}
        response.text = json.dumps({"prompt_id": "p-2"})
        with patch.object(ComfyClient, "_post", return_value=response) as post:
            client.queue_prompt({"1": {"class_type": "SaveImage", "inputs": {}}})
        assert "extra_data" not in post.call_args.kwargs["json"]
