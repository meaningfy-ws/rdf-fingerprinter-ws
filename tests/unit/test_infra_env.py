"""infra/.env.example: placeholders only, every setting the service reads, none of the library's (D-15)."""

import os
import re
from pathlib import Path

import pytest
import yaml

from fingerprinter.config import Settings

REPO = Path(__file__).parents[2]
ENV_EXAMPLE = REPO / "infra" / ".env.example"
COMPOSE = REPO / "infra" / "compose.yaml"
DOCKERFILE = REPO / "infra" / "docker" / "Dockerfile"
WORKFLOWS = REPO / ".github" / "workflows"
CONFIG = REPO / "fingerprinter" / "config.py"

LIBRARY_OPERATIONAL_VARIABLES = tuple(
    f"RDF_FINGERPRINTER_{name}"
    for name in (
        "PROFILE_FILE",
        "RETRY_BACKOFF_SECONDS",
        "TIMEOUT_MARKERS",
        "ERROR_EXCERPT_LENGTH",
        "SHAPES_NAMESPACE",
        "DEFAULT_GRAPH_LABEL",
        "PREFIXES_FILE",
        "PREFIX_LOOKUP",
    )
)
SECRET_PLACEHOLDER = "change-me"
KNOWN_SETTING = (
    "RDF_FINGERPRINTER_FUSEKI_LOCATION"  # read through _service_url, a scan must find it
)


def example_settings() -> dict[str, str]:
    lines = (line.strip() for line in ENV_EXAMPLE.read_text().splitlines())
    return dict(line.split("=", 1) for line in lines if line and not line.startswith("#"))


def settings_read_by_config() -> set[str]:
    """Every variable ``Settings.from_env`` reads: the literal names, and the location and port of each service."""
    source = CONFIG.read_text()
    literal = set(re.findall(r'"((?:RDF_FINGERPRINTER_|SHOW_)[A-Z_]+)"', source))
    services = re.findall(r'_service_url\("([A-Z]+)"', source)
    return literal | {
        f"RDF_FINGERPRINTER_{s}_{part}" for s in services for part in ("LOCATION", "PORT")
    }


def interpolated_in(path: Path) -> set[str]:
    """Every ``${NAME}``, ``${NAME:-default}`` or compose-escaped ``$${NAME}`` the file mentions."""
    return set(re.findall(r"\$\$?\{((?:RDF_FINGERPRINTER_|SHOW_)[A-Z_]+)", path.read_text()))


def set_by_stack_files() -> set[str]:
    """Variables the compose ``environment:`` blocks and the workflows' ``env:`` blocks assign."""
    names: set[str] = set(
        re.findall(r"^\s+((?:RDF_FINGERPRINTER_)[A-Z_]+):", COMPOSE.read_text(), re.M)
    )
    for workflow in WORKFLOWS.glob("*.yml"):
        names |= set(
            re.findall(r"^\s+((?:RDF_FINGERPRINTER_)[A-Z_]+):", workflow.read_text(), re.M)
        )
    return names


@pytest.mark.parametrize("variable", LIBRARY_OPERATIONAL_VARIABLES)
def test_the_library_operational_variables_are_not_set(variable):
    assert variable not in example_settings(), f"{variable} is set in the example"
    assert variable not in set_by_stack_files(), f"{variable} is set in compose or a workflow"


def test_the_config_scan_finds_a_known_setting():
    assert KNOWN_SETTING in settings_read_by_config(), (
        "the scan of config.py found nothing it should"
    )


def test_every_setting_the_service_reads_is_in_the_example():
    missing = settings_read_by_config() - example_settings().keys()
    assert missing == set(), f"not in .env.example: {sorted(missing)}"


@pytest.mark.parametrize("path", [COMPOSE, DOCKERFILE], ids=lambda p: p.name)
def test_every_variable_the_stack_files_interpolate_is_in_the_example(path):
    missing = interpolated_in(path) - example_settings().keys()
    assert interpolated_in(path), f"{path.name}: no variable found, the scan is broken"
    assert missing == set(), (
        f"{path.name} uses variables missing from .env.example: {sorted(missing)}"
    )


@pytest.mark.parametrize(
    "variable",
    [
        "RDF_FINGERPRINTER_API_SECRET_KEY",
        "RDF_FINGERPRINTER_UI_SECRET_KEY",
        "RDF_FINGERPRINTER_FUSEKI_PASSWORD",
    ],
)
def test_secrets_are_placeholders(variable):
    assert example_settings()[variable] == SECRET_PLACEHOLDER, f"{variable} holds a real value"


def test_the_example_is_a_working_configuration(monkeypatch):
    for name in [
        n for n in os.environ if n.startswith("RDF_FINGERPRINTER_") or n == "SHOW_SWAGGER_UI"
    ]:
        monkeypatch.delenv(name)
    for name, value in example_settings().items():
        monkeypatch.setenv(name, value)
    settings = Settings.from_env()
    assert settings.api_url == "http://fingerprinter-api:4020"


# --- The hardened stack (harden-deployment: networks, egress proxy, secrets per service) ---

INFRA = REPO / "infra"
DEV_COMPOSE = INFRA / "compose.dev.yaml"
SQUID_CONF = INFRA / "proxy" / "squid.conf"
NGINX_TEMPLATE = INFRA / "edge" / "default.conf.template"

