"""Every sentence and label of the approved PDFs, in Hungarian and English.

The keys are shared by the plan and the audit document. Values are shown verbatim, so
changing one changes the rendered PDF (raise ``layout.LAYOUT_VERSION`` then).
"""

from supplier_evaluation.contracts import HISTORY_GENERATED, HISTORY_OBSERVED

# Fixed English sentences every decision record carries (application/planning_decisions.py
# ``_audit``). Records stay verbatim; Hungarian PDFs show a translation and quote the original.
RECORDED_TEXT_HU = {
    "caller-supplied audit reference; not authenticated buyer identity": (
        "A hívó által megadott naplóhivatkozás; nem hitelesített beszerzői személyazonosság"
    ),
    "Controlled demonstration; synthetic ML evidence; no current operational validity asserted": (
        "Ellenőrzött bemutató; szintetikus ML-bizonyíték; aktuális üzemi érvényességet nem állít"
    ),
}
SOLVER_OUTCOME_HU = {
    "optimal": "optimális",
    "infeasible": "nincs megvalósítható terv",
    "no_proven_optimum": "nincs igazolt optimum",
    "solver_error": "megoldói hiba",
    "invalid_input": "elutasított bemenet",
}

TEXT = {
    "hu": {
        "doc_title": "Jóváhagyott beszerzési terv",
        "summary": "Összefoglaló",
        "footer": "Jóváhagyott beszerzési terv | {case}",
        "page": "{page}. oldal",
        HISTORY_GENERATED: (
            "Bemutató adatok: a beszállítói értékelés generált (szimulált) Odoo beszerzési "
            "előzményeken tanított döntési fából származik. Nem valós beszállítói teljesítmény."
        ),
        HISTORY_OBSERVED: (
            "A beszállítói értékelés megfigyelt Odoo beszerzési előzményeken tanított döntési "
            "fából származik. A pontszám nem kalibrált meghibásodási valószínűség."
        ),
        "score_note": "A pontszám nem kalibrált meghibásodási valószínűség.",
        "scope": (
            "Ez a dokumentum a jóváhagyott eredeti tervet rögzíti. A stresszteszt-forgatókönyvek "
            "külön elemzési esetek maradnak. A dokumentum nem Odoo beszerzési rendelés."
        ),
        "incomplete": (
            "HIÁNYOS ÖSSZEHASONLÍTÁS: a kiválasztott terv igazolt, de egy későbbi "
            "összehasonlító számítás nem sikerült. Rögzített megoldói eredmény: {status}."
        ),
        "product": "Termék",
        "demand": "Jóváhagyott mennyiség",
        "required_date": "Szükséges határidő",
        "plan": "Kiválasztott terv",
        "minimum_plan": "Minimális költségű terv",
        "alternative_plan": "{n}. alternatív terv (alacsonyabb kockázati kitettség)",
        "balanced_plan": "Kiegyensúlyozott terv (legkisebb függés egy beszállítótól)",
        "total_cost": "Teljes költség",
        "supplier_count": "Beszállítók száma",
        "largest_share": "Legnagyobb beszállítói részarány",
        "exposure": "Kockázati kitettség",
        "exposure_note": (
            "A kockázati kitettség a beszállítói kockázati pontszámok mennyiséggel súlyozott "
            "átlaga; nem kalibrált meghibásodási valószínűség."
        ),
        "premium": "Költségtöbblet a minimális költséghez képest",
        "allocation": "Jóváhagyott elosztás",
        "supplier": "Beszállító",
        "quantity": "Mennyiség",
        "unit": "Mértékegység",
        "unit_price": "Egységár",
        "line_total": "Sor összesen",
        "share": "Részarány",
        "currency": "Pénznem",
        "total": "Összesen",
        "decision": "Emberi döntés",
        "outcome": "Döntés",
        "approved": "Jóváhagyva",
        "decided_by": "Döntéshozó (audit hivatkozás)",
        "recorded_at": "Rögzítve",
        "rationale": "Indoklás",
        "no_rationale": "Nincs megadva (minimális költségű terv kiválasztása)",
        "proposals_follow": (
            "A beszállítónkénti rendelési tételek a következő oldalakon találhatók."
        ),
        "proposal": "Rendelési tétel – jóváhagyott terv",
        "offer": "Ajánlat",
        "case": "Beszerzési eset",
        "line": "Tétel adatai",
        "dates": "Határidők",
        "promised_date": "Vállalt szállítási dátum",
        "terms": "Tervezési feltételezések",
        "terms_note": (
            "A beszerző által rögzített vagy javaslaton hagyott tervezési feltételek; nem "
            "beszállítói vállalások."
        ),
        "moq": "Minimális rendelési mennyiség",
        "none": "nincs",
        "capacity": "Kapacitás",
        "price_range": "Ár érvényességi mennyiségi sávja",
        "delivery_range": "Szállítható mennyiségi sáv",
        "proposal_note": (
            "A tétel a jóváhagyott tervből készült, nem Odoo beszerzési rendelés. A "
            "beszállító megnevezése nem helyettesíti a jogi adatokat (cím, adószám)."
        ),
        "audit_title": "Audit melléklet – jóváhagyott beszerzési terv",
        "audit_footer": "Audit melléklet | {case}",
        "verification": "Ellenőrzési azonosítók",
        "decision_time": "Döntés időpontja",
        "audit_pointer": (
            "A teljes audit melléklet a rendszer Audit nézetéből tölthető le (azonos "
            "jóváhagyott tartalom-hash)."
        ),
        "data_source": "Adatforrás",
        "database": "Odoo adatbázis",
        "data_origin": "Adatok eredete",
        "origin_generated": "generált (szimulált) előzmények",
        "origin_observed": "megfigyelt előzmények",
        "quotation_group": "Ajánlatcsoport",
        "history_cutoff": "Előzmények lezárási időpontja",
        "capture_hash": "Előzmény-rögzítés SHA-256",
        "model": "Beszállítóértékelő modell",
        "model_id": "Modellazonosító",
        "training_id": "Tanítási azonosító",
        "trained_through": "Tanítási adatok vége",
        "artifact_hash": "Modellfájl SHA-256",
        "assessments": "Beszállítói értékelések",
        "class": "Besorolás",
        "score": "Kockázati pontszám",
        "metrics": "Előzmény-mutatók",
        "path": "Döntési útvonal",
        "window": "Előzmény-ablak",
        "optimization": "Optimalizálás",
        "solver": "Megoldó",
        "solver_outcome": "Megoldói eredmény",
        "time_limit": "Időkorlát",
        "seconds": "mp",
        "max_suppliers": "Beszállítók maximális száma",
        "concentration": "Koncentrációs korlát (legnagyobb részarány)",
        "epsilons": "Megengedett költségtöbblet az alternatív tervekhez",
        "decision_audit": "Döntési napló",
        "attribution": "Döntéshozó azonosítása",
        "demonstration": "Rögzített nyilatkozat",
        "plan_index": "Terv sorszáma",
        "reference_time": "Tervezési referenciaidő",
        "identity": "Tartalmi azonosítók",
        "content_version": "Tartalomverzió",
        "snapshot_hash": "Tervpillanatkép SHA-256",
        "content_hash": "Jóváhagyott tartalom SHA-256",
        "provenance": "Mezőszintű adatforrások",
        "field": "Mező",
        "source": "Forrás",
        "reference": "Hivatkozás",
        "observed_at": "Időpont",
        "original_text": "(eredeti, rögzített szöveg)",
        "original_quoted": "(eredeti, rögzített szöveg: „{text}”)",
        "yes": "igen",
        "no": "nem",
        "available": "Elérhető",
    },
    "en": {
        "doc_title": "Approved procurement plan",
        "summary": "Summary",
        "footer": "Approved procurement plan | {case}",
        "page": "Page {page}",
        HISTORY_GENERATED: (
            "Demonstration data: supplier assessments come from a decision tree trained on "
            "generated (simulated) Odoo purchase history. Not real supplier performance."
        ),
        HISTORY_OBSERVED: (
            "Supplier assessments come from a decision tree trained on observed Odoo purchase "
            "history. The score is not a calibrated failure probability."
        ),
        "score_note": "The score is not a calibrated failure probability.",
        "scope": (
            "This document records the approved original plan. Stress scenarios remain "
            "separate analytical cases. This document is not an Odoo Purchase Order."
        ),
        "incomplete": (
            "INCOMPLETE COMPARISON: the selected plan was proven, but a later comparison "
            "calculation failed. Saved solver outcome: {status}."
        ),
        "product": "Product",
        "demand": "Approved quantity",
        "required_date": "Required date",
        "plan": "Selected plan",
        "minimum_plan": "Minimum-cost plan",
        "alternative_plan": "Alternative plan {n} (lower risk exposure)",
        "balanced_plan": "Balanced plan (smallest dependence on one supplier)",
        "total_cost": "Total cost",
        "supplier_count": "Number of suppliers",
        "largest_share": "Largest supplier share",
        "exposure": "Risk exposure",
        "exposure_note": (
            "Risk exposure is the quantity-weighted average of supplier risk scores; it is "
            "not a calibrated failure probability."
        ),
        "premium": "Cost premium over the minimum cost",
        "allocation": "Approved allocation",
        "supplier": "Supplier",
        "quantity": "Quantity",
        "unit": "Unit",
        "unit_price": "Unit price",
        "line_total": "Line total",
        "share": "Share",
        "currency": "Currency",
        "total": "Total",
        "decision": "Human decision",
        "outcome": "Outcome",
        "approved": "Approved",
        "decided_by": "Decided by (audit reference)",
        "recorded_at": "Recorded at",
        "rationale": "Rationale",
        "no_rationale": "Not given (minimum-cost plan selected)",
        "proposals_follow": "One order line per supplier follows.",
        "proposal": "Order line – approved plan",
        "offer": "Quotation",
        "case": "Procurement case",
        "line": "Line details",
        "dates": "Dates",
        "promised_date": "Promised delivery date",
        "terms": "Planning assumptions",
        "terms_note": (
            "Planning terms recorded or kept as suggested by the buyer; not supplier commitments."
        ),
        "moq": "Minimum order quantity",
        "none": "none",
        "capacity": "Capacity",
        "price_range": "Price validity quantity range",
        "delivery_range": "Deliverable quantity range",
        "proposal_note": (
            "This line is derived from the approved plan and is not an Odoo Purchase "
            "Order. Supplier labels do not establish legal names, addresses or tax details."
        ),
        "audit_title": "Audit appendix – approved procurement plan",
        "audit_footer": "Audit appendix | {case}",
        "verification": "Verification identifiers",
        "decision_time": "Decision time",
        "audit_pointer": (
            "The full audit appendix can be downloaded from the system's Audit view (same "
            "approved content hash)."
        ),
        "data_source": "Data source",
        "database": "Odoo database",
        "data_origin": "Data origin",
        "origin_generated": "generated (simulated) history",
        "origin_observed": "observed history",
        "quotation_group": "Quotation group",
        "history_cutoff": "History cutoff",
        "capture_hash": "History capture SHA-256",
        "model": "Supplier evaluation model",
        "model_id": "Model ID",
        "training_id": "Training ID",
        "trained_through": "Training data until",
        "artifact_hash": "Model artifact SHA-256",
        "assessments": "Supplier assessments",
        "class": "Class",
        "score": "Risk score",
        "metrics": "History metrics",
        "path": "Decision path",
        "window": "History window",
        "optimization": "Optimization",
        "solver": "Solver",
        "solver_outcome": "Solver outcome",
        "time_limit": "Time limit",
        "seconds": "s",
        "max_suppliers": "Maximum number of suppliers",
        "concentration": "Concentration limit (largest share)",
        "epsilons": "Allowed cost tolerance for alternative plans",
        "decision_audit": "Decision log",
        "attribution": "Actor attribution",
        "demonstration": "Recorded statement",
        "plan_index": "Plan index",
        "reference_time": "Planning reference time",
        "identity": "Content identity",
        "content_version": "Content version",
        "snapshot_hash": "Planning snapshot SHA-256",
        "content_hash": "Approved content SHA-256",
        "provenance": "Field-level data sources",
        "field": "Field",
        "source": "Source",
        "reference": "Reference",
        "observed_at": "Time",
        "original_text": "(original recorded text)",
        "original_quoted": "(original recorded text: “{text}”)",
        "yes": "yes",
        "no": "no",
        "available": "Available",
    },
}
