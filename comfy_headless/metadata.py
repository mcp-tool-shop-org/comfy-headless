"""
Comfy Headless - Metadata / Provenance Module
=============================================

v3.1.0: the metadata profile. Provenance round-trip -- no graph of its own,
a read/write utility surface.

On write, ComfyUI's ``SaveImage`` embeds PNG **tEXt chunks** (not EXIF),
two keys by default:

* ``prompt`` -- the API-format graph (the exact ``/prompt`` payload).
  Machine-runnable.
* ``workflow`` -- the GUI/litegraph format (for the canvas).

The API-format graph is therefore recoverable from any output PNG,
independently of the GUI chunk: read the ``prompt`` chunk and re-POST it
verbatim (``ComfyClient.rerun_from_png``). Custom provenance goes in via
``extra_pnginfo`` on the ``/prompt`` submission -- anything in that dict is
serialized as an extra text chunk by the save nodes, no custom node needed
(``ComfyClient.queue_prompt(workflow, extra_pnginfo={...})``).

Everything here is pure stdlib (struct + zlib): no Pillow dependency. All
three PNG text chunk flavors are parsed -- ``tEXt`` (latin-1), ``zTXt``
(zlib-compressed latin-1) and ``iTXt`` (UTF-8, optionally compressed).

Caveats (by design, documented rather than papered over):

* WebP/JPEG outputs carry the same data in EXIF, a different reader path
  that this module does not implement -- a clear error names the format.
* ``SaveVideo`` / ``VHS_VideoCombine`` do not embed the graph in a PNG chunk;
  provenance dies on video outputs unless carried externally.
* Some hardened deployments strip unknown ``extra_pnginfo`` keys --
  round-trip test against the real target before relying on custom keys.
* GUI(litegraph) -> API conversion has NO server route (``graphToPrompt`` is
  client-side TypeScript). The supported answer is ComfyUI's
  "Workflow -> Export (API)"; this module reads the result of that or the
  ``prompt`` chunk, and does not attempt a best-effort converter.
"""

import json
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .exceptions import ValidationError
from .logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    "PNG_SIGNATURE",
    "ProvenanceRecord",
    "read_png_text_chunks",
    "read_workflow_metadata",
    "extract_prompt_graph",
]

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Cap for a single decompressed text chunk. ComfyUI graphs are tens of KB;
# anything beyond this is malformed or hostile (zip bomb), not provenance.
_MAX_DECOMPRESSED_CHUNK = 64 * 1024 * 1024


@dataclass
class ProvenanceRecord:
    """Parsed provenance from a ComfyUI output image."""

    # The API-format graph from the "prompt" chunk -- re-POSTable verbatim.
    prompt: dict[str, Any] | None = None
    # The GUI/litegraph-format graph from the "workflow" chunk.
    workflow: dict[str, Any] | None = None
    # Every other text chunk (including custom extra_pnginfo keys), raw.
    # Also holds the raw string for prompt/workflow chunks that failed to
    # parse as JSON.
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def has_prompt(self) -> bool:
        return self.prompt is not None


def _read_source(source: "str | Path | bytes | bytearray | memoryview") -> bytes:
    if isinstance(source, (bytes, bytearray, memoryview)):
        return bytes(source)
    return Path(source).read_bytes()


def _sniff_format(data: bytes) -> str:
    if data.startswith(PNG_SIGNATURE):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def _decompress_capped(payload: bytes) -> bytes:
    """zlib-decompress with a hard output cap (zip-bomb guard)."""
    d = zlib.decompressobj()
    out = d.decompress(payload, _MAX_DECOMPRESSED_CHUNK)
    if d.unconsumed_tail:
        raise ValueError("decompressed text chunk exceeds the size cap")
    return out


