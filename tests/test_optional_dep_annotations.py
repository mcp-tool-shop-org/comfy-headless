"""Guard against optional-dependency annotations being evaluated at import time.

## Why this file exists

`comfy-headless` supports a core-only install: `pip install comfy-headless` pulls
almost nothing, and optional features (`httpx`, `gradio`, `websockets`, `psutil`,
`pydantic`, `opentelemetry`) are absent. Those modules use the pattern::

    try:
        import httpx
    except ImportError:
        httpx = None

If such a module then annotates a function at class-body or module level::

    def request(self) -> httpx.Response: ...

...that annotation is **evaluated when the module is imported** on Python < 3.14,
raising ``AttributeError: 'NoneType' object has no attribute 'Response'`` and making
the whole package unimportable on a core-only install.

v3.0.0 shipped exactly this bug. It reached a tagged release because:

* the test suite runs in a dev environment where every extra IS installed, so the
  annotation resolved fine; and
* the maintainer's local interpreter was Python 3.14, where :pep:`649` defers
  annotation evaluation — so a manual core-only venv check passed locally while
  CI on Python 3.11 failed.

The package declares ``requires-python = ">=3.10"``. Python 3.10-3.13 all evaluate
annotations eagerly, so the bug affected most of the supported range.

## The rule this enforces

Any module that keeps an optional dependency in a module-level name which may be
``None`` MUST declare ``from __future__ import annotations``. That turns every
annotation into a string and makes evaluation-at-import impossible, on every
supported Python version.

This is a static check on purpose: it holds regardless of which interpreter or
which extras the suite happens to run under, so it cannot be masked the way the
original bug was.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "comfy_headless"

#: Names that may legitimately be ``None`` at runtime on a core-only install.
OPTIONAL_DEPENDENCIES = frozenset(
    {
        "httpx",
        "gradio",
        "gr",
        "websockets",
        "psutil",
        "pydantic",
        "opentelemetry",
        "trace",
    }
)


def _python_modules() -> list[Path]:
    return sorted(p for p in PACKAGE_DIR.glob("*.py"))


def _has_future_annotations(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


def _names_assigned_none(tree: ast.Module) -> set[str]:
    """Module-level names explicitly assigned ``None`` (the fallback pattern)."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not (isinstance(node.value, ast.Constant) and node.value.value is None):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                found.add(target.id)
    return found


def _annotation_root_names(tree: ast.Module) -> set[str]:
    """Root identifiers appearing in any annotation, e.g. ``httpx`` in ``httpx.Response``."""
    roots: set[str] = set()

    def walk_annotation(annotation: ast.expr | None) -> None:
        if annotation is None:
            return
        for sub in ast.walk(annotation):
            if isinstance(sub, ast.Name):
                roots.add(sub.id)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            walk_annotation(node.returns)
            args = node.args
            for arg in [
                *args.posonlyargs,
                *args.args,
                *args.kwonlyargs,
                args.vararg,
                args.kwarg,
            ]:
                if arg is not None:
                    walk_annotation(arg.annotation)
        elif isinstance(node, ast.AnnAssign):
            walk_annotation(node.annotation)

    return roots


class TestOptionalDependencyAnnotations:
    def test_modules_annotating_optional_deps_defer_evaluation(self) -> None:
        """No module may evaluate an optional dependency's annotation at import time."""
        offenders: dict[str, set[str]] = {}

        for path in _python_modules():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if _has_future_annotations(tree):
                continue

            risky = (
                _annotation_root_names(tree) & _names_assigned_none(tree) & OPTIONAL_DEPENDENCIES
            )
            if risky:
                offenders[path.name] = risky

        assert not offenders, (
            "These modules annotate an optional dependency that can be None at "
            "runtime, without `from __future__ import annotations`. On Python "
            "< 3.14 the annotation is evaluated at import time and a core-only "
            "install raises AttributeError, making the package unimportable:\n  "
            + "\n  ".join(f"{name}: {sorted(names)}" for name, names in offenders.items())
        )

    def test_guard_actually_inspects_the_package(self) -> None:
        """A silently empty scan would make the check above vacuously true."""
        modules = _python_modules()
        assert len(modules) > 10, f"expected the package modules, found {len(modules)}"
        assert (PACKAGE_DIR / "http_client.py") in modules

    def test_detector_catches_the_original_bug(self, tmp_path: Path) -> None:
        """The v3.0.0 defect, reconstructed, must be flagged by the logic above."""
        source = (
            "try:\n"
            "    import httpx\n"
            "except ImportError:\n"
            "    httpx = None\n"
            "\n"
            "class AsyncHttpClient:\n"
            "    async def request(self) -> httpx.Response: ...\n"
        )
        tree = ast.parse(source)

        assert not _has_future_annotations(tree)
        assert "httpx" in _names_assigned_none(tree)
        assert "httpx" in _annotation_root_names(tree)
