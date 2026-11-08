"""Root test configuration.

Test-type markers (``unit``, ``feature``, ``integration``, ``e2e``) are stamped onto every collected
test by file path in ``pytest_collection_modifyitems``, not by per-file ``pytestmark``: a
``pytestmark`` in a ``conftest.py`` is silently ignored (a conftest is a plugin, not a test
module). The markers are registered in ``pytest.ini``.
"""

from pathlib import Path

import pytest

from tests.containers import fuseki, redis_url  # noqa: F401  (fixtures shared by two tiers)


@pytest.fixture(autouse=True)
def isolated_folders(tmp_path, monkeypatch):
    """Uploads and reports go to the test's own folders, never to the repository's db/ and reports/."""
    for variable, folder in (
        ("RDF_FINGERPRINTER_FILE_DB", "service-db"),
        ("RDF_FINGERPRINTER_REPORTS_DB", "service-reports"),
    ):
        (tmp_path / folder).mkdir()
        monkeypatch.setenv(variable, str(tmp_path / folder))


TESTS_ROOT_DIR = Path(__file__).parent

# The first directory that starts a test's path below tests/ gives its marker.
_MARKERS_BY_DIR = (
    ("unit/", "unit"),
    ("feature/", "feature"),
    ("integration/", "integration"),
    ("e2e/", "e2e"),
)


def marker_for_path(path: str) -> str | None:
    """The marker implied by the directory a test file lives in, matched below ``tests/`` only."""
    try:
        relative = Path(path).relative_to(TESTS_ROOT_DIR).as_posix()
    except ValueError:
        return None
    return next(
        (marker for directory, marker in _MARKERS_BY_DIR if relative.startswith(directory)), None
    )


def pytest_collection_modifyitems(items: list) -> None:
    """Stamp each collected test with the marker of its directory."""
    for item in items:
        marker = marker_for_path(str(item.path))
        if marker:
            item.add_marker(getattr(pytest.mark, marker))
