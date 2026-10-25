"""The supported Python range is current: 3.13 to 3.15, with 3.15 the one CI and lint use first.

These tests read the project's own metadata and workflows, so the claim in the classifiers, the
floor in ``requires-python``, the tool targets, the CI matrix and the container image cannot drift
apart or fall back to an interpreter the studio no longer tests on.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = ("3.13", "3.14", "3.15")
RETIRED = ("3.10", "3.11", "3.12")


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def _python_versions(text: str) -> set[str]:
    """Every ``python-version`` value in a workflow, matrix lists and single values alike."""

    found: set[str] = set()
    for line in text.splitlines():
        if "python-version" in line and not line.lstrip().startswith("#"):
            found.update(re.findall(r"\b3\.\d{1,2}\b", line))
    return found


def test_requires_python_floor_is_3_13():
    assert _pyproject()["project"]["requires-python"] == ">=3.13"


def test_classifiers_name_exactly_the_supported_pythons():
    classifiers = _pyproject()["project"]["classifiers"]
    versions = {
        c.rsplit("::", 1)[1].strip()
        for c in classifiers
        if c.startswith("Programming Language :: Python :: 3.")
    }
    assert versions == set(SUPPORTED)


def test_tool_targets_follow_the_floor():
    config = _pyproject()["tool"]
    assert config["ruff"]["target-version"] == "py313"
    assert config["mypy"]["python_version"] == "3.13"


def test_ci_tests_every_supported_python_and_no_retired_one():
    versions = _python_versions(_workflow("ci.yml"))
    assert set(SUPPORTED) <= versions
    assert not versions & set(RETIRED)


def test_ci_lint_build_and_audit_run_on_the_newest_python():
    text = _workflow("ci.yml")
    for job in ("lint", "pip-audit"):
        block = re.search(rf"^  {job}:\n(.*?)(?=^  \S|\Z)", text, re.S | re.M)
        assert block, job
        assert "python-version: '3.15'" in block.group(1), job


def test_publish_workflow_uses_supported_pythons_only():
    versions = _python_versions(_workflow("publish.yml"))
    assert set(SUPPORTED) <= versions
    assert not versions & set(RETIRED)


def test_container_image_is_on_the_newest_python():
    images = re.findall(
        r"^FROM python:(\S+?)-slim", (ROOT / "Dockerfile").read_text(encoding="utf-8"), re.M
    )
    assert images and set(images) == {"3.15"}


def test_the_package_refuses_an_older_interpreter_by_metadata_only():
    """No runtime shim for old Pythons: the floor lives in ``requires-python`` alone."""

    source = (ROOT / "comfy_headless" / "_version.py").read_text(encoding="utf-8")
    assert "version_info" not in source
