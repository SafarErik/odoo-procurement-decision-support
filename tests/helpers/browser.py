"""Browser-suite helpers shared by the e2e modules."""

from uuid import uuid4


def no_horizontal_scroll(page):
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")


def create_base_case(client):
    """One base case through the same API calls the Open RFQs page makes."""
    url = "/api/v2/procurement/planning-cases"
    preview = client.get(url + "/odoo-history/preview", params={"purchase_group_id": 501})
    assert preview.status_code == 200, preview.text
    payload = {"purchase_group_id": 501, "terms": preview.json()["terms"]}
    created = client.post(
        url + "/from-odoo-history", json=payload, headers={"Idempotency-Key": str(uuid4())}
    )
    assert created.status_code == 201, created.text
    return created.json()
