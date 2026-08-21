"""
Comfy Headless - Workflow System
================================

Template-based workflow compilation for ComfyUI.
Makes complex workflows accessible through simple parameters.

Features:
- Workflow templates with parameter injection
- Presets for common configurations
- Automatic model resolution
- VRAM-aware optimization
- Validation and error handling

v2.4.0 Enhancements (2026 Best Practices):
- Semantic versioning for workflows (SemVer)
- Workflow validation with JSON schema
- Hash-based change detection
- Immutable workflow snapshots
- Workflow caching with TTL
- DAG validation and cycle detection
- Node-level type checking
"""

import copy
import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    # Enums
    "WorkflowCategory",
    "ParameterType",
    # Data classes
    "ParameterDef",
    "PresetDef",
    "WorkflowTemplate",
    "CompiledWorkflow",
    # Versioning
    "WorkflowVersion",
    "WorkflowSnapshot",
    # Snapshot management
    "SnapshotManager",
    "get_snapshot_manager",
    # Hashing and caching
    "compute_workflow_hash",
    "WorkflowCache",
    "get_workflow_cache",
    # DAG validation
    "DAGValidator",
    "validate_workflow_dag",
    # Presets
    "GENERATION_PRESETS",
    # Compiler
    "WorkflowCompiler",
    "get_compiler",
    # Optimizer
    "WorkflowOptimizer",
    "get_optimizer",
    # Library
    "TemplateLibrary",
    "get_library",
    # Built-in templates
    "create_txt2img_template",
    "create_txt2img_hires_template",
    "create_upscale_template",
    "create_inpaint_template",
    "create_qwen_txt2img_template",
    # Qwen / ControlNet builders (v3.1.0)
    "build_qwen_edit_workflow",
    "build_controlnet_workflow",
    "QWEN_TXT2IMG_UNETS",
    "QWEN_EDIT_UNETS",
    "UNION_CONTROL_TYPES",
    # Convenience functions
    "compile_workflow",
    "get_preset_info",
    "list_presets",
    # VRAM estimation constants (WorkflowOptimizer class attributes)
    # VRAM_BASE_MODEL_GB, VRAM_PER_MEGAPIXEL_GB, VRAM_PER_VIDEO_FRAME_GB
]


# =============================================================================
# ENUMS
# =============================================================================


class WorkflowCategory(str, Enum):
    TEXT_TO_IMAGE = "text-to-image"
    IMG_TO_IMG = "img-to-img"
    UPSCALE = "upscale"
    VIDEO = "video"
    INPAINT = "inpaint"


class ParameterType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    CHOICE = "choice"
    MODEL = "model"
    IMAGE = "image"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ParameterDef:
    """Definition of a workflow parameter."""

    type: ParameterType
    node_id: str
    input_name: str
    required: bool = False
    default: Any = None
    min: float | None = None
    max: float | None = None
    choices: list[str] | None = None
    label: str | None = None
    description: str | None = None


@dataclass
class PresetDef:
    """A preset configuration."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class WorkflowTemplate:
    """A workflow template that can be compiled with parameters."""

    id: str
    name: str
    description: str
    category: WorkflowCategory
    workflow: dict[str, Any]
    parameters: dict[str, ParameterDef] = field(default_factory=dict)
    presets: dict[str, PresetDef] = field(default_factory=dict)
    min_vram_gb: int = 6
    tags: list[str] = field(default_factory=list)


@dataclass
class CompiledWorkflow:
    """A compiled workflow ready for execution."""

    template_id: str
    template_name: str
    workflow: dict[str, Any]
    parameters: dict[str, Any]
    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    # v2.4: Added versioning and hashing
    version: str = "1.0.0"
    workflow_hash: str = ""
    compiled_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Compute hash after initialization."""
        if not self.workflow_hash and self.workflow:
            self.workflow_hash = compute_workflow_hash(self.workflow)


# =============================================================================
# WORKFLOW VERSIONING (2026 Best Practice: Semantic Versioning)
# =============================================================================


@dataclass
class WorkflowVersion:
    """
    Semantic version for workflows (SemVer).

    - Major: Breaking changes (restructured nodes, removed parameters)
    - Minor: Backward-compatible additions (new optional parameters)
    - Patch: Bug fixes, small clarifications
    """

    major: int = 1
    minor: int = 0
    patch: int = 0
    label: str = ""  # e.g., "beta", "rc1"

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.label}" if self.label else base

    @classmethod
    def parse(cls, version_str: str) -> "WorkflowVersion":
        """Parse version string like '1.2.3' or '1.2.3-beta'."""
        label = ""
        if "-" in version_str:
            version_str, label = version_str.split("-", 1)
        parts = version_str.split(".")
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 1,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
            label=label,
        )

    def bump_major(self) -> "WorkflowVersion":
        return WorkflowVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> "WorkflowVersion":
        return WorkflowVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "WorkflowVersion":
        return WorkflowVersion(self.major, self.minor, self.patch + 1)

    def __lt__(self, other: "WorkflowVersion") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


