"""``Fingerprinter`` on the rdf-fingerprinter library; the only module that imports ``fingerprint``.

Library errors (``ValueError`` for usage errors, ``EndpointUnreachable``) are not caught here: the
job service turns them into a failed job (design D-15).
"""

import shutil
from pathlib import Path
from typing import Any

from fingerprint import config as library_config
from fingerprint.service_layer.handlers import fingerprint_report
from fingerprint.service_layer.settings import resolve_settings

from fingerprinter.domain.model import FingerprintOutcome, ReportFormat


def describe_failure(failure: Any) -> str:
    """One line for a measurement that failed: what, where, and why."""
    where = [
        part
        for part in (failure.graph, failure.class_iri, failure.property, failure.check_id)
        if part
    ]
    reason = f": {failure.message}" if failure.message else ""
    return " ".join([f"{failure.query_kind} failed", *where]) + reason


def _move_into(report_format: ReportFormat, source: Path, work_folder: Path) -> Path:
    folder = work_folder / report_format.value
    folder.mkdir()
    return Path(shutil.move(source, folder / source.name))


class LibraryFingerprinter:
    def fingerprint(
        self, endpoint_url: str, graphs: tuple[str, ...], work_folder: Path
    ) -> FingerprintOutcome:
        # env={}: collection settings never come from the worker's environment (D-15)
        settings = resolve_settings(env={}, selected_graphs=list(graphs) or None)
        report, run = fingerprint_report(
            endpoint_url, work_folder, settings, formats=(), prefix_list=None
        )
        return FingerprintOutcome(
            files={
                ReportFormat.HTML: (_move_into(ReportFormat.HTML, report, work_folder),),
                ReportFormat.JSON: (
                    _move_into(
                        ReportFormat.JSON, work_folder / library_config.profile_file, work_folder
                    ),
                ),
            },
            failures=tuple(describe_failure(failure) for failure in run.failures or ()),
        )
