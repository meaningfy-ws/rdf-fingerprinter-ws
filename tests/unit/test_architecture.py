"""The package-boundaries spec: each contract of .importlinter catches its forbidden import (task 2.6).

Each case lints a temporary copy of the package with one forbidden import added, and expects
lint-imports to fail naming that import.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


def lint(package_root: Path) -> subprocess.CompletedProcess[str]:
    lint_imports = Path(sys.executable).parent / "lint-imports"
    return subprocess.run(
        [str(lint_imports), "--config", str(ROOT / ".importlinter"), "--no-cache"],
        cwd=package_root,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(package_root), "PATH": str(Path(sys.executable).parent)},
    )


@pytest.fixture
def package_copy(tmp_path: Path) -> Path:
    shutil.copytree(
        ROOT / "fingerprinter",
        tmp_path / "fingerprinter",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return tmp_path


def add_import(package_root: Path, module: str, statement: str) -> None:
    path = package_root / Path(*module.split(".")).with_suffix(".py")
    path.write_text(f"{statement}  # noqa\n" + path.read_text())


def test_the_delivered_code_passes(package_copy: Path) -> None:
    result = lint(package_copy)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("scenario", "module", "statement", "named"),
    [
        (
            "A forbidden import fails the check",
            "fingerprinter.services.jobs",
            "import fingerprinter.adapters.fuseki",
            "fingerprinter.services.jobs -> fingerprinter.adapters.fuseki",
        ),
        (
            "A framework import in the domain fails the check",
            "fingerprinter.domain.model",
            "import flask",
            "fingerprinter.domain.model -> flask",
        ),
        (
            "A service import in the UI fails the check",
            "fingerprinter.entrypoints.ui.views",
            "import fingerprinter.services.jobs",
            "fingerprinter.entrypoints.ui.views -> fingerprinter.services.jobs",
        ),
        (
            "A second importer of the library fails the check",
            "fingerprinter.adapters.fuseki",
            "import fingerprint",
            "fingerprinter.adapters.fuseki -> fingerprint",
        ),
    ],
)
def test_a_forbidden_import_is_named(
    package_copy: Path, scenario: str, module: str, statement: str, named: str
) -> None:
    add_import(package_copy, module, statement)

    result = lint(package_copy)

    assert result.returncode != 0, scenario
    assert named in result.stdout, result.stdout
