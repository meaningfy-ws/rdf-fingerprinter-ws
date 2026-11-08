"""The shared layout and the copy: self-contained assets, one place for labels (design U-1, U-2)."""

import re
from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup

from fingerprinter.domain.model import JobState, ReportFormat
from fingerprinter.entrypoints.api import PROBLEM_STATUS
from fingerprinter.entrypoints.ui import labels
from fingerprinter.entrypoints.ui.api_model import ApiState
from tests.unit.ui.fake_api import make_app, record

UI = Path(__file__).parents[3] / "fingerprinter" / "entrypoints" / "ui"
OPENAPI = UI.parent / "api" / "openapi" / "fingerprinter.yml"
CSS = (UI / "static" / "app.css").read_text()
PAGES = ["/", "/jobs/new?from=endpoint", "/jobs/new?from=file"]


@pytest.fixture
def client(api):
    return make_app(api).test_client()


def soup(response) -> BeautifulSoup:
    return BeautifulSoup(response.data, "html.parser")


# --- self-contained pages -----------------------------------------------------------------------


@pytest.mark.parametrize("path", PAGES)
def test_every_page_references_only_same_origin_scripts_styles_and_fonts(client, path):
    page = soup(client.get(path))

    references = [tag["src"] for tag in page.find_all(src=True)]
    references += [tag["href"] for tag in page.find_all("link", href=True)]

    assert any(reference.endswith("app.css") for reference in references)
    assert any(reference.endswith("htmx.min.js") for reference in references)
    for reference in references:
        assert reference.startswith("/") and not reference.startswith("//"), reference
        assert client.get(reference).status_code == 200, reference
    assert "@import" not in "".join(style.get_text() for style in page.find_all("style"))


def test_the_stylesheet_loads_nothing_from_elsewhere():
    assert not re.search(r"@import|@font-face|url\(\s*['\"]?(https?:)?//", CSS)


@pytest.mark.parametrize("path", PAGES)
def test_the_old_toolkits_are_gone(client, path):
    html = client.get(path).get_data(as_text=True).lower()

    for gone in ("materialize", "jquery", "googleapis", "material-icons", "main.css"):
        assert gone not in html
    assert not (UI / "static" / "main.css").exists()


def test_htmx_is_vendored_at_its_pinned_version_with_its_licence():
    assert 'version:"2.0.4"' in (UI / "static" / "vendor" / "htmx.min.js").read_text()
    assert "Zero-Clause BSD" in (UI / "static" / "vendor" / "htmx.LICENSE").read_text()


# --- the base layout ----------------------------------------------------------------------------


@pytest.mark.parametrize("path", PAGES)
def test_every_page_has_the_header_a_live_region_and_one_main(client, path):
    page = soup(client.get(path))

    header = page.find("header")
    assert header.find("svg") is not None  # the mark
    links = {a.get_text(strip=True): a["href"] for a in header.find_all("a")}
    assert links["Jobs"] == "/"
    assert "New job" in links
    announce = page.find(id="announce")
    assert announce["aria-live"] == "polite"
    assert len(page.find_all("main")) == 1
    assert page.html["lang"] == "en"


def test_a_flashed_message_is_shown_in_the_flash_area(client):
    with client.session_transaction() as session:
        session["_flashes"] = [("error", "Boom."), ("success", "Job started.")]

    page = soup(client.get("/"))

    flashes = page.find(id="flashes").find_all(class_="flash")
    assert [(f.get_text(strip=True), "flash-error" in f["class"]) for f in flashes] == [
        ("Boom.", True),
        ("Job started.", False),
    ]


def test_the_icons_are_inline_decorative_svg_macros():
    macros = (UI / "templates" / "icons.html").read_text()

    for name in ("logo", "plus", "download", "more", "upload"):
        assert f"macro {name}(" in macros
    assert "aria-hidden" in macros


# --- the stylesheet -----------------------------------------------------------------------------


def _tokens(block: str) -> dict[str, str]:
    return dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})", block))


LIGHT, _, DARK = CSS.partition("@media (prefers-color-scheme: dark)")


