"""Session-scoped Fuseki and Redis containers for the integration and e2e tests (design D-11, D-13); started once per run."""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy, LogMessageWaitStrategy

FUSEKI_IMAGE = "stain/jena-fuseki:5.1.0"
FUSEKI_PORT = 3030
FUSEKI_ADMIN_USER = "admin"
FUSEKI_ADMIN_PASSWORD = "integration-test-password"
REDIS_IMAGE = "redis:7-alpine"
REDIS_PORT = 6379


@dataclass(frozen=True)
class FusekiServer:
    host: str
    port: int
    user: str
    password: str

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class RedisServer:
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"


@pytest.fixture(scope="session")
def fuseki() -> Iterator[FusekiServer]:
    container = (
        DockerContainer(FUSEKI_IMAGE)
        .with_exposed_ports(FUSEKI_PORT)
        .with_env("ADMIN_PASSWORD", FUSEKI_ADMIN_PASSWORD)
        .waiting_for(HttpWaitStrategy(FUSEKI_PORT, "/$/ping").for_status_code(200))
    )
    with container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(FUSEKI_PORT)
        yield FusekiServer(host, int(port), FUSEKI_ADMIN_USER, FUSEKI_ADMIN_PASSWORD)


@pytest.fixture(scope="session")
def redis_server() -> Iterator[RedisServer]:
    container = (
        DockerContainer(REDIS_IMAGE)
        .with_exposed_ports(REDIS_PORT)
        .waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
    )
    with container:
        host = container.get_container_host_ip()
        yield RedisServer(host, int(container.get_exposed_port(REDIS_PORT)))
