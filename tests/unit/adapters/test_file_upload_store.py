import io
from pathlib import Path

from fingerprinter.adapters.file_upload_store import FileUploadStore


def test_save_writes_the_stream_under_the_job_folder(tmp_path):
    store = FileUploadStore(tmp_path / "db")

    path = store.save("job-1", io.BytesIO(b"<rdf/>"), "data.rdf")

    assert path == tmp_path / "db" / "job-1" / "data.rdf"
    assert path.read_bytes() == b"<rdf/>"


def test_save_cleans_the_file_name(tmp_path):
    store = FileUploadStore(tmp_path / "db")

    path = store.save("job-1", io.BytesIO(b"x"), "../../etc/my data.ttl")

    assert path == tmp_path / "db" / "job-1" / "etc_my_data.ttl"


def test_discard_removes_the_job_folder_and_tolerates_a_missing_one(tmp_path):
    store = FileUploadStore(tmp_path / "db")
    store.save("job-1", io.BytesIO(b"x"), "data.ttl")

    store.discard("job-1")
    store.discard("job-1")

    assert not Path(tmp_path / "db" / "job-1").exists()
