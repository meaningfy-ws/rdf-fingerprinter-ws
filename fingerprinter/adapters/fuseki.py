"""``DatasetStore`` on Fuseki: the admin API ``/$/datasets`` and the Graph Store Protocol."""

from collections.abc import Mapping
from pathlib import Path

import requests

from fingerprinter.domain.model import file_extension

TIMEOUT_SECONDS = 60


def _check(response: requests.Response) -> None:
    """Raise for a refused request; the message carries the status, never the internal URL."""
    if not response.ok:
        raise requests.HTTPError(f"dataset store failed: {response.status_code}")


class FusekiDatasetStore:
    def __init__(self, base_url: str, user: str, password: str, mime_types: Mapping[str, str]):
        self.base_url = base_url.rstrip("/")
        self.auth = (user, password)
        self.mime_types = mime_types

    def create(self, name: str) -> None:
        response = requests.post(
            f"{self.base_url}/$/datasets",
            data={"dbType": "tdb", "dbName": name},
            auth=self.auth,
            timeout=TIMEOUT_SECONDS,
        )
        _check(response)

    def load_file(self, name: str, path: Path) -> None:
        extension = file_extension(path.name)
        if extension not in self.mime_types:
            raise ValueError(f'Format of "{path.name}" is not supported: .{extension}')
        # the open file is streamed as the request body, so large files stay out of memory
        with path.open("rb") as data:
            response = requests.post(
                f"{self.base_url}/{name}/data",
                data=data,
                headers={"Content-Type": self.mime_types[extension]},
                auth=self.auth,
                timeout=TIMEOUT_SECONDS,
            )
        _check(response)

    def delete(self, name: str) -> None:
        response = requests.delete(
            f"{self.base_url}/$/datasets/{name}", auth=self.auth, timeout=TIMEOUT_SECONDS
        )
        if response.status_code != requests.codes.not_found:
            _check(response)

    def sparql_url(self, name: str) -> str:
        return f"{self.base_url}/{name}/sparql"
