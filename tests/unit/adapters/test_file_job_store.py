import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from fingerprinter.adapters.file_job_store import FileJobStore
from fingerprinter.domain.exceptions import FormatNotAvailable, JobNotFound
from fingerprinter.domain.model import (
    FingerprintOutcome,
    JobRecord,
    JobState,
    ReportFormat,
    Source,
)

CREATED = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
FINISHED = datetime(2026, 11, 8, 10, 0, 7, tzinfo=UTC)


@pytest.fixture
def store(tmp_path: Path) -> FileJobStore:
    return FileJobStore(tmp_path / "reports", clock=lambda: FINISHED)


def record(job_id: str = "job-1", source: Source | None = None, created=CREATED) -> JobRecord:
    return JobRecord(
        id=job_id,
        source=source or Source(endpoint="http://example.org/sparql", graphs=("http://g",)),
        created_at=created,
        state=JobState.QUEUED,
    )


def outcome(tmp_path: Path, **files: tuple[str, ...]) -> FingerprintOutcome:
    """An outcome whose files exist under a work folder, e.g. ``html=("main.html",)``."""
    work = tmp_path / "work"
    result: dict[ReportFormat, tuple[Path, ...]] = {}
    for name, filenames in files.items():
        folder = work / name
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        for filename in filenames:
            (folder / filename).write_text(f"{name}:{filename}")
            paths.append(folder / filename)
        result[ReportFormat(name)] = tuple(paths)
    return FingerprintOutcome(files=result)


def test_create_then_get_returns_the_record(store):
    store.create(record())

    assert store.get("job-1") == record()


def test_meta_json_is_the_record_in_the_api_shape(store, tmp_path):
    store.create(record())

    meta = json.loads((tmp_path / "reports" / "job-1" / "meta.json").read_text())

    assert meta == {
        "id": "job-1",
        "source": {"endpoint": "http://example.org/sparql", "graphs": ["http://g"]},
        "created_at": "2026-11-08T10:00:00+00:00",
        "state": "queued",
        "reason": None,
        "failures": [],
        "formats": [],
        "finished_at": None,
        "files": {},
    }


def test_a_file_source_round_trips(store):
    store.create(record(source=Source(file="data.rdf")))

    assert store.get("job-1").source == Source(file="data.rdf")


@pytest.mark.parametrize("job_id", ["unknown", "../escape", ""])
def test_get_of_an_unknown_id_raises_job_not_found(store, job_id):
    with pytest.raises(JobNotFound):
        store.get(job_id)


def test_set_state_keeps_the_rest_of_the_record(store):
    store.create(record())

    store.set_state("job-1", JobState.FAILED, "boom", ("a",))

    stored = store.get("job-1")
    assert (stored.state, stored.reason, stored.failures) == (JobState.FAILED, "boom", ("a",))
    assert stored.source == record().source


def test_set_state_writes_the_failures_to_meta_json(store, tmp_path):
    store.create(record())

    store.set_state("job-1", JobState.COMPLETED_WITH_FAILURES, failures=("m1 failed", "m2 failed"))

    meta = json.loads((tmp_path / "reports" / "job-1" / "meta.json").read_text())
    assert meta["state"] == "completed_with_failures"
    assert meta["failures"] == ["m1 failed", "m2 failed"]


@pytest.mark.parametrize(
    ("state", "stamped"),
    [
        (JobState.QUEUED, False),
        (JobState.RUNNING, False),
        (JobState.COMPLETED, True),
        (JobState.COMPLETED_WITH_FAILURES, True),
        (JobState.FAILED, True),
        (JobState.CANCELLED, True),
    ],
)
def test_set_state_stamps_finished_at_with_the_clock_for_a_final_state_only(store, state, stamped):
    store.create(record())

    store.set_state("job-1", state)

    assert store.get("job-1").finished_at == (FINISHED if stamped else None)


def test_the_clock_defaults_to_the_current_utc_time(tmp_path):
    store = FileJobStore(tmp_path / "reports")
    store.create(record())

    store.set_state("job-1", JobState.COMPLETED)

    finished = store.get("job-1").finished_at
    assert finished is not None
    assert abs((datetime.now(UTC) - finished).total_seconds()) < 60


