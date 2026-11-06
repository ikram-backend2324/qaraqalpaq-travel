from .translations import DEFAULT_LANG, LANG_CODES


class LanguageMiddleware:
    """Language from ?lang=xx (saved to session/cookie), else session, else cookie, else default."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get("lang")
        chosen = None
        if lang in LANG_CODES:
            chosen = lang
            request.session["lang"] = lang
        else:
            lang = request.session.get("lang") or request.COOKIES.get("qqt_lang")
            if lang not in LANG_CODES:
                hdr = (request.META.get("HTTP_ACCEPT_LANGUAGE") or "").lower()
                lang = "ru" if hdr.startswith("ru") else ("uz" if hdr.startswith("uz") else DEFAULT_LANG)
        request.lang = lang
        response = self.get_response(request)
        if chosen:
            response.set_cookie("qqt_lang", chosen, max_age=3600 * 24 * 365, samesite="Lax")
        return response