def _luminance(colour: str) -> float:
    channels = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_the_dark_theme_follows_the_system_setting_and_redefines_the_tokens():
    assert _tokens(DARK)["--ground"] == "#0F1115"
    assert _tokens(LIGHT)["--ground"] == "#F6F7F9"
    assert set(_tokens(LIGHT)) <= set(_tokens(DARK)) | {"--accent", "--accent-ink", "--danger"}


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=["light", "dark"])
def test_each_badge_pair_has_a_contrast_of_at_least_4_5(theme):
    tokens = _tokens(LIGHT) | _tokens(theme)
    badge_classes = {entry.badge_class for entry in labels.STATES.values()}

    assert len(badge_classes) >= 5
    for badge_class in badge_classes:
        name = badge_class.removeprefix("badge-")
        assert _contrast(tokens[f"--{name}-bg"], tokens[f"--{name}-fg"]) >= 4.5, name


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=["light", "dark"])
def test_text_and_links_read_on_the_ground_and_the_surface(theme):
    tokens = _tokens(LIGHT) | _tokens(theme)

    for text in ("--text", "--muted", "--link"):
        for ground in ("--ground", "--surface"):
            assert _contrast(tokens[text], tokens[ground]) >= 4.5, (text, ground)
    assert _contrast(tokens["--accent-ink"], tokens["--accent"]) >= 4.5
    assert _contrast(tokens["--accent-ink"], tokens["--danger"]) >= 4.5


def test_controls_have_focus_rings_and_44_pixel_targets():
    assert ":focus-visible" in CSS
    assert re.search(r"--target\s*:\s*44px", CSS)
    assert "min-height: var(--target)" in CSS


# --- labels (U-2) -------------------------------------------------------------------------------


def test_labels_name_every_job_state():
    assert set(labels.STATES) == {state.value for state in JobState}
    assert {key: entry.label for key, entry in labels.STATES.items()} == {
        "queued": "Queued",
        "running": "Running…",
        "completed": "Done",
        "completed_with_failures": "Done with warnings",
        "failed": "Failed",
        "cancelled": "Cancelled",
    }


def test_the_ui_states_are_the_states_of_the_openapi_contract():
    enum = yaml.safe_load(OPENAPI.read_text())["components"]["schemas"]["JobState"]["enum"]
    stopped = next(f.states for f in labels.FILTERS if f.id == "stopped")

    assert {state.value for state in ApiState} == set(enum)
    assert set(labels.STATES) == set(ApiState)
    assert (labels.ACTIVE_STATES | labels.OUTPUT_STATES | stopped) == set(ApiState)


def test_there_is_a_sentence_for_each_problem_the_api_sends_and_for_no_other():
    assert set(labels.PROBLEMS) == {problem.__name__ for problem in PROBLEM_STATUS}


def test_labels_name_every_format_in_display_order():
    assert [f.id for f in labels.FORMATS] == [
        "html", "json", "shacl", "puml", "svg", "pattern", "shex", "pitfalls", "zip",
    ]  # fmt: skip
    assert {report_format.value for report_format in ReportFormat} <= {f.id for f in labels.FORMATS}
    assert [f.name for f in labels.FORMATS] == [
        "Report", "Profile (JSON)", "SHACL shapes", "Class diagram (PlantUML)",
        "Class diagram (SVG)", "Pattern schema", "ShEx schema", "Pitfalls (TSV)",
        "Download all (.zip)",
    ]  # fmt: skip
    assert all(f.description for f in labels.FORMATS if f.id != "zip")


@pytest.mark.parametrize(
    ("state", "kwargs", "note"),
    [
        ("queued", {}, "Waiting for a worker"),
        ("running", {}, "Fingerprinting"),
        ("completed", {"took": "2.4 s"}, "Took 2.4 s"),
        ("completed", {}, ""),
        ("completed_with_failures", {"failures": 3}, "3 parts could not be produced"),
        ("completed_with_failures", {"failures": 1}, "1 part could not be produced"),
        ("failed", {"reason": "endpoint unreachable: http://x"}, "endpoint unreachable"),
        ("failed", {"reason": "Bad things. More detail"}, "Bad things"),
        ("failed", {"reason": "no separator"}, "no separator"),
        ("failed", {"reason": None}, ""),
        ("cancelled", {}, "Cancelled"),
    ],
)
def test_the_note_under_a_badge(state, kwargs, note):
    assert labels.state_note(state, **kwargs) == note


def test_a_long_failure_reason_is_cut_to_80_characters_with_an_ellipsis():
    note = labels.state_note("failed", reason="x" * 200)

    assert len(note) == 80
    assert note.endswith("…")
    assert labels.state_note("failed", reason="y" * 80) == "y" * 80


@pytest.mark.parametrize(
    ("endpoint", "graphs", "line"),
    [
        (True, 0, "SPARQL endpoint · all graphs"),
        (True, 1, "SPARQL endpoint · 1 named graph"),
        (True, 3, "SPARQL endpoint · 3 named graphs"),
        (False, 0, "RDF file"),
    ],
)
def test_the_kind_line_under_a_source(endpoint, graphs, line):
    assert labels.source_kind(endpoint=endpoint, graphs=graphs) == line


def test_the_flash_messages_of_the_actions():
    assert (labels.JOB_STARTED, labels.REPORT_DELETED, labels.JOB_CANCELLED) == (
        "Job started.",
        "Report deleted.",
        "Job cancelled.",
    )