def test_set_state_of_an_unknown_id_raises_job_not_found(store):
    with pytest.raises(JobNotFound):
        store.set_state("unknown", JobState.RUNNING)


def test_list_returns_every_record_oldest_first(store):
    store.create(record("b", created=datetime(2026, 11, 8, 12, tzinfo=UTC)))
    store.create(record("a", created=CREATED))

    assert [r.id for r in store.list()] == ["a", "b"]


def test_list_ignores_folders_without_a_record(store, tmp_path):
    store.create(record())
    (tmp_path / "reports" / "stray").mkdir()

    assert [r.id for r in store.list()] == ["job-1"]


def test_list_skips_a_record_deleted_while_listing(store, monkeypatch):
    store.create(record("job-1"))
    store.create(record("job-2"))
    get = store.get

    def deleted_meanwhile(job_id):
        if job_id == "job-1":
            raise JobNotFound(job_id)
        return get(job_id)

    monkeypatch.setattr(store, "get", deleted_meanwhile)

    assert [r.id for r in store.list()] == ["job-2"]


def test_list_of_a_missing_reports_folder_is_empty(tmp_path):
    assert FileJobStore(tmp_path / "nowhere").list() == []


def test_save_outputs_moves_files_into_format_folders_and_records_the_formats(store, tmp_path):
    store.create(record())

    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",), json=("profile.json",)))

    folder = tmp_path / "reports" / "job-1"
    assert (folder / "html" / "main.html").read_text() == "html:main.html"
    assert (folder / "json" / "profile.json").read_text() == "json:profile.json"
    assert not (tmp_path / "work" / "html" / "main.html").exists()
    assert store.get("job-1").formats == (ReportFormat.HTML, ReportFormat.JSON)


def test_save_outputs_lists_the_files_per_format_without_the_zip(store, tmp_path):
    store.create(record())

    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",), puml=("b.puml", "a.puml")))

    assert store.get("job-1").files == {
        ReportFormat.HTML: ("main.html",),
        ReportFormat.PUML: ("a.puml", "b.puml"),
    }
    meta = json.loads((tmp_path / "reports" / "job-1" / "meta.json").read_text())
    assert meta["files"] == {"html": ["main.html"], "puml": ["a.puml", "b.puml"]}


def test_everything_is_zipped(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",), json=("profile.json",)))

    with zipfile.ZipFile(store.file_for("job-1", ReportFormat.ZIP)) as archive:
        assert sorted(archive.namelist()) == ["html/main.html", "json/profile.json"]


def test_everything_is_zipped_with_all_seven_formats(store, tmp_path):
    store.create(record())
    store.save_outputs(
        "job-1",
        outcome(
            tmp_path,
            html=("main.html",),
            json=("profile.json",),
            shacl=("shapes.ttl",),
            puml=("a.puml", "b.puml"),
            pattern=("p1.md", "p2.csv"),
            shex=("shapes.shex",),
            pitfalls=("pitfalls.tsv",),
        ),
    )

    assert len(store.get("job-1").formats) == 7
    with zipfile.ZipFile(store.file_for("job-1", ReportFormat.ZIP)) as archive:
        assert sorted(archive.namelist()) == [
            "html/main.html",
            "json/profile.json",
            "pattern/p1.md",
            "pattern/p2.csv",
            "pitfalls/pitfalls.tsv",
            "puml/a.puml",
            "puml/b.puml",
            "shacl/shapes.ttl",
            "shex/shapes.shex",
        ]


def test_a_format_without_files_is_not_listed_in_the_record_or_the_zip(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",), shacl=()))

    assert store.get("job-1").formats == (ReportFormat.HTML,)
    with zipfile.ZipFile(store.file_for("job-1", ReportFormat.ZIP)) as archive:
        assert archive.namelist() == ["html/main.html"]


def test_save_outputs_refuses_a_job_that_already_has_outputs(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))

    with pytest.raises(FileExistsError):
        store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))