NETWORKS = {
    "edge": {"edge", "app"},
    "fingerprinter-ui": {"app"},
    "fingerprinter-api": {"app", "work"},
    "fingerprinter-worker": {"work"},
    "fingerprinter-flower": {"monitor", "edge"},
    "egress": {"work", "edge"},
    "redis": {"work", "monitor"},
    "fuseki": {"work"},
    "plantuml": {"work"},
}
INTERNAL = {"app", "work", "monitor"}
SECRETS = {
    "RDF_FINGERPRINTER_API_SECRET_KEY",
    "RDF_FINGERPRINTER_UI_SECRET_KEY",
    "RDF_FINGERPRINTER_FUSEKI_PASSWORD",
}
SECRETS_PER_SERVICE = {
    "fingerprinter-api": {
        "RDF_FINGERPRINTER_API_SECRET_KEY",
        "RDF_FINGERPRINTER_FUSEKI_PASSWORD",
    },
    "fingerprinter-ui": {"RDF_FINGERPRINTER_UI_SECRET_KEY"},
    "fingerprinter-worker": {"RDF_FINGERPRINTER_FUSEKI_PASSWORD"},
    "fingerprinter-flower": set(),
}
BLOCKED_RANGES = (
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
)


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def stack() -> dict:
    return load(COMPOSE)


def service_env(name: str) -> dict:
    return stack()["services"][name].get("environment", {})


def test_the_networks_are_pinned():
    services = stack()["services"]
    assert {name: set(s["networks"]) for name, s in services.items()} == NETWORKS


def test_only_the_edge_network_has_a_route_out():
    networks = stack()["networks"]
    assert {n for n, spec in networks.items() if (spec or {}).get("internal")} == INTERNAL
    assert set(networks) == INTERNAL | {"edge"}


@pytest.mark.parametrize(
    "service", ["fingerprinter-ui", "fingerprinter-api", "fingerprinter-worker"]
)
def test_the_app_containers_are_on_no_network_with_a_route_out(service):
    assert not set(stack()["services"][service]["networks"]) & {"edge"}


def test_the_worker_shares_no_network_with_flower_or_the_api():
    services = stack()["services"]
    worker = set(services["fingerprinter-worker"]["networks"])
    assert not worker & set(services["fingerprinter-flower"]["networks"])
    assert not worker & set(services["fingerprinter-ui"]["networks"])
    assert "app" not in worker


def test_only_loopback_ports_are_published_and_only_by_the_edge_and_flower():
    published = {name: s["ports"] for name, s in stack()["services"].items() if "ports" in s}
    assert set(published) == {"edge", "fingerprinter-flower"}
    assert all(p.startswith("127.0.0.1:") for ports in published.values() for p in ports)


@pytest.mark.parametrize("service", ["fingerprinter-api", "fingerprinter-worker"])
def test_the_api_and_the_worker_reach_user_urls_through_the_egress_proxy(service):
    env = service_env(service)
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        assert env[name] == "http://egress:3128"
    assert env["NO_PROXY"] == env["no_proxy"] == "fuseki,plantuml"


@pytest.mark.parametrize("service", ["fingerprinter-ui", "fingerprinter-flower"])
def test_the_other_containers_have_no_proxy_settings(service):
    assert not {k for k in service_env(service) if k.lower().endswith("_proxy")}


def test_the_squid_config_refuses_the_ranges_before_allowing_anything():
    conf = SQUID_CONF.read_text()
    for cidr in BLOCKED_RANGES:
        assert re.search(rf"^acl blocked dst (?:.* )?{re.escape(cidr)}(\s|$)", conf, re.M), cidr
    assert conf.index("http_access deny blocked") < conf.index("http_access allow all")
    assert "cache deny all" in conf


@pytest.mark.parametrize(("service", "secrets"), SECRETS_PER_SERVICE.items())
def test_each_container_holds_only_its_secrets(service, secrets):
    held = {k for k, v in service_env(service).items() if k in SECRETS}
    assert held == secrets


@pytest.mark.parametrize("service", sorted(NETWORKS))
def test_no_service_takes_the_whole_env_file(service):
    assert "env_file" not in stack()["services"][service]


def test_the_worker_holds_no_flask_key():
    assert not {k for k in service_env("fingerprinter-worker") if k.endswith("_SECRET_KEY")}


def test_the_third_party_images_are_pinned_exactly():
    services = stack()["services"]
    assert services["egress"]["image"] == "ubuntu/squid:6.6-24.04_beta"
    assert services["edge"]["image"] == "nginx:1.27.3-alpine"


def test_the_dev_override_publishes_the_three_dependencies_on_loopback_only():
    dev = load(DEV_COMPOSE)
    assert set(dev["services"]) == {"redis", "fuseki", "plantuml"}
    for service in dev["services"].values():
        assert service["networks"] == ["dev"]
        assert all(p.startswith("127.0.0.1:") for p in service["ports"])
    assert not (dev["networks"]["dev"] or {}).get("internal")


def test_the_edge_listens_on_the_ui_and_api_ports_with_the_upload_limit():
    conf = NGINX_TEMPLATE.read_text()
    for variable in ("UI_PORT", "API_PORT"):
        assert f"listen ${{RDF_FINGERPRINTER_{variable}}};" in conf
    assert "client_max_body_size ${RDF_FINGERPRINTER_MAX_UPLOAD_MB}m;" in conf
    edge_env = service_env("edge")
    assert set(edge_env) == {
        "RDF_FINGERPRINTER_API_PORT",
        "RDF_FINGERPRINTER_UI_PORT",
        "RDF_FINGERPRINTER_MAX_UPLOAD_MB",
    }
