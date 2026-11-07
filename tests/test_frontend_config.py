"""Fast tests for the frontend-to-backend boundary: Reflex config and the API client layer."""

import asyncio
from uuid import uuid4

import httpx
import pytest

from frontend.api import cases, documents, http, library, odoo_history, suppliers
from frontend.i18n import tr
from frontend.rxconfig import config as reflex_config
from tests.helpers.planning_api import TOKEN

CASE = str(uuid4())


def test_reflex_runtime_does_not_conflict_with_fastapi() -> None:
    """Reflex uses a separate state-backend port and imports the flat app module."""

    assert reflex_config.backend_port == 8001
    assert reflex_config.module == "app"


def _parse(response):
    return response.json()["value"]


@pytest.mark.parametrize(
    "respond,expected",
    [
        (lambda r: httpx.Response(200, json={"value": 7}), (7, "")),
        (lambda r: httpx.Response(503), (None, "err_library")),
        (lambda r: httpx.Response(404), (None, "err_case_missing")),
        (lambda r: httpx.Response(200, json={"other": 1}), (None, "err_library_data")),
        (lambda r: httpx.Response(200, text="not json"), (None, "err_library_data")),
        (lambda r: (_ for _ in ()).throw(httpx.ConnectError("down")), (None, "err_library")),
    ],
)
def test_one_error_mapping_for_every_read(frontend_api, respond, expected):
    frontend_api(httpx.MockTransport(respond))
    value, error = asyncio.run(
        http.get_json(
            "http://api.test/x",
            _parse,
            lang="en",
            unavailable="err_library",
            invalid="err_library_data",
            statuses={404: "err_case_missing"},
        )
    )
    assert (value, error) == (expected[0], expected[1] and tr(expected[1], "en"))


@pytest.mark.parametrize("token", ["", "two words", "ékezet"])
def test_a_missing_or_unsafe_token_sends_nothing(frontend_api, token):
    frontend_api(httpx.MockTransport(lambda r: pytest.fail("No request without a token.")), token)
    assert asyncio.run(library.fetch_library({}, lang="en")) == (None, tr("err_token", "en"))
    _, error, uncertain = asyncio.run(cases.submit_planning_request("http://x", {}, CASE))
    assert error == tr("err_token", "en") and not uncertain


def test_requests_carry_the_bearer_token_and_the_documented_timeout(frontend_api):
    seen = []

    def respond(request):
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        seen.append((request.method, request.url.path, request.extensions["timeout"]["read"]))
        return httpx.Response(503)

    frontend_api(httpx.MockTransport(respond))

    async def every_call():
        await cases.fetch_planning_case(CASE)
        await library.fetch_library({})
        await library.fetch_scenarios(CASE, {})
        await suppliers.fetch_supplier_overview(CASE)
        await odoo_history.fetch_quotation_groups()
        await odoo_history.fetch_odoo_history(5)
        await documents.fetch_planning_pdf(CASE, "a" * 64)
        await cases.submit_planning_request(cases.scenarios_url(CASE), {}, CASE)

    asyncio.run(every_call())
    timeouts = {(method, path.rsplit("/", 1)[-1]): timeout for method, path, timeout in seen}
    assert len(timeouts) == len(seen) == 8
    # Stored reads use the short tier; live Odoo reads, PDF rendering and saves the long one.
    short = [CASE, "planning-cases", "scenarios", "suppliers"]
    assert {timeouts["GET", name] for name in short} == {http.TIMEOUT}
    long = [
        ("GET", "quotation-groups"),
        ("GET", "preview"),
        ("GET", "a" * 64),
        ("POST", "scenarios"),
    ]
    assert {timeouts[key] for key in long} == {http.LONG_TIMEOUT}


def test_noncanonical_identities_never_reach_a_url(frontend_api):
    frontend_api(httpx.MockTransport(lambda r: pytest.fail("Identity guard must stop this.")))
    for identity in ("../other", CASE.upper(), "{" + CASE + "}"):
        assert asyncio.run(library.fetch_scenarios(identity, {}))[0] is None
        assert asyncio.run(cases.fetch_planning_case(identity))[0] is None
