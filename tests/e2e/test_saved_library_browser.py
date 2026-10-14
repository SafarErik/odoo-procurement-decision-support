"""#32 real-stack discovery, bounded PostgreSQL workload and browser reopening."""

import hashlib
import json
import math
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, insert, text

from application.planning_library import library_query
from application.planning_serialization import snapshot_json
from persistence.planning_cases import library_statement
from persistence.schema import PlanningCaseRecord

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def post(stack, path, payload):
    response = stack.client.post(path, json=payload, headers={"Idempotency-Key": str(uuid4())})
    assert response.status_code == 201, response.text
    return response.json()


def replicate(case, case_id, saved, *, company=None, parent_id=None):
    snapshot = json.loads(json.dumps(case["snapshot"]))
    if company is not None:
        snapshot["facts"]["company_id"] = company
    encoded = snapshot_json(snapshot)
    return {
        "case_id": case_id,
        "parent_id": parent_id,
        "created_at": saved,
        "idempotency_key": str(uuid4()),
        "fingerprint": "0" * 64,
        "snapshot_version": snapshot["snapshot_version"],
        "snapshot_hash": hashlib.sha256(encoded.encode()).hexdigest(),
        "snapshot": snapshot,
    }


def test_find_expand_reopen_and_library_workload(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    company = stack.payload["company_id"]
    base = post(stack, BASE, stack.payload)
    child = post(
        stack,
        f"{BASE}/{base['case_id']}/scenarios",
        {
            "kind": "supplier_outage",
            "source": stack.payload["requirement_source"],
            "suppliers": [
                {"supplier_id": stack.payload["suppliers"][0]["supplier_id"], "available": False}
            ],
        },
    )
    approved = post(stack, BASE, stack.payload)
    no_award = post(stack, BASE, stack.payload)
    for case, outcome in ((approved, "approve"), (no_award, "no_award")):
        post(
            stack,
            f"{BASE}/{case['case_id']}/final-decision",
            {
                "snapshot_hash": case["snapshot_hash"],
                "outcome": outcome,
                "plan_index": 0 if outcome == "approve" else None,
                "actor_reference": "ux32-test",
                "rationale": "Controlled test",
                "demonstration_acknowledged": True,
            },
        )
    engine = create_engine(stack.env["DECISION_DATABASE_URL"])
    try:
        saved = datetime.now(UTC) - timedelta(days=1)
        rows = [
            replicate(base, str(uuid4()), saved - timedelta(seconds=i // 5)) for i in range(997)
        ]
        child_rows = [
            replicate(
                child, str(uuid4()), saved - timedelta(seconds=i // 5), parent_id=base["case_id"]
            )
            for i in range(59)
        ]
        other = replicate(base, str(uuid4()), datetime.now(UTC), company="other-company")
        with engine.begin() as connection:
            connection.execute(insert(PlanningCaseRecord), [*rows, *child_rows, other])
            connection.execute(text("ANALYZE planning_cases"))
        stack.stop(stack.api)
        stack.start_api(stored_only=True)
        assert not stack.env["ODOO_BASE_URL"] and not stack.env["T15_TRUSTED_MODEL_DIRECTORY"]
        params = {"workspace": "unclassified"}
        response = stack.client.get(BASE, params=params)
        if response.status_code != 200:
            from application.planning_library import list_planning_cases
            from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
            from persistence.postgres import create_session_factory

            _, factory = create_session_factory(stack.env["DECISION_DATABASE_URL"])
            list_planning_cases(
                SqlAlchemyPlanningUnitOfWork(factory), library_query(company, **params)
            )
        assert response.status_code == 200, response.text
        first = response.json()
        assert len(first["items"]) == 20 and first["next_cursor"]
        assert all(
            row["company_id"] == company
            and row["parent_id"] is None
            and row["workspace"] == "unclassified"
            for row in first["items"]
        )
        second = stack.client.get(BASE, params=params | {"cursor": first["next_cursor"]}).json()
        assert not {r["case_id"] for r in first["items"]} & {r["case_id"] for r in second["items"]}
        expected = sorted(
            [
                *rows,
                replicate(base, base["case_id"], datetime.fromisoformat(base["created_at"])),
                replicate(
                    approved, approved["case_id"], datetime.fromisoformat(approved["created_at"])
                ),
                replicate(
                    no_award, no_award["case_id"], datetime.fromisoformat(no_award["created_at"])
                ),
            ],
            key=lambda r: (r["created_at"], r["case_id"]),
            reverse=True,
        )
        assert [r["case_id"] for r in first["items"] + second["items"]] == [
            r["case_id"] for r in expected[:40]
        ]
        # New rows arrive on refresh; the existing continuation still starts below its boundary.
        with engine.begin() as connection:
            connection.execute(
                insert(PlanningCaseRecord), replicate(base, str(uuid4()), datetime.now(UTC))
            )
        assert (
            stack.client.get(BASE, params=params | {"cursor": first["next_cursor"]}).json()
            == second
        )
        for status, case in (("approved", approved), ("no_award", no_award)):
            data = stack.client.get(BASE, params=params | {"status": status}).json()
            assert [r["case_id"] for r in data["items"]] == [case["case_id"]]
        for query in (base["case_id"], " " + stack.payload["requirement"]["product_id"] + " "):
            assert stack.client.get(BASE, params=params | {"q": query}).json()["items"]
        for query in ("%", "_", "' OR 1=1 --"):
            assert not stack.client.get(BASE, params=params | {"q": query}).json()["items"]
        assert not stack.client.get(BASE).json()["items"]
        assert not stack.client.get(BASE, params={"workspace": "practice"}).json()["items"]
        for changes in (
            {"status": "approved"},
            {"q": "different"},
            {"workspace": "practice"},
            {"limit": "10"},
        ):
            assert (
                stack.client.get(
                    BASE, params=params | {"cursor": first["next_cursor"]} | changes
                ).status_code
                == 422
            )
        assert (
            stack.client.get(f"{BASE}/{child['case_id']}/scenarios", params=params).status_code
            == 422
        )
        assert (
            stack.client.get(f"{BASE}/{other['case_id']}/scenarios", params=params).status_code
            == 404
        )
        assert stack.client.get(BASE, params={"company_id": "other-company"}).status_code == 422
        assert stack.client.get(BASE, headers={"Authorization": "Bearer wrong"}).status_code == 401
        child_url = f"{BASE}/{base['case_id']}/scenarios"
        children = stack.client.get(child_url, params=params).json()
        assert len(children["items"]) == 20 and children["next_cursor"]
        assert all(
            r["parent_id"] == base["case_id"] and r["scenario_kind"] == "supplier_outage"
            for r in children["items"]
        )
        more = stack.client.get(
            child_url, params=params | {"cursor": children["next_cursor"]}
        ).json()
        assert len(more["items"]) == 20
        assert not {r["case_id"] for r in children["items"]} & {r["case_id"] for r in more["items"]}
        assert (
            stack.client.get(BASE, params=params | {"cursor": children["next_cursor"]}).status_code
            == 422
        )
        measurements = []
        stack.evidence["library_measurements"] = measurements
        for label, url, filters in (
            ("base-first", BASE, params),
            ("base-next", BASE, params | {"cursor": first["next_cursor"]}),
            ("base-product", BASE, params | {"q": stack.payload["requirement"]["product_id"]}),
            ("base-draft", BASE, params | {"status": "draft"}),
            ("children-first", child_url, params),
            ("children-next", child_url, params | {"cursor": children["next_cursor"]}),
        ):
            timings = []
            measurements.append({"query": label, "samples": timings})
            for index in range(32):
                start = time.perf_counter()
                response = stack.client.get(url, params=filters)
                elapsed = time.perf_counter() - start
                timings.append(
                    {"seconds": elapsed, "status": response.status_code, "warmup": index < 2}
                )
                assert response.status_code == 200 and len(response.json()["items"]) == 20
            p95 = sorted(t["seconds"] for t in timings[2:])[math.ceil(30 * 0.95) - 1]
            query = library_query(
                company, parent_id=base["case_id"] if "children" in label else None, **filters
            )
            sql = str(
                library_statement(query).compile(engine, compile_kwargs={"literal_binds": True})
            )
            with engine.connect() as connection:
                plan = list(
                    connection.execute(
                        text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql)
                    ).scalars()
                )
            measurements[-1].update(p95_seconds=p95, query_plan=plan)
        stack.evidence["library_measurements"] = measurements
        stack.evidence["library_fixture"] = (
            "1,000 company bases + 60 children, then one concurrent insertion; "
            "replicated valid saved snapshots, not new ML evidence"
        )
        (stack.root / "library-timings.json").write_text(
            json.dumps(measurements, indent=2), encoding="utf-8"
        )
        assert all(m["p95_seconds"] <= 1 for m in measurements)
        page.goto(stack.frontend_url + "/cases")
        expect(page.get_by_role("heading", name="Saved cases", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="No saved cases in this view")).to_be_visible()
        page.get_by_label("Workspace", exact=True).select_option("unclassified")
        page.get_by_label("Product or case ID", exact=True).fill(base["case_id"])
        page.get_by_role("button", name="Refresh", exact=True).click()
        expect(page.get_by_role("button", name="Open case", exact=True)).to_be_visible()
        page.get_by_role("button", name="Show scenarios", exact=True).click()
        expect(page.get_by_role("heading", name="Saved scenarios", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Open scenario", exact=True)).to_have_count(20)
        page.screenshot(path=str(stack.root / "library-desktop.png"), full_page=True)
        for width in (768, 390, 320):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            expect(page.get_by_role("button", name="Open case", exact=True)).to_be_visible()
            page.screenshot(path=str(stack.root / f"library-{width}.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 900})
        page.get_by_role("button", name="Open case", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
        assert "case_id=" + base["case_id"] in page.url
        page.reload()
        expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
        assert (
            stack.client.get(f"{BASE}/{base['case_id']}").json()["snapshot_hash"]
            == base["snapshot_hash"]
        )
        page.goto(stack.frontend_url + "/planning?case_id=invalid&view=plans")
        expect(page.get_by_role("alert")).to_be_visible()
        expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_have_count(0)
        page.goto(stack.frontend_url + "/cases")
        stack.stop(stack.api)
        page.get_by_role("button", name="Refresh", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Saved cases are unavailable")
        expect(page.get_by_role("heading", name="No saved cases in this view")).to_have_count(0)
        stack.start_api(stored_only=True)
        page.get_by_role("button", name="Refresh", exact=True).click()
        expect(page.get_by_role("button", name="Open case", exact=True)).to_be_visible()
        stack.evidence["checks"].append(
            "UX32 scoped filtered/keyset SQL + six measured queries; stored-only "
            "find/expand/keyboard-open/bookmark, 768/390/320 reflow and real outage/recovery"
        )
        # Corruption gate uses only the owned disposable database, after useful-flow checks.
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE planning_cases DISABLE TRIGGER planning_cases_immutable")
            )
            connection.execute(
                text("UPDATE planning_cases SET snapshot_hash=:hash WHERE case_id=:id"),
                {"hash": "f" * 64, "id": base["case_id"]},
            )
            connection.execute(
                text("ALTER TABLE planning_cases ENABLE TRIGGER planning_cases_immutable")
            )
        response = stack.client.get(BASE, params=params | {"q": base["case_id"]})
        assert (
            response.status_code == 503
            and response.json()["detail"]["code"] == "invalid_library_data"
        )
    finally:
        engine.dispose()