def test_save_outputs_of_an_unknown_job_raises_job_not_found(store, tmp_path):
    with pytest.raises(JobNotFound):
        store.save_outputs("unknown", outcome(tmp_path, html=("main.html",)))


def test_the_report_page_is_downloaded(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))

    assert store.file_for("job-1", ReportFormat.HTML).read_text() == "html:main.html"


def test_a_multi_file_format_is_zipped_on_download(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, puml=("a.puml", "b.puml")))

    download = store.file_for("job-1", ReportFormat.PUML)

    assert download.name == "job-1-puml.zip"
    with zipfile.ZipFile(download) as archive:
        assert sorted(archive.namelist()) == ["a.puml", "b.puml"]


def test_the_zip_of_a_multi_file_format_is_built_when_the_outputs_are_saved(store, tmp_path):
    store.create(record())

    store.save_outputs("job-1", outcome(tmp_path, puml=("a.puml", "b.puml"), html=("main.html",)))

    assert sorted(p.name for p in (tmp_path / "reports" / "job-1").iterdir()) == [
        "html", "job-1-puml.zip", "meta.json", "puml", "report.zip",
    ]  # fmt: skip
    with zipfile.ZipFile(tmp_path / "reports" / "job-1" / "report.zip") as archive:
        assert sorted(archive.namelist()) == ["html/main.html", "puml/a.puml", "puml/b.puml"]


def test_one_listed_file_of_a_format_is_found_by_name(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, puml=("a.puml", "b.puml")))

    assert store.file_for("job-1", ReportFormat.PUML, "b.puml").read_text() == "puml:b.puml"


@pytest.mark.parametrize("name", ["c.puml", "../meta.json", "../../etc/passwd", "puml/a.puml", ""])
def test_a_file_the_record_does_not_list_is_not_available(store, tmp_path, name):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, puml=("a.puml", "b.puml")))

    with pytest.raises(FormatNotAvailable):
        store.file_for("job-1", ReportFormat.PUML, name)


def test_the_zip_has_no_listed_files(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))

    with pytest.raises(FormatNotAvailable):
        store.file_for("job-1", ReportFormat.ZIP, "report.zip")


def test_a_format_with_no_file_is_not_available(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))
    (tmp_path / "reports" / "job-1" / "shacl").mkdir()

    with pytest.raises(FormatNotAvailable):
        store.file_for("job-1", ReportFormat.SHACL)


def test_file_for_a_job_without_outputs_is_not_available(store):
    store.create(record())

    for report_format in (ReportFormat.HTML, ReportFormat.ZIP):
        with pytest.raises(FormatNotAvailable):
            store.file_for("job-1", report_format)


def test_file_for_an_unknown_job_raises_job_not_found(store):
    with pytest.raises(JobNotFound):
        store.file_for("unknown", ReportFormat.HTML)


def test_discard_outputs_keeps_only_the_record_and_clears_the_formats(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, puml=("a.puml", "b.puml")))
    store.file_for("job-1", ReportFormat.PUML)

    store.discard_outputs("job-1")

    assert sorted(p.name for p in (tmp_path / "reports" / "job-1").iterdir()) == ["meta.json"]
    assert (store.get("job-1").formats, store.get("job-1").files) == ((), {})


def test_outputs_can_be_saved_again_after_a_discard(store, tmp_path):
    store.create(record())
    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))
    store.discard_outputs("job-1")

    store.save_outputs("job-1", outcome(tmp_path, html=("main.html",)))

    assert store.get("job-1").formats == (ReportFormat.HTML,)


def test_delete_removes_the_job_and_a_second_delete_is_not_found(store, tmp_path):
    store.create(record())

    store.delete("job-1")

    assert not (tmp_path / "reports" / "job-1").exists()
    with pytest.raises(JobNotFound):
        store.delete("job-1")


def test_delete_all_removes_every_job_and_tolerates_an_empty_store(store):
    store.delete_all()
    store.create(record("a"))
    store.create(record("b"))

    store.delete_all()

    assert store.list() == []
