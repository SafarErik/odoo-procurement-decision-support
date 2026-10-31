"""Write generated purchase history into the dedicated Odoo test database only.

    python -m tools.seed_odoo_history plan    print the generated plan, write nothing
    python -m tools.seed_odoo_history apply   write it into ODOO_SEED_DATABASE
    python -m tools.seed_odoo_history apply N write only the first N orders (smoke run)
    python -m tools.seed_odoo_history groups  add the P4 evaluation quotation groups
                                              (5 and 10 suppliers of the RFQ product)

Owner-approved (2026-10-17) scripted administrator writes for P1. The tool refuses
to write unless the target is exactly ``pdss_history_gen``, ``ODOO_SEED_DATABASE``
names it, and that database carries the system parameter
``pdss.seed_target = pdss_history_gen`` set by the owner. It never runs from the
backend. Everything it creates is tagged ``PDSS-GEN-P1`` and ``[GEN]``.

History timestamps (order, confirmation, receipt) are deliberately back-dated on
these generated records: they follow a simulated clock and are not observations.
"""

import math
import random
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

ALLOWED_DATABASE = "pdss_history_gen"
SEED_PARAMETER = "pdss.seed_target"
TAG = "PDSS-GEN-P1"
SEED = 20261017
MONTHS = 18
# Fixed simulated clock: the plan is reproducible and every receipt lies in the past.
CLOCK = datetime(2026, 10, 17, tzinfo=UTC)
# The feature window reads expected arrivals in [cutoff - 134 d, cutoff - 14 d) (settlement 14 d,
# lookback 120 d). The last seeded arrival is about CLOCK, so later live cutoffs find no lines.
# This is an upper bound: a supplier needs three lines in the window and can run out earlier
# (the four-supplier demo group about 2027-01-10; tools.demo checks the preview for that).
REPRODUCTION_LAST_CUTOFF = CLOCK + timedelta(days=134)
ROOT = Path(__file__).resolve().parents[1]
ODOO_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class Product:
    code: str
    name: str
    base_price: float


@dataclass(frozen=True)
class Supplier:
    code: str
    name: str
    behaviour: str
    lead_days: int
    price_factor: float
    products: tuple[str, ...]


@dataclass(frozen=True)
class Receipt:
    at: datetime
    quantity: int


@dataclass
class Order:
    code: str
    supplier: str
    product: str
    ordered_at: datetime
    expected_at: datetime
    quantity: int
    unit_price: float
    receipts: list[Receipt] = field(default_factory=list)
    short_closed: bool = False


@dataclass(frozen=True)
class Plan:
    seed: int
    start: datetime
    now: datetime
    products: tuple[Product, ...]
    suppliers: tuple[Supplier, ...]
    orders: tuple[Order, ...]
    rfq_product: str
    rfq_suppliers: tuple[str, ...]


PRODUCTS = (
    Product("PRD-01", "[GEN] Steel bracket M8", 1450.0),
    Product("PRD-02", "[GEN] Aluminium profile 40x40", 3900.0),
    Product("PRD-03", "[GEN] Hydraulic hose 1/2in", 2650.0),
)
# (behaviour, count): latent reliability shapes; see behaviour_at().
BEHAVIOURS = (
    ("reliable", 3),
    ("steady_late", 2),
    ("deteriorating", 3),
    ("improving", 2),
    ("partial_shipper", 2),
    ("volatile", 2),
    ("temporary_shock", 2),
)
NAMES = (
    "Alpha Metals", "Bravo Components", "Carpathia Supply", "Danube Parts",
    "Eger Industrial", "Fenyves Trade", "Gyor Fasteners", "Hegyalja Tools",
    "Iron Valley", "Jasz Hydraulics", "Kalocsa Profiles", "Lakeside Steel",
    "Mecsek Engineering", "Nyirseg Logistics", "Orseg Machining", "Pannon Industrial",
    "Rába Components", "Sopron Metalworks", "Tisza Supply", "Ujpest Hydraulics",
    "Vac Fasteners", "Zala Profiles", "Balaton Parts", "Bükk Tools",
    "Csepel Steel", "Dunakeszi Trade", "Esztergom Industrial", "Fót Machining",
    "Gödöllő Components", "Hatvan Logistics", "Isaszeg Metals", "Kecskemét Supply",
    "Lenti Hydraulics", "Miskolc Engineering", "Nagykanizsa Parts", "Pápa Industrial",
    "Siófok Trade", "Szeged Metals", "Tata Components", "Veszprém Supply",
)  # fmt: skip
EXTRA_BEHAVIOURS = (
    ("reliable", 5),
    ("steady_late", 3),
    ("deteriorating", 4),
    ("improving", 3),
    ("partial_shipper", 3),
    ("volatile", 3),
    ("temporary_shock", 3),
)