@dataclass
class WorkflowSnapshot:
    """
    Immutable snapshot of a compiled workflow for version control.

    Supports rollback, comparison, and audit trails.
    """

    id: str
    version: WorkflowVersion
    workflow: dict[str, Any]
    parameters: dict[str, Any]
    workflow_hash: str
    created_at: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize snapshot for storage."""
        return {
            "id": self.id,
            "version": str(self.version),
            "workflow": self.workflow,
            "parameters": self.parameters,
            "workflow_hash": self.workflow_hash,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowSnapshot":
        """Deserialize snapshot from storage."""
        return cls(
            id=data["id"],
            version=WorkflowVersion.parse(data["version"]),
            workflow=data["workflow"],
            parameters=data["parameters"],
            workflow_hash=data["workflow_hash"],
            created_at=data["created_at"],
            metadata=data.get("metadata", {}),
        )

    def diff(self, other: "WorkflowSnapshot") -> dict[str, Any]:
        """
        Compare this snapshot with another.

        Returns a dict showing differences in parameters and workflow structure.
        """
        diffs = {
            "version_changed": str(self.version) != str(other.version),
            "hash_changed": self.workflow_hash != other.workflow_hash,
            "parameter_changes": {},
            "node_changes": {"added": [], "removed": [], "modified": []},
        }

        # Parameter differences
        all_params = set(self.parameters.keys()) | set(other.parameters.keys())
        for param in all_params:
            old_val = self.parameters.get(param)
            new_val = other.parameters.get(param)
            if old_val != new_val:
                diffs["parameter_changes"][param] = {
                    "old": old_val,
                    "new": new_val,
                }

        # Node differences
        old_nodes = set(self.workflow.keys())
        new_nodes = set(other.workflow.keys())

        diffs["node_changes"]["added"] = list(new_nodes - old_nodes)
        diffs["node_changes"]["removed"] = list(old_nodes - new_nodes)

        for node_id in old_nodes & new_nodes:
            if self.workflow[node_id] != other.workflow[node_id]:
                diffs["node_changes"]["modified"].append(node_id)

        return diffs


class SnapshotManager:
    """
    Manages workflow snapshots for version control and rollback.

    Provides:
    - Automatic snapshot creation on compilation
    - Persistent storage (JSON files)
    - Rollback to previous versions
    - Snapshot comparison and diff
    - Retention policies (max snapshots per workflow)
    """

    def __init__(
        self,
        storage_path: str | None = None,
        max_snapshots_per_workflow: int = 10,
        auto_snapshot: bool = True,
    ):
        """
        Initialize the snapshot manager.

        Args:
            storage_path: Directory for snapshot storage. Defaults to temp dir.
            max_snapshots_per_workflow: Max snapshots to keep per workflow ID.
            auto_snapshot: Whether to auto-snapshot on compilation.
        """
        from pathlib import Path

        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            from .config import get_temp_dir

            self.storage_path = get_temp_dir() / "snapshots"

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_snapshots = max_snapshots_per_workflow
        self.auto_snapshot = auto_snapshot

        # In-memory index for quick lookups
        self._index: dict[str, list[str]] = {}  # workflow_id -> [snapshot_ids]
        self._load_index()

    def _load_index(self):
        """Load snapshot index from disk."""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file) as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load snapshot index: {e}")
                self._index = {}
        else:
            self._index = {}

    def _save_index(self):
        """Save snapshot index to disk."""
        index_file = self.storage_path / "index.json"
        try:
            with open(index_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save snapshot index: {e}")

    def _generate_snapshot_id(self, workflow_id: str) -> str:
        """Generate a unique snapshot ID."""
        import uuid

        timestamp = int(time.time())
        short_uuid = uuid.uuid4().hex[:8]
        return f"{workflow_id}_{timestamp}_{short_uuid}"

    def create_snapshot(
        self,
        compiled: "CompiledWorkflow",
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowSnapshot:
        """
        Create a snapshot from a compiled workflow.

        Args:
            compiled: The compiled workflow to snapshot
            metadata: Optional metadata (author, reason, etc.)

        Returns:
            The created snapshot
        """
        snapshot_id = self._generate_snapshot_id(compiled.template_id)

        # Determine version
        existing = self.list_snapshots(compiled.template_id)
        if existing:
            latest = existing[-1]
            # Bump patch version if hash changed, otherwise same version
            if latest.workflow_hash != compiled.workflow_hash:
                version = latest.version.bump_patch()
            else:
                version = latest.version
        else:
            version = WorkflowVersion(1, 0, 0)

        snapshot = WorkflowSnapshot(
            id=snapshot_id,
            version=version,
            workflow=copy.deepcopy(compiled.workflow),
            parameters=copy.deepcopy(compiled.parameters),
            workflow_hash=compiled.workflow_hash,
            created_at=time.time(),
            metadata=metadata or {},
        )

        # Save to disk
        self._save_snapshot(snapshot)

        # Update index
        if compiled.template_id not in self._index:
            self._index[compiled.template_id] = []
        self._index[compiled.template_id].append(snapshot_id)
        self._save_index()

        # Enforce retention policy
        self._enforce_retention(compiled.template_id)

        logger.debug(
            f"Created snapshot {snapshot_id} for {compiled.template_id}",
            extra={"version": str(version), "hash": compiled.workflow_hash},
        )

        return snapshot

    def _save_snapshot(self, snapshot: WorkflowSnapshot):
        """Save a snapshot to disk."""
        snapshot_file = self.storage_path / f"{snapshot.id}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

    def _load_snapshot(self, snapshot_id: str) -> WorkflowSnapshot | None:
        """Load a snapshot from disk."""
        snapshot_file = self.storage_path / f"{snapshot_id}.json"
        if not snapshot_file.exists():
            return None
        try:
            with open(snapshot_file) as f:
                data = json.load(f)
            return WorkflowSnapshot.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load snapshot {snapshot_id}: {e}")
            return None

    def _enforce_retention(self, workflow_id: str):
        """Remove old snapshots beyond the retention limit."""
        snapshot_ids = self._index.get(workflow_id, [])
        if len(snapshot_ids) <= self.max_snapshots:
            return

        # Remove oldest snapshots
        to_remove = snapshot_ids[: -self.max_snapshots]
        for snapshot_id in to_remove:
            self.delete_snapshot(snapshot_id)

        self._index[workflow_id] = snapshot_ids[-self.max_snapshots :]
        self._save_index()

    def get_snapshot(self, snapshot_id: str) -> WorkflowSnapshot | None:
        """Get a snapshot by ID."""
        return self._load_snapshot(snapshot_id)

    def list_snapshots(
        self,
        workflow_id: str,
        limit: int | None = None,
    ) -> list[WorkflowSnapshot]:
        """
        List all snapshots for a workflow.

        Args:
            workflow_id: The workflow template ID
            limit: Maximum number of snapshots to return (most recent)

        Returns:
            List of snapshots, sorted by creation time (oldest first)
        """
        snapshot_ids = self._index.get(workflow_id, [])
        if limit:
            snapshot_ids = snapshot_ids[-limit:]

        snapshots = []
        for sid in snapshot_ids:
            snapshot = self._load_snapshot(sid)
            if snapshot:
                snapshots.append(snapshot)

        return sorted(snapshots, key=lambda s: s.created_at)

    def get_latest(self, workflow_id: str) -> WorkflowSnapshot | None:
        """Get the most recent snapshot for a workflow."""
        snapshots = self.list_snapshots(workflow_id, limit=1)
        return snapshots[-1] if snapshots else None

    def rollback(
        self,
        snapshot_id: str,
        _compiler: Optional["WorkflowCompiler"] = None,
    ) -> CompiledWorkflow | None:
        """
        Rollback to a previous snapshot.

        Args:
            snapshot_id: The snapshot to restore
            compiler: Optional compiler for re-compilation

        Returns:
            A CompiledWorkflow from the snapshot, or None if not found
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            logger.warning(f"Snapshot not found: {snapshot_id}")
            return None

        # Extract workflow ID from snapshot ID
        parts = snapshot_id.rsplit("_", 2)
        workflow_id = parts[0] if len(parts) >= 3 else "unknown"

        compiled = CompiledWorkflow(
            template_id=workflow_id,
            template_name=f"Restored from {snapshot_id}",
            workflow=copy.deepcopy(snapshot.workflow),
            parameters=copy.deepcopy(snapshot.parameters),
            is_valid=True,
            version=str(snapshot.version),
            workflow_hash=snapshot.workflow_hash,
            compiled_at=time.time(),
        )

        logger.info(
            f"Rolled back to snapshot {snapshot_id}", extra={"version": str(snapshot.version)}
        )

        return compiled

    def compare(
        self,
        snapshot_id_a: str,
        snapshot_id_b: str,
    ) -> dict[str, Any] | None:
        """
        Compare two snapshots.

        Args:
            snapshot_id_a: First snapshot ID
            snapshot_id_b: Second snapshot ID

        Returns:
            Diff dictionary or None if either snapshot not found
        """
        snapshot_a = self.get_snapshot(snapshot_id_a)
        snapshot_b = self.get_snapshot(snapshot_id_b)

        if not snapshot_a or not snapshot_b:
            return None

        return snapshot_a.diff(snapshot_b)

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        snapshot_file = self.storage_path / f"{snapshot_id}.json"
        if snapshot_file.exists():
            try:
                snapshot_file.unlink()
                logger.debug(f"Deleted snapshot: {snapshot_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete snapshot {snapshot_id}: {e}")
                return False
        return False

    def stats(self) -> dict[str, Any]:
        """Get snapshot manager statistics."""
        total_snapshots = sum(len(ids) for ids in self._index.values())
        return {
            "storage_path": str(self.storage_path),
            "workflow_count": len(self._index),
            "total_snapshots": total_snapshots,
            "max_per_workflow": self.max_snapshots,
            "auto_snapshot": self.auto_snapshot,
        }


# Global snapshot manager instance
_snapshot_manager: SnapshotManager | None = None


def get_snapshot_manager(
    storage_path: str | None = None,
    max_snapshots: int = 10,
) -> SnapshotManager:
    """Get the global snapshot manager."""
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = SnapshotManager(
            storage_path=storage_path,
            max_snapshots_per_workflow=max_snapshots,
        )
    return _snapshot_manager


# =============================================================================
# WORKFLOW HASHING AND CACHING
# =============================================================================


