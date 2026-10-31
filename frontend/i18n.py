"""UI texts (English keys, Hungarian default) and locale-aware formatting; no Reflex imports."""

from datetime import date, datetime
from decimal import Decimal

LANGUAGES = ("hu", "en")
DEFAULT_LANGUAGE = "hu"

_MONTHS = {
    "hu": (
        "jan.",
        "febr.",
        "márc.",
        "ápr.",
        "máj.",
        "jún.",
        "júl.",
        "aug.",
        "szept.",
        "okt.",
        "nov.",
        "dec.",
    ),
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
}
_SYMBOLS = {"HUF": "Ft", "EUR": "€", "USD": "$", "GBP": "£"}
# Odoo unit names the buyer reads every day; anything else is shown as Odoo names it.
_UNITS = {
    "Units": ("db", "pcs"),
    "Unit": ("db", "pcs"),
    "piece": ("db", "pcs"),
    "kg": ("kg", "kg"),
}


def language(value) -> str:
    return value if value in LANGUAGES else DEFAULT_LANGUAGE


def _group(text: str, lang: str) -> str:
    sign = "-" if text.startswith("-") else ""
    whole, _, fraction = text.lstrip("+-").partition(".")
    separator = " " if lang == "hu" else ","
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    grouped = separator.join([whole, *groups])
    if fraction:
        grouped += ("," if lang == "hu" else ".") + fraction
    return sign + grouped


def number(value, lang: str, digits: int | None = None) -> str:
    """Grouped number; ``digits`` rounds for display, otherwise stored digits are kept."""
    amount = Decimal(str(value))
    text = f"{amount:.{digits}f}" if digits is not None else f"{amount:f}"
    return _group(text, language(lang))


def money(value, currency: str, lang: str, *, signed: bool = False) -> str:
    """Amount with at least two decimals and never fewer than the stored digits."""
    lang = language(lang)
    amount = Decimal(str(value))
    # Pad to two decimals but never round stored digits (no quantize: it fails on long values).
    # Read the stored exponent: normalize() rounds to the context precision first.
    exponent = amount.as_tuple().exponent
    text = f"{amount:.2f}" if isinstance(exponent, int) and exponent >= -2 else f"{amount:f}"
    grouped = _group(text, lang)
    sign = ""
    if signed and amount > 0:
        sign = "+"
    if grouped.startswith("-"):
        sign, grouped = "−", grouped[1:]
    symbol = _SYMBOLS.get(currency, currency)
    if lang == "en":
        # English: €/$/£ before the amount, otherwise the ISO code after it (1,545.70 HUF).
        if symbol in ("€", "$", "£"):
            return f"{sign}{symbol}{grouped}"
        return f"{sign}{grouped} {currency}"
    return f"{sign}{grouped} {symbol}"


def percent(ratio, lang: str, digits: int = 1) -> str:
    text = number(Decimal(str(ratio)) * 100, lang, digits)
    return text + (" %" if language(lang) == "hu" else "%")


def day(value, lang: str) -> str:
    """ISO date or datetime as a buyer-readable date."""
    parsed = value if isinstance(value, date) else datetime.fromisoformat(str(value)[:10]).date()
    month = _MONTHS[language(lang)][parsed.month - 1]
    if language(lang) == "hu":
        return f"{parsed.year}. {month} {parsed.day}."
    return f"{parsed.day} {month} {parsed.year}"


def moment(value, lang: str) -> str:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return f"{day(parsed.date(), lang)} {parsed.hour:02d}:{parsed.minute:02d} UTC"


def unit(name: str, lang: str) -> str:
    pair = _UNITS.get(name)
    return name if pair is None else pair[0 if language(lang) == "hu" else 1]


def tr(key: str, lang: str, **values) -> str:
    hu, en = TEXT[key]
    text = hu if language(lang) == "hu" else en
    return text.format(**values) if values else text