def behaviour_at(kind: str, month: float, phase: float) -> tuple[float, float, float]:
    """Latent (on-time probability, partial-shipment probability, mean lateness days)."""
    if kind == "reliable":
        on_time, partial, late = 0.93, 0.05, 2.0
    elif kind == "steady_late":
        on_time, partial, late = 0.55, 0.15, 6.0
    elif kind == "deteriorating":
        start = 6 + 4 * phase
        on_time = 0.92 - 0.47 * min(1.0, max(0.0, (month - start) / 4))
        partial, late = 0.08 + 0.2 * (0.92 - on_time), 3.0 + 6 * (0.92 - on_time)
    elif kind == "improving":
        start = 5 + 3 * phase
        on_time = 0.5 + 0.4 * min(1.0, max(0.0, (month - start) / 5))
        partial, late = 0.25 - 0.2 * (on_time - 0.5), 7.0 - 8 * (on_time - 0.5)
    elif kind == "partial_shipper":
        on_time, partial, late = 0.85, 0.45, 3.0
    elif kind == "volatile":
        on_time = 0.74 + 0.18 * math.sin(2 * math.pi * (month / 6 + phase))
        partial, late = 0.12, 4.0
    elif kind == "temporary_shock":
        shock = 9 + 4 * phase
        on_time = 0.3 if shock <= month < shock + 3 else 0.9
        partial, late = (0.4, 10.0) if shock <= month < shock + 3 else (0.06, 2.0)
    else:
        raise ValueError(f"Unknown behaviour {kind}")
    return on_time, partial, late


def _suppliers(rng: random.Random, behaviours, *, first_index: int) -> list[Supplier]:
    kinds = [kind for kind, count in behaviours for _ in range(count)]
    out = []
    for offset, kind in enumerate(kinds):
        index = first_index + offset
        count = rng.choice((1, 2, 2, 2, 3))
        products = tuple(sorted(rng.sample([p.code for p in PRODUCTS], count)))
        out.append(
            Supplier(
                f"SUP-{index + 1:02}",
                f"[GEN] {NAMES[index]}",
                kind,
                rng.randint(7, 21),
                round(rng.uniform(0.9, 1.15), 3),
                products,
            )
        )
    return out


def _at_working_hour(rng: random.Random, day: datetime) -> datetime:
    return day.replace(
        hour=rng.randint(6, 15), minute=rng.choice((0, 15, 30, 45)), second=0, microsecond=0
    )