def compute_workflow_hash(workflow: dict[str, Any]) -> str:
    """
    Compute a deterministic hash for a workflow.

    Used for change detection and caching.
    """
    # Sort keys for deterministic serialization
    serialized = json.dumps(workflow, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


class WorkflowCache:
    """
    LRU cache for compiled workflows with TTL support.

    Reduces compilation overhead for repeated requests.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[CompiledWorkflow, float]] = {}
        self._access_order: list[str] = []

    def _make_key(self, template_id: str, params: dict[str, Any], preset: str | None) -> str:
        """Create cache key from compilation inputs."""
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
        return f"{template_id}:{preset or 'none'}:{params_hash}"

    def get(
        self, template_id: str, params: dict[str, Any], preset: str | None = None
    ) -> CompiledWorkflow | None:
        """Get cached workflow if valid."""
        key = self._make_key(template_id, params, preset)

        if key not in self._cache:
            return None

        workflow, timestamp = self._cache[key]

        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            logger.debug(f"Cache expired: {key}")
            return None

        # Update access order (LRU)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cache hit: {key}")
        return workflow

    def set(
        self,
        template_id: str,
        params: dict[str, Any],
        preset: str | None,
        workflow: CompiledWorkflow,
    ):
        """Cache a compiled workflow."""
        key = self._make_key(template_id, params, preset)

        # Evict if at capacity
        while len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                logger.debug(f"Cache evicted: {oldest_key}")

        self._cache[key] = (workflow, time.time())
        self._access_order.append(key)
        logger.debug(f"Cache set: {key}")

    def invalidate(self, template_id: str | None = None):
        """Invalidate cache entries."""
        if template_id:
            # Invalidate specific template
            keys_to_remove = [k for k in self._cache if k.startswith(f"{template_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            logger.debug(f"Cache invalidated for template: {template_id}")
        else:
            # Clear all
            self._cache.clear()
            self._access_order.clear()
            logger.debug("Cache cleared")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


# Global cache instance
_workflow_cache = WorkflowCache()


def get_workflow_cache() -> WorkflowCache:
    """Get the global workflow cache."""
    return _workflow_cache


# =============================================================================
# DAG VALIDATION (2026: Node-level type checking)
# =============================================================================


class DAGValidator:
    """
    Validates workflow DAG structure.

    Checks:
    - No cycles (must be acyclic)
    - All referenced nodes exist
    - Node type constraints
    - Input/output compatibility

    Node output types can be fetched dynamically from ComfyUI or use
    the static fallback list.
    """

    # Known node types and their outputs (static fallback)
    NODE_OUTPUTS = {
        "CheckpointLoaderSimple": ["MODEL", "CLIP", "VAE"],
        "CLIPTextEncode": ["CONDITIONING"],
        "EmptyLatentImage": ["LATENT"],
        "KSampler": ["LATENT"],
        "VAEDecode": ["IMAGE"],
        "VAEEncode": ["LATENT"],
        "SaveImage": [],
        "LatentUpscale": ["LATENT"],
        "LoadImage": ["IMAGE", "MASK"],
        "ImageScale": ["IMAGE"],
        "ImageUpscaleWithModel": ["IMAGE"],
        "UpscaleModelLoader": ["UPSCALE_MODEL"],
        "SetLatentNoiseMask": ["LATENT"],
        "ControlNetLoader": ["CONTROL_NET"],
        "ControlNetApply": ["CONDITIONING"],
        "LoraLoader": ["MODEL", "CLIP"],
        "ADE_LoadAnimateDiffModel": ["MOTION_MODEL_ADE"],
        # Add more as needed
    }

    # Cache for dynamically fetched node info
    _dynamic_node_cache: dict[str, list[str]] | None = None
    _cache_timestamp: float = 0.0
    _cache_ttl: float = 300.0  # 5 minutes

    def __init__(self, comfyui_url: str | None = None):
        """
        Initialize DAGValidator.

        Args:
            comfyui_url: Optional ComfyUI URL for dynamic node fetching.
                        If None, uses static NODE_OUTPUTS only.
        """
        self.comfyui_url = comfyui_url

    def fetch_node_info(self, force: bool = False) -> dict[str, list[str]]:
        """
        Fetch node type information from ComfyUI.

        Caches results for 5 minutes to avoid repeated requests.

        Args:
            force: Force refresh even if cache is valid

        Returns:
            Dict mapping node class types to their output types
        """
        import time

        # Check cache
        if (
            not force
            and self._dynamic_node_cache is not None
            and time.time() - self._cache_timestamp < self._cache_ttl
        ):
            return self._dynamic_node_cache

        if not self.comfyui_url:
            return self.NODE_OUTPUTS.copy()

        try:
            import requests

            from .config import settings

            response = requests.get(
                f"{self.comfyui_url}/object_info", timeout=settings.comfyui.timeout_connect
            )

            if response.status_code == 200:
                data = response.json()
                node_outputs: dict[str, list[str]] = {}

                for node_type, info in data.items():
                    # Extract output types from the node info
                    output_info = info.get("output", [])
                    if isinstance(output_info, list):
                        node_outputs[node_type] = output_info
                    else:
                        node_outputs[node_type] = []

                self._dynamic_node_cache = node_outputs
                self._cache_timestamp = time.time()

                logger.debug(
                    "Fetched node info from ComfyUI", extra={"node_count": len(node_outputs)}
                )
                return node_outputs

        except Exception as e:
            logger.debug(f"Failed to fetch node info: {e}")

        # Fallback to static list
        return self.NODE_OUTPUTS.copy()

    def get_node_outputs(self, class_type: str) -> list[str] | None:
        """Get output types for a node class."""
        # Try dynamic cache first
        if self._dynamic_node_cache and class_type in self._dynamic_node_cache:
            return self._dynamic_node_cache[class_type]

        # Fall back to static list
        return self.NODE_OUTPUTS.get(class_type)

    def validate(self, workflow: dict[str, Any]) -> list[str]:
        """Validate workflow and return list of errors."""
        errors = []

        if not workflow:
            return ["Workflow is empty"]

        # Check for cycles
        cycle_error = self._check_cycles(workflow)
        if cycle_error:
            errors.append(cycle_error)

        # Validate node references
        errors.extend(self._validate_references(workflow))

        # Validate node types (if class_type present)
        errors.extend(self._validate_node_types(workflow))

        return errors

    def _check_cycles(self, workflow: dict[str, Any]) -> str | None:
        """Check for cycles in the DAG using DFS."""
        # Build adjacency list
        graph: dict[str, set[str]] = {node_id: set() for node_id in workflow}

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs", {})
            for input_value in inputs.values():
                # Connection format: [source_node_id, output_index]
                if isinstance(input_value, list) and len(input_value) == 2:
                    source_id = str(input_value[0])
                    if source_id in workflow:
                        graph[node_id].add(source_id)

        # DFS cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited and has_cycle(node):
                return "Workflow contains a cycle (not a valid DAG)"

        return None

    def _validate_references(self, workflow: dict[str, Any]) -> list[str]:
        """Validate all node references exist."""
        errors = []
        node_ids = set(workflow.keys())

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue

            inputs = node.get("inputs", {})
            for input_name, input_value in inputs.items():
                if isinstance(input_value, list) and len(input_value) == 2:
                    source_id = str(input_value[0])
                    if source_id not in node_ids:
                        errors.append(
                            f"Node '{node_id}' input '{input_name}' references "
                            f"non-existent node '{source_id}'"
                        )

        return errors

    def _validate_node_types(self, workflow: dict[str, Any]) -> list[str]:
        """Validate node class types and connections."""
        errors = []

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue

            class_type = node.get("class_type")
            if not class_type:
                continue

            # Check if we know this node type (using dynamic or static info)
            outputs = self.get_node_outputs(class_type)
            if outputs is not None:
                inputs = node.get("inputs", {})

                for _input_name, input_value in inputs.items():
                    if isinstance(input_value, list) and len(input_value) == 2:
                        source_id = str(input_value[0])
                        output_idx = input_value[1]

                        source_node = workflow.get(source_id)
                        if source_node:
                            source_type = source_node.get("class_type")
                            source_outputs = self.get_node_outputs(source_type)
                            if source_outputs is not None and output_idx >= len(source_outputs):
                                errors.append(
                                    f"Node '{node_id}' references invalid output "
                                    f"index {output_idx} from '{source_id}' "
                                    f"(has {len(source_outputs)} outputs)"
                                )

        return errors


# Global validator (no ComfyUI URL by default - uses static list)
_dag_validator = DAGValidator()


def validate_workflow_dag(workflow: dict[str, Any], comfyui_url: str | None = None) -> list[str]:
    """
    Validate workflow DAG structure.

    Args:
        workflow: The workflow to validate
        comfyui_url: Optional ComfyUI URL for dynamic node info fetching

    Returns:
        List of validation errors (empty if valid)
    """
    if comfyui_url:
        # Use dynamic validator with URL
        validator = DAGValidator(comfyui_url=comfyui_url)
        validator.fetch_node_info()  # Pre-fetch node info
        return validator.validate(workflow)

    return _dag_validator.validate(workflow)


# =============================================================================
# GENERATION PRESETS
# =============================================================================

GENERATION_PRESETS = {
    "draft": {
        "description": "Fast preview - lower quality, quick results",
        "steps": 12,
        "cfg": 6.0,
        "width": 512,
        "height": 512,
    },
    "fast": {
        "description": "Good balance of speed and quality",
        "steps": 20,
        "cfg": 7.0,
        "width": 768,
        "height": 768,
    },
    "quality": {
        "description": "High quality for final renders",
        "steps": 30,
        "cfg": 7.5,
        "width": 1024,
        "height": 1024,
    },
    "hd": {
        "description": "Maximum quality, slower generation",
        "steps": 40,
        "cfg": 7.5,
        "width": 1024,
        "height": 1024,
    },
    "portrait": {
        "description": "Optimized for portraits",
        "steps": 30,
        "cfg": 7.0,
        "width": 768,
        "height": 1152,
    },
    "landscape": {
        "description": "Optimized for landscapes",
        "steps": 30,
        "cfg": 7.0,
        "width": 1152,
        "height": 768,
    },
    "cinematic": {
        "description": "Widescreen cinematic ratio",
        "steps": 35,
        "cfg": 7.5,
        "width": 1536,
        "height": 640,
    },
    "square": {
        "description": "Perfect square for social media",
        "steps": 25,
        "cfg": 7.0,
        "width": 1024,
        "height": 1024,
    },
}


# =============================================================================
# WORKFLOW COMPILER
# =============================================================================


class WorkflowCompiler:
    """
    Compiles workflow templates into executable ComfyUI workflows.

    This is the core of making complex workflows accessible - users provide
    simple parameters and presets, the compiler handles the complexity.

    v2.4 Enhancements:
    - Caching with TTL for repeated compilations
    - DAG validation before execution
    - Workflow hashing for change detection
    - Version tracking
    """

    def __init__(
        self,
        available_checkpoints: list[str] = None,
        use_cache: bool = True,
        validate_dag: bool = True,
    ):
        self.available_checkpoints = available_checkpoints or []
        self.preferred_checkpoints = [
            "dreamshaper_8.safetensors",
            "juggernautXL_v9Rundiffusionphoto2.safetensors",
            "sd_xl_base_1.0.safetensors",
            "v1-5-pruned-emaonly.safetensors",
        ]
        self.use_cache = use_cache
        self.validate_dag = validate_dag
        self._cache = get_workflow_cache()
        self._validator = _dag_validator

    def compile(
        self,
        template: WorkflowTemplate,
        params: dict[str, Any],
        preset: str | None = None,
        skip_cache: bool = False,
    ) -> CompiledWorkflow:
        """
        Compile a template with parameters into an executable workflow.

        Args:
            template: The workflow template
            params: User-provided parameters
            preset: Optional preset name to apply
            skip_cache: Bypass cache for this compilation

        Returns:
            CompiledWorkflow ready for ComfyUI
        """
        # Check cache first (v2.4)
        if self.use_cache and not skip_cache:
            cached = self._cache.get(template.id, params, preset)
            if cached:
                logger.debug(f"Using cached workflow: {template.id}")
                return cached

        warnings = []
        errors = []

        # Deep copy the base workflow
        workflow = copy.deepcopy(template.workflow)

        # Start with template defaults
        final_params = {}
        for name, param_def in template.parameters.items():
            if param_def.default is not None:
                final_params[name] = param_def.default

        # Apply preset if specified
        if preset:
            if preset in template.presets:
                preset_def = template.presets[preset]
                final_params.update(preset_def.parameters)
            elif preset in GENERATION_PRESETS:
                final_params.update(GENERATION_PRESETS[preset])
            else:
                warnings.append(f"Unknown preset '{preset}', using defaults")

        # Override with user parameters
        final_params.update(params)

        # Validate required parameters
        for name, param_def in template.parameters.items():
            if param_def.required and name not in final_params:
                errors.append(f"Missing required parameter: {name}")

        if errors:
            return CompiledWorkflow(
                template_id=template.id,
                template_name=template.name,
                workflow=workflow,
                parameters=final_params,
                is_valid=False,
                errors=errors,
            )

        # Inject parameters into workflow
        for name, value in final_params.items():
            if name not in template.parameters:
                continue

            param_def = template.parameters[name]

            # Validate and coerce value
            validated_value, warning = self._validate_value(name, value, param_def)
            if warning:
                warnings.append(warning)

            # Handle special cases
            if param_def.type == ParameterType.MODEL:
                validated_value = self._resolve_model(validated_value)
            elif name == "seed" and validated_value == -1:
                validated_value = random.randint(0, 2**32 - 1)
                final_params["seed"] = validated_value

            # Inject into workflow
            try:
                self._inject_parameter(workflow, param_def, validated_value)
            except Exception as e:
                errors.append(f"Failed to inject '{name}': {e}")

        # Validate final workflow (basic)
        validation_errors = self._validate_workflow(workflow)
        errors.extend(validation_errors)

        # v2.4: Enhanced DAG validation
        if self.validate_dag and not errors:
            dag_errors = self._validator.validate(workflow)
            errors.extend(dag_errors)

        # Create compiled workflow with hash
        compiled = CompiledWorkflow(
            template_id=template.id,
            template_name=template.name,
            workflow=workflow,
            parameters=final_params,
            is_valid=len(errors) == 0,
            warnings=warnings,
            errors=errors,
            version="1.0.0",
            workflow_hash=compute_workflow_hash(workflow),
            compiled_at=time.time(),
        )

        # Cache successful compilations (v2.4)
        if self.use_cache and compiled.is_valid:
            self._cache.set(template.id, params, preset, compiled)
            logger.debug(f"Cached workflow: {template.id} (hash: {compiled.workflow_hash})")

        return compiled

    def _validate_value(
        self, name: str, value: Any, param_def: ParameterDef
    ) -> tuple[Any, str | None]:
        """Validate and coerce a parameter value."""
        warning = None

        # Type coercion
        if param_def.type == ParameterType.INT:
            try:
                value = int(value)
            except (ValueError, TypeError):
                warning = f"'{name}' should be int, using default"
                value = param_def.default or 0

        elif param_def.type == ParameterType.FLOAT:
            try:
                value = float(value)
            except (ValueError, TypeError):
                warning = f"'{name}' should be float, using default"
                value = param_def.default or 0.0

        elif param_def.type == ParameterType.BOOL:
            value = bool(value)

        elif (
            param_def.type == ParameterType.CHOICE
            and param_def.choices
            and value not in param_def.choices
        ):
            warning = f"'{name}' value '{value}' invalid, using default"
            value = param_def.default or param_def.choices[0]

        # Range validation
        if param_def.min is not None and value < param_def.min:
            warning = f"'{name}' below min {param_def.min}, clamping"
            value = param_def.min

        if param_def.max is not None and value > param_def.max:
            warning = f"'{name}' above max {param_def.max}, clamping"
            value = param_def.max

        return value, warning

    def _resolve_model(self, value: str) -> str:
        """Resolve model name, handling 'auto' selection."""
        if value == "auto" or not value:
            # Try preferred checkpoints first
            for cp in self.preferred_checkpoints:
                if cp in self.available_checkpoints:
                    return cp
            # Fall back to first available
            if self.available_checkpoints:
                return self.available_checkpoints[0]
            return "dreamshaper_8.safetensors"
        return value

    def _inject_parameter(self, workflow: dict[str, Any], param_def: ParameterDef, value: Any):
        """Inject a parameter value into the workflow."""
        node_id = param_def.node_id
        input_name = param_def.input_name

        if node_id not in workflow:
            raise KeyError(f"Node '{node_id}' not found")

        node = workflow[node_id]
        if "inputs" not in node:
            node["inputs"] = {}

        node["inputs"][input_name] = value

    def _validate_workflow(self, workflow: dict[str, Any]) -> list[str]:
        """Validate workflow structure."""
        errors = []

        if not workflow:
            errors.append("Workflow is empty")
            return errors

        # Check node connections
        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue

            inputs = node.get("inputs", {})
            for _input_name, input_value in inputs.items():
                # Check if it's a connection [node_id, output_index]
                if isinstance(input_value, list) and len(input_value) == 2:
                    source_id = str(input_value[0])
                    if source_id not in workflow:
                        errors.append(f"Node '{node_id}' references missing node '{source_id}'")

        return errors


# =============================================================================
# WORKFLOW OPTIMIZER
# =============================================================================


class WorkflowOptimizer:
    """
    Optimizes workflows for available hardware.

    Key for making this accessible - automatically adjusts settings
    so users don't get OOM errors on their hardware.
    """

    def __init__(self, available_vram_gb: float = 8.0):
        self.available_vram_gb = available_vram_gb

    def optimize(
        self, workflow: dict[str, Any], estimated_vram_gb: float
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Optimize workflow for available VRAM.

        Returns:
            Tuple of (optimized_workflow, list_of_changes_made)
        """
        optimized = copy.deepcopy(workflow)
        changes = []

        if estimated_vram_gb <= self.available_vram_gb:
            return optimized, changes

        # Strategy 1: Reduce resolution
        for _node_id, node in optimized.items():
            if not isinstance(node, dict):
                continue

            if node.get("class_type") == "EmptyLatentImage":
                inputs = node.get("inputs", {})
                width = inputs.get("width", 1024)
                height = inputs.get("height", 1024)

                # Calculate reduction factor
                vram_ratio = estimated_vram_gb / self.available_vram_gb
                if vram_ratio > 1.5:
                    scale = 0.75
                elif vram_ratio > 1.2:
                    scale = 0.85
                else:
                    scale = 0.9

                new_width = int(width * scale) // 64 * 64  # Keep divisible by 64
                new_height = int(height * scale) // 64 * 64

                if new_width != width or new_height != height:
                    inputs["width"] = new_width
                    inputs["height"] = new_height
                    changes.append(
                        f"Reduced resolution: {width}x{height} -> {new_width}x{new_height}"
                    )

        return optimized, changes

    # =========================================================================
    # VRAM Estimation Constants
    # =========================================================================
    # These constants are empirically derived from typical ComfyUI workloads.
    # Actual VRAM usage varies based on model architecture, batch size, and
    # precision (fp16/fp32/bf16). These provide conservative estimates.

    # Base VRAM for model loading (GB) - SD 1.5/SDXL checkpoint in fp16
    VRAM_BASE_MODEL_GB = 4.0

    # VRAM per megapixel for latent diffusion (GB/MP)
    # Derived from: 1024x1024 image ≈ 1.5GB additional VRAM on SDXL
    VRAM_PER_MEGAPIXEL_GB = 1.5

    # VRAM per video frame (GB/frame)
    # AnimateDiff/SVD add ~300MB per frame due to temporal attention
    VRAM_PER_VIDEO_FRAME_GB = 0.3

    def estimate_vram(self, workflow: dict[str, Any]) -> float:
        """
        Estimate VRAM requirements for a workflow.

        This is a rough estimate based on resolution and model type.
        Uses empirically-derived constants for typical ComfyUI workloads.

        Constants:
            VRAM_BASE_MODEL_GB: Base VRAM for model loading (~4GB for SDXL fp16)
            VRAM_PER_MEGAPIXEL_GB: Additional VRAM per megapixel (~1.5GB/MP)
            VRAM_PER_VIDEO_FRAME_GB: Additional VRAM per video frame (~0.3GB/frame)
        """
        base_vram = self.VRAM_BASE_MODEL_GB

        for _node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue

            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            # Resolution-based VRAM
            if class_type == "EmptyLatentImage":
                width = inputs.get("width", 512)
                height = inputs.get("height", 512)
                megapixels = (width * height) / 1_000_000
                base_vram += megapixels * self.VRAM_PER_MEGAPIXEL_GB

            # Video adds significant VRAM
            if "AnimateDiff" in class_type or "Video" in class_type:
                frames = inputs.get("batch_size", inputs.get("frames", 16))
                base_vram += frames * self.VRAM_PER_VIDEO_FRAME_GB

        return base_vram


# =============================================================================
# BUILT-IN TEMPLATES
# =============================================================================


def create_txt2img_template() -> WorkflowTemplate:
    """Create the standard text-to-image template."""

    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 7.0,
                "denoise": 1.0,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "seed": -1,
                "steps": 25,
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "dreamshaper_8.safetensors"},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1, "height": 1024, "width": 1024},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["4", 1], "text": ""},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["4", 1], "text": "ugly, blurry, low quality"},
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

    parameters = {
        "prompt": ParameterDef(
            type=ParameterType.STRING,
            node_id="6",
            input_name="text",
            required=True,
            label="Prompt",
            description="What you want to generate",
        ),
        "negative": ParameterDef(
            type=ParameterType.STRING,
            node_id="7",
            input_name="text",
            default="ugly, blurry, low quality, distorted, deformed",
            label="Negative Prompt",
        ),
        "checkpoint": ParameterDef(
            type=ParameterType.MODEL,
            node_id="4",
            input_name="ckpt_name",
            default="auto",
            label="Model",
        ),
        "width": ParameterDef(
            type=ParameterType.INT,
            node_id="5",
            input_name="width",
            default=1024,
            min=256,
            max=2048,
            label="Width",
        ),
        "height": ParameterDef(
            type=ParameterType.INT,
            node_id="5",
            input_name="height",
            default=1024,
            min=256,
            max=2048,
            label="Height",
        ),
        "steps": ParameterDef(
            type=ParameterType.INT,
            node_id="3",
            input_name="steps",
            default=25,
            min=1,
            max=100,
            label="Steps",
        ),
        "cfg": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="3",
            input_name="cfg",
            default=7.0,
            min=1.0,
            max=20.0,
            label="CFG Scale",
        ),
        "seed": ParameterDef(
            type=ParameterType.INT,
            node_id="3",
            input_name="seed",
            default=-1,
            label="Seed (-1 = random)",
        ),
        "sampler": ParameterDef(
            type=ParameterType.CHOICE,
            node_id="3",
            input_name="sampler_name",
            default="euler_ancestral",
            choices=["euler", "euler_ancestral", "dpmpp_2m", "dpmpp_sde", "ddim"],
            label="Sampler",
        ),
        "scheduler": ParameterDef(
            type=ParameterType.CHOICE,
            node_id="3",
            input_name="scheduler",
            default="normal",
            choices=["normal", "karras", "exponential", "sgm_uniform"],
            label="Scheduler",
        ),
    }

    presets = {
        "draft": PresetDef(
            name="Draft",
            description="Quick preview",
            parameters={"steps": 12, "cfg": 6.0, "width": 512, "height": 512},
        ),
        "fast": PresetDef(
            name="Fast",
            description="Good balance",
            parameters={"steps": 20, "cfg": 7.0, "width": 768, "height": 768},
        ),
        "quality": PresetDef(
            name="Quality",
            description="High quality",
            parameters={"steps": 30, "cfg": 7.5, "width": 1024, "height": 1024},
        ),
        "portrait": PresetDef(
            name="Portrait",
            description="Portrait ratio",
            parameters={"steps": 30, "cfg": 7.0, "width": 768, "height": 1152},
        ),
        "landscape": PresetDef(
            name="Landscape",
            description="Landscape ratio",
            parameters={"steps": 30, "cfg": 7.0, "width": 1152, "height": 768},
        ),
    }

    return WorkflowTemplate(
        id="txt2img_standard",
        name="Text to Image",
        description="Standard text-to-image generation workflow",
        category=WorkflowCategory.TEXT_TO_IMAGE,
        workflow=workflow,
        parameters=parameters,
        presets=presets,
        min_vram_gb=6,
        tags=["basic", "txt2img", "standard"],
    )