# Natural Hungarian procurement wording first, then English. Keys are English and stable.
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
    # Common
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
    "demo_supplier": ("Bemutató szállító {n}", "Demo supplier {n}"),
    "group_n": ("{n}. csoport", "Group {n}"),
    "badge_generated": ("Generált adat", "Generated data"),
    "badge_synthetic": ("Bemutató adat", "Demo data"),
    "badge_scenario": ("Forgatókönyv", "Scenario"),
    "generated_note": (
        "A szállítói előzmények ebben a tesztadatbázisban generáltak, nem valós teljesítmény.",
        "Supplier history in this test database is generated, not real performance.",
    ),
    "synthetic_note": (
        "Bemutató eset: a szállítói értékelés szintetikus modellből származik.",
        "Demo case: supplier assessments come from a synthetic model.",
    ),
    # Statuses
    "status_optimal": ("Tervek elkészültek", "Plans ready"),
    "status_infeasible": ("Nincs megvalósítható terv", "No feasible plan"),
    "status_no_proven_optimum": ("Nincs igazolt optimum", "No proven optimum"),
    "status_solver_error": ("A megoldó nem érhető el", "Solver unavailable"),
    "status_invalid_input": ("Elutasított bemenet", "Input rejected"),
    "decision_draft": ("Döntésre vár", "Awaiting decision"),
    "decision_approved": ("Jóváhagyva", "Approved"),
    "decision_no_award": ("Nem rendelünk", "No award"),
    "decision_scenario": ("Forgatókönyv – döntés az alapügyön", "Scenario – decide on the base"),
    # Plans
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
    # Buyer explanations of solver notes
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
    # Supplier assessment
    "class_regular": ("rendben", "regular"),
    "class_problematic": ("problémás", "problematic"),
    "class_schedule_regular": ("rendben", "regular"),
    "class_schedule_watch": ("figyelendő", "watch"),
    "history_summary": (
        "{on_time} határidőre · átlagos késés {late} · teljesítési arány {fill} · "
        "{lines} lezárt sor",
        "{on_time} on time · average lateness {late} · fill rate {fill} · {lines} settled lines",
    ),
    "days": ("{value} nap", "{value} days"),
    "class_meaning_history": (
        "„Problémás”: a következő 60 napban az átlagos késés 3 napnál több, vagy a "
        "teljesítési arány 85 % alatti.",
        "“Problematic”: in the next 60 days the average delay exceeds 3 days or the fill "
        "rate is below 85%.",
    ),
    "class_meaning_synthetic": (
        "Szintetikus tanítócímke: az öt jövőbeli átvételből legalább kettő késik.",
        "Synthetic training label: at least two of five future receipts are late.",
    ),
    "path_root": (
        "A döntési fa a gyökérben dönt; nincs elágazási feltétel.",
        "The tree decides at its root; there are no branch conditions.",
    ),
    # Scenarios
    "kind_supplier_outage": ("Szállító kiesése", "Supplier outage"),
    "kind_capacity_change": ("Kapacitásváltozás", "Capacity change"),
    "kind_demand_change": ("Igényváltozás", "Demand change"),
    "kind_price_change": ("Árváltozás", "Price change"),
    "kind_combined": ("Kombinált változás", "Combined changes"),
    "kind_capacity_reduction": ("Kapacitáscsökkenés", "Capacity reduction"),
    "kind_demand_increase": ("Igénynövekedés", "Demand increase"),
    "kind_price_increase": ("Áremelkedés", "Price increase"),
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
    "history_summary_synthetic": (
        "{on_time} határidőre, {receipts} teljesített átvétel alapján",
        "{on_time} on time across {receipts} completed receipts",
    ),
    "state_conflict": (
        "Döntési ütközés – nyissa meg a rögzített döntést",
        "Decision conflict – reopen the recorded decision",
    ),
    "state_saving": ("Mentés folyamatban…", "Saving…"),
    "state_unconfirmed": (
        "A mentés nincs visszaigazolva – ismételje meg ugyanazt a kérést",
        "Save unconfirmed – retry the same request",
    ),
    "state_approved": ("Jóváhagyott terv", "Approved plan"),
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
    "metric_outcome": ("Eredmény", "Outcome"),
    "metric_demand": ("Igény", "Demand"),
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
    "captured_at": ("Odoo-adatok kiolvasva: {time} UTC", "Odoo data read at {time} UTC"),
    # Error and recovery texts from the HTTP boundary
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

from frontend.i18n_ui import UI_TEXT  # noqa: E402 - screen texts live in their own module

TEXT.update(UI_TEXT)
