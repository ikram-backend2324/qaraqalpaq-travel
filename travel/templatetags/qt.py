from django import template

register = template.Library()


@register.filter
def tr(obj, arg):
    """{{ obj|tr:"name,qq" }} -> obj.name_qq (falls back to English)."""
    field, lang = arg.split(",")
    return obj.tr(field, lang)


@register.filter
def tget(t, key):
    return t.get(key, key)


@register.filter
def prefixed(key, prefix):
    return f"{prefix}{key}"


@register.filter
def stars(r):
    try:
        return f"★ {float(r):.1f}"
    except (TypeError, ValueError):
        return ""