def create_txt2img_hires_template() -> WorkflowTemplate:
    """Create hi-res fix template (generate small, upscale)."""

    # This workflow generates at lower res then upscales
    workflow = {
        # First pass - generate at lower resolution
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "dreamshaper_8.safetensors"},
        },
        "2": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1, "height": 512, "width": 512},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": ""},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": "ugly, blurry"},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["2", 0],
                "seed": -1,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        # Upscale latent
        "6": {
            "class_type": "LatentUpscale",
            "inputs": {
                "samples": ["5", 0],
                "upscale_method": "nearest-exact",
                "width": 1024,
                "height": 1024,
                "crop": "disabled",
            },
        },
        # Second pass - refine at high resolution
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["6", 0],
                "seed": -1,
                "steps": 15,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 0.5,  # Lower denoise for refinement
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["7", 0], "vae": ["1", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "comfy_hires", "images": ["8", 0]},
        },
    }

    parameters = {
        "prompt": ParameterDef(
            type=ParameterType.STRING,
            node_id="3",
            input_name="text",
            required=True,
        ),
        "negative": ParameterDef(
            type=ParameterType.STRING,
            node_id="4",
            input_name="text",
            default="ugly, blurry, low quality",
        ),
        "checkpoint": ParameterDef(
            type=ParameterType.MODEL,
            node_id="1",
            input_name="ckpt_name",
            default="auto",
        ),
        "width": ParameterDef(
            type=ParameterType.INT,
            node_id="6",
            input_name="width",
            default=1024,
            min=512,
            max=2048,
        ),
        "height": ParameterDef(
            type=ParameterType.INT,
            node_id="6",
            input_name="height",
            default=1024,
            min=512,
            max=2048,
        ),
        "steps": ParameterDef(
            type=ParameterType.INT,
            node_id="5",
            input_name="steps",
            default=20,
            min=10,
            max=50,
        ),
        "hires_steps": ParameterDef(
            type=ParameterType.INT,
            node_id="7",
            input_name="steps",
            default=15,
            min=5,
            max=30,
        ),
        "hires_denoise": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="7",
            input_name="denoise",
            default=0.5,
            min=0.2,
            max=0.8,
        ),
        "seed": ParameterDef(
            type=ParameterType.INT,
            node_id="5",
            input_name="seed",
            default=-1,
        ),
        "cfg": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="5",
            input_name="cfg",
            default=7.0,
            min=1.0,
            max=15.0,
        ),
    }

    return WorkflowTemplate(
        id="txt2img_hires",
        name="Text to Image (Hi-Res Fix)",
        description="Generate at lower resolution then upscale for sharper details",
        category=WorkflowCategory.TEXT_TO_IMAGE,
        workflow=workflow,
        parameters=parameters,
        presets={},
        min_vram_gb=8,
        tags=["hires", "upscale", "quality"],
    )