def _orders(suppliers, rng: random.Random, start: datetime, now: datetime) -> list[Order]:
    price = {p.code: p.base_price for p in PRODUCTS}
    orders: list[Order] = []
    for s in suppliers:
        phase = rng.random()
        drift = 0.0
        for product in s.products:
            day = start + timedelta(days=rng.randint(0, 14))
            number = 0
            while day < now - timedelta(days=s.lead_days):
                number += 1
                ordered = _at_working_hour(rng, day)
                expected = (ordered + timedelta(days=s.lead_days)).replace(
                    hour=12, minute=0, second=0
                )
                month = (expected - start).days / 30.44
                drift = max(-0.12, min(0.12, drift + rng.gauss(0, 0.02)))
                p_on, p_partial, late_mean = behaviour_at(s.behaviour, month, phase)
                p_on = min(0.98, max(0.05, p_on + drift))
                order = Order(
                    f"{TAG}:{s.code}:{product}:{number:03}",
                    s.code,
                    product,
                    ordered,
                    expected,
                    rng.randrange(50, 410, 10),
                    round(price[product] * s.price_factor * rng.uniform(0.97, 1.03), 2),
                )
                if rng.random() < p_on:
                    delay = timedelta(hours=rng.uniform(-48, 20))
                else:
                    days = 1 + min(29.0, rng.expovariate(1 / max(1.0, late_mean)))
                    delay = timedelta(days=days)
                first = _at_working_hour(rng, expected + delay)
                if first <= ordered:
                    first = ordered + timedelta(hours=4)
                if rng.random() < p_partial:
                    part = int(order.quantity * rng.uniform(0.4, 0.8))
                    if first < now:
                        order.receipts.append(Receipt(first, part))
                    short_close = 0.4 if s.behaviour == "partial_shipper" else 0.25
                    if rng.random() < short_close:
                        order.short_closed = first < now
                    else:
                        rest = _at_working_hour(rng, first + timedelta(days=rng.uniform(3, 15)))
                        if rest < now:
                            order.receipts.append(Receipt(rest, order.quantity - part))
                elif first < now:
                    order.receipts.append(Receipt(first, order.quantity))
                orders.append(order)
                day += timedelta(days=rng.randint(10, 24))
    return orders


def build_plan(now: datetime, seed: int = SEED) -> Plan:
    """Deterministic generated history ending at ``now``; no Odoo access."""
    if now.utcoffset() != timedelta(0):
        raise ValueError("Use an explicit UTC clock.")
    rng = random.Random(seed)
    now = now.replace(microsecond=0)
    start = (now - timedelta(days=round(MONTHS * 30.44))).replace(hour=0, minute=0, second=0)
    kinds = [kind for kind, count in BEHAVIOURS for _ in range(count)]
    suppliers = []
    for index, kind in enumerate(kinds):
        count = rng.choice((1, 2, 2, 2, 3))
        products = tuple(sorted(rng.sample([p.code for p in PRODUCTS], count)))
        suppliers.append(
            Supplier(
                f"SUP-{index + 1:02}",
                f"[GEN] {NAMES[index]}",
                kind,
                rng.randint(7, 21),
                round(rng.uniform(0.9, 1.15), 3),
                products,
            )
        )
    # The open RFQ compares four suppliers of PRD-01 with different behaviours.
    rfq_kinds = ("reliable", "deteriorating", "partial_shipper", "steady_late")
    rfq_suppliers = []
    for kind in rfq_kinds:
        index = next(i for i, s in enumerate(suppliers) if s.behaviour == kind)
        s = suppliers[index]
        if "PRD-01" not in s.products:
            suppliers[index] = Supplier(
                s.code, s.name, s.behaviour, s.lead_days, s.price_factor,
                tuple(sorted({*s.products, "PRD-01"})),
            )  # fmt: skip
        rfq_suppliers.append(s.code)

    orders = _orders(suppliers, rng, start, now)
    # Second batch (added after the first training run proved 16 suppliers too few for a
    # supplier-grouped temporal split): its own random stream keeps batch one unchanged.
    extra_rng = random.Random(seed + 1)
    extra = _suppliers(extra_rng, EXTRA_BEHAVIOURS, first_index=len(suppliers))
    orders += _orders(extra, extra_rng, start, now)
    suppliers += extra
    return Plan(
        seed, start, now, PRODUCTS, tuple(suppliers), tuple(orders), "PRD-01", tuple(rfq_suppliers)
    )


