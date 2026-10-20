"""Hungarian-first workflow copy; English keys and complete bilingual pairs."""

REVAMP_TEXT: dict[str, tuple[str, str]] = {
    "err_reason": (
        "Röviden indokolja meg a döntését (1–2000 karakter).",
        "Briefly explain your decision (1–2,000 characters).",
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
    "prepare_title": (
        "Beszerzés előkészítése",
        "Prepare your procurement",
    ),
    "prepare_subtitle": (
        "Ellenőrizze az igényt és a beszállítói feltételeket, majd készítse el a terveket.",
        "Check your demand and supplier terms, then create the plans.",
    ),
    "nav_home": (
        "Kezdőlap",
        "Home",
    ),
    "nav_rfqs": (
        "Új beszerzés",
        "New procurement",
    ),
    "home_title": (
        "Átlátható beszerzés. Megalapozott döntés.",
        "Clear procurement. Informed decisions.",
    ),
    "home_intro": (
        "Indítson új összehasonlítást az Odoo ajánlataiból, vagy folytassa egy mentett ügy "
        "értékelését.",
        "Start a comparison from Odoo quotations or continue evaluating a saved case.",
    ),
    "new_procurement": (
        "Új beszerzési döntés",
        "New procurement decision",
    ),
    "continue_case": (
        "Ügy folytatása",
        "Continue case",
    ),
    "all_cases": (
        "Összes ügy megnyitása",
        "Browse all cases",
    ),
    "home_pending": (
        "Döntésre váró ügyek",
        "Awaiting your decision",
    ),
    "home_recent": (
        "Legutóbb mentett ügyek",
        "Recently saved cases",
    ),
    "home_pending_empty": (
        "Nincs döntésre váró mentett ügy. Új összehasonlítást az Odoo ajánlataiból indíthat.",
        "No saved cases await a decision. Start a new comparison from Odoo quotations.",
    ),
    "home_recent_empty": (
        "Még nincs mentett ügy. Az első terv elkészítése után itt folytathatja a munkát.",
        "No saved cases yet. Your first saved plan will appear here.",
    ),
    "home_scope": (
        "Listánként a legutóbbi legfeljebb öt ügy látható. A mentett tervek megtekintése "
        "nem kér új adatokat az Odoo-ból.",
        "Each list shows up to five recent cases. Viewing saved plans does not request new "
        "Odoo data.",
    ),
    "home_source_title": (
        "1. Ellenőrizze az adatokat",
        "1. Check the inputs",
    ),
    "home_source_body": (
        "Odoo-ajánlatok és beszerzői feltételek.",
        "Odoo quotations and buyer-supplied terms.",
    ),
    "home_compare_title": (
        "2. Mérlegelje a terveket",
        "2. Compare the plans",
    ),
    "home_compare_body": (
        "Költség, kitettség és beszállítói megosztás.",
        "Cost, exposure and supplier allocation.",
    ),
    "home_decide_title": (
        "3. Rögzítse a döntését",
        "3. Record your decision",
    ),
    "home_decide_body": (
        "Jóváhagyás után letölthető PDF-javaslat.",
        "Download a proposal PDF after approval.",
    ),
    "step_source": (
        "Ajánlatok",
        "Quotations",
    ),
    "step_demand": (
        "Igény",
        "Demand",
    ),
    "step_terms": (
        "Feltételek",
        "Supplier terms",
    ),
    "step_review": (
        "Ellenőrzés",
        "Review",
    ),
    "creation_progress": (
        "Beszerzés előkészítésének lépései",
        "Procurement preparation steps",
    ),
    "source_odoo": (
        "Odoo-ból beolvasva",
        "Read from Odoo",
    ),
    "source_buyer": (
        "Beszerző által megadva",
        "Buyer supplied",
    ),
    "source_suggested": (
        "Javasolt érték",
        "Suggested value",
    ),
    "source_explainer_title": (
        "Honnan jönnek az ajánlatok?",
        "Where do these quotations come from?",
    ),
    "source_explainer_body": (
        "Az Odoo-ban már összekapcsolt ajánlatkéréseket mutatjuk, csoportonként. Egy "
        "csoport egy termék beszállítói ajánlatait fogja össze. Az árakat és előzményeket "
        "beolvassuk; az igényt és a kiegészítő feltételeket Ön ellenőrzi.",
        "These groups contain requests for quotation already linked in Odoo. Each group "
        "brings together supplier quotations for one product. We read prices and history; "
        "you review the demand and supplemental terms.",
    ),
    "rfqs_title": (
        "Odoo-ajánlatok kiválasztása",
        "Choose Odoo quotations",
    ),
    "rfqs_subtitle": (
        "Válasszon ajánlatcsoportot a beszerzési döntés előkészítéséhez.",
        "Choose a quotation group to prepare a procurement decision.",
    ),
    "quotation_details": (
        "A csoport ajánlatai",
        "Quotations in this group",
    ),
    "quotation_reference": (
        "Odoo-hivatkozás",
        "Odoo reference",
    ),
    "quotation_quantity": (
        "Ajánlati mennyiség",
        "Quoted quantity",
    ),
    "quotation_state": (
        "Odoo-állapot",
        "Odoo status",
    ),
    "quotation_draft": (
        "Piszkozat",
        "Draft",
    ),
    "quotation_sent": (
        "Elküldve",
        "Sent",
    ),
    "quotation_other": (
        "Egyéb állapot",
        "Other status",
    ),
    "quotation_quantity_note": (
        "Az ajánlati mennyiség nem a jóváhagyott beszerzési igény. A szükséges mennyiséget "
        "a következő lépésben adja meg.",
        "Quoted quantities are not approved demand. Enter the required quantity in the next step.",
    ),
    "choose_group": (
        "Ajánlatok megtekintése",
        "View quotations",
    ),
    "selected_group": (
        "Kiválasztott ajánlatcsoport",
        "Selected quotation group",
    ),
    "start_comparison": (
        "Igény megadása",
        "Set demand",
    ),
    "change_group": (
        "Másik ajánlatcsoport",
        "Change quotation group",
    ),
    "groups_updated": (
        "Ajánlatok lekérve:",
        "Quotations retrieved:",
    ),
    "group_company": (
        "Vállalati hatókör:",
        "Company scope:",
    ),
    "continue_terms": (
        "Tovább a beszállítói feltételekhez",
        "Continue to supplier terms",
    ),
    "back_demand": (
        "Vissza az igényhez",
        "Back to demand",
    ),
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
        "Ezek az alkalmazás megjelenített alapszabályai. A költségkeret az olcsóbb tervhez "
        "képest megengedett többlet, amelyen belül kisebb kitettségű alternatívát keresünk.",
        "These are the application's displayed default rules. The cost allowance is the "
        "permitted premium over the cheapest plan when searching for a lower-exposure "
        "alternative.",
    ),
    "draft_session_note": (
        "Az előkészítés még nincs mentve. A lépések között visszaléphet; az oldal "
        "újratöltésekor a beírt adatok elveszhetnek.",
        "Preparation is not saved yet. You can move between steps; reloading the page may "
        "lose your inputs.",
    ),
    "review_terms": (
        "Feltételek áttekintése",
        "Review terms",
    ),
    "calculate_save": (
        "Tervek elkészítése és mentése",
        "Calculate and save plans",
    ),
    "review_body": (
        "Ellenőrizze az igényt, a beszállítói feltételeket és az adatforrásokat. A "
        "tervkészítés elmenti az összehasonlítást; a jóváhagyás külön lépés.",
        "Check demand, supplier terms and sources. Calculating plans saves the comparison; "
        "approval is a separate step.",
    ),
    "review_sources": (
        "A javaslaton maradt értékeket külön jelöljük. Az ár Odoo-adat; az itt ellenőrzött "
        "feltételek beszerzői bemenetek.",
        "Unchanged suggestions are marked. Prices come from Odoo; the terms reviewed here "
        "are buyer inputs.",
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
    "tab_scenarios": (
        "Mi történne, ha…?",
        "What if…?",
    ),
    "scenario_optional": (
        "Választható vizsgálat: az alapügy változatlan marad. A módosított ár "
        "feltételezés, nem új Odoo-ajánlat.",
        "Optional analysis: the base case stays unchanged. A modified price is an "
        "assumption, not a new Odoo quotation.",
    ),
    "exposure_explained": (
        "A kitettség a beszállítói értékelések mennyiséggel súlyozott jelzőszáma. Kisebb "
        "érték kisebb modellezett kitettséget jelent, nem garantált szállítást vagy "
        "hibavalószínűséget.",
        "Exposure is the quantity-weighted supplier evaluation score. A lower value "
        "indicates lower modelled exposure, not guaranteed delivery or failure probability.",
    ),
    "review_selection": (
        "Kiválasztás áttekintése",
        "Review selection",
    ),
    "show_history": (
        "Beszállítói előzmények megtekintése",
        "View supplier history",
    ),
    "allocation_details": (
        "Rendelési mennyiségek összevetése",
        "Compare allocated quantities",
    ),
    "suggested_terms": (
        "Javaslaton maradt értékek",
        "Unchanged suggested values",
    ),
}
