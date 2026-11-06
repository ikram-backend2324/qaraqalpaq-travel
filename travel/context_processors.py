from .translations import LANGS, strings


def i18n(request):
    # Query string without "lang", so switching language keeps filters/dates.
    q = request.GET.copy() if hasattr(request, "GET") else None
    if q is not None:
        q.pop("lang", None)
    lang_qs = (q.urlencode() + "&") if q else ""
    lang = getattr(request, "lang", "en")
    cart = request.session.get("cart", {}) if hasattr(request, "session") else {}
    return {"t": strings(lang), "lang": lang, "langs": LANGS, "lang_qs": lang_qs, "cart_count": sum(cart.values()) if cart else 0}
