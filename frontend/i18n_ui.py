"""Static screen texts (English keys → Hungarian, English); merged into ``i18n.TEXT``."""

from frontend.i18n_revamp import REVAMP_TEXT

UI_TEXT: dict[str, tuple[str, str]] = {
    # Generic
    "error_title": ("Valami nem sikerült", "Something went wrong"),
    "cancel": ("Mégse", "Cancel"),
    "total": ("Összesen", "Total"),
    "change": ("Változás", "Change"),
    "currency": ("Pénznem", "Currency"),
    "availability": ("Elérhetőség", "Availability"),
    "audit": ("Audit", "Audit"),
    "required_short": ("szükséges:", "required"),
    "promised_short": ("vállalt szállítás:", "promised"),
    "suppliers_word": ("szállító", "suppliers"),
    "back_to_cases": ("Vissza az ügyekhez", "Back to cases"),
    "back_to_base": ("Vissza az alapügyhöz", "Back to the base case"),
    "back_to_overview": ("Vissza az áttekintéshez", "Back to overview"),
    "copy_case_id": ("Ügyazonosító másolása", "Copy case ID"),
    "copy_request": ("Pontos kérés másolása", "Copy exact request"),
    "request_key": ("Kérésazonosító", "Request key"),
    # Cases
    "cases_title": ("Ügyek", "Cases"),
    "cases_subtitle": ("Mentett beszerzési összehasonlítások.", "Saved procurement comparisons."),
    "new_comparison": ("Új beszerzés", "New procurement"),
    "search_label": ("Keresés", "Search"),
    "search_placeholder": ("Termék vagy ügyazonosító", "Product or case ID"),
    "filter_status": ("Döntés állapota", "Decision status"),
    "filter_origin": ("Adatforrás", "Data source"),
    "filter_all_decisions": ("Minden döntés", "All decisions"),
    "filter_all_sources": ("Minden forrás", "All sources"),
    "filter_odoo": ("Odoo", "Odoo"),
    "col_product": ("Termék", "Product"),
    "col_demand": ("Igény", "Demand"),
    "col_required": ("Szükséges", "Required by"),
    "col_min_cost": ("Legkisebb költség", "Minimum cost"),
    "col_decision": ("Döntés", "Decision"),
    "col_actions": ("Műveletek", "Actions"),
    "col_outcome": ("Eredmény", "Outcome"),
    "col_saved": ("Mentve", "Saved"),
    "col_supplier": ("Szállító", "Supplier"),
    "col_metric": ("Mutató", "Metric"),
    "open_case": ("Megnyitás", "Open case"),
    "open_scenario": ("Megnyitás", "Open"),
    "show_scenarios": ("Forgatókönyvek", "Scenarios"),
    "hide_scenarios": ("Forgatókönyvek elrejtése", "Hide scenarios"),
    "saved_scenarios": ("Mentett forgatókönyvek", "Saved scenarios"),
    "no_scenarios": ("Ehhez az ügyhöz még nincs forgatókönyv.", "No scenarios for this case yet."),
    "more_scenarios": ("További forgatókönyvek", "More scenarios"),
    "selected_case": ("Kijelölt ügy", "Selected case"),
    "view_pdf": ("Jóváhagyott PDF megtekintése", "View approved PDF"),
    "cases_on_page": ("ügy ezen az oldalon", "cases on this page"),
    "next_page": ("Következő oldal", "Next page"),
    "loading_cases": ("Ügyek betöltése…", "Loading cases…"),
    "empty_cases_title": ("Még nincs mentett ügy", "No saved cases yet"),
    "empty_cases_body": (
        "Indítson összehasonlítást egy nyitott Odoo-ajánlatkérésből.",
        "Start a comparison from an open Odoo RFQ.",
    ),
    "empty_filtered_title": ("Nincs találat", "No matches"),
    "empty_filtered_body": (
        "Módosítsa a szűrőket vagy a keresést.",
        "Change the filters or the search.",
    ),
    # Open RFQs
    "loading_rfqs": ("Ajánlatkérések betöltése az Odoo-ból…", "Loading RFQs from Odoo…"),
    "empty_rfqs_title": ("Nincs nyitott ajánlatkérés", "No open RFQs"),
    "empty_rfqs_body": (
        "Hozzon létre ajánlatkérést az Odoo-ban, majd frissítsen.",
        "Create an RFQ in Odoo, then refresh.",
    ),
    "rfqs_truncated": (
        "Csak a legutóbbi nyitott ajánlatokat néztük át; a régebbiek nem szerepelnek.",
        "Only the most recent open quotations were scanned; older ones are not listed.",
    ),
    "not_usable": ("Nem használható", "Not usable"),
    "terms_below": ("Feltételek lent", "Terms below"),
    "terms_title": ("Igény és szállítói feltételek", "Demand and supplier terms"),
    "history_title": ("Szállítói előzmények az Odoo-ból", "Supplier history from Odoo"),
    "history_note": (
        "A lezárt beszerzési sorokból számolva.",
        "Calculated from settled purchase lines.",
    ),
    "kpi_on_time": ("Határidőre", "On time"),
    "kpi_lateness": ("Átlagos késés (nap)", "Average lateness (days)"),
    "kpi_fill": ("Teljesítési arány", "Fill rate"),
    "kpi_lines": ("Lezárt sorok", "Settled lines"),
    "demand_title": ("Az Ön igénye", "Your demand"),
    "demand_label": ("Igényelt mennyiség", "Quantity needed"),
    "required_label": ("Szükséges dátum", "Required by"),
    "supplier_terms_title": ("Szállítói feltételek", "Supplier terms"),
    "supplier_terms_note": (
        "Az árak az Odoo-ajánlatokból jönnek. A kapacitást, a minimális rendelési mennyiséget, "
        "az ár és a szállítás érvényes mennyiségi tartományát és a vállalt dátumot Ön adja meg; "
        "az előre kitöltött értékek csak javaslatok.",
        "Prices come from the Odoo quotations. You set capacity, minimum order quantity, the "
        "quantity ranges in which the price and the delivery are valid, and the promised date; "
        "pre-filled values are only suggestions.",
    ),
    "offer_price": ("Egységár", "Unit price"),
    "capacity_label": ("Kapacitás", "Capacity"),
    "moq_label": ("Min. rendelési mennyiség", "Minimum order qty"),
    "promised_label": ("Vállalt szállítás", "Promised date"),
    "price_range_label": ("Ár érvényes mennyiségre", "Price valid for qty"),
    "delivery_range_label": ("Szállítás érvényes mennyiségre", "Delivery valid for qty"),
    "range_min": ("Legkisebb", "Minimum"),
    "range_max": ("Legnagyobb", "Maximum"),
    "suggested_value": ("javasolt, nem módosította", "suggested, not changed"),
    "policy_label": ("Szabályok", "Rules"),
    "review_title": ("Áttekintés mentés előtt", "Review before saving"),
    "review_note": (
        "A tervek elkészítése elmenti az összehasonlítást, de még nem hagy jóvá semmit.",
        "Calculating saves the comparison; it does not approve anything.",
    ),
    "review_pending": (
        "A mentés visszaigazolásra vár. Ismételje meg ugyanazt a kérést.",
        "The save awaits confirmation. Retry the same request.",
    ),
    "edit_terms": ("Feltételek módosítása", "Edit terms"),
    # Case page
    "tab_overview": ("Áttekintés", "Overview"),
    "tab_suppliers": ("Szállítók", "Suppliers"),
    "tab_plans": ("Tervek", "Plans"),
    "tab_decision": ("Döntés és PDF", "Decision & PDF"),
    "loading_case": ("Ügy betöltése…", "Loading case…"),
    "case_error_title": ("Az ügy nem nyitható meg", "The case cannot be opened"),
    "kpi_min_cost": ("Legkisebb költség", "Minimum cost"),
    "kpi_plans": ("Összevethető tervek", "Plans to compare"),
    "compare_options": ("Hasonlítsa össze a lehetőségeket", "Compare your options"),
    "options_note": (
        "Válasszon tervet a szállítói megosztás alapján. A kiválasztás még nem jóváhagyás.",
        "Choose a plan based on its supplier split. Selecting is not approving.",
    ),
    "options_decided": (
        "A döntés rögzítve van; a tervek csak megtekinthetők.",
        "The decision is recorded; plans are read-only.",
    ),
    "compare_plans": ("Tervek összehasonlítása", "Compare plans"),
    "suppliers_flagged": ("problémás besorolású", "flagged as problematic"),
    "inspect_suppliers": ("Szállítók megtekintése", "Inspect suppliers"),
    "next_step": ("Következő lépés", "Next step"),
    "step_saved": ("Összehasonlítás mentve", "Comparison saved"),
    "step_saved_body": (
        "A tervek elkészültek és mentve vannak.",
        "The plans are calculated and saved.",
    ),
    "step_choose": ("Terv kiválasztása", "Choose a plan"),
    "step_choose_body": (
        "Válassza ki, melyik tervvel menne tovább.",
        "Pick the plan you want to take forward.",
    ),
    "step_decide": ("Döntés rögzítése", "Record the decision"),
    "step_decide_body": (
        "Rövid indoklással rögzítse a döntést; ebből készül a PDF.",
        "Record the decision with a short reason; the PDF is made from it.",
    ),
    "review_decision": ("Döntés áttekintése", "Review decision"),
    "open_pdf_tab": ("Jóváhagyott PDF", "Approved PDF"),
    "open_decision_tab": ("Rögzített döntés", "Recorded decision"),
    "infeasible_body": (
        "Ezekkel a feltételekkel az igény nem teljesíthető. Nem találtunk ki mennyiségeket "
        "vagy költségeket; a pontos korlátokat az Audit mutatja.",
        "Demand cannot be met under these limits. No quantities or costs were invented; "
        "Audit shows the exact limits.",
    ),
    "no_result_body": (
        "Nincs igazolt eredmény. Ez nem jelenti azt, hogy a feladat megoldhatatlan; a részletek "
        "az Auditban.",
        "No proven result. This does not mean the problem is infeasible; see Audit.",
    ),
    "incomplete_body": (
        "Az összehasonlítás nem teljes: csak az igazolt tervek látszanak.",
        "The comparison is incomplete: only proven plans are shown.",
    ),
    # Suppliers
    "suppliers_title": ("Szállítói értékelés", "Supplier assessment"),
    "suppliers_intro": (
        "A döntési fa az Odoo-beszerzési előzmények mutatóiból sorolja be a szállítókat. "
        "A besorolás a kockázatot jelzi, nem a késés okát.",
        "The decision tree classifies suppliers from Odoo purchase-history indicators. The "
        "class signals risk, not the reason for a delay.",
    ),
    "loading_suppliers": ("Szállítói adatok betöltése…", "Loading supplier data…"),
    "kpi_compare": ("Szállítók összevetése", "Suppliers compared"),
    "kpi_compare_note": (
        "Az ügy mentésekor rögzített előzmény-mutatók.",
        "History indicators recorded when the case was saved.",
    ),
    "planned_quantity": ("Tervezett mennyiség", "Planned quantity"),
    "history_kpis": ("Előzmény-mutatók", "History indicators"),
    "why_class": ("Miért ez a besorolás?", "Why this class?"),
    "score_note": (
        "A kockázati pontszám nem kalibrált meghibásodási valószínűség.",
        "The risk score is not a calibrated failure probability.",
    ),
    "scenario_same_scores": (
        "A forgatókönyvek az alapügy mentett értékelését használják; a szállítókat nem "
        "soroljuk be újra.",
        "Scenarios reuse the base case's saved assessments; suppliers are not reclassified.",
    ),
    # Plans
    "plan_comparison": ("Tervek összehasonlítása", "Plan comparison"),
    "plans_intro": (
        "Ugyanaz a termék és ugyanaz az igény; a tervek a szállítói megosztásban térnek el.",
        "Same product and demand; the plans differ in their supplier split.",
    ),
    "select_for_review": ("Kiválasztás", "Select"),
    "selected_for_review": ("Kiválasztva", "Selected"),
    "approved_plan": ("Jóváhagyott terv", "Approved plan"),
    "total_cost": ("Összköltség", "Total cost"),
    "premium": ("Többletköltség", "Extra cost"),
    "demand_covered": ("Fedezett igény", "Demand covered"),
    "risk_exposure": ("Kockázati kitettség", "Risk exposure"),
    "chart_tradeoff": ("Költség és kockázat", "Cost versus risk"),
    "chart_tradeoff_note": (
        "Minden pont egy mentett terv. Balra olcsóbb, lejjebb kisebb a kockázati kitettség "
        "(0–100). A kitettség nem meghibásodási valószínűség.",
        "Each point is a saved plan. Further left is cheaper, lower is less risk exposure "
        "(0–100). Exposure is not a failure probability.",
    ),
    "chart_tradeoff_aria": (
        "Pontdiagram: a tervek összköltsége és kockázati kitettsége; az értékek a táblázatban.",
        "Scatter chart of plan cost against risk exposure; values are in the table.",
    ),
    "chart_cost": ("Összköltség", "Total cost"),
    "chart_exposure": ("Kitettség", "Exposure"),
    "chart_alternatives": ("Alternatívák", "Alternatives"),
    "selected_allocation": ("Kiválasztott megosztás", "Selected allocation"),
    "suggested_look": ("Legkisebb kockázatú terv", "Lowest-risk plan"),
    "selection_not_approval": (
        "A kiválasztás még nem jóváhagyás.",
        "Selecting does not approve the plan.",
    ),
    "what_shapes": ("Mi alakítja a megosztást?", "What shapes the allocation?"),
    "no_binding": (
        "Ebben a tervben nincs kizárás vagy elért korlát.",
        "No exclusions or binding limits in this plan.",
    ),
    # Scenarios
    "scenarios_intro": (
        "Próbálja ki, mi történik, ha egy szállító kiesik, vagy megváltozik a kapacitás, az "
        "igény vagy az ár. A forgatókönyv külön mentődik; az eredeti ügy és az Odoo nem "
        "változik.",
        "Try what happens if a supplier drops out or capacity, demand or price changes. Each "
        "scenario is saved separately; the original case and Odoo stay unchanged.",
    ),
    "err_base_scenarios": (
        "A mentett forgatókönyvek most nem érhetők el. Próbálja újra.",
        "Saved scenarios are unavailable right now. Please retry.",
    ),
    "loading_scenarios": ("Forgatókönyvek betöltése…", "Loading scenarios…"),
    "scenario_new": ("Új forgatókönyv", "New scenario"),
    "scenario_new_body": (
        "Az eredeti ügyből indul, ugyanazzal az optimalizálással és szállítói értékeléssel.",
        "Starts from the original case with the same optimisation and supplier assessment.",
    ),
    "scenario_type": ("Forgatókönyv típusa", "Scenario type"),
    "scenario_supplier": ("Érintett szállító", "Supplier to change"),
    "choose_supplier": ("Válasszon szállítót", "Choose a supplier"),
    "original_terms": ("Eredeti feltételek", "Original terms"),
    "new_demand": ("Új igény", "New demand"),
    "original_demand": ("Eredeti igény", "Original demand"),
    "new_capacity": ("Új kapacitás", "New capacity"),
    "capacity_hint": (
        "Lehet több vagy kevesebb is; a 0 megszünteti a kapacitást.",
        "Higher or lower; zero removes the capacity.",
    ),
    "new_price": ("Új egységár", "New unit price"),
    "price_hint": (
        "Lehet magasabb vagy alacsonyabb. Feltételezés, nem új Odoo-ajánlat (pl. 12,50).",
        "Higher or lower. An assumption, not a new Odoo quotation (e.g. 12.50).",
    ),
    "combined_hint": (
        "Adjon meg legalább két változást; a kapacitás és az ár egy szállítóra vonatkozik.",
        "Enter at least two changes; capacity and price apply to one supplier.",
    ),
    "draft_title": ("Feltételezések", "Assumptions"),
    "draft_note": (
        "Hogy van-e megvalósítható terv, azt a számítás dönti el.",
        "The calculation decides whether a feasible plan exists.",
    ),
    "run_scenario": ("Forgatókönyv futtatása és mentése", "Run and save scenario"),
    "saved_scenario": ("Mentett forgatókönyv", "Saved scenario"),
    "scenario_table": ("Alapügy és forgatókönyv", "Base case and scenario"),
    "chart_base": ("Alapügy", "Base case"),
    "chart_scenario": ("Forgatókönyv", "Scenario"),
    "chart_scenario_title": (
        "Mennyiség szállítónként (legkisebb költségű terv)",
        "Quantity per supplier (minimum-cost plan)",
    ),
    "chart_scenario_aria": (
        "Oszlopdiagram: szállítónkénti mennyiség az alapügyben és a forgatókönyvben; az "
        "értékek a táblázatban.",
        "Bar chart of quantity per supplier in base and scenario; values are in the table.",
    ),
    "scenario_no_plan_body": (
        "Ebben a forgatókönyvben nincs igazolt terv. A költség és a mennyiségek nem ismertek, "
        "nem nullák.",
        "This scenario has no proven plan. Its cost and quantities are unknown, not zero.",
    ),
    "scenario_footnote": (
        "A forgatókönyvek elemzések, nem hagyhatók jóvá. A szimulált árak feltételezések.",
        "Scenarios are analyses and cannot be approved. Simulated prices are assumptions.",
    ),
    # Decision
    "record_decision": ("Döntés rögzítése", "Record the decision"),
    "record_decision_body": (
        "Válasszon tervet, vagy rögzítse, hogy most nem rendel. A döntés végleges, és minden "
        "döntéshez rövid indoklás kell.",
        "Choose a plan or record no award. The decision is one-time and cannot be replaced. "
        "Every decision needs a brief reason.",
    ),
    "plan_for_approval": ("Jóváhagyandó terv", "Plan to approve"),
    "choose_plan": ("Válasszon tervet…", "Choose a plan…"),
    "record_no_award": ("Most nem rendelünk", "Record no award"),
    "choose_plan_instead": ("Mégis tervet választok", "Choose a plan instead"),
    "no_award_effect": (
        "Ha nem rendelünk, egyik terv sem kerül jóváhagyásra, és PDF sem készül.",
        "No award: no allocation is approved and no PDF is produced.",
    ),
    "decision_actor": ("Döntéshozó", "Decided by"),
    "actor_placeholder": ("Név vagy azonosító", "Name or reference"),
    "decision_reason": ("Indoklás", "Reason"),
    "reason_placeholder": (
        "Miért ezt a tervet választja, vagy miért nem rendel?",
        "Why this plan, or why no award?",
    ),
    "ack_label": (
        "Tudomásul veszem, hogy a szállítói előzmények tesztadatbázisból származnak, és a "
        "döntés nem hoz létre rendelést az Odoo-ban.",
        "I acknowledge this is demonstration data: supplier history comes from a test "
        "database and the decision creates no Odoo order.",
    ),
    "review_approval": ("Jóváhagyás áttekintése", "Review approval"),
    "review_no_award": ("Döntés áttekintése", "Review decision"),
    "confirm_approval": ("Jóváhagyás megerősítése", "Confirm approval"),
    "confirm_no_award": ("Megerősítem: nem rendelünk", "Confirm no award"),
    "confirm_body": (
        "A megerősítéssel a döntés végleges lesz. A Mégse gombbal mentés nélkül visszaléphet. "
        "Az Odoo-ban nem jön létre rendelés.",
        "Confirming records the decision once; it cannot be replaced. Cancel returns without "
        "saving. No Odoo order is created.",
    ),
    "approve_plan": ("Terv jóváhagyása", "Approve plan"),
    "decision_plan": ("Terv", "Plan"),
    "decision_recorded": ("Rögzítve", "Recorded"),
    "approved_allocation": ("Jóváhagyott megosztás", "Approved allocation"),
    "retry_pdf": ("PDF újra", "Retry PDF"),
    "pdf_language_note": (
        "A PDF a felület nyelvén készül.",
        "The PDF follows the interface language.",
    ),
    "no_award_no_pdf": ("Ha nem rendelünk, PDF sem készül.", "No award has no PDF."),
    "no_odoo_order": (
        "A döntés nem hoz létre beszerzési rendelést az Odoo-ban.",
        "The decision does not create a purchase order in Odoo.",
    ),
    "scenario_no_decision": (
        "Forgatókönyvről nem lehet dönteni. A döntést az alapügyön rögzítheti.",
        "A scenario cannot be decided. Record the decision on the base case.",
    ),
    "decision_paused": (
        "A döntés szünetel: előbb nyissa meg a rögzített döntést fent.",
        "Decisions are paused: reopen the recorded decision above first.",
    ),
    # Recovery
    "recovery_title": ("Fejezze be ugyanazt a mentést", "Finish the same save"),
    "recovery_body": (
        "Nem érkezett válasz; lehet, hogy a mentés már megtörtént. Az „Ugyanazon kérés "
        "ismétlése” gomb ugyanazt a kérést küldi el ugyanazzal az azonosítóval, ezért nem jön "
        "létre másodpéldány.",
        "No response arrived; the save may already be stored. “Retry the same request” sends "
        "the same request with the same key, so no duplicate is created.",
    ),
    "recovery_conflict_title": ("Nyissa meg a rögzített döntést", "Reopen the recorded decision"),
    "recovery_conflict_body": (
        "A szerver ütközést jelzett. Olvassa el a rögzített döntést; új jóváhagyás nem írhatja "
        "felül.",
        "The server reported a conflict. Read the recorded decision; a new approval cannot "
        "replace it.",
    ),
    "reopen_decision": ("Rögzített döntés megnyitása", "Reopen recorded decision"),
    "retry_same": ("Ugyanazon kérés ismétlése", "Retry the same request"),
    "recovery_session_note": (
        "A helyreállítási adatok csak ebben a munkamenetben élnek. Távozás előtt másolja ki őket.",
        "Recovery data lives only in this session. Copy it before leaving.",
    ),
    "recovery_copy": ("Helyreállítási adatok", "Recovery record"),
    # Audit
    "audit_title": ("Audit", "Audit"),
    "audit_intro": (
        "A mentett ügy pontos értékei ellenőrzéshez és hibakereséshez.",
        "Exact values of the saved case, for checking and troubleshooting.",
    ),
    "audit_pdf": ("Audit melléklet (PDF)", "Audit appendix (PDF)"),
    "retry_audit_pdf": ("Audit melléklet újra", "Retry audit appendix"),
    "audit_pdf_note": (
        "Ugyanabból a jóváhagyott tartalomból (azonos hash) készül, mint a jóváhagyott terv PDF.",
        "Rendered from the same approved content (same hash) as the approved plan PDF.",
    ),
    "audit_case_id": ("Ügyazonosító", "Case ID"),
    "audit_base_id": ("Alapügy", "Base case"),
    "audit_snapshot_hash": ("Pillanatkép-hash", "Snapshot hash"),
    "audit_content_hash": ("Jóváhagyott tartalom hash", "Approved content hash"),
    "audit_company": ("Vállalat", "Company"),
    "audit_product": ("Termékazonosító", "Product identity"),
    "audit_cutoff": ("Adatok időpontja", "Data cutoff"),
    "audit_saved": ("Mentve (UTC)", "Saved (UTC)"),
    "audit_input_kind": ("Bemenet típusa", "Input kind"),
    "audit_inputs": ("Mentett bemenetek és szabályok", "Saved inputs and rules"),
    "audit_ranges": ("Ár / szállítás mennyiségi tartománya", "Price / delivery quantity range"),
    "audit_plans": (
        "Tervek pontos értékei és megoldói jegyzetek",
        "Exact plan values and solver notes",
    ),
    "audit_cost_exact": ("Pontos költség", "Exact cost"),
    "audit_exposure_exact": ("Pontos kitettség", "Exact exposure"),
    "audit_premium_exact": ("Pontos többlet", "Exact premium"),
    "audit_plan": ("Terv", "Plan"),
    "audit_supplier_id": ("Szállítóazonosító", "Supplier ID"),
    "audit_quantity": ("Mennyiség", "Quantity"),
    "audit_tree": ("Döntési fa útvonalai és modell", "Decision-tree paths and model"),
    "audit_class": ("Osztály", "Class"),
    "audit_score": ("Pontszám", "Score"),
    "audit_model": ("Modell", "Model"),
    "audit_history_ref": ("Előzmény-hivatkozás", "History reference"),
    "audit_window": ("Előzmény-ablak", "History window"),
    "audit_valid_until": ("Érvényes (UTC)", "Valid until (UTC)"),
    "audit_provenance": ("Mezőszintű eredet", "Field provenance"),
    "audit_field": ("Mező", "Field"),
    "audit_source": ("Forrás", "Source"),
    "audit_reference": ("Hivatkozás", "Reference"),
    "audit_observed": ("Időpont", "Observed at"),
    "audit_decision": ("Rögzített döntés (pontos)", "Recorded decision (exact)"),
    "audit_last_request": ("Utolsó kérés", "Last request"),
    "audit_last_request_note": (
        "Hibabejelentéshez: az eredeti URL, adatok és kulcs.",
        "For support: the original URL, payload and key.",
    ),
    "audit_snapshot": ("Teljes mentett pillanatkép (JSON)", "Complete saved snapshot (JSON)"),
    "audit_snapshot_note": (
        "A fenti feliratok nem helyettesítik ezt a rekordot.",
        "The labels above do not replace this record.",
    ),
}

UI_TEXT.update(REVAMP_TEXT)