def plan_summary(plan: Plan) -> dict:
    receipts = sum(len(o.receipts) for o in plan.orders)
    return {
        "seed": plan.seed,
        "start": plan.start.isoformat(),
        "now": plan.now.isoformat(),
        "products": len(plan.products),
        "suppliers": {s.code: [s.behaviour, list(s.products)] for s in plan.suppliers},
        "orders": len(plan.orders),
        "receipts": receipts,
        "partial_orders": sum(len(o.receipts) > 1 or o.short_closed for o in plan.orders),
        "open_orders": sum(not o.receipts and not o.short_closed for o in plan.orders),
        "rfq": {"product": plan.rfq_product, "suppliers": list(plan.rfq_suppliers)},
    }


def _odoo(value: datetime) -> str:
    return value.astimezone(UTC).strftime(ODOO_FORMAT)


class SeedRefused(RuntimeError):
    pass


class OdooWriter:
    """Minimal JSON-2 client bound to the one allowed database."""

    def __init__(self, base_url: str, database: str, api_key: str, transport=None):
        if database != ALLOWED_DATABASE:
            raise SeedRefused(f"Refusing database {database!r}; only {ALLOWED_DATABASE!r}.")
        if not api_key:
            raise SeedRefused("ODOO_SEED_ADMIN_API_KEY is not set.")
        self.database = database
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=60,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}", "X-Odoo-Database": database},
        )

    def call(self, model: str, method: str, body: dict | None = None):
        response = self.client.post(f"/json/2/{model}/{method}", json=body or {})
        if response.status_code != 200:
            raise RuntimeError(
                f"{model}.{method} HTTP {response.status_code}: {response.text[:300]}"
            )
        return response.json()

    def verify_target(self) -> None:
        if self.call("ir.config_parameter", "get_param", {"key": SEED_PARAMETER}) != self.database:
            raise SeedRefused(f"{SEED_PARAMETER} is not set to {self.database} in this database.")
        uid = self.call("res.users", "context_get")["uid"]
        if (
            self.call("res.users", "has_group", {"ids": [uid], "group_ext_id": "base.group_system"})
            is not True
        ):
            raise SeedRefused("The seeding key does not belong to an administrator.")


def _get_or_create(writer, model, key, rows):
    """Reuse generated records by their tag key so an interrupted run can resume."""
    found = writer.call(
        model, "search_read",
        {"domain": [[key, "in", [r[key] for r in rows]]], "fields": ["id", key]},
    )  # fmt: skip
    ids = {r[key]: r["id"] for r in found}
    missing = [r for r in rows if r[key] not in ids]
    if missing:
        created = writer.call(model, "create", {"vals_list": missing})
        ids |= {r[key]: i for r, i in zip(missing, created, strict=True)}
    return [ids[r[key]] for r in rows]


