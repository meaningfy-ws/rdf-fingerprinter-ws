"""``Fingerprinter`` on the rdf-fingerprinter library; the only module that imports ``fingerprint``.

Library errors of a run (``ValueError`` for usage errors, ``EndpointUnreachable``) are not caught
here: the job service turns them into a failed job (design D-15). Those of a graph listing become
``GraphListingFailed``.
"""

import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fingerprint import config as library_config
from fingerprint.adapters.exceptions import EndpointUnreachable, PermanentError, QueryTimeout
from fingerprint.service_layer.handlers import fingerprint_report, list_named_graphs
from fingerprint.service_layer.representations import generate_representations
from fingerprint.service_layer.settings import resolve_settings

from fingerprinter.domain.exceptions import GraphListingFailed
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


# Why a graph listing failed, in words for the user: the library's messages can name the URL.
LISTING_FAILURES: Mapping[type[Exception], str] = {
    EndpointUnreachable: "the endpoint could not be reached",
    QueryTimeout: "the endpoint did not answer in time",
    PermanentError: "the endpoint refused the query",
}
LISTING_TIMEOUT_SECONDS = 20


def _move_into(report_format: ReportFormat, source: Path, work_folder: Path) -> Path:
    folder = work_folder / report_format.value
    folder.mkdir()
    return Path(shutil.move(source, folder / source.name))


# The formats the library generates after profiling, each into its own folder (design D-3), with
# the id the library's generator registry knows it by.
GENERATOR_IDS: Mapping[ReportFormat, str] = {
    ReportFormat.SHACL: "shacl",
    ReportFormat.PUML: "puml",
    ReportFormat.PATTERN: "pattern",
    ReportFormat.SHEX: "shex",
    ReportFormat.PITFALLS: "pitfalls",
}
# the pitfall findings reach the report page and the pitfalls output only with the scan on
PITFALL_SCAN = True


def _generate(run: Any, work_folder: Path) -> dict[ReportFormat, tuple[Path, ...]]:
    """Render every generated format of the run, each into its own folder of ``work_folder``."""
    return {
        report_format: tuple(
            generate_representations(run, work_folder / report_format.value, [generator_id])
        )
        for report_format, generator_id in GENERATOR_IDS.items()
    }


class LibraryFingerprinter:
    def named_graphs(self, url: str) -> tuple[str, ...]:
        settings = resolve_settings(env={}, config={"timeout_seconds": LISTING_TIMEOUT_SECONDS})
        try:
            return tuple(list_named_graphs(url, settings))
        except tuple(LISTING_FAILURES) as error:
            reason = next(why for kind, why in LISTING_FAILURES.items() if isinstance(error, kind))
            raise GraphListingFailed(reason) from error

    def fingerprint(
        self, endpoint_url: str, graphs: tuple[str, ...], work_folder: Path
    ) -> FingerprintOutcome:
        # env={}: collection settings never come from the worker's environment (D-15)
        settings = resolve_settings(
            env={}, selected_graphs=list(graphs) or None, config={"pitfall_scan": PITFALL_SCAN}
        )
        report, run = fingerprint_report(
            endpoint_url, work_folder, settings, formats=(), prefix_list=None
        )
        profile = work_folder / library_config.profile_file
        files: dict[ReportFormat, tuple[Path, ...]] = {
            ReportFormat.HTML: (_move_into(ReportFormat.HTML, report, work_folder),),
            ReportFormat.JSON: (_move_into(ReportFormat.JSON, profile, work_folder),),
            **_generate(run, work_folder),
        }
        return FingerprintOutcome(
            files=files,
            failures=tuple(describe_failure(failure) for failure in run.failures or ()),
        )