def create_upscale_template() -> WorkflowTemplate:
    """
    Create an image upscaling workflow template.

    Uses RealESRGAN or similar upscale model for 2x/4x upscaling.
    """
    workflow = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {
                "image": "",  # Placeholder - will be replaced with actual image path
                "upload": "image",
            },
        },
        "2": {
            "class_type": "UpscaleModelLoader",
            "inputs": {
                "model_name": "RealESRGAN_x4plus.pth",
            },
        },
        "3": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {
                "upscale_model": ["2", 0],
                "image": ["1", 0],
            },
        },
        "4": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["3", 0],
                "upscale_method": "lanczos",
                "width": 2048,
                "height": 2048,
                "crop": "disabled",
            },
        },
        "5": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "upscaled",
                "images": ["4", 0],
            },
        },
    }

    parameters = {
        "image": ParameterDef(
            type=ParameterType.IMAGE,
            node_id="1",
            input_name="image",
            required=True,
            description="Input image to upscale",
        ),
        "upscale_model": ParameterDef(
            type=ParameterType.MODEL,
            node_id="2",
            input_name="model_name",
            default="RealESRGAN_x4plus.pth",
            description="Upscale model (RealESRGAN, ESRGAN, etc.)",
        ),
        "width": ParameterDef(
            type=ParameterType.INT,
            node_id="4",
            input_name="width",
            default=2048,
            min=512,
            max=8192,
            description="Target width",
        ),
        "height": ParameterDef(
            type=ParameterType.INT,
            node_id="4",
            input_name="height",
            default=2048,
            min=512,
            max=8192,
            description="Target height",
        ),
    }

    return WorkflowTemplate(
        id="upscale",
        name="Image Upscale",
        description="Upscale images using AI models (RealESRGAN, ESRGAN)",
        category=WorkflowCategory.UPSCALE,
        workflow=workflow,
        parameters=parameters,
        presets={
            "2x": {"width": 2048, "height": 2048},
            "4x": {"width": 4096, "height": 4096},
        },
        min_vram_gb=4,
        tags=["upscale", "enhance", "resolution"],
    )