def apply_plan(plan: Plan, writer: OdooWriter, *, limit: int | None = None, log=print) -> dict:
    """Write the plan; orders whose tagged origin already exists are skipped."""
    writer.verify_target()
    uom = writer.call(
        "uom.uom", "search_read", {"domain": [["name", "=", "Units"]], "fields": ["id"]}
    )[0]["id"]
    company = writer.call(
        "res.company", "search_read", {"domain": [], "fields": ["id"], "limit": 1}
    )[0]["id"]
    note = "Generated by tools/seed_odoo_history.py (PDSS P1); not observed business data."
    product_ids = dict(zip(
        [p.code for p in plan.products],
        _get_or_create(writer, "product.product", "default_code", [
            {"name": p.name, "default_code": f"{TAG}-{p.code}", "type": "consu",
             "is_storable": True, "purchase_ok": True, "uom_id": uom,
             "description_purchase": note}
            for p in plan.products
        ]),
        strict=True,
    ))  # fmt: skip
    supplier_ids = dict(zip(
        [s.code for s in plan.suppliers],
        _get_or_create(writer, "res.partner", "ref", [
            {"name": s.name, "is_company": True, "supplier_rank": 1,
             "ref": f"{TAG}-{s.code}", "comment": note}
            for s in plan.suppliers
        ]),
        strict=True,
    ))  # fmt: skip
    existing = {
        r["origin"]
        for r in writer.call(
            "purchase.order", "search_read",
            {"domain": [["origin", "=like", f"{TAG}%"]], "fields": ["origin"]},
        )
    }  # fmt: skip
    ordered = sorted(plan.orders, key=lambda o: o.ordered_at)[:limit]
    todo = [o for o in ordered if o.code not in existing]
    log(f"{len(ordered) - len(todo)} orders already present, writing {len(todo)}")
    for number, order in enumerate(todo, 1):
        _write_order(writer, order, product_ids, supplier_ids, uom, company)
        if number % 50 == 0:
            log(f"  {number}/{len(todo)} orders written")
    rfq_ids, group = [], None
    if any(o.startswith(f"{TAG}:RFQ:") for o in existing):
        rfqs = writer.call(
            "purchase.order",
            "search_read",
            {
                "domain": [["origin", "=like", f"{TAG}:RFQ:%"]],
                "fields": ["purchase_group_id", "order_line"],
            },
        )
        rfq_ids = [r["id"] for r in rfqs]
        # Quotations are compared net of tax; Odoo adds the default purchase tax on create.
        writer.call(
            "purchase.order.line",
            "write",
            {"ids": [i for r in rfqs for i in r["order_line"]], "vals": {"tax_ids": [[6, 0, []]]}},
        )
        group = rfqs[0]["purchase_group_id"][0] if rfqs[0]["purchase_group_id"] else None
    elif limit is None:
        for code in plan.rfq_suppliers:
            supplier = next(s for s in plan.suppliers if s.code == code)
            base = next(p for p in plan.products if p.code == plan.rfq_product).base_price
            rfq_ids += writer.call(
                "purchase.order",
                "create",
                {"vals_list": [{
                    "partner_id": supplier_ids[code], "company_id": company,
                    "origin": f"{TAG}:RFQ:{code}", "partner_ref": TAG,
                    "order_line": [[0, 0, {
                        "product_id": product_ids[plan.rfq_product], "product_qty": 200,
                        "product_uom_id": uom, "price_unit": round(base * supplier.price_factor, 2),
                        "date_planned": _odoo(plan.now + timedelta(days=supplier.lead_days)),
                        "tax_ids": [[6, 0, []]],
                    }]],
                }]},
            )  # fmt: skip
        group = writer.call(
            "purchase.order.group", "create", {"vals_list": [{"order_ids": [[6, 0, rfq_ids]]}]}
        )[0]
    return {
        "database": writer.database,
        "products": product_ids,
        "suppliers": supplier_ids,
        "rfq_order_ids": rfq_ids,
        "purchase_group_id": group,
        "summary": plan_summary(plan),
    }


