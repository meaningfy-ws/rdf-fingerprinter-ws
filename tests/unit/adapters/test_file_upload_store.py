import io
from pathlib import Path

import pytest

from fingerprinter.adapters.file_upload_store import FileUploadStore
from fingerprinter.domain.exceptions import UploadTooLarge


def test_save_writes_the_stream_under_the_job_folder(tmp_path):
    store = FileUploadStore(tmp_path / "db", max_bytes=1024)

    path = store.save("job-1", io.BytesIO(b"<rdf/>"), "data.rdf")

    assert path == tmp_path / "db" / "job-1" / "data.rdf"
    assert path.read_bytes() == b"<rdf/>"


def test_save_cleans_the_file_name(tmp_path):
    store = FileUploadStore(tmp_path / "db", max_bytes=1024)

    path = store.save("job-1", io.BytesIO(b"x"), "../../etc/my data.ttl")

    assert path == tmp_path / "db" / "job-1" / "etc_my_data.ttl"


def test_discard_removes_the_job_folder_and_tolerates_a_missing_one(tmp_path):
    store = FileUploadStore(tmp_path / "db", max_bytes=1024)
    store.save("job-1", io.BytesIO(b"x"), "data.ttl")

    store.discard("job-1")
    store.discard("job-1")

    assert not Path(tmp_path / "db" / "job-1").exists()


def test_a_file_of_exactly_the_limit_is_saved(tmp_path):
    store = FileUploadStore(tmp_path / "db", max_bytes=1024)

    path = store.save("job-1", io.BytesIO(b"x" * 1024), "data.ttl")

    assert path.stat().st_size == 1024


def test_a_file_over_the_limit_is_refused_and_nothing_stays_on_disk(tmp_path):
    store = FileUploadStore(tmp_path / "db", max_bytes=1024)

    with pytest.raises(UploadTooLarge, match="data.ttl"):
        store.save("job-1", io.BytesIO(b"x" * 1025), "data.ttl")

    assert not (tmp_path / "db" / "job-1").exists()