def create_inpaint_template() -> WorkflowTemplate:
    """
    Create an inpainting workflow template.

    Uses mask-based inpainting to fill or replace parts of an image.
    """
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.safetensors"},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {
                "image": "",  # Input image
                "upload": "image",
            },
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {
                "image": "",  # Mask image (white = inpaint area)
                "upload": "image",
            },
        },
        "4": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["1", 2],
            },
        },
        "5": {
            "class_type": "SetLatentNoiseMask",
            "inputs": {
                "samples": ["4", 0],
                "mask": ["3", 0],
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": "",  # Positive prompt
            },
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": "ugly, blurry, low quality, distorted",
            },
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": -1,
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["1", 2],
            },
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "inpaint",
                "images": ["9", 0],
            },
        },
    }

    parameters = {
        "image": ParameterDef(
            type=ParameterType.IMAGE,
            node_id="2",
            input_name="image",
            required=True,
            description="Input image to inpaint",
        ),
        "mask": ParameterDef(
            type=ParameterType.IMAGE,
            node_id="3",
            input_name="image",
            required=True,
            description="Mask image (white = areas to inpaint)",
        ),
        "prompt": ParameterDef(
            type=ParameterType.STRING,
            node_id="6",
            input_name="text",
            required=True,
            description="What to generate in masked area",
        ),
        "negative": ParameterDef(
            type=ParameterType.STRING,
            node_id="7",
            input_name="text",
            default="ugly, blurry, low quality, distorted",
        ),
        "checkpoint": ParameterDef(
            type=ParameterType.MODEL,
            node_id="1",
            input_name="ckpt_name",
            default="auto",
        ),
        "steps": ParameterDef(
            type=ParameterType.INT,
            node_id="8",
            input_name="steps",
            default=25,
            min=10,
            max=50,
        ),
        "cfg": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="8",
            input_name="cfg",
            default=7.0,
            min=1.0,
            max=15.0,
        ),
        "denoise": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="8",
            input_name="denoise",
            default=1.0,
            min=0.1,
            max=1.0,
            description="Denoise strength (1.0 = full replace, lower = blend)",
        ),
        "seed": ParameterDef(
            type=ParameterType.INT,
            node_id="8",
            input_name="seed",
            default=-1,
        ),
    }

    return WorkflowTemplate(
        id="inpaint",
        name="Inpaint",
        description="Fill or replace parts of an image using a mask",
        category=WorkflowCategory.IMG_TO_IMG,
        workflow=workflow,
        parameters=parameters,
        presets={
            "fill": {"denoise": 1.0, "steps": 25},
            "blend": {"denoise": 0.7, "steps": 20},
            "touch_up": {"denoise": 0.4, "steps": 15},
        },
        min_vram_gb=6,
        tags=["inpaint", "mask", "edit", "fill"],
    )


# =============================================================================
# QWEN-IMAGE FAMILY (v3.1.0)
# =============================================================================
#
# Qwen-Image lives in models/diffusion_models and loads through UNETLoader --
# NOT CheckpointLoaderSimple (searching the checkpoint namespace and
# concluding "Qwen doesn't exist" is a known trap). Text encoding goes
# through CLIPLoader with type="qwen_image", and the latent MUST be
# EmptySD3LatentImage: the 16-channel DiT latent. EmptyLatentImage is the
# 4-channel SD1.5/SDXL latent and produces garbage here.
#
# All class_types and model filenames verified against the live catalog
# (2026-08-21).

QWEN_TXT2IMG_UNETS = [
    "qwen_image_2512_fp8_e4m3fn.safetensors",
    "qwen_image_2512_bf16.safetensors",
]
QWEN_EDIT_UNETS = [
    "qwen_image_edit_2511_fp8mixed.safetensors",
    "qwen_image_edit_2511_int8_convrot.safetensors",
    "qwen_image_edit_2509_bf16.safetensors",
]
QWEN_CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
QWEN_VAE = "qwen_image_vae.safetensors"

# SetUnionControlNetType's enum, verbatim from the live schema. The
# slash-grouped values are SINGLE literal choices, not alternatives to split.
UNION_CONTROL_TYPES = [
    "auto",
    "openpose",
    "depth",
    "hed/pidi/scribble/ted",
    "canny/lineart/anime_lineart/mlsd",
    "normal",
    "segment",
    "tile",
    "repaint",
]


