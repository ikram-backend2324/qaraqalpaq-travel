"""AI trip planner via OpenRouter, with a rule-based fallback built from the catalogue."""
import logging
import re

import requests
from django.conf import settings

from .translations import LANG_NAMES_EN

log = logging.getLogger(__name__)
URL = "https://openrouter.ai/api/v1/chat/completions"

GLOSSARY_QQ = (
    "Write in modern Karakalpak Latin alphabet (á, ó, ú, ı, ń, ǵ), never Uzbek or Kazakh spellings "
    "(no o' or g'). Use: day = 'kún', morning = 'tańerteń', evening = 'keshte', night = 'tún', "
    "fortress = 'qala', yurt = 'yurta', guide = 'gid', driver = 'aydawshı', museum = 'muzey', "
    "hour = 'saat', next = 'keyingi'. Keep sentences short and simple."
)

SYSTEM = (
    "You are the travel planner of Qaraqalpaq Travel, a platform for trips in Karakalpakstan (Uzbekistan). "
    "Answer ONLY in {lang}. {rule} Build a realistic day-by-day itinerary using ONLY the places, stays, guides "
    "and drivers listed in the CATALOGUE below (use their exact names and prices in USD). Respect distances: "
    "Nukus to the Ellikqala fortresses is about 2.5-3 hours by car, Nukus to Moynaq about 3-3.5 hours, "
    "the Ustyurt plateau needs a 4x4 and a full day. Format: one line per day starting with the day label, "
    "then 2-4 short bullet lines starting with '• '. End with one line with the estimated total cost. "
    "Plain text only: no markdown, no asterisks, no headings."
)


def ai_enabled():
    return bool(settings.OPENROUTER_API_KEY)


def clean(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?m)^\s*[\*\-]\s+", "• ", text)
    text = re.sub(r"(?m)^#+\s*", "", text)
    return text.replace("**", "").strip()


def _call(messages, max_tokens=900):
    models = [settings.OPENROUTER_MODEL] + [m for m in settings.OPENROUTER_FALLBACK_MODELS if m != settings.OPENROUTER_MODEL]
    last = None
    for model in models:
        try:
            r = requests.post(URL, timeout=60, headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": settings.SITE_URL, "X-Title": "Qaraqalpaq Travel",
            }, json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5})
            if r.status_code == 200:
                text = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                if text.strip():
                    return clean(text), model
            last = f"{model}: HTTP {r.status_code}"
        except Exception as exc:
            last = f"{model}: {exc}"
        log.warning("OpenRouter: %s", last)
    raise RuntimeError(last or "AI unavailable")


def catalogue_text(lang):
    from .models import Place, Service, Stay
    lines = ["PLACES:"]
    for p in Place.objects.all():
        lines.append(f"- {p.tr('name', lang)} ({p.district}): {p.tr('desc', lang)[:160]}")
    lines.append("STAYS:")
    for s in Stay.objects.select_related("near"):
        near = s.near.tr("name", lang) if s.near else ""
        lines.append(f"- {s.name} [{s.kind}] near {near}: ${s.price_usd}/night, up to {s.capacity} guests")
    lines.append("GUIDES & DRIVERS:")
    for v in Service.objects.all():
        extra = f", {v.vehicle}" if v.vehicle else ""
        lines.append(f"- {v.name} ({v.kind}{extra}), based in {v.base}, {v.languages}: ${v.price_usd}/day — {v.tr('spec', lang)}")
    return "\n".join(lines)


def plan(days, interests, budget, lang):
    user = (f"Plan a {days}-day trip. Interests: {', '.join(interests) or 'general'}. Budget level: {budget}. "
            "Start and end in Nukus.")
    if not ai_enabled():
        return rule_plan(days, interests, budget, lang), "rules", True
    try:
        rule = GLOSSARY_QQ if lang == "qq" else ""
        text, model = _call([
            {"role": "system", "content": SYSTEM.format(lang=LANG_NAMES_EN.get(lang, "English"), rule=rule)
             + "\n\nCATALOGUE:\n" + catalogue_text(lang)},
            {"role": "user", "content": user},
        ])
        return text, model, False
    except Exception:
        return rule_plan(days, interests, budget, lang), "rules", True


