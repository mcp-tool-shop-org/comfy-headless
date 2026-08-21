"""
Comfy Headless - ComfyUI API Client
=====================================

Production-ready HTTP client for ComfyUI communication with:
- Connection pooling via requests.Session
- Automatic retry with exponential backoff
- Circuit breaker for failure resilience
- Structured logging
- Proper error handling

Usage:
    from comfy_headless import ComfyClient

    client = ComfyClient()
    if client.is_online():
        result = client.generate_image("a beautiful sunset")
"""

import json
import mimetypes
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import settings
from .exceptions import (
    ComfyUIConnectionError,
    ComfyUIOfflineError,
    InvalidParameterError,
    MissingNodePackError,
    SecurityError,
    UploadError,
    ValidationError,
)
from .logging_config import LogContext, get_logger
from .retry import RateLimiter, get_circuit_breaker


def _safe_json_parse(response: "requests.Response", context: str = "") -> dict:
    """
    Safely parse JSON from a response with proper error handling.

    Args:
        response: The requests Response object
        context: Description of what we were trying to do (for error messages)

    Returns:
        Parsed JSON as dict

    Raises:
        ComfyUIConnectionError: If JSON parsing fails
    """
    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(
            f"Invalid JSON response{f' ({context})' if context else ''}",
            extra={"error": str(e), "response_text": response.text[:200] if response.text else ""},
        )
        raise ComfyUIConnectionError(
            message=f"Invalid JSON response from ComfyUI{f' while {context}' if context else ''}",
            url=response.url,
            cause=e,
        ) from e


def _safe_get_nested(data: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely navigate nested dictionaries without raising KeyError or TypeError.

    Args:
        data: The root dictionary to navigate
        *keys: Sequence of keys to traverse
        default: Value to return if path doesn't exist or has wrong type

    Returns:
        The value at the nested path, or default if not found

    Example:
        _safe_get_nested(workflow, "3", "inputs", "seed", default=-1)
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


# Node types that carry the sampling seed, and the input each one uses.
# Kept here (rather than a single hardcoded class name) because the video
# builders emit several different sampler front-ends.
_SEED_INPUTS: dict[str, str] = {
    "KSampler": "seed",
    "KSamplerAdvanced": "noise_seed",
    "CogVideoSampler": "seed",
    "RandomNoise": "noise_seed",
    "SamplerCustom": "noise_seed",
}


def _extract_workflow_seed(workflow: dict, default: int = -1) -> int:
    """
    Pull the effective sampling seed back out of a built workflow.

    The video builders resolve ``seed=-1`` into a concrete random value while
    building, so this is how the caller learns which seed was actually used.

    Args:
        workflow: ComfyUI API-format workflow (node_id -> node_data)
        default: Value to return when no seed-carrying node is present

    Returns:
        The seed found on the first seed-carrying node, else ``default``.
    """
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        seed_input = _SEED_INPUTS.get(node.get("class_type"))
        if seed_input is None:
            continue
        found = _safe_get_nested(node, "inputs", seed_input, default=None)
        if isinstance(found, int):
            return found
    return default


# =============================================================================
# UPLOAD HELPERS
# =============================================================================

# Folder types accepted by ComfyUI's /upload/* routes.
UPLOAD_FOLDER_TYPES = ("input", "temp", "output")

# Magic-byte signatures used to pick an extension when raw bytes are uploaded
# without a filename. ComfyUI stores whatever name we send, and node COMBO
# lists filter by extension, so guessing well matters.
_IMAGE_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"BM", ".bmp"),
)

_AUDIO_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"fLaC", ".flac"),
    (b"ID3", ".mp3"),
    (b"\xff\xfb", ".mp3"),
    (b"\xff\xf3", ".mp3"),
    (b"\xff\xf2", ".mp3"),
    (b"OggS", ".ogg"),
)


def _sniff_audio_extension(data: bytes) -> str:
    """Guess a file extension from audio magic bytes (defaults to .wav)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"
    for magic, ext in _AUDIO_MAGIC:
        if data.startswith(magic):
            return ext
    return ".wav"


def _sniff_image_extension(data: bytes) -> str:
    """Guess a file extension from image magic bytes (defaults to .png)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    for magic, ext in _IMAGE_MAGIC:
        if data.startswith(magic):
            return ext
    return ".png"


def _normalize_upload_subfolder(subfolder: str | None) -> str:
    """
    Normalize a server-side subfolder and reject traversal attempts.

    ComfyUI interprets the subfolder relative to its input directory, so a
    caller-supplied value must never be able to climb out of it.

    Raises:
        SecurityError: If the subfolder looks like a traversal attempt
    """
    if not subfolder:
        return ""

    normalized = str(subfolder).replace("\\", "/").strip("/")
    if not normalized:
        return ""

    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts) or ":" in normalized:
        logger.warning("Rejected upload subfolder", extra={"upload_subfolder": str(subfolder)})
        raise SecurityError(
            "Invalid upload subfolder: possible traversal attempt",
            suggestions=["Use a simple relative subfolder name such as 'refs'"],
        )
    return "/".join(parts)


def _resolve_upload_payload(
    path_or_bytes: "str | Path | bytes | bytearray | memoryview",
    filename: str | None,
) -> tuple[bytes, str]:
    """
    Read an upload source into (bytes, filename).

    Args:
        path_or_bytes: Local file path or raw image bytes
        filename: Explicit name to store on the server (optional)

    Returns:
        Tuple of (file bytes, filename to send)

    Raises:
        InvalidParameterError: If the source type is unsupported
        ValidationError: If the file cannot be read
    """
    if isinstance(path_or_bytes, (bytes, bytearray, memoryview)):
        data = bytes(path_or_bytes)
        name = filename or f"comfy_headless_{uuid.uuid4().hex[:8]}{_sniff_image_extension(data)}"
        return data, name

    if isinstance(path_or_bytes, (str, Path)):
        source = Path(path_or_bytes)
        try:
            data = source.read_bytes()
        except OSError as e:
            raise ValidationError(
                f"Unable to read image file: {source}",
                user_message="That image file could not be read",
                details={"path": str(source)},
                suggestions=["Check the path exists and is readable"],
                cause=e,
            ) from e
        return data, filename or source.name

    raise InvalidParameterError(
        parameter="path_or_bytes",
        value=type(path_or_bytes).__name__,
        reason="expected a file path or raw image bytes",
    )


def _normalize_original_ref(original_ref: "dict | str") -> str:
    """
    Serialize the ``original_ref`` field for /upload/mask.

    Accepts either the dict returned by :meth:`ComfyClient.upload_image` or a
    bare filename, and emits the JSON blob ComfyUI expects.

    Raises:
        ValidationError: If no usable filename can be found
    """
    if isinstance(original_ref, str):
        name: str | None = original_ref
        subfolder: Any = ""
        folder_type: Any = "input"
    elif isinstance(original_ref, dict):
        name = original_ref.get("name") or original_ref.get("filename")
        subfolder = original_ref.get("subfolder", "")
        folder_type = original_ref.get("type", "input")
    else:
        raise ValidationError(
            f"Invalid original_ref type: {type(original_ref).__name__}",
            suggestions=["Pass the dict returned by upload_image(), or a filename string"],
        )

    if not isinstance(name, str) or not name:
        raise ValidationError(
            "original_ref must identify the base image by name",
            suggestions=["Pass the dict returned by upload_image(), or a filename string"],
        )

    return json.dumps(
        {
            "filename": name,
            "subfolder": subfolder if isinstance(subfolder, str) else "",
            "type": folder_type if isinstance(folder_type, str) and folder_type else "input",
        }
    )


# Lazy import for video module to avoid circular imports
_video_builder = None


def _get_video_builder():
    """Lazy import of VideoWorkflowBuilder."""
    global _video_builder
    if _video_builder is None:
        from .video import get_video_builder

        _video_builder = get_video_builder()
    return _video_builder


logger = get_logger(__name__)

__all__ = ["ComfyClient"]