def create_qwen_txt2img_template() -> WorkflowTemplate:
    """
    Create the Qwen-Image-2512 text-to-image template.

    Defaults follow the model's published recipe, not the SDXL habits:
    steps 20, cfg 2.5 (NOT 7.0), euler/simple, 1328x1328 native bucket,
    ModelSamplingAuraFlow shift 3.1.
    """
    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "qwen_image_2512_fp8_e4m3fn.safetensors",
                "weight_dtype": "default",
            },
        },
        "2": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["1", 0], "shift": 3.1},
        },
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": QWEN_CLIP, "type": "qwen_image", "device": "default"},
        },
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": ""}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": ""}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": QWEN_VAE}},
        # 16-channel DiT latent -- EmptyLatentImage would be silent garbage.
        "7": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": 1328, "height": 1328, "batch_size": 1},
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["7", 0],
                "seed": -1,
                "steps": 20,
                "cfg": 2.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["6", 0]}},
        "10": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "comfy_headless_qwen", "images": ["9", 0]},
        },
    }

    parameters = {
        "prompt": ParameterDef(
            type=ParameterType.STRING,
            node_id="4",
            input_name="text",
            required=True,
            label="Prompt",
        ),
        "negative": ParameterDef(
            type=ParameterType.STRING,
            node_id="5",
            input_name="text",
            default="",
            label="Negative Prompt",
        ),
        "unet": ParameterDef(
            type=ParameterType.CHOICE,
            node_id="1",
            input_name="unet_name",
            default="qwen_image_2512_fp8_e4m3fn.safetensors",
            choices=QWEN_TXT2IMG_UNETS,
            label="Diffusion model",
        ),
        "width": ParameterDef(
            type=ParameterType.INT,
            node_id="7",
            input_name="width",
            default=1328,
            min=256,
            max=2048,
        ),
        "height": ParameterDef(
            type=ParameterType.INT,
            node_id="7",
            input_name="height",
            default=1328,
            min=256,
            max=2048,
        ),
        "steps": ParameterDef(
            type=ParameterType.INT, node_id="8", input_name="steps", default=20, min=1, max=100
        ),
        "cfg": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="8",
            input_name="cfg",
            default=2.5,
            min=1.0,
            max=15.0,
        ),
        "seed": ParameterDef(type=ParameterType.INT, node_id="8", input_name="seed", default=-1),
        "shift": ParameterDef(
            type=ParameterType.FLOAT,
            node_id="2",
            input_name="shift",
            default=3.1,
            min=0.5,
            max=12.0,
            description="ModelSamplingAuraFlow shift",
        ),
    }

    presets = {
        "qwen_square": PresetDef(
            name="Qwen Square",
            description="Native 1328x1328 bucket",
            parameters={"width": 1328, "height": 1328},
        ),
        "qwen_portrait": PresetDef(
            name="Qwen Portrait",
            description="Native portrait bucket",
            parameters={"width": 768, "height": 1344},
        ),
        "qwen_landscape": PresetDef(
            name="Qwen Landscape",
            description="Native landscape bucket",
            parameters={"width": 1344, "height": 768},
        ),
    }

    return WorkflowTemplate(
        id="qwen_txt2img",
        name="Qwen-Image 2512 Text to Image",
        description="Qwen-Image-2512 DiT text-to-image (UNETLoader path, 16-channel latent)",
        category=WorkflowCategory.TEXT_TO_IMAGE,
        workflow=workflow,
        parameters=parameters,
        presets=presets,
        min_vram_gb=16,
        tags=["qwen", "txt2img", "dit"],
    )


def build_qwen_edit_workflow(
    prompt: str,
    image_refs: "list[str] | tuple[str, ...]",
    negative: str = "",
    unet: str = "qwen_image_edit_2511_fp8mixed.safetensors",
    width: int = 1328,
    height: int = 1328,
    steps: int = 20,
    cfg: float = 2.5,
    shift: float = 3.1,
    seed: int = -1,
    filename_prefix: str = "comfy_headless_qwen_edit",
) -> dict[str, Any]:
    """
    Build a Qwen-Image-Edit-2511 workflow.

    The reference-image mechanism, verbatim from the live schema: reference
    images go into ``TextEncodeQwenImageEditPlus`` as up to three DISCRETE
    inputs ``image1``/``image2``/``image3`` -- not a batched list -- and they
    do NOT pass through VAEEncode. The VAE is wired into the encoder's
    ``vae`` input and raw IMAGE goes into ``image1..3``. This node replaces
    the positive CLIPTextEncode; the negative stays a plain CLIPTextEncode.

    Args:
        prompt: Edit instruction.
        image_refs: 1-3 server-side image refs (from
            ``ComfyClient.upload_image()["ref"]``).
        negative: Negative prompt.
        unet: Edit checkpoint (see ``QWEN_EDIT_UNETS``).
        width/height/steps/cfg/shift/seed: Sampling parameters.
        filename_prefix: Output prefix.

    Returns:
        ComfyUI API-format workflow JSON.
    """
    from .exceptions import InvalidParameterError

    refs = list(image_refs)
    if not 1 <= len(refs) <= 3:
        raise InvalidParameterError(
            parameter="image_refs",
            value=len(refs),
            reason="Qwen-Image-Edit takes 1-3 reference images (image1..image3)",
        )

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    workflow: dict[str, Any] = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": unet, "weight_dtype": "default"},
        },
        "2": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["1", 0], "shift": shift},
        },
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": QWEN_CLIP, "type": "qwen_image", "device": "default"},
        },
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": QWEN_VAE}},
    }

    encode_inputs: dict[str, Any] = {
        "clip": ["3", 0],
        "prompt": prompt,
        "vae": ["4", 0],
    }
    for i, ref in enumerate(refs, start=1):
        node_id = str(4 + i)  # "5", "6", "7"
        workflow[node_id] = {"class_type": "LoadImage", "inputs": {"image": ref}}
        encode_inputs[f"image{i}"] = [node_id, 0]

    workflow.update(
        {
            "8": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": encode_inputs},
            "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": negative}},
            "10": {
                "class_type": "EmptySD3LatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
            },
            "11": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": ["8", 0],
                    "negative": ["9", 0],
                    "latent_image": ["10", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0,
                },
            },
            "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["4", 0]}},
            "13": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": filename_prefix, "images": ["12", 0]},
            },
        }
    )
    return workflow