@pytest.mark.parametrize(
    ("problem", "limit", "sentence"),
    [
        ({"type": "urn:fingerprinter:InvalidSource"},
         None, "Enter an http or https SPARQL endpoint URL, without a user name or password."),
        ({"type": "urn:fingerprinter:UploadTooLarge"},
         512, "The file is too large (limit 512 MB)."),
        ({"type": "urn:fingerprinter:UnsupportedFileType", "accepted": ["rdf", "ttl"]},
         None, "This file type is not supported. Accepted: rdf, ttl."),
        ({"type": "urn:fingerprinter:QueueUnavailable"},
         None, "The job queue is unavailable. Try again later."),
        ({"type": "urn:fingerprinter:JobNotFound"}, None, "No such job or report."),
        ({"type": "urn:fingerprinter:FormatNotAvailable"}, None, "No such job or report."),
        ({"type": "urn:fingerprinter:JobNotCancellable"},
         None, "This job has already finished."),
        ({"type": "urn:fingerprinter:JobIsActive"},
         None, "Cancel the job before deleting it."),
        ({"type": "urn:other:Teapot", "detail": "I am a teapot."}, None, "I am a teapot."),
        (None, None, "Something went wrong on the server. Try again."),
        ({"type": "about:blank"}, None, "Something went wrong on the server. Try again."),
    ],
)  # fmt: skip
def test_one_sentence_per_problem_type(problem, limit, sentence):
    assert labels.problem_sentence(problem, upload_limit_mb=limit) == sentence


def test_the_unreachable_service_sentences():
    assert labels.UNREACHABLE == "The service is not reachable. Try again in a moment."
    assert labels.UPDATES_PAUSED == "Status updates paused: the service is not reachable."


# --- framing, cookies, expired forms (stage-1 review S1-2) ---------------------------------------


@pytest.mark.parametrize("path", [*PAGES, "/jobs/nope/delete", "/static/app.css"])
def test_every_response_refuses_to_be_framed_by_another_site(client, path):
    headers = client.get(path).headers

    assert headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in headers["Content-Security-Policy"]


def test_the_session_cookie_is_same_site_lax_and_secure_only_when_asked(api):
    plain = make_app(api)
    secure = make_app(api, secure_cookies=True)

    assert plain.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert plain.config["SESSION_COOKIE_SECURE"] is False
    assert secure.config["SESSION_COOKIE_SECURE"] is True
    assert secure.config["SESSION_COOKIE_HTTPONLY"] is True


EXPIRED = "This form expired. Please try again."


def expired_client(api):
    app = make_app(api, csrf=True)
    app.config["WTF_CSRF_TIME_LIMIT"] = -1  # every token is already too old
    return app.test_client()


def test_an_expired_endpoint_form_is_shown_again_with_what_was_typed(api):
    client = expired_client(api)
    token = soup(client.get("/jobs/new")).find("input", attrs={"name": "csrf_token"})["value"]

    response = client.post(
        "/jobs/endpoint",
        data={"csrf_token": token, "sparql_endpoint_url": "http://e/sparql", "graphs": "g1"},
    )

    page = soup(response)
    assert response.status_code == 400
    assert page.find(class_="flash-error").get_text(strip=True) == EXPIRED
    assert page.find("input", id="sparql_endpoint_url")["value"] == "http://e/sparql"
    assert page.find("input", attrs={"name": "csrf_token"})["value"]
    assert api.calls == []


def test_an_expired_file_form_is_shown_again(api):
    client = expired_client(api)

    response = client.post("/jobs/file", data={}, content_type="multipart/form-data")

    page = soup(response)
    assert response.status_code == 400
    assert page.find(class_="flash-error").get_text(strip=True) == EXPIRED
    assert page.find("input", type="file") is not None


@pytest.mark.parametrize(("action", "title"), [("delete", "Delete this report?"),
                                               ("cancel", "Cancel this job?")])  # fmt: skip
def test_an_expired_confirmation_is_shown_again(api, action, title):
    api.jobs = [record("j1", "running" if action == "cancel" else "completed")]
    client = expired_client(api)

    response = client.post(f"/jobs/j1/{action}")

    page = soup(response)
    assert response.status_code == 400
    assert page.find(class_="flash-error").get_text(strip=True) == EXPIRED
    assert page.find(attrs={"role": "alertdialog"}).find("h1").text == title
    assert not [call for call in api.calls if call[0] in ("delete_job", "cancel_job")]


def test_an_expired_post_to_a_route_without_a_form_says_the_form_expired(api):
    app = make_app(api, csrf=True)
    app.add_url_rule("/probe", "probe", lambda: "never", methods=["POST"])

    response = app.test_client().post("/probe")

    assert response.status_code == 400
    assert EXPIRED in soup(response).find("main").text