def rule_plan(days, interests, budget, lang):
    """Deterministic plan from the catalogue (works without the AI key)."""
    from .models import Place, Service, Stay
    from .translations import strings
    t = strings(lang)
    order = []
    if "art" in interests or not interests:
        order.append("savitsky")
    if "history" in interests or not interests:
        order += ["toprak-qala", "ayaz-qala", "chilpyk", "mizdakhan"]
    if "aral" in interests or not interests:
        order.append("moynaq")
    if "nature" in interests:
        order.append("ustyurt")
    order = list(dict.fromkeys(order)) or ["savitsky", "ayaz-qala", "moynaq"]
    places = {p.slug: p for p in Place.objects.all()}
    stays = list(Stay.objects.select_related("near"))
    pick = {"low": min, "mid": lambda xs, key: sorted(xs, key=key)[len(xs) // 2], "high": max}.get(budget, min)
    lines, total = [], 0
    # Short interest list on a long trip: add nearby highlights instead of empty days.
    for extra in ["savitsky", "mizdakhan", "chilpyk", "toprak-qala", "ayaz-qala", "moynaq", "ustyurt"]:
        if len(order) >= days:
            break
        if extra not in order:
            order.append(extra)
    # Group by area so one day never mixes far-apart regions (Nókis / Ellikqala / Moynaq / Ustyurt).
    areas = [["savitsky", "mizdakhan", "chilpyk"], ["toprak-qala", "ayaz-qala"], ["moynaq"], ["ustyurt"]]
    chunks = [[x for x in area if x in order] for area in areas]
    chunks = [c for c in chunks if c]
    # More days than areas: split the biggest area over extra days.
    while len(chunks) < days and any(len(c) > 1 for c in chunks):
        i = max(range(len(chunks)), key=lambda k: len(chunks[k]))
        c = chunks[i]
        chunks[i:i + 1] = [c[:len(c) // 2 + len(c) % 2], c[len(c) // 2 + len(c) % 2:]]
    chunks = chunks[:max(days, 1)]
    while len(chunks) < days:
        chunks.append([])
    drivers = {d.base: d for d in Service.objects.filter(kind="driver")}
    # Which driver base serves which site (closest base first).
    driver_for = {"moynaq": "Moynaq", "ustyurt": "Nókis", "ayaz-qala": "Ellikqala", "toprak-qala": "Ellikqala"}
    last_stay = None
    for d, chunk in enumerate(chunks, 1):
        label = f"{d}-{t['day']}" if lang in ("qq", "uz") else (f"{t['day'].capitalize()} {d}" if lang == "en" else f"День {d}")
        lines.append(label)
        if not chunk:
            lines.append(f"• {t['free_day']}")
        for slug in chunk:
            if slug in places:
                lines.append(f"• {places[slug].tr('name', lang)}")
        if d < days:
            near = [s for s in stays if s.near and s.near.slug in chunk]
            stay = pick(near, key=lambda s: s.price_usd) if near else (last_stay or pick(stays, key=lambda s: s.price_usd))
            last_stay = stay
            lines.append(f"• {stay.name} — ${stay.price_usd}")
            total += stay.price_usd
        bases = [driver_for[s] for s in chunk if s in driver_for]
        if bases:
            drv = drivers.get(bases[-1]) or min(drivers.values(), key=lambda x: x.price_usd, default=None)
            if drv:
                lines.append(f"• {drv.name} ({drv.vehicle}) — ${drv.price_usd}")
                total += drv.price_usd
        lines.append("")
    lines.append(f"{t['total']}: ~${total}")
    return "\n".join(lines).strip()