def build_controlnet_workflow(
    prompt: str,
    control_image_ref: str,
    control_type: str = "auto",
    base: str = "qwen",
    negative: str = "",
    strength: float = 1.0,
    start_percent: float = 0.0,
    end_percent: float = 1.0,
    preprocess: str | None = None,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    seed: int = -1,
    model_name: str | None = None,
    control_net_name: str | None = None,
    filename_prefix: str = "comfy_headless_controlnet",
) -> dict[str, Any]:
    """
    Build a union-ControlNet text-to-image workflow (Qwen and SDXL share one
    code path): ControlNetLoader -> SetUnionControlNetType ->
    ControlNetApplyAdvanced.

    Args:
        prompt: Positive prompt.
        control_image_ref: Server-side ref of the control hint image
            (already preprocessed, unless ``preprocess`` is set).
        control_type: One of ``UNION_CONTROL_TYPES`` (verbatim enum; the
            slash-grouped entries are single literal values). Prefer an
            explicit type over "auto" when you know the hint kind -- "auto"
            asks the model to infer it.
        base: "qwen" (Qwen-Image-2512 + Fun ControlNet Union) or "sdxl"
            (SDXL + controlnet-union-sdxl-1.0).
        strength/start_percent/end_percent: ControlNetApplyAdvanced schedule.
        preprocess: Optional "canny" runs the core Canny edge detector on the
            control image first. All other preprocessors (openpose, depth,
            lineart, HED, MLSD, normal, tile) live in the
            ``comfyui_controlnet_aux`` pack and are NOT emitted -- supply a
            pre-made hint image instead.
        width/height/steps/cfg: Default per base (Qwen: 1328/20/2.5,
            SDXL: 1024/25/7.0).
        model_name: Override the base diffusion model file.
        control_net_name: Override the ControlNet file.

    Returns:
        ComfyUI API-format workflow JSON.
    """
    from .exceptions import InvalidParameterError

    if control_type not in UNION_CONTROL_TYPES:
        raise InvalidParameterError(
            parameter="control_type",
            value=control_type,
            reason="not a SetUnionControlNetType value",
            allowed_values=UNION_CONTROL_TYPES,
        )
    if base not in ("qwen", "sdxl"):
        raise InvalidParameterError(
            parameter="base",
            value=base,
            reason="unsupported ControlNet base",
            allowed_values=["qwen", "sdxl"],
        )
    if preprocess not in (None, "canny"):
        raise InvalidParameterError(
            parameter="preprocess",
            value=preprocess,
            reason="only the core 'canny' preprocessor is emitted; others need comfyui_controlnet_aux",
            allowed_values=["canny"],
        )
    if not control_image_ref:
        raise ValueError("ControlNet requires a control image (control_image_ref)")

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    qwen = base == "qwen"
    width = width or (1328 if qwen else 1024)
    height = height or (1328 if qwen else 1024)
    steps = steps or (20 if qwen else 25)
    cfg = cfg if cfg is not None else (2.5 if qwen else 7.0)

    workflow: dict[str, Any] = {
        "5": {"class_type": "LoadImage", "inputs": {"image": control_image_ref}},
        "7": {
            "class_type": "SetUnionControlNetType",
            "inputs": {"control_net": ["6", 0], "type": control_type},
        },
    }

    control_image_source = ["5", 0]
    if preprocess == "canny":
        workflow["12"] = {
            "class_type": "Canny",
            "inputs": {"image": ["5", 0], "low_threshold": 0.4, "high_threshold": 0.8},
        }
        control_image_source = ["12", 0]

    if qwen:
        workflow.update(
            {
                "1": {
                    "class_type": "UNETLoader",
                    "inputs": {
                        "unet_name": model_name or "qwen_image_2512_fp8_e4m3fn.safetensors",
                        "weight_dtype": "default",
                    },
                },
                "2": {
                    "class_type": "ModelSamplingAuraFlow",
                    "inputs": {"model": ["1", 0], "shift": 3.1},
                },
                "3": {
                    "class_type": "CLIPLoader",
                    "inputs": {
                        "clip_name": QWEN_CLIP,
                        "type": "qwen_image",
                        "device": "default",
                    },
                },
                "4": {"class_type": "VAELoader", "inputs": {"vae_name": QWEN_VAE}},
                "6": {
                    "class_type": "ControlNetLoader",
                    "inputs": {
                        "control_net_name": control_net_name
                        or "Qwen-Image-2512-Fun-Controlnet-Union-2602.safetensors"
                    },
                },
                "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": prompt}},
                "9": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"clip": ["3", 0], "text": negative},
                },
                # Qwen-family ControlNets want the VAE wired into the apply node.
                "10": {
                    "class_type": "ControlNetApplyAdvanced",
                    "inputs": {
                        "positive": ["8", 0],
                        "negative": ["9", 0],
                        "control_net": ["7", 0],
                        "image": control_image_source,
                        "strength": strength,
                        "start_percent": start_percent,
                        "end_percent": end_percent,
                        "vae": ["4", 0],
                    },
                },
                "11": {
                    "class_type": "EmptySD3LatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "13": {
                    "class_type": "KSampler",
                    "inputs": {
                        "model": ["2", 0],
                        "positive": ["10", 0],
                        "negative": ["10", 1],
                        "latent_image": ["11", 0],
                        "seed": seed,
                        "steps": steps,
                        "cfg": cfg,
                        "sampler_name": "euler",
                        "scheduler": "simple",
                        "denoise": 1.0,
                    },
                },
                "14": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["13", 0], "vae": ["4", 0]},
                },
                "15": {
                    "class_type": "SaveImage",
                    "inputs": {"filename_prefix": filename_prefix, "images": ["14", 0]},
                },
            }
        )
    else:
        workflow.update(
            {
                "1": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": model_name or "sd_xl_base_1.0.safetensors"},
                },
                "6": {
                    "class_type": "ControlNetLoader",
                    "inputs": {
                        "control_net_name": control_net_name
                        or "controlnet-union-sdxl-1.0.safetensors"
                    },
                },
                "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": prompt}},
                "9": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"clip": ["1", 1], "text": negative},
                },
                "10": {
                    "class_type": "ControlNetApplyAdvanced",
                    "inputs": {
                        "positive": ["8", 0],
                        "negative": ["9", 0],
                        "control_net": ["7", 0],
                        "image": control_image_source,
                        "strength": strength,
                        "start_percent": start_percent,
                        "end_percent": end_percent,
                    },
                },
                "11": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "13": {
                    "class_type": "KSampler",
                    "inputs": {
                        "model": ["1", 0],
                        "positive": ["10", 0],
                        "negative": ["10", 1],
                        "latent_image": ["11", 0],
                        "seed": seed,
                        "steps": steps,
                        "cfg": cfg,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                    },
                },
                "14": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["13", 0], "vae": ["1", 2]},
                },
                "15": {
                    "class_type": "SaveImage",
                    "inputs": {"filename_prefix": filename_prefix, "images": ["14", 0]},
                },
            }
        )

    return workflow


# =============================================================================
# TEMPLATE LIBRARY
# =============================================================================


class TemplateLibrary:
    """
    Manages available workflow templates.

    This makes it easy to add new workflows without touching the UI.
    """

    def __init__(self):
        self._templates: dict[str, WorkflowTemplate] = {}
        self._load_builtin()

    def _load_builtin(self):
        """Load built-in templates."""
        templates = [
            create_txt2img_template(),
            create_txt2img_hires_template(),
            create_upscale_template(),
            create_inpaint_template(),
            create_qwen_txt2img_template(),
        ]
        for t in templates:
            self._templates[t.id] = t

    def get(self, template_id: str) -> WorkflowTemplate | None:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def list_all(self, category: WorkflowCategory | None = None) -> list[WorkflowTemplate]:
        """List all templates, optionally filtered by category."""
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return sorted(templates, key=lambda t: t.name)

    def list_presets(self) -> dict[str, dict[str, Any]]:
        """List all generation presets."""
        return GENERATION_PRESETS.copy()

    def add(self, template: WorkflowTemplate):
        """Add a custom template."""
        self._templates[template.id] = template

    def get_for_intent(self, intent: str, styles: list[str] = None) -> WorkflowTemplate:
        """
        Get the best template for a given intent and styles.

        This is key for accessibility - users describe what they want,
        we pick the right workflow automatically.
        """
        # Simple matching for now - can be enhanced with ML
        if intent in ["portrait", "character"] or intent in ["landscape", "architecture"]:
            return self.get("txt2img_standard")
        elif "quality" in (styles or []) or "detailed" in (styles or []):
            return self.get("txt2img_hires")

        # Default
        return self.get("txt2img_standard")


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

_compiler: WorkflowCompiler | None = None
_library: TemplateLibrary | None = None
_optimizer: WorkflowOptimizer | None = None


def get_compiler(checkpoints: list[str] = None) -> WorkflowCompiler:
    """Get the workflow compiler."""
    global _compiler
    if _compiler is None:
        _compiler = WorkflowCompiler(checkpoints)
    elif checkpoints:
        _compiler.available_checkpoints = checkpoints
    return _compiler


def get_library() -> TemplateLibrary:
    """Get the template library."""
    global _library
    if _library is None:
        _library = TemplateLibrary()
    return _library


def get_optimizer(vram_gb: float = 8.0) -> WorkflowOptimizer:
    """Get the workflow optimizer."""
    global _optimizer
    if _optimizer is None or _optimizer.available_vram_gb != vram_gb:
        _optimizer = WorkflowOptimizer(vram_gb)
    return _optimizer


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def compile_workflow(
    prompt: str,
    negative: str = "",
    preset: str = "quality",
    template_id: str = "txt2img_standard",
    **kwargs,
) -> CompiledWorkflow:
    """
    High-level workflow compilation.

    This is the main entry point for simple usage:

        workflow = compile_workflow(
            prompt="a beautiful sunset",
            preset="quality"
        )
    """
    library = get_library()
    compiler = get_compiler()

    template = library.get(template_id)
    if not template:
        template = library.get("txt2img_standard")

    params = {
        "prompt": prompt,
        "negative": negative or "ugly, blurry, low quality, distorted",
        **kwargs,
    }

    return compiler.compile(template, params, preset=preset)


def get_preset_info(preset_name: str) -> dict[str, Any] | None:
    """Get information about a preset."""
    return GENERATION_PRESETS.get(preset_name)


def list_presets() -> list[str]:
    """List available preset names."""
    return list(GENERATION_PRESETS.keys())