def read_png_text_chunks(source: "str | Path | bytes | bytearray | memoryview") -> dict[str, str]:
    """
    Read every PNG text chunk (tEXt, zTXt, iTXt) as ``{keyword: text}``.

    Malformed individual chunks are skipped with a debug log rather than
    failing the whole read -- provenance parsing must tolerate drift.

    Raises:
        ValidationError: If the source is not a PNG. WebP/JPEG carry the
            same data in EXIF -- a different reader path this module does
            not implement -- and the error says so.
    """
    data = _read_source(source)
    fmt = _sniff_format(data)
    if fmt != "png":
        raise ValidationError(
            f"Provenance reading supports PNG only; got {fmt}",
            details={"detected_format": fmt},
            suggestions=[
                "ComfyUI embeds the graph in PNG tEXt chunks",
                "WebP/JPEG outputs put the same data in EXIF (not implemented here)",
            ],
        )

    chunks: dict[str, str] = {}
    offset = len(PNG_SIGNATURE)
    size = len(data)

    while offset + 8 <= size:
        (length,) = struct.unpack(">I", data[offset : offset + 4])
        ctype = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        if payload_end + 4 > size:
            logger.debug("Truncated PNG chunk %r; stopping", ctype)
            break
        payload = data[payload_start:payload_end]
        offset = payload_end + 4  # skip CRC; provenance reads don't verify it

        try:
            if ctype == b"tEXt":
                keyword, _, text = payload.partition(b"\x00")
                chunks[keyword.decode("latin-1")] = text.decode("latin-1")
            elif ctype == b"zTXt":
                keyword, _, rest = payload.partition(b"\x00")
                if not rest:
                    continue
                method, compressed = rest[0], rest[1:]
                if method != 0:
                    continue
                chunks[keyword.decode("latin-1")] = _decompress_capped(compressed).decode("latin-1")
            elif ctype == b"iTXt":
                keyword, _, rest = payload.partition(b"\x00")
                if len(rest) < 2:
                    continue
                compression_flag, compression_method = rest[0], rest[1]
                rest = rest[2:]
                _language, _, rest = rest.partition(b"\x00")
                _translated, _, text = rest.partition(b"\x00")
                if compression_flag == 1:
                    if compression_method != 0:
                        continue
                    text = _decompress_capped(text)
                chunks[keyword.decode("latin-1")] = text.decode("utf-8")
            elif ctype == b"IEND":
                break
        except Exception as e:  # malformed chunk: skip, don't fail the read
            logger.debug("Skipping malformed PNG %r chunk: %s", ctype, e)

    return chunks


def read_workflow_metadata(
    source: "str | Path | bytes | bytearray | memoryview",
) -> ProvenanceRecord:
    """
    Parse ComfyUI provenance out of an output PNG.

    Returns a :class:`ProvenanceRecord` with the API-format graph
    (``prompt``), the GUI-format graph (``workflow``) and every other text
    chunk raw (``extra`` -- where custom ``extra_pnginfo`` keys land).
    """
    chunks = read_png_text_chunks(source)
    record = ProvenanceRecord()
    for keyword, text in chunks.items():
        if keyword in ("prompt", "workflow"):
            try:
                parsed = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                logger.debug("PNG %r chunk is not valid JSON; keeping raw", keyword)
                record.extra[keyword] = text
                continue
            if keyword == "prompt" and isinstance(parsed, dict):
                record.prompt = parsed
            elif keyword == "workflow" and isinstance(parsed, dict):
                record.workflow = parsed
            else:
                record.extra[keyword] = text
        else:
            record.extra[keyword] = text
    return record


def extract_prompt_graph(
    source: "str | Path | bytes | bytearray | memoryview",
) -> dict[str, Any]:
    """
    Recover the machine-runnable API-format graph from an output PNG.

    This is the real capability the metadata profile exists for: the exact
    ``/prompt`` payload that produced an image is embedded in it and can be
    re-POSTed verbatim (see ``ComfyClient.rerun_from_png``).

    Raises:
        ValidationError: If the PNG carries no parseable ``prompt`` chunk
            (e.g. the server ran with ``--disable-metadata``, or the file
            was scrubbed in transit).
    """
    record = read_workflow_metadata(source)
    if record.prompt is None:
        raise ValidationError(
            "No API-format 'prompt' graph found in the PNG",
            details={
                "chunks_found": sorted(record.extra)
                + (["workflow"] if record.workflow is not None else [])
            },
            suggestions=[
                "The server may run with --disable-metadata",
                "Metadata does not survive re-encoding or most upload pipelines",
                "The GUI 'workflow' chunk is NOT runnable via /prompt; "
                "use ComfyUI's 'Workflow -> Export (API)' for a runnable graph",
            ],
        )
    return record.prompt
