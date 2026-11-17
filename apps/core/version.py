"""Project version, read from pyproject.toml (the single source of truth)."""

import tomllib
from functools import cache
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"


@cache
def get_project_version(pyproject_path: Path = PYPROJECT_PATH) -> str:
    """Return `[project].version` from pyproject.toml, or "unknown" if unavailable."""
    try:
        with pyproject_path.open("rb") as file:
            data = tomllib.load(file)
    except OSError, tomllib.TOMLDecodeError:
        return "unknown"
    return str(data.get("project", {}).get("version", "unknown"))
