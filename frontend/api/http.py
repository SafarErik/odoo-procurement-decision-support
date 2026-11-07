"""The one way the frontend reaches the backend API: URL, Bearer token, timeout, errors.

The service token is read here only and never reaches the browser. Nothing retries
automatically, redirects are not followed and proxy variables are ignored.
"""

import httpx

from frontend.config import settings
from frontend.i18n import tr

# Timeout policy (seconds). Stored reads answer from PostgreSQL. The long tier is for calls
# where the backend works per request: solving and saving a case or decision, reading Odoo
# live (quotation groups, history preview) and rendering a PDF.
TIMEOUT = 15
LONG_TIMEOUT = 45

# Raised while parsing a response body: the data is invalid, a retry would not help.
DATA_ERRORS = (ValueError, TypeError, KeyError, AttributeError, ArithmeticError)

transport: httpx.AsyncBaseTransport | None = None  # tests swap in an ASGI or mock transport


class TokenMissing(Exception):
    """The service token is empty or not one ASCII word; no request was sent."""


class Unreachable(Exception):
    """No usable HTTP answer: connection, timeout or protocol failure."""


def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    token = settings.api_service_token.get_secret_value()
    if not token or not token.isascii() or any(c.isspace() for c in token):
        raise TokenMissing
    return {"Authorization": "Bearer " + token, **(extra or {})}


def _client(timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout, transport=transport, trust_env=False, follow_redirects=False
    )


async def send(method: str, url: str, *, timeout: float = TIMEOUT, headers=None, **kwargs):
    """One authenticated request; raises ``TokenMissing`` or ``Unreachable``."""
    request_headers = _headers(headers)
    try:
        async with _client(timeout) as client:
            return await client.request(method, url, headers=request_headers, **kwargs)
    except httpx.HTTPError as error:
        raise Unreachable from error


async def get_bytes(url: str, *, params: dict, limit: int, timeout: float = LONG_TIMEOUT):
    """Stream a 200 body of at most ``limit`` bytes; returns ``(headers, data)``.

    Raises ``TokenMissing``, ``Unreachable`` or ``ValueError`` (other status, too large).
    """
    request_headers = _headers()
    try:
        async with _client(timeout) as client:
            async with client.stream("GET", url, params=params, headers=request_headers) as reply:
                if reply.status_code != 200:
                    raise ValueError(f"Unexpected status {reply.status_code}")
                data = bytearray()
                async for chunk in reply.aiter_bytes():
                    if len(data) + len(chunk) > limit:
                        raise ValueError("Response exceeds limit")
                    data.extend(chunk)
                return reply.headers, bytes(data)
    except httpx.HTTPError as error:
        raise Unreachable from error


async def get_json(
    url, parse, *, lang, unavailable, invalid, statuses=None, params=None, timeout=TIMEOUT
):
    """GET ``url`` and ``parse`` the response; returns ``(value, "")`` or ``(None, text)``.

    Unreachable or non-200 → ``unavailable`` (or ``statuses[code]``); unparsable → ``invalid``.
    """
    try:
        response = await send("GET", url, params=params, timeout=timeout)
    except TokenMissing:
        return None, tr("err_token", lang)
    except Unreachable:
        return None, tr(unavailable, lang)
    if response.status_code != 200:
        return None, tr((statuses or {}).get(response.status_code, unavailable), lang)
    try:
        return parse(response), ""
    except DATA_ERRORS:
        return None, tr(invalid, lang)
