"""``DatasetStore`` on Fuseki: the admin API ``/$/datasets`` and the Graph Store Protocol."""

from collections.abc import Mapping
from pathlib import Path

import requests

TIMEOUT_SECONDS = 60


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
        response.raise_for_status()

    def load_file(self, name: str, path: Path) -> None:
        extension = path.suffix.lstrip(".").lower()
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
        response.raise_for_status()

    def delete(self, name: str) -> None:
        response = requests.delete(
            f"{self.base_url}/$/datasets/{name}", auth=self.auth, timeout=TIMEOUT_SECONDS
        )
        if response.status_code != requests.codes.not_found:
            response.raise_for_status()

    def sparql_url(self, name: str) -> str:
        return f"{self.base_url}/{name}/sparql"
