"""Every UI text in one dict: English key -> (Hungarian, English).

Hungarian is the default and must read as natural procurement language, not a
translation. Families named ``prefix_<code>`` in a section title are looked up with
a code from the API, so grep for the prefix before deleting one of them.
"""

TEXT: dict[str, tuple[str, str]] = {
    # Shell and navigation
    "app_name": ("Beszerzési döntéstámogatás", "Procurement decision support"),
    "nav_cases": ("Ügyek", "Cases"),
    "nav_label": ("Fő navigáció", "Main navigation"),
    "menu": ("Menü", "Menu"),
    "close_menu": ("Menü bezárása", "Close menu"),
    "skip": ("Ugrás a tartalomra", "Skip to content"),
    "language": ("Nyelv", "Language"),
    "discard_title": ("Elveti a nem mentett módosításokat?", "Discard your unsaved changes?"),
    "discard_body": (
        "Maradjon a szerkesztésnél, vagy vesse el a vázlatot. A mentett ügyek megmaradnak.",
        "Stay to keep editing, or discard the draft. Saved cases stay stored.",
    ),
    "stay": ("Maradok", "Stay"),
    "discard": ("Vázlat elvetése", "Discard draft"),
    "nav_home": ("Kezdőlap", "Home"),
    "new_procurement": ("Új beszerzés", "New procurement"),
    # Shared words and labels
    "loading": ("Betöltés…", "Loading…"),
    "waiting_api": ("Várakozás a szerverre…", "Waiting for the server…"),
    "retry": ("Újra", "Retry"),
    "refresh": ("Frissítés", "Refresh"),
    "open": ("Megnyitás", "Open"),
    "unavailable": ("Nem elérhető", "Unavailable"),
    "none": ("Nincs", "None"),
    "available": ("Elérhető", "Available"),
    "not_available": ("Nem elérhető", "Not available"),
    "required_by": ("szükséges: {date}", "required {date}"),
    "pieces": ("{quantity} {unit}", "{quantity} {unit}"),
    "supplier_n": ("{n}. szállító", "Supplier {n}"),
    "product_n": ("{n}. termék", "Product {n}"),
    "group_n": ("{n}. csoport", "Group {n}"),
    "badge_generated": ("Generált adat", "Generated data"),
    "generated_note": (
        "A szállítói előzmények ebben a tesztadatbázisban generáltak, nem valós teljesítmény.",
        "Supplier history in this test database is generated, not real performance.",
    ),
    "days": ("{value} nap", "{value} days"),
    "captured_at": ("Odoo-adatok kiolvasva: {time} UTC", "Odoo data read at {time} UTC"),
    "error_title": ("Valami nem sikerült", "Something went wrong"),
    "cancel": ("Mégse", "Cancel"),
    "total": ("Összesen", "Total"),
    "change": ("Változás", "Change"),
    "currency": ("Pénznem", "Currency"),
    "availability": ("Elérhetőség", "Availability"),
    "required_short": ("szükséges:", "required"),
    "promised_short": ("vállalt szállítás:", "promised"),
    "suppliers_word": ("szállító", "suppliers"),
    "back_to_cases": ("Vissza az ügyekhez", "Back to cases"),
    "back_to_base": ("Vissza az alapügyhöz", "Back to the base case"),
    "back_to_overview": ("Vissza az áttekintéshez", "Back to overview"),
    "copy_case_id": ("Ügyazonosító másolása", "Copy case ID"),
    "copy_request": ("Pontos kérés másolása", "Copy exact request"),
    "request_key": ("Kérésazonosító", "Request key"),
    "total_cost": ("Összköltség", "Total cost"),
    "scenario": ("Forgatókönyv", "Scenario"),
    "outcome": ("Eredmény", "Outcome"),
    "demand": ("Igény", "Demand"),
    "min_cost": ("Legkisebb költség", "Minimum cost"),
    "base_case": ("Alapügy", "Base case"),
    "plan": ("Terv", "Plan"),
    # Outcome, decision and save states (status_<planning status>)
    "status_optimal": ("Tervek elkészültek", "Plans ready"),
    "status_infeasible": ("Nincs megvalósítható terv", "No feasible plan"),
    "status_no_proven_optimum": ("Nincs igazolt optimum", "No proven optimum"),
    "status_solver_error": ("A megoldó nem érhető el", "Solver unavailable"),
    "status_invalid_input": ("Elutasított bemenet", "Input rejected"),
    "decision_draft": ("Döntésre vár", "Awaiting decision"),
    "decision_approved": ("Jóváhagyva", "Approved"),
    "decision_no_award": ("Nem rendelünk", "No award"),
    "decision_scenario": ("Forgatókönyv – döntés az alapügyön", "Scenario – decide on the base"),
    "state_conflict": (
        "Döntési ütközés – nyissa meg a rögzített döntést",
        "Decision conflict – reopen the recorded decision",
    ),
    "state_saving": ("Mentés folyamatban…", "Saving…"),
    "state_unconfirmed": (
        "A mentés nincs visszaigazolva – ismételje meg ugyanazt a kérést",
        "Save unconfirmed – retry the same request",
    ),
    "state_no_award": ("Rögzítve: nem rendelünk", "Recorded: no award"),
    "state_scenario": (
        "Mentett forgatókönyv – döntés az alapügyön",
        "Saved scenario – decide on the base case",
    ),
    "state_no_award_selected": (
        "„Nem rendelünk” kiválasztva – még nincs rögzítve",
        "No award selected – not yet recorded",
    ),
    "state_selected": (
        "Terv kiválasztva – még nincs jóváhagyva",
        "Plan selected – not yet approved",
    ),
    "state_awaiting": (
        "Mentett összehasonlítás – döntésre vár",
        "Saved comparison – awaiting a decision",
    ),
    # Home
    "home_title": ("Beszerzési döntések", "Procurement decisions"),
    "home_intro": (
        "Folytasson egy döntésre váró ügyet, vagy indítson újat az Odoo-ajánlatokból.",
        "Continue a case that awaits a decision, or start a new one from Odoo quotations.",
    ),
    "continue_case": ("Ügy folytatása", "Continue case"),
    "all_cases": ("Összes ügy megnyitása", "Browse all cases"),
    "home_pending": ("Döntésre váró ügyek", "Awaiting your decision"),
    "home_recent": ("Legutóbb mentett ügyek", "Recently saved cases"),
    "home_pending_empty": ("Nincs döntésre váró ügy.", "No case is waiting for a decision."),
    "home_recent_empty": (
        "Még nincs mentett ügy. Az első terv elkészítése után itt folytathatja a munkát.",
        "No saved cases yet. Your first saved plan will appear here.",
    ),
    "home_scope": (
        "Listánként a legutóbbi öt ügy látható.",
        "Each list shows the five most recent cases.",
    ),
    # Cases library
    "cases_subtitle": ("Mentett beszerzési összehasonlítások.", "Saved procurement comparisons."),
    "search_label": ("Keresés", "Search"),
    "search_placeholder": ("Termék vagy ügyazonosító", "Product or case ID"),
    "filter_status": ("Döntés állapota", "Decision status"),
    "filter_all_decisions": ("Minden döntés", "All decisions"),
    "col_product": ("Termék", "Product"),
    "col_required": ("Szükséges", "Required by"),
    "col_decision": ("Döntés", "Decision"),
    "col_actions": ("Műveletek", "Actions"),
    "col_saved": ("Mentve", "Saved"),
    "col_supplier": ("Szállító", "Supplier"),
    "col_metric": ("Mutató", "Metric"),
    "open_case": ("Megnyitás", "Open case"),
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
    # New procurement: steps and Odoo quotations (quotation_<state>, issue_<code>, source_<kind>)
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
    "prepare_title": ("Beszerzés előkészítése", "Prepare your procurement"),
    "prepare_subtitle": (
        "Ellenőrizze az igényt és a beszállítói feltételeket, majd készítse el a terveket.",
        "Check your demand and supplier terms, then create the plans.",
    ),
    "step_source": ("Ajánlatok", "Quotations"),
    "step_terms": ("Feltételek", "Supplier terms"),
    "step_review": ("Ellenőrzés", "Review"),
    "creation_progress": ("Beszerzés előkészítésének lépései", "Procurement preparation steps"),
    "source_odoo": ("Odoo-ból beolvasva", "Read from Odoo"),
    "source_buyer": ("Beszerző által megadva", "Buyer supplied"),
    "source_suggested": ("Javasolt érték", "Suggested value"),
    "rfqs_title": ("Odoo-ajánlatok kiválasztása", "Choose Odoo quotations"),
    "rfqs_subtitle": (
        "Válasszon ajánlatcsoportot a beszerzési döntés előkészítéséhez.",
        "Choose a quotation group to prepare a procurement decision.",
    ),
    "quotation_details": ("A csoport ajánlatai", "Quotations in this group"),
    "quotation_reference": ("Odoo-hivatkozás", "Odoo reference"),
    "quotation_quantity": ("Ajánlati mennyiség", "Quoted quantity"),
    "quotation_state": ("Odoo-állapot", "Odoo status"),
    "quotation_draft": ("Piszkozat", "Draft"),
    "quotation_sent": ("Elküldve", "Sent"),
    "quotation_other": ("Egyéb állapot", "Other status"),
    "quotation_quantity_note": (
        "Az ajánlati mennyiség nem azonos a beszerzendő mennyiséggel; azt a következő "
        "lépésben adja meg.",
        "The quoted quantity is not the quantity to buy; you enter that in the next step.",
    ),
    "choose_group": ("Ajánlatok megtekintése", "View quotations"),
    "selected_group": ("Kiválasztott ajánlatcsoport", "Selected quotation group"),
    "start_comparison": ("Igény megadása", "Set demand"),
    "change_group": ("Másik ajánlatcsoport", "Change quotation group"),
    "groups_updated": ("Ajánlatok lekérve:", "Quotations retrieved:"),
    "draft_session_note": (
        "Az előkészítés még nincs mentve. A lépések között visszaléphet; az oldal "
        "újratöltésekor a beírt adatok elveszhetnek.",
        "Preparation is not saved yet. You can move between steps; reloading the page may "
        "lose your inputs.",
    ),
    "issue_unsupported_offer_count": (
        "Legalább 3, legfeljebb 10 ajánlat szükséges",
        "Between 3 and 10 quotations are required",
    ),
    "issue_not_all_open": ("Nem minden ajánlat nyitott", "Not every quotation is open"),
    "issue_not_single_line": ("Az ajánlatok nem egysorosak", "Quotations are not single-line"),
    "issue_duplicate_supplier": ("Egy szállító többször szerepel", "A supplier appears twice"),
    "issue_mixed_context": (
        "Eltérő termék, egység vagy pénznem",
        "Different product, unit or currency",
    ),
    "issue_discount_or_tax": ("Kedvezményt vagy adót tartalmaz", "Contains a discount or tax"),
    # New procurement: demand and supplier history preview
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
    "continue_terms": ("Tovább a beszállítói feltételekhez", "Continue to supplier terms"),
    "demand_intro": (
        "Mennyire van szüksége, és mikorra? Ezek az Ön által ellenőrzött beszerzési feltételek.",
        "How much do you need, and by when? These are the procurement terms you review.",
    ),
    "demand_help": (
        "A teljes, jóváhagyott igény egész mennyiségben. Ezt osztjuk el a beszállítók között.",
        "The total approved demand in whole units, to be allocated across suppliers.",
    ),
    "date_help": (
        "A legkésőbbi elfogadható beérkezés napja.",
        "The latest acceptable receipt date.",
    ),
    "show_history": ("Beszállítói előzmények megtekintése", "View supplier history"),
    # New procurement: supplier terms and rules (range_<min|max>)
    "supplier_terms_title": ("Szállítói feltételek", "Supplier terms"),
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
    "back_demand": ("Vissza az igényhez", "Back to demand"),
    "capacity_help": (
        "Legfeljebb ennyi rendelhető ettől a beszállítótól. A javaslat nem igazolt kapacitás.",
        "Maximum quantity available from this supplier. A suggestion is not verified capacity.",
    ),
    "moq_help": (
        "A kötelező legkisebb rendelés. Üresen: nincs minimum; ezt is ellenőrizze.",
        "Mandatory minimum order quantity. Empty means no minimum; verify this too.",
    ),
    "range_help": (
        "Csak ebben a mennyiségi tartományban használható az ár vagy a szállítási vállalás.",
        "The price or delivery commitment applies only within this quantity range.",
    ),
    "promised_help": (
        "Az adott mennyiségre vállalt szállítás napja. A javaslatot ellenőrizze a beszállítóval.",
        "Delivery date committed for the quantity. Verify the suggestion with the supplier.",
    ),
    "terms_guidance": (
        "Nyissa le a beszállítókat, és ellenőrizze a feltételeiket. A javasolt értékek nem "
        "igazolt beszállítói vállalások.",
        "Expand each supplier and review their terms. Suggested values are not verified "
        "supplier commitments.",
    ),
    "policy_explanation": (
        "A költségkeret megmutatja, legfeljebb mennyivel lehet drágább egy alternatíva a "
        "legolcsóbb tervnél. Ezen belül kisebb kockázatú megosztást keresünk.",
        "The allowance is how much more an alternative may cost than the cheapest plan; "
        "within it we look for a lower-risk split.",
    ),
    "review_terms": ("Feltételek áttekintése", "Review terms"),
    # New procurement: review and save
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
    "calculate_save": ("Tervek elkészítése és mentése", "Calculate and save plans"),
    "review_body": (
        "Ellenőrizze az igényt, a beszállítói feltételeket és az adatok forrását.",
        "Check the demand, the supplier terms and where each value comes from.",
    ),
    "review_sources": (
        "A javaslaton maradt értékeket külön jelöljük. Az ár Odoo-adat; az itt ellenőrzött "
        "feltételek beszerzői bemenetek.",
        "Unchanged suggestions are marked. Prices come from Odoo; the terms reviewed here "
        "are buyer inputs.",
    ),
    "suggested_terms": ("Javaslaton maradt értékek", "Unchanged suggested values"),
    # Case page and Overview tab
    "tab_overview": ("Áttekintés", "Overview"),
    "tab_suppliers": ("Szállítók", "Suppliers"),
    "tab_plans": ("Tervek", "Plans"),
    "tab_decision": ("Döntés és PDF", "Decision & PDF"),
    "loading_case": ("Ügy betöltése…", "Loading case…"),
    "case_error_title": ("Az ügy nem nyitható meg", "The case cannot be opened"),
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
    "case_next_compare": (
        "Következő teendő: hasonlítsa össze a terveket.",
        "Next: compare the plans.",
    ),
    "case_next_decide": (
        "A kiválasztott tervet a Döntés és PDF nézetben véglegesítheti.",
        "Finalize the selected plan in Decision & PDF.",
    ),
    "case_next_closed": (
        "A döntés rögzítve. Az ügy és az indoklás visszanézhető.",
        "Decision recorded. You can review the case and its rationale.",
    ),
    "case_next_scenario": (
        "Ez egy vizsgálati forgatókönyv. Döntést az alapügyben rögzíthet.",
        "This is a what-if scenario. Record a decision in the base case.",
    ),
    "case_next_unavailable": (
        "Nincs jóváhagyható terv. Tekintse át az eredmény állapotát és magyarázatát.",
        "No plan can be approved. Review the outcome and its explanation.",
    ),
    "tab_scenarios": ("Mi lenne, ha…?", "What if…?"),
    "kpi_suppliers": ("Értékelt szállítók", "Assessed suppliers"),
    # Suppliers tab
    "path_root": (
        "A döntési fa a gyökérben dönt; nincs elágazási feltétel.",
        "The tree decides at its root; there are no branch conditions.",
    ),
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
    "kpi_help_title": ("Hogyan olvassa a mutatókat?", "How to read the indicators"),
    "kpi_help_rates": (
        "Határidőre: azoknak az előzménybeli rendelési soroknak az aránya, amelyek első "
        "beérkezése a vállalt dátumhoz képest legfeljebb egy napot késett. "
        "Teljesítési arány: a beérkezett és rendelt mennyiségek aránya; a túlszállítás nem növeli. "
        "Mindkettőnél a nagyobb érték kedvezőbb.",
        "On time: the share of historical order lines whose first receipt was no more than "
        "one day after the expected date. Fill rate compares received and ordered quantities, "
        "capping overdelivery. Higher is better for both.",
    ),
    "kpi_help_lateness": (
        "Az átlagos késés az első beérkezés eltérése napokban; a negatív érték korábbi "
        "beérkezést jelent. Beérkezés hiányában a referencia-időpontig számolunk. "
        "A szórás a teljesítési idő ingadozását mutatja. "
        "A kisebb szórás kiszámíthatóbb teljesítést jelez.",
        "Average lateness measures the first receipt's delay in days; a negative value means "
        "early receipt. Missing receipts are measured up to the reference time. "
        "The standard deviation describes variation in delivery timing. "
        "A lower deviation means more consistent timing.",
    ),
    "kpi_help_sample": (
        "A lezárt rendelési sorok száma a beszállítóhoz tartozó előzményadat mennyisége. "
        "A faútvonal végén szereplő hasonló esetek a modell tanítómintájából származnak; "
        "ez másik mintaszám. Kevés előzményt körültekintően értelmezzen.",
        "Settled lines count the historical records for this supplier. Similar cases at "
        "the end of the tree path come from the model's training sample, a different count. "
        "Interpret sparse history with care.",
    ),
    "kpi_reference": ("Az értékelés referencia-időpontja", "Assessment reference time"),
    # Plans tab
    "plan_minimum": ("Legolcsóbb terv", "Cheapest plan"),
    "plan_alternative": ("{n}. alternatíva", "Alternative {n}"),
    "plan_lower_risk": ("legkisebb kockázat", "lowest risk"),
    "above_minimum": ("{amount} a legolcsóbbhoz képest", "{amount} above minimum"),
    "minimum_for_limits": (
        "A legolcsóbb terv ezekkel a feltételekkel",
        "Cheapest plan under these limits",
    ),
    "exposure_value": ("{value} / 100", "{value} / 100"),
    "tradeoff_summary": (
        "A legkisebb kockázatú terv {amount} összeggel drágább, és {points} ponttal kisebb a "
        "kockázati kitettsége.",
        "The lowest-risk plan costs {amount} more and lowers risk exposure by {points} points.",
    ),
    "tradeoff_summary_up": (
        "A legkisebb kockázatú terv {amount} összeggel drágább; a kockázati kitettség "
        "{points} ponttal változik.",
        "The lowest-risk plan costs {amount} more; risk exposure changes by {points} points.",
    ),
    "no_alternative_failed": (
        "Az alternatívák keresése nem fejeződött be, ezért csak a legolcsóbb terv látható. Ez "
        "nem jelenti, hogy nincs alternatíva.",
        "The search for alternatives did not finish, so only the cheapest plan is shown. This "
        "does not establish that no alternative exists.",
    ),
    "no_alternative_found": (
        "A megengedett többletköltségen belül nincs kisebb kockázatú terv.",
        "No lower-risk plan exists within the allowed extra cost.",
    ),
    "no_alternative_requested": (
        "Ehhez az ügyhöz nem kértünk alternatívát.",
        "No alternatives were requested for this case.",
    ),
    "policy_text": (
        "Legfeljebb {suppliers} szállító · szállítónként legfeljebb {share} · alternatívák "
        "{allowance} többletköltségig",
        "At most {suppliers} suppliers · at most {share} per supplier · alternatives up to "
        "{allowance} extra cost",
    ),
    "policy_no_share": ("nincs részesedési korlát", "no share limit"),
    "plan_comparison": ("Tervek összehasonlítása", "Plan comparison"),
    "plans_intro": (
        "Ugyanaz a termék és ugyanaz az igény; a tervek a szállítói megosztásban térnek el.",
        "Same product and demand; the plans differ in their supplier split.",
    ),
    "select_for_review": ("Kiválasztás", "Select"),
    "selected_for_review": ("Kiválasztva", "Selected"),
    "approved_plan": ("Jóváhagyott terv", "Approved plan"),
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
    "exposure_explained": (
        "A kitettség a beszállítói értékelések mennyiséggel súlyozott jelzőszáma. Kisebb "
        "érték kisebb modellezett kitettséget jelent, nem garantált szállítást vagy "
        "hibavalószínűséget.",
        "Exposure is the quantity-weighted supplier evaluation score. A lower value "
        "indicates lower modelled exposure, not guaranteed delivery or failure probability.",
    ),
    "allocation_details": ("Rendelési mennyiségek összevetése", "Compare allocated quantities"),
    "plan_budget": ("legfeljebb +{allowance} többletköltséggel", "within +{allowance} extra cost"),
    "plan_balanced": ("Kiegyensúlyozott terv", "Balanced plan"),
    "plan_balanced_hint": ("kiegyensúlyozott", "balanced"),
    "policy_balanced": (
        " · kiegyensúlyozott terv {allowance} többletköltségig",
        " · balanced plan up to {allowance} extra cost",
    ),
    "largest_share_label": ("Legnagyobb függés egy szállítótól", "Largest share of one supplier"),
    "balanced_explained": (
        "A kiegyensúlyozott terv a lehető legkisebbre veszi azt a mennyiséget, amely egyetlen "
        "szállítótól függ, a megadott költségkereten belül, és a kockázati kitettsége nem "
        "lehet nagyobb a legolcsóbb tervénél. Ha egy szállító kiesik, legfeljebb ennyi "
        "hiányzik az igényből.",
        "The balanced plan minimises the quantity that depends on a single supplier, within "
        "the cost allowance and without a higher risk exposure than the cheapest plan. If one "
        "supplier drops out, at most this share of the demand is missing.",
    ),
    # Plans tab: buyer explanations of solver notes (why_<note code>)
    "why_zero_in_optimal_plan": (
        "Ebben a tervben nem kap mennyiséget; ez nem kizárás.",
        "Not selected in this plan; this is not an exclusion.",
    ),
    "why_capacity_binding": (
        "A teljes megadott kapacitását felhasználja.",
        "Uses all of its capacity.",
    ),
    "why_concentration_binding": (
        "Elérte az egy szállítónak megengedett legnagyobb mennyiséget.",
        "Reaches the largest quantity allowed for one supplier.",
    ),
    "why_supplier_count_binding": (
        "A terv a megengedett legtöbb szállítót használja.",
        "Uses the maximum allowed number of suppliers.",
    ),
    "why_unavailable": ("Kizárva: nem elérhető.", "Excluded: unavailable."),
    "why_deadline_ineligible": (
        "Kizárva: a vállalt szállítási dátum a szükséges dátum után van.",
        "Excluded: the promised date is after the required date.",
    ),
    "why_no_valid_quantity": (
        "Kizárva: egyetlen pozitív mennyiség sem felel meg a korlátoknak.",
        "Excluded: no positive quantity meets the limits.",
    ),
    "why_moq_binding": (
        "Pontosan a minimális rendelési mennyiséget kapja.",
        "Gets exactly its minimum order quantity.",
    ),
    "why_price_lower_binding": (
        "Az ár alsó mennyiségi határán van.",
        "At the lower quantity limit of its price.",
    ),
    "why_price_upper_binding": (
        "Az ár felső mennyiségi határán van.",
        "At the upper quantity limit of its price.",
    ),
    "why_delivery_lower_binding": (
        "A szállítási vállalás alsó határán van.",
        "At the lower limit of its delivery promise.",
    ),
    "why_delivery_upper_binding": (
        "A szállítási vállalás felső határán van.",
        "At the upper limit of its delivery promise.",
    ),
    "why_integer_concentration_ceiling": (
        "Elérte az egész darabra kerekített részesedési korlátot.",
        "Reaches the whole-unit share limit.",
    ),
    "why_insufficient_effective_capacity": (
        "A felhasználható mennyiségek nem fedezik az igényt.",
        "The usable quantities cannot cover demand.",
    ),
    "why_supplier_count_capacity_shortfall": (
        "A megengedett számú szállítóval az igény nem fedezhető.",
        "Demand cannot be covered with the allowed number of suppliers.",
    ),
    # What if…? tab (kind_<scenario kind>)
    "kind_supplier_outage": ("Szállító kiesése", "Supplier outage"),
    "kind_capacity_change": ("Kapacitásváltozás", "Capacity change"),
    "kind_demand_change": ("Igényváltozás", "Demand change"),
    "kind_price_change": ("Árváltozás", "Price change"),
    "kind_combined": ("Kombinált változás", "Combined changes"),
    "assume_demand": ("Igény: {quantity}", "Demand: {quantity}"),
    "assume_outage": ("{name}: kiesik", "{name}: unavailable"),
    "assume_capacity": ("{name}: kapacitás {quantity}", "{name}: capacity {quantity}"),
    "assume_price": ("{name}: egységár {price}", "{name}: unit price {price}"),
    "scenario_delta": (
        "A legkisebb költség {amount} értékkel, a kockázati kitettség {points} ponttal változik.",
        "Minimum cost changes by {amount}; risk exposure changes by {points} points.",
    ),
    "scenario_no_plan": (
        "Ebben a forgatókönyvben nincs igazolt legkisebb költségű terv. Az alapügy változatlan.",
        "This scenario has no proven minimum-cost plan. The base case is unchanged.",
    ),
    "scenario_demand_changed": (
        "Az igény megváltozott, ezért az összegek nem közvetlen megtakarítások.",
        "Demand changed, so the totals are not a like-for-like saving.",
    ),
    "metric_min_cost": ("Legkisebb összköltség", "Minimum total cost"),
    "metric_exposure": ("Kockázati kitettség (0–100)", "Risk exposure (0–100)"),
    "draft_choose_supplier": ("Válassza ki a kieső szállítót.", "Choose the supplier to remove."),
    "draft_demand": ("Igény: {old} → {new} {unit}", "Demand: {old} → {new} {unit}"),
    "draft_capacity": (
        "{name} kapacitása: {old} → {new} {unit}",
        "{name} capacity: {old} → {new} {unit}",
    ),
    "draft_price": ("{name} egységára: {old} → {new}", "{name} unit price: {old} → {new}"),
    "draft_empty": (
        "Adja meg az új értéket a feltételezés áttekintéséhez.",
        "Enter the new value to review your assumption.",
    ),
    "scenarios_intro": (
        "Próbálja ki, mi történik, ha egy szállító kiesik, vagy megváltozik a kapacitás, az "
        "igény vagy az ár. A forgatókönyv külön mentődik; az eredeti ügy és az Odoo nem "
        "változik.",
        "Try what happens if a supplier drops out or capacity, demand or price changes. Each "
        "scenario is saved separately; the original case and Odoo stay unchanged.",
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
    "scenario_no_decision": (
        "Forgatókönyvről nem lehet dönteni. A döntést az alapügyön rögzítheti.",
        "A scenario cannot be decided. Record the decision on the base case.",
    ),
    # Decision & PDF tab, including the PDF viewer (pdf_*)
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
    "confirm_approval": ("Jóváhagyás megerősítése", "Confirm approval"),
    "confirm_no_award": ("Megerősítem: nem rendelünk", "Confirm no award"),
    "confirm_body": (
        "A megerősítéssel a döntés végleges lesz. A Mégse gombbal mentés nélkül visszaléphet. "
        "Az Odoo-ban nem jön létre rendelés.",
        "Confirming records the decision once; it cannot be replaced. Cancel returns without "
        "saving. No Odoo order is created.",
    ),
    "approve_plan": ("Terv jóváhagyása", "Approve plan"),
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
    "decision_paused": (
        "A döntés szünetel: előbb nyissa meg a rögzített döntést fent.",
        "Decisions are paused: reopen the recorded decision above first.",
    ),
    "pdf_download": ("Jóváhagyott PDF letöltése", "Download approved PDF"),
    "pdf_previous": ("Előző oldal", "Previous page"),
    "pdf_unavailable": ("A PDF előnézet nem érhető el", "PDF preview unavailable"),
    "pdf_page": ("{page}. oldal / {pages}", "Page {page} of {pages}"),
    "pdf_loading_pages": ("Oldalak betöltése…", "Loading PDF pages…"),
    "pdf_zoom": ("Nagyítás", "Zoom"),
    "pdf_fit": ("Teljes szélesség", "Fit width"),
    "pdf_failed": (
        "Az előnézet nem érhető el. A jóváhagyás mentve van; töltse le a PDF-et.",
        "Preview unavailable. The approval is saved; download the PDF.",
    ),
    "pdf_region": ("Jóváhagyott beszerzési PDF", "Approved procurement PDF"),
    "pdf_loading_viewer": ("PDF-megjelenítő betöltése…", "Loading PDF viewer…"),
    # Save recovery
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
    # Audit view
    "audit": ("Audit", "Audit"),
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
    "audit_pdf_download": ("Audit melléklet letöltése", "Download audit appendix"),
    "audit_pdf_region": ("Audit melléklet PDF", "Audit appendix PDF"),
    # Errors from the HTTP boundary and form validation
    "err_key": (
        "A kérés azonosítója érvénytelen. Készítsen új kérést.",
        "The request key is invalid. Prepare a new request.",
    ),
    "err_token": (
        "A szerver hozzáférése nincs beállítva (szolgáltatási token).",
        "Server access is not configured (service token).",
    ),
    "err_rejected": ("A szerver elutasította a hozzáférést.", "The server rejected access."),
    "err_base_missing": (
        "Az alapügy nem található. Nyissa meg újra.",
        "The base case was not found. Open it again.",
    ),
    "err_key_conflict": (
        "Mentési ütközés: ez a kérésazonosító más adatokhoz tartozik. A pontos kérést az "
        "Audit nézetből másolhatja.",
        "Save conflict: this request key belongs to different inputs. Copy the exact request "
        "from Audit.",
    ),
    "err_rejected_inputs": (
        "A szerver elutasította a bemeneteket: a mennyiség, a feltételek vagy a modell nem "
        "illeszkedik.",
        "The server rejected the inputs: quantity, terms or model do not fit.",
    ),
    "err_too_large": ("A kérés túl nagy.", "The request is too large."),
    "err_history_insufficient": (
        "Legalább egy szállítónak háromnál kevesebb lezárt beszerzési sora van az Odoo-ban. "
        "Nem mentettünk ügyet.",
        "At least one supplier has fewer than three settled purchase lines in Odoo. No case "
        "was saved.",
    ),
    "err_history_unavailable": (
        "Az Odoo-előzmény hiányzik vagy nem elérhető. Nem mentettünk ügyet.",
        "Odoo history is missing or unavailable. No case was saved.",
    ),
    "err_history_model": (
        "A mentett modell nem érhető el vagy nem illik ehhez az előzményhez. Nem mentettünk ügyet.",
        "The saved model is unavailable or does not fit this history. No case was saved.",
    ),
    "err_odoo_changed": (
        "Az Odoo-ajánlatok megváltoztak az áttekintés óta. Töltse be újra a csoportot.",
        "Odoo quotations changed since the review. Reload the group.",
    ),
    "err_decision_conflict": (
        "Döntési ütközés: az ügyhöz már tartozhat rögzített döntés. Nyissa meg a rögzített "
        "döntést; ne hagyja jóvá újra.",
        "Decision conflict: this case may already have a recorded decision. Reopen it; do not "
        "approve again.",
    ),
    "err_decision_rejected": (
        "A szerver elutasította a döntést. Ellenőrizze a tervet, a nevet és az indoklást.",
        "The server rejected the decision. Check the plan, name and reason.",
    ),
    "err_uncertain": (
        "Nem biztos, hogy a mentés megtörtént. Ismételje meg ugyanazt a kérést; ne hozzon "
        "létre újat.",
        "The save is unconfirmed. Retry the same request; do not create a new one.",
    ),
    "err_case_id": ("Érvénytelen ügyazonosító.", "Invalid case identifier."),
    "err_case_missing": ("Az ügy nem található.", "This case was not found."),
    "err_case_unavailable": (
        "Az ügy most nem tölthető be. Próbálja újra; a megnyitás semmit nem számol újra.",
        "The case cannot be loaded right now. Retry; opening never recalculates.",
    ),
    "err_case_invalid": (
        "A szerver hiányos vagy nem támogatott ügyadatot adott.",
        "The server returned incomplete or unsupported case data.",
    ),
    "err_library": (
        "A mentett ügyek nem érhetők el. Próbálja újra.",
        "Saved cases are unavailable. Retry.",
    ),
    "err_library_data": (
        "A mentett ügyek adatai nem ellenőrizhetők.",
        "Saved case data could not be verified.",
    ),
    "err_groups": (
        "A nyitott ajánlatkérések nem érhetők el. Ellenőrizze az Odoo-kapcsolatot.",
        "Open RFQs are unavailable. Check the Odoo connection.",
    ),
    "err_groups_data": (
        "Az ajánlatkérések listája nem ellenőrizhető. Frissítsen.",
        "The RFQ listing could not be verified. Refresh.",
    ),
    "err_preview": (
        "Az Odoo-előzmény nem érhető el. Próbálja újra.",
        "Odoo history is unavailable. Retry.",
    ),
    "err_preview_data": (
        "Az Odoo-előzmény előnézete nem ellenőrizhető. Töltse be újra.",
        "The Odoo history preview could not be verified. Reload it.",
    ),
    "err_preview_incomplete": (
        "Az előnézet hiányos. Töltse be újra az ügy létrehozása előtt.",
        "The preview is incomplete. Reload it before creating a case.",
    ),
    "err_model_unavailable": (
        "Az előzmény elérhető, de a hozzá illő modell nem. Ügy nem hozható létre.",
        "History is available, but a compatible model is not. A case cannot be created.",
    ),
    "err_suppliers": (
        "A szállítói áttekintés nem érhető el. A terv adatai ettől még érvényesek.",
        "The supplier overview is unavailable. The plan data stays valid.",
    ),
    "err_pdf": (
        "A PDF most nem érhető el. A jóváhagyás mentve van; próbálja újra. Ne hagyja jóvá újra.",
        "The PDF is unavailable right now. The approval is saved; retry. Do not approve again.",
    ),
    "err_pdf_not_approved": (
        "Csak jóváhagyott alapügyhöz van PDF.",
        "Only an approved base case has a PDF.",
    ),
    "err_original": ("Az alapügy adatai nem érhetők el.", "The base case data is unavailable."),
    "err_choose_group": ("Válasszon nyitott ajánlatkérést.", "Choose an open RFQ."),
    "err_load_group": ("Előbb töltse be az ajánlatkérést.", "Load the RFQ first."),
    "err_fix_fields": ("Javítsa a jelölt mezőket.", "Fix the highlighted fields."),
    "err_quantity": (
        "Adjon meg 1 és 1000 közötti egész számot.",
        "Enter a whole number from 1 to 1,000.",
    ),
    "err_capacity": (
        "Adjon meg 0 és 1000 közötti egész számot.",
        "Enter a whole number from 0 to 1,000.",
    ),
    "err_moq": (
        "Hagyja üresen, vagy adjon meg 1 és 1000 közötti egész számot.",
        "Leave blank, or enter a whole number from 1 to 1,000.",
    ),
    "err_range": (
        "Adjon meg 1 és 1000 közötti egész számokat; az alsó határ nem lehet nagyobb a felsőnél.",
        "Enter whole numbers from 1 to 1,000; the lower bound cannot exceed the upper bound.",
    ),
    "err_date": ("Adjon meg érvényes dátumot.", "Enter a valid date."),
    "err_date_past": (
        "A szükséges dátum nem lehet a múltban.",
        "The required date cannot be in the past.",
    ),
    "err_date_now_past": (
        "A szükséges dátum időközben elmúlt. Módosítsa a feltételeket.",
        "The required date has passed. Edit the terms.",
    ),
    "err_review_changed": (
        "Az áttekintett ügy megváltozott. Nézze át újra a döntést.",
        "The reviewed case changed. Review the decision again.",
    ),
    "err_decide_base": (
        "Csak döntés nélküli alapügyről lehet dönteni.",
        "Only an undecided base case can be decided.",
    ),
    "err_choose_plan": (
        "Válasszon tervet, vagy jelölje, hogy most nem rendel.",
        "Choose a plan or No award.",
    ),
    "err_actor": ("Adja meg a nevét (1–255 karakter).", "Enter your name (1–255 characters)."),
    "err_ack": (
        "Erősítse meg, hogy bemutató adatokkal dolgozik.",
        "Confirm that you are working with demonstration data.",
    ),
    "err_scenario_load": ("Előbb nyisson meg egy ügyet.", "Open a case first."),
    "err_scenario_kind": ("Válasszon forgatókönyv-típust.", "Choose a scenario type."),
    "err_scenario_supplier": (
        "Válassza ki a módosítandó szállítót.",
        "Choose the supplier to change.",
    ),
    "err_scenario_demand_same": (
        "Az új igény nem lehet azonos az eredetivel ({quantity} {unit}).",
        "The new demand must differ from the original {quantity} {unit}.",
    ),
    "err_scenario_capacity_same": (
        "{name}: az új kapacitás nem lehet azonos az eredetivel ({capacity} {unit}). "
        "A 0 megszünteti.",
        "{name}: capacity must differ from its original {capacity} {unit}. Zero removes it.",
    ),
    "err_scenario_price": (
        "{name}: adjon meg pozitív, az eredeti {price} egységártól eltérő árat (pl. 12,50).",
        "{name}: enter a positive price different from the original {price} per unit "
        "(for example 12.50).",
    ),
    "err_scenario_combined": (
        "Kombinált változáshoz legalább két változás kell (igény, kapacitás vagy ár).",
        "Combined changes need at least two changes (demand, capacity or price).",
    ),
    "err_scenario_fields": (
        "Ellenőrizze a forgatókönyv mezőit és a szállítót.",
        "Check the scenario fields and the supplier.",
    ),
    "err_no_decision_record": (
        "Nem érkezett rögzített döntés. Őrizze meg a helyreállítási adatokat, és ne hagyja "
        "jóvá újra.",
        "No recorded decision was returned. Keep the recovery record and do not approve again.",
    ),
    "err_base_scenarios": (
        "A mentett forgatókönyvek most nem érhetők el. Próbálja újra.",
        "Saved scenarios are unavailable right now. Please retry.",
    ),
    "err_reason": (
        "Röviden indokolja meg a döntését (1–2000 karakter).",
        "Briefly explain your decision (1–2,000 characters).",
    ),
    # Notices
    "notice_saved": (
        "Az összehasonlítás mentve. A jóváhagyás külön lépés.",
        "Comparison saved. Approval is a separate step.",
    ),
    "notice_decided": ("A döntés rögzítve.", "Decision recorded."),
    "notice_reopened": (
        "A rögzített döntést újra megnyitottuk.",
        "The recorded decision was reopened.",
    ),
}