def _write_order(writer, order: Order, product_ids, supplier_ids, uom, company) -> None:
    po = writer.call(
        "purchase.order",
        "create",
        {"vals_list": [{
            "partner_id": supplier_ids[order.supplier], "company_id": company,
            "date_order": _odoo(order.ordered_at), "origin": order.code, "partner_ref": TAG,
            "order_line": [[0, 0, {
                "product_id": product_ids[order.product], "product_qty": order.quantity,
                "product_uom_id": uom, "price_unit": order.unit_price,
                "date_planned": _odoo(order.expected_at),
            }]],
        }]},
    )[0]  # fmt: skip
    writer.call("purchase.order", "button_confirm", {"ids": [po]})
    confirmed = order.ordered_at + timedelta(hours=2)
    writer.call(
        "purchase.order",
        "write",
        {
            "ids": [po],
            "vals": {"date_order": _odoo(order.ordered_at), "date_approve": _odoo(confirmed)},
        },
    )
    remaining = order.quantity
    for index, receipt in enumerate(order.receipts):
        open_receipts = [["purchase_id", "=", po], ["state", "not in", ["done", "cancel"]]]
        picking = writer.call(
            "stock.picking", "search_read", {"domain": open_receipts, "fields": ["id", "move_ids"]}
        )[0]
        writer.call(
            "stock.move",
            "write",
            {"ids": picking["move_ids"], "vals": {"quantity": receipt.quantity, "picked": True}},
        )
        last = index == len(order.receipts) - 1
        remaining -= receipt.quantity
        context = {"skip_backorder": True, "skip_sms": True}
        if remaining > 0 and last and order.short_closed:
            context["picking_ids_not_to_backorder"] = [picking["id"]]
        writer.call(
            "stock.picking", "button_validate", {"ids": [picking["id"]], "context": context}
        )
        when = _odoo(receipt.at)
        writer.call(
            "stock.picking",
            "write",
            {"ids": [picking["id"]], "vals": {"date_done": when, "scheduled_date": when}},
        )
        moves = writer.call(
            "stock.move",
            "search_read",
            {
                "domain": [["picking_id", "=", picking["id"]], ["state", "=", "done"]],
                "fields": ["id", "move_line_ids"],
            },
        )
        writer.call(
            "stock.move", "write", {"ids": [m["id"] for m in moves], "vals": {"date": when}}
        )
        writer.call(
            "stock.move.line",
            "write",
            {"ids": [i for m in moves for i in m["move_line_ids"]], "vals": {"date": when}},
        )
    if order.short_closed and not order.receipts:
        raise ValueError("A short-closed order needs a receipt.")


EVALUATION_SIZES = (5, 10)


def evaluation_groups(plan: Plan) -> dict[int, tuple[str, ...]]:
    """P4 quotation groups for the RFQ product: the original four plus the suppliers
    with the most settled lines in the recent feature window, so every one is scorable."""
    window = (plan.now - timedelta(days=134), plan.now - timedelta(days=14))
    recent = {
        s.code: sum(
            o.supplier == s.code
            and o.product == plan.rfq_product
            and window[0] <= o.expected_at <= window[1]
            for o in plan.orders
        )
        for s in plan.suppliers
        if plan.rfq_product in s.products
    }
    others = sorted(
        (c for c, n in recent.items() if c not in plan.rfq_suppliers and n >= 4),
        key=lambda c: (-recent[c], c),
    )
    ranked = (*plan.rfq_suppliers, *others)
    if len(ranked) < max(EVALUATION_SIZES):
        raise ValueError("Too few scorable suppliers for the evaluation groups.")
    return {size: ranked[:size] for size in EVALUATION_SIZES}