class ComfyClient:
    """
    HTTP client for ComfyUI API with production-ready features.

    Attributes:
        base_url: ComfyUI server URL
        client_id: Unique identifier for this client instance
    """

    def __init__(
        self,
        base_url: str | None = None,
        rate_limit: int | None = None,
        rate_limit_per_seconds: float = 1.0,
    ):
        """
        Initialize the ComfyUI client.

        Args:
            base_url: ComfyUI server URL (default from settings)
            rate_limit: Max requests per time window (None = no limit)
            rate_limit_per_seconds: Time window for rate limiting
        """
        self.base_url = (base_url or settings.comfyui.url).rstrip("/")
        self.client_id = str(uuid.uuid4())
        self._session: requests.Session | None = None
        self._circuit = get_circuit_breaker("comfyui")

        # Rate limiter (optional)
        self._rate_limiter: RateLimiter | None = None
        if rate_limit is not None and rate_limit > 0:
            self._rate_limiter = RateLimiter(rate=rate_limit, per_seconds=rate_limit_per_seconds)
            logger.debug(f"Rate limiter enabled: {rate_limit} req/{rate_limit_per_seconds}s")

        logger.info(
            "ComfyClient initialized",
            extra={"base_url": self.base_url, "client_id": self.client_id[:8]},
        )

    @property
    def session(self) -> requests.Session:
        """Get or create the HTTP session with connection pooling."""
        if self._session is None or not hasattr(self._session, "headers"):
            self._session = self._create_session()
        return self._session

    def _create_session(self) -> requests.Session:
        """Create a configured requests session."""
        session = requests.Session()

        # Configure retry for transient errors
        retry_strategy = Retry(
            total=settings.retry.max_retries,
            backoff_factor=settings.retry.backoff_base,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def close(self):
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None
            logger.debug("HTTP session closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # =========================================================================
    # INTERNAL REQUEST METHODS
    # =========================================================================

    def _request(
        self, method: str, endpoint: str, timeout: float | None = None, **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with circuit breaker and rate limiter protection.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            timeout: Request timeout
            **kwargs: Additional request arguments

        Returns:
            Response object

        Raises:
            ComfyUIConnectionError: If connection fails
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or settings.comfyui.timeout_read

        # Apply rate limiting if configured
        if self._rate_limiter is not None and not self._rate_limiter.acquire(
            blocking=True, timeout=30.0
        ):
            logger.warning(f"Rate limit timeout for {endpoint}")
            raise ComfyUIConnectionError(
                message="Rate limit timeout - too many requests", url=self.base_url
            )

        try:
            with self._circuit:
                response = self.session.request(method, url, timeout=timeout, **kwargs)
                return response

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {endpoint}", extra={"error": str(e)})
            raise ComfyUIConnectionError(
                message=f"Failed to connect to ComfyUI at {self.base_url}",
                url=self.base_url,
                cause=e,
            ) from e
        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timeout: {endpoint}", extra={"timeout": timeout})
            raise ComfyUIConnectionError(
                message=f"Request timed out after {timeout}s", url=url, cause=e
            ) from e
        except Exception as e:
            logger.error(f"Request failed: {endpoint}", extra={"error": str(e)})
            raise ComfyUIConnectionError(message=f"Request failed: {e}", url=url, cause=e) from e

    def _get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self._request("GET", endpoint, **kwargs)

    def _post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a POST request."""
        return self._request("POST", endpoint, **kwargs)

    # =========================================================================
    # CONNECTION
    # =========================================================================

    def is_online(self) -> bool:
        """
        Check if ComfyUI is running and responsive.

        Uses a quick check that bypasses circuit breaker and session retries
        for fast UI initialization when ComfyUI is offline.

        Returns:
            True if ComfyUI is online, False otherwise
        """
        try:
            # Bypass session (which has retry adapter) - use raw requests
            # Use tuple timeout: (connect_timeout, read_timeout) for faster failure
            response = requests.get(
                f"{self.base_url}/system_stats",
                timeout=(1.0, 1.0),  # Fast fail - 1 second connect, 1 second read
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_system_stats(self) -> dict | None:
        """
        Get ComfyUI system stats including GPU and VRAM info.

        Returns:
            Dict with system stats or None if unavailable
        """
        try:
            response = self._get("/system_stats")
            if response.ok:
                return _safe_json_parse(response, "getting system stats")
        except ComfyUIConnectionError:
            # JSON parse error - already logged
            pass
        except Exception as e:
            logger.debug(f"Failed to get system stats: {e}")
        return None

    def get_vram_gb(self) -> float:
        """
        Get available GPU VRAM in gigabytes.

        Queries ComfyUI's /system_stats endpoint for GPU memory info.
        Falls back to 8GB if unable to detect.

        Returns:
            VRAM in GB (total, not free)
        """
        try:
            stats = self.get_system_stats()
            if stats:
                # ComfyUI returns devices array with vram_total in bytes
                devices = stats.get("devices", [])
                if devices:
                    vram_bytes = devices[0].get("vram_total", 0)
                    if vram_bytes > 0:
                        vram_gb = vram_bytes / (1024**3)
                        logger.debug(f"Detected VRAM: {vram_gb:.1f}GB")
                        return vram_gb
        except Exception as e:
            logger.debug(f"VRAM detection failed: {e}")

        # Fallback to reasonable default
        logger.debug("Using default VRAM estimate: 8GB")
        return 8.0

    def get_free_vram_gb(self) -> float:
        """
        Get free GPU VRAM in gigabytes.

        Returns:
            Free VRAM in GB
        """
        try:
            stats = self.get_system_stats()
            if stats:
                devices = stats.get("devices", [])
                if devices:
                    vram_free = devices[0].get("vram_free", 0)
                    if vram_free > 0:
                        return vram_free / (1024**3)
        except Exception as e:
            logger.debug(f"Free VRAM detection failed: {e}")
        return 0.0

    def ensure_online(self):
        """
        Ensure ComfyUI is online, raising an exception if not.

        Raises:
            ComfyUIOfflineError: If ComfyUI is not running
        """
        if not self.is_online():
            raise ComfyUIOfflineError(url=self.base_url)

    def check_vram_available(self, required_gb: float, raise_on_insufficient: bool = False) -> bool:
        """
        Check if sufficient VRAM is available for an operation.

        Args:
            required_gb: Required VRAM in gigabytes
            raise_on_insufficient: If True, raise InsufficientVRAMError

        Returns:
            True if sufficient VRAM available

        Raises:
            InsufficientVRAMError: If raise_on_insufficient=True and not enough VRAM
        """
        from .exceptions import InsufficientVRAMError

        free_vram = self.get_free_vram_gb()

        if free_vram <= 0:
            # Can't detect free VRAM, assume it's ok
            logger.debug("Cannot detect free VRAM, assuming sufficient")
            return True

        if free_vram < required_gb:
            logger.warning(
                "Insufficient VRAM", extra={"required_gb": required_gb, "available_gb": free_vram}
            )
            if raise_on_insufficient:
                raise InsufficientVRAMError(required_gb=required_gb, available_gb=free_vram)
            return False

        logger.debug(
            "VRAM check passed", extra={"required_gb": required_gb, "available_gb": free_vram}
        )
        return True

    def estimate_vram_for_image(
        self, width: int = 1024, height: int = 1024, batch_size: int = 1
    ) -> float:
        """
        Estimate VRAM required for image generation.

        Based on empirical measurements with SDXL.

        Args:
            width: Image width
            height: Image height
            batch_size: Number of images to generate

        Returns:
            Estimated VRAM in GB
        """
        # Base model VRAM (SDXL fp16)
        base_vram = 4.0

        # Additional VRAM per megapixel
        megapixels = (width * height) / 1_000_000
        latent_vram = megapixels * 1.5

        # Batch size multiplier (not linear, ~60% per additional image)
        batch_multiplier = 1 + (batch_size - 1) * 0.6

        total = (base_vram + latent_vram) * batch_multiplier

        logger.debug(
            f"VRAM estimate for {width}x{height}",
            extra={"estimated_gb": total, "batch_size": batch_size},
        )
        return total

    def estimate_vram_for_video(
        self, width: int = 512, height: int = 512, frames: int = 16, model: str = "animatediff"
    ) -> float:
        """
        Estimate VRAM required for video generation.

        Args:
            width: Video width
            height: Video height
            frames: Number of frames
            model: Video model type

        Returns:
            Estimated VRAM in GB
        """
        # Base model VRAM
        base_vram = 4.0

        # Resolution component
        megapixels = (width * height) / 1_000_000
        resolution_vram = megapixels * 1.5

        # Temporal component (per frame)
        frame_vram = frames * 0.3

        # Model-specific multipliers
        model_multipliers = {
            # AnimateDiff family
            "animatediff": 1.0,
            "animatediff_v3": 1.1,
            "animatediff_lightning": 0.8,
            # SVD
            "svd": 1.3,
            "svd_xt": 1.3,
            # CogVideoX
            "cogvideo": 1.5,
            "cogvideox": 1.5,
            # Hunyuan (original)
            "hunyuan": 2.0,
            # v2.5.0: Hunyuan 1.5
            "hunyuan_15": 1.8,  # 720p FP16
            "hunyuan_15_fast": 1.4,  # Distilled, 6-step
            "hunyuan_15_i2v": 1.8,
            # v2.5.0: LTX-Video 2
            "ltxv": 1.3,  # Fast and efficient
            "ltxv_i2v": 1.4,
            # v2.5.0: Wan
            "wan": 1.0,  # 1.3B variant (very efficient)
            "wan_14b": 1.6,  # 14B FP8
            "wan_fast": 2.0,  # Dual model approach
            "wan_i2v": 1.4,
            # v2.5.0: Mochi
            "mochi": 2.2,  # 10B parameters
            "mochi_fp8": 1.6,
        }
        multiplier = model_multipliers.get(model.lower(), 1.0)

        total = (base_vram + resolution_vram + frame_vram) * multiplier

        logger.debug(
            f"VRAM estimate for {width}x{height}x{frames}f",
            extra={"estimated_gb": total, "model": model},
        )
        return total

    def recommend_image_preset(self, intent: str = "general") -> str:
        """
        Recommend an image generation preset based on detected VRAM.

        Args:
            intent: Generation intent (portrait, landscape, quality, fast)

        Returns:
            Recommended preset name
        """
        vram = self.get_vram_gb()

        if vram < 6:
            return "draft"
        elif vram < 8:
            return "fast"
        elif vram < 12:
            if intent == "portrait":
                return "portrait"
            elif intent == "landscape":
                return "landscape"
            return "quality"
        else:  # 12GB+
            if intent in ("cinematic", "film"):
                return "cinematic"
            return "hd"

    def recommend_video_preset(self, intent: str = "general") -> str:
        """
        Recommend a video generation preset based on detected VRAM.

        Args:
            intent: Generation intent (portrait, action, cinematic, quality)

        Returns:
            Recommended preset name
        """
        vram = self.get_vram_gb()

        try:
            from .video import get_recommended_preset

            return get_recommended_preset(intent=intent, vram_gb=vram)
        except ImportError:
            # Fallback if video module unavailable
            # v2.5.0: Updated recommendations with new models
            if vram < 8:
                return "quick"  # AnimateDiff Lightning
            elif vram < 12:
                return "wan_1.3b"  # Wan 1.3B is efficient
            elif vram < 16:
                return "ltx_standard"  # LTX-Video is great at 16GB
            elif vram < 24:
                return "hunyuan15_720p"  # Hunyuan 1.5 at 720p
            else:
                return "hunyuan15_quality"  # Full quality Hunyuan 1.5

    # =========================================================================
    # MODELS & INFO
    # =========================================================================

    def _get_object_info(self, node_type: str, input_name: str) -> list[str]:
        """Get input options for a node type."""
        try:
            response = self._get(f"/object_info/{node_type}")
            if response.ok:
                data = _safe_json_parse(response, f"getting object info for {node_type}")
                # Safe dictionary navigation with bounds checking
                node_data = data.get(node_type, {})
                if not isinstance(node_data, dict):
                    return []
                input_data = node_data.get("input", {})
                if not isinstance(input_data, dict):
                    return []
                required_data = input_data.get("required", {})
                if not isinstance(required_data, dict):
                    return []
                options = required_data.get(input_name, [])
                # Options should be a list with at least one element (the options list)
                if isinstance(options, list) and len(options) > 0:
                    first_element = options[0]
                    if isinstance(first_element, list):
                        return first_element
                return []
        except ComfyUIConnectionError:
            # JSON parse error - already logged
            pass
        except Exception as e:
            logger.debug(f"Failed to get object info for {node_type}: {e}")
        return []

    def get_checkpoints(self) -> list[str]:
        """Get available checkpoint models."""
        return self._get_object_info("CheckpointLoaderSimple", "ckpt_name")

    def get_samplers(self) -> list[str]:
        """Get available samplers."""
        samplers = self._get_object_info("KSampler", "sampler_name")
        return samplers or ["euler", "euler_ancestral", "dpmpp_2m", "dpmpp_sde"]

    def get_schedulers(self) -> list[str]:
        """Get available schedulers."""
        schedulers = self._get_object_info("KSampler", "scheduler")
        return schedulers or ["normal", "karras", "exponential", "sgm_uniform"]

    def get_loras(self) -> list[str]:
        """Get available LoRA models."""
        return self._get_object_info("LoraLoader", "lora_name")

    def get_motion_models(self) -> list[str]:
        """Get available AnimateDiff motion models."""
        return self._get_object_info("ADE_LoadAnimateDiffModel", "model_name")

    def get_all_installed_nodes(self) -> list[str]:
        """
        Get all installed node types (class_types) in ComfyUI.

        This queries the /object_info endpoint to get all available nodes,
        which is useful for checking workflow dependencies.

        Returns:
            List of all installed node class_type names (e.g., ["KSampler", "CLIPTextEncode", ...])
        """
        try:
            response = self._get("/object_info")
            if response.ok:
                data = _safe_json_parse(response, "getting all object info")
                if isinstance(data, dict):
                    return list(data.keys())
        except ComfyUIConnectionError:
            # JSON parse error - already logged
            pass
        except Exception as e:
            logger.debug(f"Failed to get all installed nodes: {e}")
        return []

    def check_workflow_dependencies(self, workflow: dict) -> dict[str, Any]:
        """
        Check if all nodes in a workflow are installed in ComfyUI.

        Args:
            workflow: The ComfyUI workflow JSON (dict of node_id -> node_data)

        Returns:
            Dict with:
                - installed: List of installed node types used by the workflow
                - missing: List of missing node types
                - all_installed: bool indicating if all dependencies are met
                - details: Dict mapping class_type to list of node_ids using it
                - missing_packs: Dict mapping a missing class_type to the
                  custom node pack that provides it (or None if it should be
                  a core node / no pack is known)
                - required_packs: Dict mapping pack id -> class_types the
                  workflow uses from that pack, whether installed or not
        """
        # Extract all class_types from the workflow
        workflow_nodes = {}
        for node_id, node in workflow.items():
            if isinstance(node, dict) and "class_type" in node:
                class_type = node["class_type"]
                if class_type not in workflow_nodes:
                    workflow_nodes[class_type] = []
                workflow_nodes[class_type].append(node_id)

        # Get all installed nodes
        installed_nodes = set(self.get_all_installed_nodes())

        # Check which are installed/missing
        installed = []
        missing = []

        for class_type in workflow_nodes:
            if class_type in installed_nodes:
                installed.append(class_type)
            else:
                missing.append(class_type)

        # Attach custom node pack provenance so a missing class_type can be
        # reported as "install pack Y" rather than just "not found".
        from .video import NODE_PACK_INFO, get_node_pack, required_node_packs

        missing_packs: dict[str, dict | None] = {}
        for class_type in missing:
            pack_id = get_node_pack(class_type)
            pack = NODE_PACK_INFO.get(pack_id) if pack_id else None
            missing_packs[class_type] = pack.to_dict() if pack else None

        return {
            "installed": sorted(installed),
            "missing": sorted(missing),
            "all_installed": len(missing) == 0,
            "details": workflow_nodes,
            "total_nodes": sum(len(ids) for ids in workflow_nodes.values()),
            "unique_types": len(workflow_nodes),
            "missing_packs": missing_packs,
            "required_packs": required_node_packs(workflow),
        }

    def require_workflow_dependencies(self, workflow: dict) -> dict[str, Any]:
        """
        Assert that every node type a workflow uses is installed.

        Same check as :meth:`check_workflow_dependencies`, but fails fast with
        a structured error naming the missing classes and the custom node
        packs that provide them, rather than letting ``POST /prompt`` reject
        the graph with an opaque validation message.

        Args:
            workflow: The ComfyUI workflow JSON (dict of node_id -> node_data)

        Returns:
            The same report dict, when nothing is missing.

        Raises:
            MissingNodePackError: If any node type is not installed.
        """
        report = self.check_workflow_dependencies(workflow)
        if not report["all_installed"]:
            raise MissingNodePackError(missing=report["missing_packs"])
        return report

    def check_workflow_types(self, workflow: dict) -> dict[str, Any]:
        """
        Client-side edge type validation against the live ``/object_info``.

        Uses the server's own acceptance rule (union-superset matching,
        transcribed in :mod:`comfy_headless.addressing`), so a MESH feeding a
        FILE_3D_* union input is never a false rejection. Only edges the
        server would provably reject are errors; partial type overlaps are
        warnings; unknown nodes are skipped (drift tolerance).

        Returns:
            Dict with:
                - checked: False when /object_info was unreachable (nothing
                  validated -- absence of errors then means nothing)
                - errors: edges the server would reject
                - warnings: accepted edges with partial type overlap
        """
        data: dict = {}
        try:
            response = self._get("/object_info")
            if response.ok:
                data = _safe_json_parse(response, "getting object info for type checking")
        except ComfyUIConnectionError:
            pass
        except Exception as e:
            logger.debug(f"Type-check fetch failed: {e}")

        if not isinstance(data, dict) or not data:
            return {"checked": False, "errors": [], "warnings": []}

        from .addressing import GraphTypeChecker, extract_object_info_types

        issues = GraphTypeChecker(extract_object_info_types(data)).check(workflow)

        def _as_dict(issue) -> dict[str, Any]:
            return {
                "node_id": issue.node_id,
                "input_name": issue.input_name,
                "source_id": issue.source_id,
                "output_index": issue.output_index,
                "received": issue.received,
                "declared": issue.declared,
                "match": issue.match.value,
                "message": issue.message,
            }

        return {
            "checked": True,
            "errors": [_as_dict(i) for i in issues if i.severity == "error"],
            "warnings": [_as_dict(i) for i in issues if i.severity == "warning"],
        }

    # =========================================================================
    # QUEUE MANAGEMENT
    # =========================================================================

    def get_queue(self) -> dict:
        """Get current queue status."""
        try:
            response = self._get("/queue")
            if response.ok:
                return _safe_json_parse(response, "getting queue status")
        except ComfyUIConnectionError:
            # JSON parse error - already logged
            pass
        except Exception as e:
            logger.debug(f"Failed to get queue: {e}")
        return {"queue_running": [], "queue_pending": []}

    def get_history(self, prompt_id: str | None = None) -> dict:
        """Get execution history, optionally for a specific prompt."""
        try:
            endpoint = f"/history/{prompt_id}" if prompt_id else "/history"
            response = self._get(endpoint)
            if response.ok:
                return _safe_json_parse(response, "getting history")
        except ComfyUIConnectionError:
            # JSON parse error - already logged
            pass
        except Exception as e:
            logger.debug(f"Failed to get history: {e}")
        return {}

    def cancel_current(self) -> bool:
        """Cancel the currently running job."""
        try:
            response = self._post("/interrupt")
            if response.ok:
                logger.info("Cancelled current job")
                return True
        except Exception as e:
            logger.warning(f"Failed to cancel job: {e}")
        return False

    def clear_queue(self) -> bool:
        """Clear all pending jobs from the queue."""
        try:
            response = self._post("/queue", json={"clear": True})
            if response.ok:
                logger.info("Cleared queue")
                return True
        except Exception as e:
            logger.warning(f"Failed to clear queue: {e}")
        return False

    # =========================================================================
    # PROMPT EXECUTION
    # =========================================================================

    def queue_prompt(self, workflow: dict, extra_pnginfo: dict | None = None) -> str | None:
        """
        Queue a workflow for execution.

        Args:
            workflow: ComfyUI workflow dict
            extra_pnginfo: Optional custom provenance. Anything in this dict
                is serialized by the save nodes as extra PNG text chunks
                alongside the default ``prompt``/``workflow`` keys -- the
                metadata profile's write path, no custom node needed. Read it
                back with ``comfy_headless.metadata.read_workflow_metadata``.
                Caveat: some hardened deployments strip unknown keys;
                round-trip test against the real target.

        Returns:
            prompt_id if successful, None otherwise

        Raises:
            QueueError: If queueing fails
        """
        # Input validation
        if not isinstance(workflow, dict):
            logger.error("Invalid workflow: must be a dictionary")
            return None

        try:
            payload: dict[str, Any] = {"prompt": workflow, "client_id": self.client_id}
            if extra_pnginfo:
                # Verified payload shape: execution.py reads
                # extra_data.get('extra_pnginfo') into the save nodes.
                payload["extra_data"] = {"extra_pnginfo": extra_pnginfo}
            response = self._post("/prompt", json=payload, timeout=settings.comfyui.timeout_queue)

            if response.ok:
                data = _safe_json_parse(response, "queueing prompt")
                prompt_id = data.get("prompt_id")
                if not isinstance(prompt_id, str):
                    logger.warning("Queue response missing prompt_id")
                    return None
                logger.info(
                    "Queued prompt", extra={"prompt_id": prompt_id[:8] if prompt_id else None}
                )
                return prompt_id
            else:
                error_msg = f"Queue failed with status {response.status_code}"
                logger.warning(error_msg, extra={"status": response.status_code})
                return None

        except ComfyUIConnectionError:
            raise
        except Exception as e:
            logger.error(f"Queue error: {e}", exc_info=True)
            return None

    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: float | None = None,
        poll_interval: float = 0.5,
        on_progress: Callable[[float, str], None] | None = None,
    ) -> dict | None:
        """
        Wait for a prompt to complete.

        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
            on_progress: Optional callback called with (progress: 0.0-1.0, status: str)

        Returns:
            History entry when complete, or None on timeout
        """
        timeout = timeout or settings.generation.generation_timeout
        start = time.time()

        logger.debug("Waiting for completion", extra={"prompt_id": prompt_id[:8]})

        last_progress = 0.0

        while time.time() - start < timeout:
            try:
                elapsed = time.time() - start
                history = self.get_history(prompt_id)

                if prompt_id in history:
                    entry = history[prompt_id]
                    status = entry.get("status", {})

                    if status.get("completed", False):
                        if on_progress:
                            on_progress(1.0, "Completed")
                        logger.info(
                            "Generation completed",
                            extra={"prompt_id": prompt_id[:8], "elapsed": f"{elapsed:.1f}s"},
                        )
                        return entry

                    if status.get("status_str") == "error":
                        if on_progress:
                            on_progress(last_progress, "Error")
                        logger.warning(
                            "Generation failed",
                            extra={"prompt_id": prompt_id[:8], "status": status},
                        )
                        return entry

                    # Calculate progress from execution info
                    if on_progress:
                        # Try to get node progress from status messages
                        messages = status.get("messages", [])
                        for msg in messages:
                            if isinstance(msg, list) and len(msg) >= 2:
                                if msg[0] == "execution_cached":
                                    # Some nodes were cached
                                    pass
                                elif msg[0] == "executing":
                                    msg[1] if len(msg) > 1 else None

                        # Estimate progress based on elapsed time
                        time_progress = min(0.95, elapsed / timeout)

                        # If we have execution info, use it
                        status_str = status.get("status_str", "processing")
                        if status_str == "queued":
                            progress = 0.05
                            status_msg = "Queued"
                        else:
                            progress = max(0.1, time_progress)
                            status_msg = f"Processing ({elapsed:.0f}s)"

                        if progress > last_progress:
                            last_progress = progress
                            on_progress(progress, status_msg)
                else:
                    # Not in history yet - still in queue
                    if on_progress:
                        queue = self.get_queue()
                        pending = queue.get("queue_pending", [])
                        running = queue.get("queue_running", [])

                        # Find position in queue
                        queue_pos = None
                        for i, item in enumerate(pending):
                            if isinstance(item, list) and len(item) > 1 and item[1] == prompt_id:
                                queue_pos = i + 1
                                break

                        is_running = any(
                            isinstance(item, list) and len(item) > 1 and item[1] == prompt_id
                            for item in running
                        )

                        if is_running:
                            progress = 0.1
                            status_msg = "Starting"
                        elif queue_pos is not None:
                            progress = 0.02
                            status_msg = f"Queue position {queue_pos}"
                        else:
                            progress = 0.05
                            status_msg = "Waiting"

                        if progress > last_progress:
                            last_progress = progress
                            on_progress(progress, status_msg)

            except Exception as e:
                logger.debug(f"Poll error: {e}")

            time.sleep(poll_interval)

        logger.warning(
            "Generation timed out", extra={"prompt_id": prompt_id[:8], "timeout": timeout}
        )
        return None

    # =========================================================================
    # ASSET UPLOADS
    # =========================================================================

    def _upload_asset(
        self,
        endpoint: str,
        path_or_bytes: "str | Path | bytes | bytearray | memoryview",
        *,
        filename: str | None = None,
        subfolder: str = "",
        overwrite: bool = False,
        folder_type: str = "input",
        extra_fields: dict[str, str] | None = None,
    ) -> dict:
        """
        Shared multipart uploader for /upload/image and /upload/mask.

        Args:
            endpoint: Upload route (e.g. "/upload/image")
            path_or_bytes: Local file path or raw image bytes
            filename: Name to store on the server (defaults to the source name)
            subfolder: Optional subfolder beneath the target folder
            overwrite: Replace an existing file instead of letting the server rename
            folder_type: "input" (default), "temp", or "output"
            extra_fields: Additional multipart form fields

        Returns:
            Dict with the server-reported name/subfolder/type plus a ready-to-use
            "ref" string for a LoadImage node.

        Raises:
            InvalidParameterError: If folder_type or the source type is invalid
            SecurityError: If the subfolder looks like a traversal attempt
            ValidationError: If the source cannot be read or is empty
            UploadError: If the server rejects the upload or answers unexpectedly
            ComfyUIConnectionError: If the connection fails
        """
        if folder_type not in UPLOAD_FOLDER_TYPES:
            raise InvalidParameterError(
                parameter="type",
                value=folder_type,
                reason="unsupported ComfyUI folder type",
                allowed_values=list(UPLOAD_FOLDER_TYPES),
            )

        safe_subfolder = _normalize_upload_subfolder(subfolder)
        data, raw_name = _resolve_upload_payload(path_or_bytes, filename)

        # Strip any directory component: only the basename is ever sent, so a
        # crafted filename cannot place the file outside the target folder.
        safe_name = Path(str(raw_name).replace("\\", "/")).name
        if not safe_name:
            raise ValidationError(
                "Upload filename cannot be empty",
                suggestions=["Pass filename='myimage.png' explicitly"],
            )
        if not data:
            raise ValidationError(
                "Refusing to upload empty image data",
                details={"filename": safe_name},
                suggestions=["Check the source file is not zero bytes"],
            )

        content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        files = {"image": (safe_name, data, content_type)}

        form: dict[str, str] = {"type": folder_type}
        if safe_subfolder:
            form["subfolder"] = safe_subfolder
        if overwrite:
            # Only sent when True on purpose: some ComfyUI builds treat the mere
            # presence of this field as truthy, so a literal "false" could
            # silently clobber an existing file.
            form["overwrite"] = "true"
        if extra_fields:
            form.update(extra_fields)

        request_id = str(uuid.uuid4())[:8]

        with LogContext(request_id):
            # NOTE: logging's `extra` cannot carry reserved LogRecord attribute
            # names ("filename", "module", ...), hence the upload_* prefixes.
            logger.info(
                "Uploading asset to ComfyUI",
                extra={
                    "endpoint": endpoint,
                    "upload_filename": safe_name,
                    "upload_subfolder": safe_subfolder,
                    "upload_type": folder_type,
                    "upload_bytes": len(data),
                },
            )

            response = self._post(
                endpoint,
                files=files,
                data=form,
                timeout=settings.comfyui.timeout_image,
            )

            if not response.ok:
                raw_body = getattr(response, "text", "") or ""
                raise UploadError(
                    message=f"Upload failed with status {response.status_code}",
                    filename=safe_name,
                    subfolder=safe_subfolder or None,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    request_id=request_id,
                    details={"response_body": raw_body[:200] if isinstance(raw_body, str) else ""},
                )

            try:
                payload = _safe_json_parse(response, f"uploading to {endpoint}")
            except ComfyUIConnectionError as e:
                raise UploadError(
                    message=f"ComfyUI returned a non-JSON response from {endpoint}",
                    filename=safe_name,
                    subfolder=safe_subfolder or None,
                    endpoint=endpoint,
                    request_id=request_id,
                    cause=e,
                    suggestions=["Confirm the server really is ComfyUI and not a proxy"],
                ) from e

            if not isinstance(payload, dict):
                raise UploadError(
                    message=f"Unexpected upload response shape from {endpoint}",
                    filename=safe_name,
                    subfolder=safe_subfolder or None,
                    endpoint=endpoint,
                    request_id=request_id,
                    details={"response_type": type(payload).__name__},
                )

            # The SERVER is authoritative about the stored name. With
            # overwrite=false a name collision makes ComfyUI store the file
            # under a new name (a counter is appended) and report it here, so
            # never assume it matches what was sent. Falling back to the local
            # filename would silently point the workflow at the wrong image.
            stored_name = payload.get("name") or payload.get("filename")
            if not isinstance(stored_name, str) or not stored_name:
                raise UploadError(
                    message=f"Upload response from {endpoint} did not report a stored filename",
                    filename=safe_name,
                    subfolder=safe_subfolder or None,
                    endpoint=endpoint,
                    request_id=request_id,
                    details={"response_keys": sorted(str(k) for k in payload)},
                    suggestions=[
                        "Expected JSON like {'name': ..., 'subfolder': ..., 'type': ...}",
                        "The server may be an incompatible or proxied ComfyUI build",
                    ],
                )

            raw_subfolder = payload.get("subfolder")
            stored_subfolder = raw_subfolder if isinstance(raw_subfolder, str) else safe_subfolder
            raw_type = payload.get("type")
            stored_type = raw_type if isinstance(raw_type, str) and raw_type else folder_type

            if stored_name != safe_name:
                logger.warning(
                    "ComfyUI stored the upload under a different name (collision rename)",
                    extra={"requested_name": safe_name, "stored_name": stored_name},
                )

            ref = f"{stored_subfolder}/{stored_name}" if stored_subfolder else stored_name
            logger.info("Upload complete", extra={"upload_ref": ref, "upload_type": stored_type})

            return {
                "name": stored_name,
                "subfolder": stored_subfolder,
                "type": stored_type,
                "ref": ref,
            }

    def upload_image(
        self,
        path_or_bytes: "str | Path | bytes | bytearray | memoryview",
        *,
        filename: str | None = None,
        subfolder: str = "",
        overwrite: bool = False,
        type: str = "input",
    ) -> dict:
        """
        Upload an image into ComfyUI's input folder (POST /upload/image).

        This is how an image gets *into* ComfyUI for img2img, ControlNet, Edit,
        image-to-3D and image-to-video workflows. Feed the returned "ref" to a
        core LoadImage node:

            uploaded = client.upload_image("photo.png")
            workflow["1"] = {
                "class_type": "LoadImage",
                "inputs": {"image": uploaded["ref"]},
            }

        The name in the response is authoritative. With overwrite=False (the
        default) ComfyUI renames on collision rather than clobbering, so the
        stored name may differ from the one sent - always use the returned value.

        The upload can be verified by reading the file back off the server:

            client.get_image(uploaded["name"], uploaded["subfolder"], "input")

        Args:
            path_or_bytes: Local file path or raw image bytes
            filename: Name to store on the server (defaults to the source name;
                required in spirit for raw bytes, where a name is generated)
            subfolder: Optional subfolder beneath the target folder
            overwrite: Replace an existing file instead of letting the server rename
            type: "input" (default), "temp", or "output"

        Returns:
            Dict with "name", "subfolder", "type" as reported by the server, plus
            "ref" - the exact string to hand a LoadImage node.

        Raises:
            InvalidParameterError: If type or the source type is invalid
            SecurityError: If the subfolder looks like a traversal attempt
            ValidationError: If the source cannot be read or is empty
            UploadError: If the server rejects the upload or answers unexpectedly
            ComfyUIConnectionError: If the connection fails
        """
        return self._upload_asset(
            "/upload/image",
            path_or_bytes,
            filename=filename,
            subfolder=subfolder,
            overwrite=overwrite,
            folder_type=type,
        )

    def upload_mask(
        self,
        path_or_bytes: "str | Path | bytes | bytearray | memoryview",
        original_ref: "dict | str",
        *,
        filename: str | None = None,
        subfolder: str = "",
        overwrite: bool = False,
        type: str = "input",
    ) -> dict:
        """
        Upload a mask for an already-uploaded image (POST /upload/mask).

        Used for inpainting / mask-editing flows. ``original_ref`` identifies the
        base image the mask belongs to and accepts either the dict returned by
        :meth:`upload_image` or a bare filename.

            base = client.upload_image("photo.png")
            mask = client.upload_mask("mask.png", base)

        Args:
            path_or_bytes: Local file path or raw mask-image bytes
            original_ref: The base image (upload_image() result dict, or filename)
            filename: Name to store on the server (defaults to the source name)
            subfolder: Optional subfolder beneath the target folder
            overwrite: Replace an existing file instead of letting the server rename
            type: "input" (default), "temp", or "output"

        Returns:
            Same shape as :meth:`upload_image`.

        Raises:
            Same as :meth:`upload_image`, plus ValidationError if original_ref
            does not identify a base image.
        """
        return self._upload_asset(
            "/upload/mask",
            path_or_bytes,
            filename=filename,
            subfolder=subfolder,
            overwrite=overwrite,
            folder_type=type,
            extra_fields={"original_ref": _normalize_original_ref(original_ref)},
        )

    def upload_audio(
        self,
        path_or_bytes: "str | Path | bytes | bytearray | memoryview",
        *,
        filename: str | None = None,
        subfolder: str = "",
        overwrite: bool = False,
        type: str = "input",
    ) -> dict:
        """
        Upload an audio file into ComfyUI's input folder.

        ComfyUI has no ``/upload/audio`` route -- ``POST /upload/image`` is
        the server's general input-file uploader (it stores whatever it is
        given without content-type validation; this is exactly how the GUI's
        LoadAudio widget uploads). Feed the returned "ref" to a core
        ``LoadAudio`` node, e.g. via ``separate_audio()``.

        For raw bytes without a ``filename``, the extension is sniffed from
        audio magic bytes (flac/mp3/ogg/wav) -- LoadAudio's file list filters
        by extension, so the name matters.

        Args / returns / raises: same shape as :meth:`upload_image`.
        """
        if isinstance(path_or_bytes, (bytes, bytearray, memoryview)) and not filename:
            data = bytes(path_or_bytes)
            filename = f"comfy_headless_{uuid.uuid4().hex[:8]}{_sniff_audio_extension(data)}"
        return self._upload_asset(
            "/upload/image",
            path_or_bytes,
            filename=filename,
            subfolder=subfolder,
            overwrite=overwrite,
            folder_type=type,
        )

    # =========================================================================
    # FILE DOWNLOADS
    # =========================================================================

    def get_image(
        self, filename: str, subfolder: str = "", folder_type: str = "output"
    ) -> bytes | None:
        """
        Download a generated image.

        Args:
            filename: Image filename
            subfolder: Subfolder within output directory
            folder_type: Folder type (usually "output")

        Returns:
            Image bytes or None if download fails
        """
        try:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            response = self._get("/view", params=params, timeout=settings.comfyui.timeout_image)
            if response.ok:
                logger.debug(f"Downloaded image: {filename}")
                return response.content
        except Exception as e:
            logger.warning(f"Failed to download image {filename}: {e}")
        return None

    def get_video(
        self, filename: str, subfolder: str = "", folder_type: str = "output"
    ) -> bytes | None:
        """Download a generated video."""
        try:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            response = self._get("/view", params=params, timeout=settings.comfyui.timeout_video)
            if response.ok:
                logger.debug(f"Downloaded video: {filename}")
                return response.content
        except Exception as e:
            logger.warning(f"Failed to download video {filename}: {e}")
        return None

    def get_file(
        self, filename: str, subfolder: str = "", folder_type: str = "output"
    ) -> bytes | None:
        """
        Download any generated output file (mesh, audio, text, ...).

        ``GET /view`` serves every output type -- SaveGLB, SaveAudioAdvanced
        and SaveText register their files in ``/history`` exactly like
        SaveImage does for PNGs, so meshes and audio come back through the
        same route. Pass the ``filename``/``subfolder``/``type`` entry from a
        ``generate_3d()``/``generate_audio()``/``run_inference()`` result.
        """
        try:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            response = self._get("/view", params=params, timeout=settings.comfyui.timeout_video)
            if response.ok:
                logger.debug(f"Downloaded file: {filename}")
                return response.content
        except Exception as e:
            logger.warning(f"Failed to download file {filename}: {e}")
        return None

    # =========================================================================
    # WORKFLOW BUILDERS
    # =========================================================================

    def build_txt2img_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        checkpoint: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        seed: int = -1,
        batch_size: int = 1,
    ) -> dict:
        """Build a basic txt2img workflow."""
        if seed == -1:
            seed = int(time.time() * 1000) % (2**32)

        if not checkpoint:
            checkpoints = self.get_checkpoints()
            checkpoint = checkpoints[0] if checkpoints else "model.safetensors"

        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": cfg,
                    "denoise": 1.0,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "seed": seed,
                    "steps": steps,
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"batch_size": batch_size, "height": height, "width": width},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"clip": ["4", 1], "text": prompt},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": negative_prompt or "bad quality, blurry, distorted",
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "comfy_headless", "images": ["8", 0]},
            },
        }

    def build_video_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        checkpoint: str = "",
        motion_model: str = "",
        width: int = 512,
        height: int = 512,
        frames: int = 16,
        fps: int = 8,
        steps: int = 20,
        cfg: float = 7.0,
        seed: int = -1,
        motion_scale: float = 1.0,
    ) -> dict:
        """Build an AnimateDiff video workflow."""
        if seed == -1:
            seed = int(time.time() * 1000) % (2**32)

        if not checkpoint:
            checkpoints = self.get_checkpoints()
            checkpoint = checkpoints[0] if checkpoints else "dreamshaper_8.safetensors"

        if not motion_model:
            motion_models = self.get_motion_models()
            motion_model = motion_models[0] if motion_models else "v3_sd15_mm.ckpt"

        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint},
            },
            "2": {
                "class_type": "ADE_LoadAnimateDiffModel",
                "inputs": {"model_name": motion_model},
            },
            "3": {
                "class_type": "ADE_ApplyAnimateDiffModel",
                "inputs": {
                    "model": ["1", 0],
                    "motion_model": ["2", 0],
                    "scale_multival": motion_scale,
                },
            },
            "4": {
                "class_type": "ADE_EmptyLatentImageLarge",
                "inputs": {"width": width, "height": height, "batch_size": frames},
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["1", 1]},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt or "bad quality, blurry, distorted",
                    "clip": ["1", 1],
                },
            },
            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["3", 0],
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "latent_image": ["4", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["7", 0], "vae": ["1", 2]},
            },
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": fps,
                    "loop_count": 0,
                    "filename_prefix": "comfy_headless_video",
                    "format": "video/h264-mp4",
                    "save_output": True,
                },
            },
        }

    # =========================================================================
    # HIGH-LEVEL GENERATION
    # =========================================================================

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        preset: str = "",
        checkpoint: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        seed: int = -1,
        wait: bool = True,
        timeout: float | None = None,
        on_progress: Callable[[float, str], None] | None = None,
    ) -> dict[str, Any]:
        """
        High-level image generation with optional preset support.

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            preset: Optional preset (draft, fast, quality, hd, portrait, landscape, cinematic)
                   When set, overrides width/height/steps/cfg with preset values
            checkpoint: Model checkpoint name
            width: Image width (ignored if preset is set)
            height: Image height (ignored if preset is set)
            steps: Sampling steps (ignored if preset is set)
            cfg: CFG scale (ignored if preset is set)
            sampler: Sampler name
            scheduler: Scheduler name
            seed: Random seed (-1 for random)
            wait: Whether to wait for completion
            timeout: Generation timeout
            on_progress: Optional callback(progress: 0.0-1.0, status: str) for progress updates

        Returns:
            Dict with success, prompt_id, images, error, seed, preset
        """
        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.generation_timeout

        with LogContext(request_id):
            result = {
                "success": False,
                "prompt_id": None,
                "images": [],
                "error": None,
                "seed": seed,
                "preset": preset or None,
            }

            logger.info(
                "Starting image generation",
                extra={"width": width, "height": height, "steps": steps, "preset": preset},
            )

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            # Try using WorkflowCompiler if preset is specified
            if preset:
                try:
                    from .workflows import GENERATION_PRESETS, compile_workflow

                    if preset in GENERATION_PRESETS:
                        compiled = compile_workflow(
                            prompt=prompt,
                            negative=negative_prompt,
                            preset=preset,
                            checkpoint=checkpoint or "auto",
                            sampler=sampler,
                            scheduler=scheduler,
                            seed=seed,
                        )
                        if compiled.is_valid:
                            workflow = compiled.workflow
                            # Extract seed from compiled workflow (safe nested access)
                            result["seed"] = _safe_get_nested(
                                workflow, "3", "inputs", "seed", default=seed
                            )
                            logger.debug(f"Using WorkflowCompiler with preset '{preset}'")
                        else:
                            logger.warning(f"Workflow compilation errors: {compiled.errors}")
                            preset = ""  # Fall back to legacy
                    else:
                        logger.warning(f"Unknown preset '{preset}', falling back to legacy")
                        preset = ""
                except Exception as e:
                    logger.warning(f"WorkflowCompiler failed: {e}, using legacy builder")
                    preset = ""

            # Legacy workflow builder (when no preset or compiler failed)
            if not preset:
                workflow = self.build_txt2img_workflow(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    checkpoint=checkpoint,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg=cfg,
                    sampler=sampler,
                    scheduler=scheduler,
                    seed=seed,
                )
                # Store actual seed used (safe nested access)
                result["seed"] = _safe_get_nested(workflow, "3", "inputs", "seed", default=seed)

            prompt_id = self.queue_prompt(workflow)
            if not prompt_id:
                result["error"] = "Failed to queue prompt"
                return result

            result["prompt_id"] = prompt_id

            if not wait:
                result["success"] = True
                return result

            history = self.wait_for_completion(prompt_id, timeout=timeout, on_progress=on_progress)
            if not history:
                result["error"] = f"Generation timed out after {timeout}s"
                return result

            status = history.get("status", {})
            if status.get("status_str") == "error":
                error_msgs = status.get("messages", [["Unknown error"]])
                result["error"] = str(error_msgs[0] if error_msgs else "Unknown error")
                return result

            # Extract images (with type validation)
            outputs = history.get("outputs", {})
            if isinstance(outputs, dict):
                for node_output in outputs.values():
                    if isinstance(node_output, dict) and "images" in node_output:
                        images_list = node_output["images"]
                        if isinstance(images_list, list):
                            for img in images_list:
                                if isinstance(img, dict):
                                    result["images"].append(
                                        {
                                            "filename": img.get("filename"),
                                            "subfolder": img.get("subfolder", ""),
                                            "type": img.get("type", "output"),
                                        }
                                    )

            result["success"] = len(result["images"]) > 0

            if result["success"]:
                logger.info("Generation complete", extra={"image_count": len(result["images"])})
            else:
                logger.warning("Generation produced no images")

            return result

    def generate_batch(
        self,
        prompts: list[str],
        negative_prompt: str = "",
        preset: str = "fast",
        checkpoint: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        seeds: list[int] | None = None,
        max_concurrent: int = 1,
        check_vram: bool = True,
        on_progress: Callable[[int, int, float, str], None] | None = None,
    ) -> dict[str, Any]:
        """
        Generate multiple images from a list of prompts.

        Args:
            prompts: List of prompts to generate
            negative_prompt: Shared negative prompt
            preset: Generation preset
            checkpoint: Model checkpoint
            width, height, steps, cfg, sampler, scheduler: Generation params
            seeds: Optional list of seeds (one per prompt, -1 for random)
            max_concurrent: Max concurrent generations (use 1 for sequential)
            check_vram: If True, check VRAM before starting
            on_progress: Callback(current_idx, total, progress, status)

        Returns:
            Dict with success, results (list of individual results), errors
        """
        import time as time_module

        total = len(prompts)
        if total == 0:
            return {"success": False, "results": [], "errors": ["No prompts provided"]}

        # Prepare seeds
        if seeds is None:
            seeds = [-1] * total
        elif len(seeds) < total:
            seeds = seeds + [-1] * (total - len(seeds))

        # Check VRAM if requested
        if check_vram:
            estimated = self.estimate_vram_for_image(width, height, max_concurrent)
            if not self.check_vram_available(estimated):
                logger.warning(
                    "Batch may exceed VRAM", extra={"estimated_gb": estimated, "batch_size": total}
                )

        results = []
        errors = []
        start_time = time_module.time()

        for idx, (prompt, seed) in enumerate(zip(prompts, seeds)):
            try:
                # Progress callback
                if on_progress:
                    on_progress(idx, total, 0.0, f"Starting {idx + 1}/{total}")

                # Wrap individual progress - bind loop vars as defaults (B023)
                def item_progress(prog: float, status: str, idx: int = idx, total: int = total):
                    if on_progress:
                        overall = (idx + prog) / total
                        on_progress(idx, total, overall, f"[{idx + 1}/{total}] {status}")

                result = self.generate_image(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preset=preset,
                    checkpoint=checkpoint,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg=cfg,
                    sampler=sampler,
                    scheduler=scheduler,
                    seed=seed,
                    wait=True,
                    on_progress=item_progress,
                )

                results.append(result)

                if not result["success"]:
                    errors.append(f"Prompt {idx}: {result.get('error', 'Unknown error')}")

                # Final progress for this item
                if on_progress:
                    overall = (idx + 1) / total
                    status = "Complete" if result["success"] else "Failed"
                    on_progress(idx, total, overall, f"[{idx + 1}/{total}] {status}")

            except Exception as e:
                logger.error(f"Batch item {idx} failed: {e}")
                errors.append(f"Prompt {idx}: {str(e)}")
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "images": [],
                        "prompt_id": None,
                        "seed": seed,
                    }
                )

        elapsed = time_module.time() - start_time
        success_count = sum(1 for r in results if r.get("success", False))

        logger.info(
            "Batch complete",
            extra={
                "total": total,
                "success": success_count,
                "failed": total - success_count,
                "elapsed": f"{elapsed:.1f}s",
            },
        )

        return {
            "success": success_count == total,
            "results": results,
            "errors": errors,
            "total": total,
            "success_count": success_count,
            "elapsed_seconds": elapsed,
        }

    def generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        preset: str = "standard",
        init_image: str | None = None,
        wait: bool = True,
        timeout: float | None = None,
        on_progress: Callable[[float, str], None] | None = None,
        # Override individual settings (backwards compatible)
        checkpoint: str = "",
        motion_model: str = "",
        width: int | None = None,
        height: int | None = None,
        frames: int | None = None,
        fps: int | None = None,
        steps: int | None = None,
        cfg: float | None = None,
        seed: int = -1,
        motion_scale: float | None = None,
    ) -> dict[str, Any]:
        """
        High-level video generation using multi-model VideoWorkflowBuilder.

        Supports AnimateDiff (v2/v3/Lightning), SVD, CogVideoX, and Hunyuan.

        Args:
            prompt: Text description of the video
            negative_prompt: What to avoid
            preset: Video preset (quick, standard, quality, cinematic, portrait,
                   action, svd_short, svd_long, cogvideo, hunyuan, hunyuan_fast)
            init_image: Image name for img2vid models (SVD/LTXV/Wan). Upload the
                   image first with upload_image() and pass its "ref" value; it
                   is wired into a core LoadImage node.
            wait: Whether to wait for completion
            timeout: Generation timeout
            on_progress: Optional callback(progress: 0.0-1.0, status: str) for progress updates
            # Override any preset settings:
            checkpoint: Model checkpoint (for AnimateDiff)
            width, height, frames, fps, steps, cfg, seed, motion_scale

        Returns:
            Dict with success, prompt_id, videos, error, seed, preset
        """
        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.video_timeout

        with LogContext(request_id):
            result = {
                "success": False,
                "prompt_id": None,
                "videos": [],
                "error": None,
                "seed": seed,
                "preset": preset,
            }

            logger.info(
                "Starting video generation", extra={"preset": preset, "prompt_length": len(prompt)}
            )

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            # Build workflow using VideoWorkflowBuilder
            try:
                from .video import build_video_workflow

                # Build overrides dict from non-None parameters
                overrides = {}
                if checkpoint:
                    overrides["checkpoint"] = checkpoint
                if width is not None:
                    overrides["width"] = width
                if height is not None:
                    overrides["height"] = height
                if frames is not None:
                    overrides["frames"] = frames
                if fps is not None:
                    overrides["fps"] = fps
                if steps is not None:
                    overrides["steps"] = steps
                if cfg is not None:
                    overrides["cfg"] = cfg
                if seed != -1:
                    overrides["seed"] = seed
                if motion_scale is not None:
                    overrides["motion_scale"] = motion_scale

                workflow = build_video_workflow(
                    prompt=prompt,
                    negative=negative_prompt or "ugly, blurry, low quality, distorted",
                    preset=preset,
                    init_image=init_image,
                    **overrides,
                )

                # Extract actual seed from workflow (video.py generates random if -1)
                if isinstance(workflow, dict):
                    result["seed"] = _extract_workflow_seed(workflow, default=seed)

            except Exception as e:
                logger.warning(f"VideoWorkflowBuilder failed, falling back to legacy: {e}")
                # Fallback to legacy build_video_workflow method
                workflow = self.build_video_workflow(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    checkpoint=checkpoint,
                    motion_model=motion_model,
                    width=width or 512,
                    height=height or 512,
                    frames=frames or 16,
                    fps=fps or 8,
                    steps=steps or 20,
                    cfg=cfg or 7.0,
                    seed=seed,
                    motion_scale=motion_scale or 1.0,
                )
                # Safe nested access for legacy workflow
                result["seed"] = _safe_get_nested(workflow, "7", "inputs", "seed", default=seed)

            prompt_id = self.queue_prompt(workflow)
            if not prompt_id:
                result["error"] = "Failed to queue prompt"
                return result

            result["prompt_id"] = prompt_id

            if not wait:
                result["success"] = True
                return result

            history = self.wait_for_completion(prompt_id, timeout=timeout, on_progress=on_progress)
            if not history:
                result["error"] = f"Generation timed out after {timeout}s"
                return result

            status = history.get("status", {})
            if status.get("status_str") == "error":
                error_msgs = status.get("messages", [["Unknown error"]])
                result["error"] = str(error_msgs[0] if error_msgs else "Unknown error")
                return result

            # Extract videos. VHS_VideoCombine reports under 'gifs'/'videos';
            # core SaveVideo (settings output="core") reports under 'images'
            # WITH an 'animated' flag -- the flag is what separates it from a
            # SaveImage node's stills.
            outputs = history.get("outputs", {})
            if isinstance(outputs, dict):
                for node_output in outputs.values():
                    if isinstance(node_output, dict):
                        keys: tuple[str, ...] = ("gifs", "videos")
                        if node_output.get("animated"):
                            keys = ("gifs", "videos", "images")
                        for key in keys:
                            if key in node_output:
                                video_list = node_output[key]
                                if isinstance(video_list, list):
                                    for vid in video_list:
                                        if isinstance(vid, dict):
                                            result["videos"].append(
                                                {
                                                    "filename": vid.get("filename"),
                                                    "subfolder": vid.get("subfolder", ""),
                                                    "type": vid.get("type", "output"),
                                                }
                                            )

            result["success"] = len(result["videos"]) > 0

            if result["success"]:
                logger.info(
                    "Video generation complete", extra={"video_count": len(result["videos"])}
                )

            return result

    # =========================================================================
    # SHARED PROFILE PLUMBING (v3.1.0)
    # =========================================================================

    def _resolve_input_ref(self, source: Any, kind: str = "image") -> str:
        """
        Turn any reasonable input-source spelling into a server-side ref.

        Accepts the dict returned by ``upload_image()``/``upload_audio()``,
        raw bytes (uploaded now), a local file path (uploaded now), or a
        string that is already a server-side ref (passed through).
        """
        if isinstance(source, dict):
            ref = source.get("ref") or source.get("name")
            if isinstance(ref, str) and ref:
                return ref
            raise ValidationError(
                "Input dict has no usable 'ref'/'name'",
                suggestions=["Pass the dict returned by upload_image()/upload_audio()"],
            )
        if isinstance(source, (bytes, bytearray, memoryview)):
            uploaded = self.upload_audio(source) if kind == "audio" else self.upload_image(source)
            return uploaded["ref"]
        if isinstance(source, (str, Path)):
            path = Path(source)
            try:
                is_file = path.is_file()
            except OSError:
                is_file = False
            if is_file:
                uploaded = self.upload_audio(path) if kind == "audio" else self.upload_image(path)
                return uploaded["ref"]
            return str(source)
        raise InvalidParameterError(
            parameter=kind,
            value=type(source).__name__,
            reason="expected an upload dict, local path, raw bytes, or server-side ref",
        )

    def _execute_and_collect(
        self,
        workflow: dict,
        result: dict[str, Any],
        wait: bool,
        timeout: float,
        on_progress: "Callable[[float, str], None] | None",
    ) -> dict | None:
        """
        Queue a workflow and (optionally) wait; fill prompt_id/error on
        ``result``. Returns the history entry when execution completed, else
        None (result explains why; for wait=False, success is already set).
        """
        prompt_id = self.queue_prompt(workflow)
        if not prompt_id:
            result["error"] = "Failed to queue prompt"
            return None
        result["prompt_id"] = prompt_id

        if not wait:
            result["success"] = True
            return None

        history = self.wait_for_completion(prompt_id, timeout=timeout, on_progress=on_progress)
        if not history:
            result["error"] = f"Generation timed out after {timeout}s"
            return None

        status = history.get("status", {})
        if status.get("status_str") == "error":
            error_msgs = status.get("messages", [["Unknown error"]])
            result["error"] = str(error_msgs[0] if error_msgs else "Unknown error")
            return None
        return history

    @staticmethod
    def _collect_output_files(history: dict, keys: "tuple[str, ...]") -> list[dict[str, Any]]:
        """
        Pull file entries ({filename, subfolder, type}) out of a history
        entry's outputs for the given keys ("images", "audio", "3d", "files",
        "gifs", "videos" -- each save-node family reports under its own key).
        """
        files: list[dict[str, Any]] = []
        outputs = history.get("outputs", {})
        if not isinstance(outputs, dict):
            return files
        for node_output in outputs.values():
            if not isinstance(node_output, dict):
                continue
            for key in keys:
                entries = node_output.get(key)
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if isinstance(entry, dict) and entry.get("filename"):
                        files.append(
                            {
                                "filename": entry.get("filename"),
                                "subfolder": entry.get("subfolder", ""),
                                "type": entry.get("type", "output"),
                            }
                        )
        return files

    @staticmethod
    def _collect_output_text(history: dict) -> list[str]:
        """
        Pull inline text results out of a history entry.

        SaveText reports the raw text under the "text" key (as a tuple)
        alongside the saved file, so most inference results need no second
        round-trip.
        """
        texts: list[str] = []
        outputs = history.get("outputs", {})
        if not isinstance(outputs, dict):
            return texts
        for node_output in outputs.values():
            if isinstance(node_output, dict):
                inline = node_output.get("text")
                if isinstance(inline, (list, tuple)):
                    texts.extend(t for t in inline if isinstance(t, str))
        return texts

    # =========================================================================
    # 3D GENERATION (v3.1.0)
    # =========================================================================

    def generate_3d(
        self,
        image: Any,
        preset: str = "standard",
        wait: bool = True,
        timeout: float | None = None,
        on_progress: "Callable[[float, str], None] | None" = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """
        High-level image-to-3D generation (Hunyuan3D-2, all core nodes).

        Args:
            image: The subject image -- a local path, raw bytes, an
                ``upload_image()`` result dict, or a server-side ref.
            preset: 3D preset (standard, draft, detail).
            wait: Whether to wait for completion.
            timeout: Generation timeout (defaults to the video timeout --
                mesh decode is slow).
            on_progress: Optional callback(progress, status).
            **overrides: Any ThreeDSettings field (steps, cfg, seed,
                octree_resolution, ...).

        Returns:
            Dict with success, prompt_id, meshes (GLB file entries for
            ``get_file()``), error, seed, preset.
        """
        from .three_d import build_3d_workflow

        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.video_timeout

        with LogContext(request_id):
            result: dict[str, Any] = {
                "success": False,
                "prompt_id": None,
                "meshes": [],
                "error": None,
                "seed": overrides.get("seed", -1),
                "preset": preset,
            }

            logger.info("Starting 3D generation", extra={"preset": preset})

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            try:
                image_ref = self._resolve_input_ref(image, kind="image")
                workflow = build_3d_workflow(image_ref, preset=preset, **overrides)
            except (ValueError, ValidationError) as e:
                result["error"] = str(e)
                return result

            result["seed"] = _extract_workflow_seed(workflow, default=result["seed"])

            history = self._execute_and_collect(workflow, result, wait, timeout, on_progress)
            if history is None:
                return result

            # SaveGLB registers under the "3d" outputs key.
            result["meshes"] = self._collect_output_files(history, ("3d",))
            result["success"] = len(result["meshes"]) > 0

            if result["success"]:
                logger.info("3D generation complete", extra={"mesh_count": len(result["meshes"])})
            else:
                logger.warning("3D generation produced no meshes")

            return result

    # =========================================================================
    # AUDIO GENERATION (v3.1.0)
    # =========================================================================

    def generate_audio(
        self,
        tags: str,
        lyrics: str = "",
        negative_tags: str = "",
        preset: str = "music",
        wait: bool = True,
        timeout: float | None = None,
        on_progress: "Callable[[float, str], None] | None" = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """
        High-level text-to-music generation (ACE-Step 1.5, all core nodes).

        Args:
            tags: Style/genre tags -- the main prompt.
            lyrics: Optional lyrics; empty for instrumental.
            negative_tags: Tags to steer away from.
            preset: Audio preset (music, music_long, jingle, music_mp3, draft).
            **overrides: Any AudioSettings field (seconds, bpm, keyscale,
                format, quality, seed, ...).

        Returns:
            Dict with success, prompt_id, audios (file entries for
            ``get_file()``), error, seed, preset.
        """
        from .audio import build_audio_workflow

        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.video_timeout

        with LogContext(request_id):
            result: dict[str, Any] = {
                "success": False,
                "prompt_id": None,
                "audios": [],
                "error": None,
                "seed": overrides.get("seed", -1),
                "preset": preset,
            }

            logger.info("Starting audio generation", extra={"preset": preset})

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            try:
                workflow = build_audio_workflow(
                    tags, lyrics=lyrics, negative_tags=negative_tags, preset=preset, **overrides
                )
            except (ValueError, ValidationError) as e:
                result["error"] = str(e)
                return result

            result["seed"] = _extract_workflow_seed(workflow, default=result["seed"])

            history = self._execute_and_collect(workflow, result, wait, timeout, on_progress)
            if history is None:
                return result

            # SaveAudioAdvanced registers under the "audio" outputs key.
            result["audios"] = self._collect_output_files(history, ("audio",))
            result["success"] = len(result["audios"]) > 0

            if result["success"]:
                logger.info(
                    "Audio generation complete", extra={"audio_count": len(result["audios"])}
                )
            else:
                logger.warning("Audio generation produced no files")

            return result

    def separate_audio(
        self,
        audio: Any,
        stems: "tuple[str, ...] | list[str] | None" = None,
        wait: bool = True,
        timeout: float | None = None,
        on_progress: "Callable[[float, str], None] | None" = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Split audio into stems (bass, drums, other, vocals).

        Requires the ``audio-separation-nodes-comfyui`` pack (declared in
        NODE_PACKS; ``check_workflow_dependencies`` names it when missing).

        Args:
            audio: Source audio -- local path, raw bytes, upload dict, or
                server-side ref.
            stems: Which stems to save (default: all four).

        Returns:
            Dict with success, prompt_id, audios (each entry carries a
            "stem" label recovered from its filename), error.
        """
        from .audio import SEPARATION_STEMS, build_audio_separation_workflow

        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.video_timeout
        stems = tuple(stems) if stems else SEPARATION_STEMS

        with LogContext(request_id):
            result: dict[str, Any] = {
                "success": False,
                "prompt_id": None,
                "audios": [],
                "error": None,
                "stems": list(stems),
            }

            logger.info("Starting audio separation", extra={"stems": list(stems)})

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            try:
                audio_ref = self._resolve_input_ref(audio, kind="audio")
                workflow = build_audio_separation_workflow(audio_ref, stems=stems, **kwargs)
            except (ValueError, ValidationError) as e:
                result["error"] = str(e)
                return result

            history = self._execute_and_collect(workflow, result, wait, timeout, on_progress)
            if history is None:
                return result

            audios = self._collect_output_files(history, ("audio",))
            for entry in audios:
                name = entry.get("filename") or ""
                entry["stem"] = next((s for s in stems if f"_{s}" in name), None)
            result["audios"] = audios
            result["success"] = len(audios) > 0

            if result["success"]:
                logger.info("Audio separation complete", extra={"stem_count": len(audios)})

            return result

    # =========================================================================
    # INFERENCE (v3.1.0)
    # =========================================================================

    def run_inference(
        self,
        image: Any,
        task: str = "caption",
        text_input: str = "",
        wait: bool = True,
        timeout: float | None = None,
        on_progress: "Callable[[float, str], None] | None" = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """
        Non-generative inference: caption, tag, detect, segment, OCR.

        Requires the ``comfyui-florence2`` pack (plus
        ``comfyui-segment-anything-2`` for detect); both are declared in
        NODE_PACKS so ``check_workflow_dependencies`` names what's missing.

        Args:
            image: Input image -- local path, raw bytes, upload dict, or ref.
            task: caption | detailed_caption | more_detailed_caption | tag |
                detect | segment | ocr.
            text_input: Required for detect/segment: what to find.
            **overrides: Any InferenceSettings field (model, precision, ...).

        Returns:
            Dict with success, prompt_id, task, text (first inline result --
            the caption/tags/coordinates, no second round-trip needed),
            texts, files (saved text files), images (segment masks as PNGs),
            error.
        """
        from .inference import build_inference_workflow

        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.generation_timeout

        with LogContext(request_id):
            result: dict[str, Any] = {
                "success": False,
                "prompt_id": None,
                "task": task,
                "text": None,
                "texts": [],
                "files": [],
                "images": [],
                "error": None,
            }

            logger.info("Starting inference", extra={"task": task})

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            try:
                image_ref = self._resolve_input_ref(image, kind="image")
                workflow = build_inference_workflow(
                    image_ref, task=task, text_input=text_input, **overrides
                )
            except (ValueError, ValidationError) as e:
                result["error"] = str(e)
                return result

            history = self._execute_and_collect(workflow, result, wait, timeout, on_progress)
            if history is None:
                return result

            result["texts"] = self._collect_output_text(history)
            result["text"] = result["texts"][0] if result["texts"] else None
            # SaveText also registers its written file under "files";
            # segment masks land under "images".
            result["files"] = self._collect_output_files(history, ("files",))
            result["images"] = self._collect_output_files(history, ("images",))
            result["success"] = bool(result["texts"] or result["files"] or result["images"])

            if result["success"]:
                logger.info("Inference complete", extra={"task": task})
            else:
                logger.warning("Inference produced no output", extra={"task": task})

            return result

    # =========================================================================
    # IMAGE EDIT (v3.1.0)
    # =========================================================================

    def edit_image(
        self,
        prompt: str,
        images: "Any | list[Any]",
        negative: str = "",
        wait: bool = True,
        timeout: float | None = None,
        on_progress: "Callable[[float, str], None] | None" = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Instruction-based image editing (Qwen-Image-Edit-2511).

        Args:
            prompt: The edit instruction.
            images: 1-3 reference images (local paths, bytes, upload dicts,
                or server-side refs; a single value is fine).
            negative: Negative prompt.
            **kwargs: Any build_qwen_edit_workflow parameter (unet, width,
                height, steps, cfg, shift, seed).

        Returns:
            Dict with success, prompt_id, images (file entries), error, seed.
        """
        from .workflows import build_qwen_edit_workflow

        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.generation_timeout

        with LogContext(request_id):
            result: dict[str, Any] = {
                "success": False,
                "prompt_id": None,
                "images": [],
                "error": None,
                "seed": kwargs.get("seed", -1),
            }

            logger.info("Starting image edit")

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            sources = images if isinstance(images, (list, tuple)) else [images]
            try:
                refs = [self._resolve_input_ref(src, kind="image") for src in sources]
                workflow = build_qwen_edit_workflow(prompt, refs, negative=negative, **kwargs)
            except (ValueError, ValidationError) as e:
                result["error"] = str(e)
                return result

            result["seed"] = _extract_workflow_seed(workflow, default=result["seed"])

            history = self._execute_and_collect(workflow, result, wait, timeout, on_progress)
            if history is None:
                return result

            result["images"] = self._collect_output_files(history, ("images",))
            result["success"] = len(result["images"]) > 0

            if result["success"]:
                logger.info("Image edit complete", extra={"image_count": len(result["images"])})

            return result

    # =========================================================================
    # PROVENANCE RE-RUN (v3.1.0, metadata profile)
    # =========================================================================

    def rerun_from_png(
        self,
        source: "str | Path | bytes | bytearray | memoryview",
        wait: bool = True,
        timeout: float | None = None,
        on_progress: "Callable[[float, str], None] | None" = None,
        extra_pnginfo: dict | None = None,
    ) -> dict[str, Any]:
        """
        Re-run the exact graph embedded in a ComfyUI output PNG.

        The API-format graph is recoverable from any (metadata-enabled)
        output PNG independently of the GUI: this reads the ``prompt`` text
        chunk and re-POSTs it verbatim. Referenced input files (LoadImage
        refs etc.) must still exist on the server.

        Args:
            source: PNG path or bytes.
            extra_pnginfo: Optional custom provenance for the re-run's own
                outputs (see :meth:`queue_prompt`).

        Returns:
            Dict with success, prompt_id, seed, and every output family:
            images, videos, audios, meshes, files, texts, error.
        """
        from .metadata import extract_prompt_graph

        request_id = str(uuid.uuid4())[:8]
        timeout = timeout or settings.generation.video_timeout

        with LogContext(request_id):
            result: dict[str, Any] = {
                "success": False,
                "prompt_id": None,
                "images": [],
                "videos": [],
                "audios": [],
                "meshes": [],
                "files": [],
                "texts": [],
                "error": None,
                "seed": -1,
            }

            try:
                workflow = extract_prompt_graph(source)
            except ValidationError as e:
                result["error"] = str(e)
                return result

            logger.info("Re-running graph from PNG provenance", extra={"nodes": len(workflow)})

            try:
                self.ensure_online()
            except ComfyUIOfflineError as e:
                result["error"] = str(e)
                return result

            result["seed"] = _extract_workflow_seed(workflow, default=-1)

            prompt_id = self.queue_prompt(workflow, extra_pnginfo=extra_pnginfo)
            if not prompt_id:
                result["error"] = "Failed to queue prompt"
                return result
            result["prompt_id"] = prompt_id

            if not wait:
                result["success"] = True
                return result

            history = self.wait_for_completion(prompt_id, timeout=timeout, on_progress=on_progress)
            if not history:
                result["error"] = f"Generation timed out after {timeout}s"
                return result

            status = history.get("status", {})
            if status.get("status_str") == "error":
                error_msgs = status.get("messages", [["Unknown error"]])
                result["error"] = str(error_msgs[0] if error_msgs else "Unknown error")
                return result

            result["images"] = self._collect_output_files(history, ("images",))
            result["videos"] = self._collect_output_files(history, ("gifs", "videos"))
            result["audios"] = self._collect_output_files(history, ("audio",))
            result["meshes"] = self._collect_output_files(history, ("3d",))
            result["files"] = self._collect_output_files(history, ("files",))
            result["texts"] = self._collect_output_text(history)
            result["success"] = any(
                result[key] for key in ("images", "videos", "audios", "meshes", "files", "texts")
            )
            return result
