from pathlib import Path

import pytest

from apps.core.version import get_project_version


@pytest.fixture(autouse=True)
def _clear_version_cache():
    get_project_version.cache_clear()
    yield
    get_project_version.cache_clear()


def test_reads_version_from_pyproject(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\nversion = "1.2.3"\n', encoding="utf-8")

    assert get_project_version(pyproject) == "1.2.3"


def test_returns_unknown_when_file_missing(tmp_path: Path):
    assert get_project_version(tmp_path / "missing.toml") == "unknown"


def test_returns_unknown_when_file_is_invalid(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("not = [valid", encoding="utf-8")

    assert get_project_version(pyproject) == "unknown"


def test_returns_unknown_when_version_is_absent(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\n', encoding="utf-8")

    assert get_project_version(pyproject) == "unknown"


def test_project_pyproject_has_semver_version():
    version = get_project_version()

    major, minor, patch = version.split(".")
    assert all(part.isdigit() for part in (major, minor, patch))