def apply_evaluation_groups(plan: Plan, writer: OdooWriter, *, log=print) -> dict[int, int]:
    """Write one open RFQ per supplier and one quotation group per size; reuse on rerun.

    Needs the history from ``apply`` (products and suppliers are looked up by tag)."""
    writer.verify_target()
    code = f"{TAG}-{plan.rfq_product}"
    product = writer.call(
        "product.product", "search_read",
        {"domain": [["default_code", "=", code]], "fields": ["id", "uom_id"]},
    )  # fmt: skip
    if not product:
        raise ValueError("Run 'apply' first: the generated RFQ product is missing.")
    company = writer.call(
        "res.company", "search_read", {"domain": [], "fields": ["id"], "limit": 1}
    )[0]["id"]
    base = next(p for p in plan.products if p.code == plan.rfq_product).base_price
    # The four-supplier workload is the RFQ group written by ``apply``.
    rfq = writer.call(
        "purchase.order",
        "search_read",
        {
            "domain": [["origin", "=like", f"{TAG}:RFQ:%"]],
            "fields": ["purchase_group_id"],
            "limit": 1,
        },
    )
    if not rfq or not rfq[0]["purchase_group_id"]:
        raise ValueError("Run 'apply' first: the four-supplier RFQ group is missing.")
    groups = {len(plan.rfq_suppliers): rfq[0]["purchase_group_id"][0]}
    for size, codes in evaluation_groups(plan).items():
        prefix = f"{TAG}:RFQ{size}:"
        found = writer.call(
            "purchase.order", "search_read",
            {
                "domain": [["origin", "=like", f"{prefix}%"]],
                "fields": ["id", "origin", "purchase_group_id"],
            },
        )  # fmt: skip
        present = {r["origin"]: r for r in found}
        expected = [f"{prefix}{code}" for code in codes]
        # An interrupted earlier run may have written only some RFQs, or none of the group.
        missing = [c for c, origin in zip(codes, expected, strict=True) if origin not in present]
        created = []
        if missing:
            partners = dict(
                (r["ref"], r["id"])
                for r in writer.call(
                    "res.partner", "search_read",
                    {
                        "domain": [["ref", "in", [f"{TAG}-{c}" for c in missing]]],
                        "fields": ["id", "ref"],
                    },
                )
            )  # fmt: skip
            for code in missing:
                supplier = next(s for s in plan.suppliers if s.code == code)
                created += writer.call(
                    "purchase.order",
                    "create",
                    {"vals_list": [{
                        "partner_id": partners[f"{TAG}-{code}"], "company_id": company,
                        "origin": f"{prefix}{code}", "partner_ref": TAG,
                        "order_line": [[0, 0, {
                            "product_id": product[0]["id"], "product_qty": 200,
                            "product_uom_id": product[0]["uom_id"][0],
                            "price_unit": round(base * supplier.price_factor, 2),
                            "date_planned": _odoo(plan.now + timedelta(days=supplier.lead_days)),
                            "tax_ids": [[6, 0, []]],
                        }]],
                    }]},
                )  # fmt: skip
        linked = {
            present[o]["purchase_group_id"][0] if present[o]["purchase_group_id"] else None
            for o in expected
            if o in present
        }
        if not missing and len(linked) == 1 and None not in linked:
            groups[size] = linked.pop()
            log(f"{size}-supplier group already present: {groups[size]}")
            continue
        # Link the complete set of RFQs of this size in one group, reused or created.
        rfq_ids = [present[o]["id"] for o in expected if o in present] + created
        groups[size] = writer.call(
            "purchase.order.group", "create", {"vals_list": [{"order_ids": [[6, 0, rfq_ids]]}]}
        )[0]
        log(f"{size}-supplier group created: {groups[size]} ({', '.join(codes)})")
    return groups


def _settings() -> dict[str, str]:
    values = {}
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.lstrip().startswith("#"):
                values[key.strip()] = value.strip()
    return values


def main(argv: list[str]) -> int:
    limit = int(argv.pop()) if len(argv) == 2 and argv[1].isdigit() else None
    if len(argv) != 1 or argv[0] not in ("plan", "apply", "groups"):
        print(__doc__)
        return 2
    import json

    plan = build_plan(CLOCK)
    if argv[0] == "plan":
        print(
            json.dumps(
                plan_summary(plan) | {"evaluation_groups": evaluation_groups(plan)}, indent=2
            )
        )
        return 0
    settings = _settings()
    writer = OdooWriter(
        settings.get("ODOO_BASE_URL", "http://127.0.0.1:8069"),
        settings.get("ODOO_SEED_DATABASE", ""),
        settings.get("ODOO_SEED_ADMIN_API_KEY", ""),
    )
    if argv[0] == "groups":
        groups = apply_evaluation_groups(plan, writer)
        # The evaluation reads these ids: the listing shows only the newest groups.
        out = ROOT / ".artifacts" / "seed" / "evaluation_groups.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps({str(k): v for k, v in groups.items()}, indent=2), encoding="utf-8"
        )
        print(json.dumps(groups))
        return 0
    manifest = apply_plan(plan, writer, limit=limit)
    out = ROOT / ".artifacts" / "seed" / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    plan_json = {
        "manifest": manifest,
        "suppliers": [asdict(s) for s in plan.suppliers],
        "note": "Generator ground truth; never a training input.",
    }
    out.write_text(json.dumps(plan_json, indent=2, default=str), encoding="utf-8")
    print(json.dumps(manifest["summary"], indent=2))
    print(f"Manifest: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
