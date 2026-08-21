"""Single source of truth for the package version.

Imported by both ``__init__`` and ``config`` so the version cannot drift between
them. Keep in sync with ``pyproject.toml``; ``tests/test_main.py`` asserts they match.
"""

__version__ = "3.0.1"
