"""Functional coverage of report-service routers."""

import httpx
from conftest import assert_ok

SERVICE = "report"


def test_report_listing(api: httpx.Client, auth_headers: dict) -> None:
    """The report listing answers with an envelope, not a 500.

    Guards the regression where ReportService could not be resolved from the
    DI container because its repositories captured a session in __init__.
    """
    body = assert_ok(api.get("/reports/", headers=auth_headers)).json()
    assert "reports" in body and "total" in body, body


def test_report_listing_pagination(api: httpx.Client, auth_headers: dict) -> None:
    """Offset and limit are accepted by the listing endpoint."""
    body = assert_ok(
        api.get("/reports/", params={"offset": 0, "limit": 5}, headers=auth_headers)
    ).json()
    assert len(body["reports"]) <= 5


def test_unknown_report_is_404(api: httpx.Client, auth_headers: dict) -> None:
    """A well-formed but unknown report id is a 404."""
    missing = "00000000-0000-0000-0000-0000000000ff"
    assert api.get(f"/reports/{missing}", headers=auth_headers).status_code == 404


def test_malformed_report_id_is_rejected(api: httpx.Client, auth_headers: dict) -> None:
    """A non-UUID path segment is a validation error, not a crash."""
    assert api.get("/reports/not-a-uuid", headers=auth_headers).status_code == 422
