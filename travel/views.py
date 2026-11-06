from django.db.models import F
from django.http import Http404
from urllib.parse import urlencode
import json
import random
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from . import ai, art
from .models import Booking, Order, PartnerLead, Place, PlanLog, Product, Service, Stay
from .translations import AMENITY_KEYS, strings

SHIPPING_USD = 25


def _parse_date(v):
    try:
        return date.fromisoformat(v)
    except (TypeError, ValueError):
        return None


def _code(prefix, pk):
    return f"{prefix}-{date.today():%y%m}-{pk:04d}"


# ---------------------------------------------------------------- pages

def home(request):
    lang = request.lang
    places = list(Place.objects.all())
    stays = list(Stay.objects.select_related("near"))
    mp = [{"t": "p", "n": p.tr("name", lang), "lat": p.lat, "lon": p.lon, "u": f"/places/{p.slug}/"} for p in places]
    mp += [{"t": "s", "n": s.name, "lat": s.lat, "lon": s.lon, "u": f"/stays/{s.slug}/", "pr": s.price_usd} for s in stays]
    return render(request, "home.html", {
        "nav": "home", "places": places, "featured": sorted(stays, key=lambda s: -s.rating)[:3],
        "map_json": json.dumps(mp, ensure_ascii=False),
        "counts": [len(places), len(stays), Service.objects.count(), Product.objects.count()],
        "today": date.today() + timedelta(days=14), "tomorrow": date.today() + timedelta(days=16),
    })


def stays(request):
    qs = Stay.objects.select_related("near")
    kind = request.GET.get("kind", "")
    near = request.GET.get("near", "")
    maxp = request.GET.get("max", "")
    guests = request.GET.get("guests", "")
    if kind in dict(Stay.KINDS):
        qs = qs.filter(kind=kind)
    if near:
        qs = qs.filter(near__slug=near)
    if maxp.isdigit():
        qs = qs.filter(price_usd__lte=int(maxp))
    if guests.isdigit():
        qs = qs.filter(capacity__gte=int(guests))
    keep = urlencode({k: request.GET[k] for k in ("from", "to", "guests") if request.GET.get(k)})
    return render(request, "stays.html", {"nav": "stays", "stays": qs, "places": Place.objects.all(),
                                          "kind": kind, "near": near, "maxp": maxp, "keep": keep})


def stay_detail(request, slug):
    stay = get_object_or_404(Stay.objects.select_related("near"), slug=slug)
    t = strings(request.lang)
    error = None
    if request.method == "POST":
        d1, d2 = _parse_date(request.POST.get("from")), _parse_date(request.POST.get("to"))
        name = (request.POST.get("name") or "").strip()[:120]
        contact = (request.POST.get("contact") or "").strip()[:160]
        try:
            guests = max(1, min(int(request.POST.get("guests", 2)), stay.capacity))
        except ValueError:
            guests = 2
        if not (d1 and d2 and d2 > d1 and d1 >= date.today() and name and contact and (d2 - d1).days <= 30):
            error = t["form_error"]
        else:
            nights = (d2 - d1).days
            total = nights * stay.price_usd
            extras = []
            for key in ("guide", "driver"):
                sv = Service.objects.filter(slug=request.POST.get(key), kind=key).first()
                if sv:
                    total += nights * sv.price_usd
                    extras.append(sv.name)
            b = Booking.objects.create(stay=stay, name=name, contact=contact, country=(request.POST.get("country") or "")[:80],
                                       date_from=d1, date_to=d2, guests=guests, extras=", ".join(extras), total_usd=total)
            _remember_booking(request, b.pk)
            return redirect(f"/booked/{b.pk}/")
    return render(request, "stay_detail.html", {
        "nav": "stays", "s": stay, "error": error,
        "guides": Service.objects.filter(kind="guide"), "drivers": Service.objects.filter(kind="driver"),
        "d1": request.GET.get("from") or (date.today() + timedelta(days=14)).isoformat(),
        "d2": request.GET.get("to") or (date.today() + timedelta(days=16)).isoformat(),
        "guests": request.GET.get("guests", "2"), "min_date": date.today().isoformat(),
        "svc_prices": json.dumps({s.slug: s.price_usd for s in Service.objects.all()}),
    })


def _remember_booking(request, pk):
    mine = request.session.get("my_bookings", [])
    request.session["my_bookings"] = (mine + [pk])[-20:]


def booked(request, pk):
    # Only the visitor who made the booking can see its details (ids are sequential).
    if pk not in request.session.get("my_bookings", []):
        raise Http404
    b = get_object_or_404(Booking.objects.select_related("stay", "service"), pk=pk)
    return render(request, "booked.html", {"b": b, "code": _code("QT", b.pk), "nights": (b.date_to - b.date_from).days})


def guides(request):
    t = strings(request.lang)
    error = None
    if request.method == "POST":
        sv = Service.objects.filter(slug=request.POST.get("service")).first()
        d1 = _parse_date(request.POST.get("from"))
        try:
            days = max(1, min(int(request.POST.get("days", 1)), 14))
        except ValueError:
            days = 1
        name = (request.POST.get("name") or "").strip()[:120]
        contact = (request.POST.get("contact") or "").strip()[:160]
        if sv and d1 and d1 >= date.today() and name and contact:
            b = Booking.objects.create(service=sv, name=name, contact=contact, date_from=d1, date_to=d1 + timedelta(days=days),
                                       guests=1, total_usd=days * sv.price_usd)
            _remember_booking(request, b.pk)
            return redirect(f"/booked/{b.pk}/")
        error = t["form_error"]
    return render(request, "guides.html", {"nav": "guides", "guides": Service.objects.filter(kind="guide"),
                                           "drivers": Service.objects.filter(kind="driver"), "error": error,
                                           "d1": (date.today() + timedelta(days=14)).isoformat(), "min_date": date.today().isoformat()})


def places(request):
    return render(request, "places.html", {"nav": "places", "places": Place.objects.all()})


def place_detail(request, slug):
    p = get_object_or_404(Place, slug=slug)
    return render(request, "place_detail.html", {"nav": "places", "p": p, "stays": Stay.objects.filter(near=p)})


def ar_view(request, slug):
    p = get_object_or_404(Place, slug=slug)
    scene = p.ar_scene or "fortress"
    return render(request, "ar.html", {"nav": "places", "p": p, "scene": scene})


def craft(request):
    cat = request.GET.get("cat", "")
    qs = Product.objects.all()
    if cat in dict(Product.CATS):
        qs = qs.filter(category=cat)
    return render(request, "craft.html", {"nav": "craft", "products": qs, "cat": cat, "cats": [c for c, _ in Product.CATS]})


def product_detail(request, slug):
    p = get_object_or_404(Product, slug=slug)
    return render(request, "product_detail.html", {"nav": "craft", "p": p,
                                                   "more": Product.objects.filter(category=p.category).exclude(pk=p.pk)[:3]})


def _cart(request):
    return {k: v for k, v in request.session.get("cart", {}).items() if v > 0}


@require_POST
def cart_add(request, slug):
    p = get_object_or_404(Product, slug=slug)
    cart = _cart(request)
    if p.stock > 0:
        cart[p.slug] = min(cart.get(p.slug, 0) + 1, p.stock)
    request.session["cart"] = cart
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"count": sum(cart.values())})
    return redirect("/cart/")


@require_POST
def cart_remove(request, slug):
    cart = _cart(request)
    cart.pop(slug, None)
    request.session["cart"] = cart
    return redirect("/cart/")


def cart_view(request):
    t = strings(request.lang)
    cart = _cart(request)
    items = []
    for p in Product.objects.filter(slug__in=cart.keys()):
        qty = min(cart[p.slug], p.stock)
        if qty > 0:
            items.append({"p": p, "qty": qty, "sum": qty * p.price_usd})
    subtotal = sum(i["sum"] for i in items)
    total = subtotal + (SHIPPING_USD if items else 0)
    error = None
    if request.method == "POST" and items:
        name = (request.POST.get("name") or "").strip()[:120]
        contact = (request.POST.get("contact") or "").strip()[:160]
        country = (request.POST.get("country") or "").strip()[:80]
        if name and contact and country:
            o = Order.objects.create(name=name, contact=contact, country=country, total_usd=total,
                                     items=[{"slug": i["p"].slug, "name": i["p"].name_en, "qty": i["qty"], "price": i["p"].price_usd} for i in items])
            for i in items:  # keep stock in sync with sold items
                Product.objects.filter(pk=i["p"].pk).update(stock=F("stock") - i["qty"])
            request.session["cart"] = {}
            return render(request, "ordered.html", {"o": o, "code": _code("EC", o.pk)})
        error = t["form_error"]
    return render(request, "cart.html", {"items": items, "subtotal": subtotal, "shipping": SHIPPING_USD, "total": total, "error": error})


def planner(request):
    return render(request, "planner.html", {"nav": "planner", "ai_on": ai.ai_enabled()})


@require_POST
def api_plan(request):
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        body = {}
    lang = body.get("lang") if body.get("lang") in ("qq", "uz", "ru", "en") else request.lang
    try:
        days = max(1, min(int(body.get("days", 3)), 7))
    except (TypeError, ValueError):
        days = 3
    interests = [i for i in body.get("interests", []) if i in ("history", "aral", "nature", "art")]
    budget = body.get("budget") if body.get("budget") in ("low", "mid", "high") else "mid"
    text, model, fallback = ai.plan(days, interests, budget, lang)
    PlanLog.objects.create(lang=lang, request=json.dumps({"days": days, "interests": interests, "budget": budget}), answer=text, model_used=model)
    return JsonResponse({"plan": text, "model": model, "fallback": fallback})


def partner(request):
    sent = False
    error = None
    if request.method == "POST":
        kind = request.POST.get("kind")
        name = (request.POST.get("name") or "").strip()[:120]
        contact = (request.POST.get("contact") or "").strip()[:160]
        loc = (request.POST.get("location") or "").strip()[:120]
        if kind in dict(PartnerLead.KINDS) and name and contact and loc:
            PartnerLead.objects.create(kind=kind, name=name, contact=contact, location=loc, note=(request.POST.get("note") or "")[:400])
            return redirect("/partner/?sent=1")
        error = strings(request.lang)["form_error"]
    sent = request.GET.get("sent") == "1"
    return render(request, "partner.html", {"nav": "partner", "sent": sent, "error": error})


def _mask(name):
    return (name[:1] + "***") if name else "—"


def dashboard(request):
    b_total = Booking.objects.aggregate(s=Sum("total_usd"))["s"] or 0
    o_total = Order.objects.aggregate(s=Sum("total_usd"))["s"] or 0
    gmv = b_total + o_total
    recent = []
    for b in Booking.objects.select_related("stay", "service")[:8]:
        recent.append({"when": b.created_at, "kind": "booking", "who": _mask(b.name),
                       "what": b.stay.name if b.stay else (b.service.name if b.service else ""), "usd": b.total_usd})
    for o in Order.objects.all()[:8]:
        recent.append({"when": o.created_at, "kind": "order", "who": _mask(o.name), "what": f"{len(o.items)} × EthnoCraft · {o.country}", "usd": o.total_usd})
    recent.sort(key=lambda r: r["when"], reverse=True)
    top = Stay.objects.annotate(n=Count("bookings")).order_by("-n")[:5]
    return render(request, "dashboard.html", {
        "nav": "dashboard", "bookings": Booking.objects.count(), "orders": Order.objects.count(),
        "gmv": gmv, "rev": round(gmv * settings.COMMISSION_RATE), "leads": PartnerLead.objects.count(),
        "recent": recent[:10], "top": top,
    })


def about(request):
    return render(request, "about.html", {"nav": "about"})


# ---------------------------------------------------------------- images & API

def _svg(body):
    r = HttpResponse(body, content_type="image/svg+xml")
    r["Cache-Control"] = "public, max-age=86400"
    return r


@cache_page(3600)
def img_stay(request, slug):
    s = get_object_or_404(Stay, slug=slug)
    return _svg(art.stay_svg(s.kind, s.palette))


@cache_page(3600)
def img_place(request, slug):
    p = get_object_or_404(Place, slug=slug)
    return _svg(art.place_svg(p.kind, p.order))


@cache_page(3600)
def img_product(request, slug):
    p = get_object_or_404(Product, slug=slug)
    return _svg(art.product_svg(p.category, p.palette))


@cache_page(3600)
def img_hero(request):
    return _svg(art.stay_svg("yurt", 5, 1600, 800))


def img_ar(request, scene, layer):
    if scene not in ("fortress", "aral") or layer not in ("past", "bg"):
        return HttpResponse(status=404)
    return _svg(art.ar_layer(scene, layer))


def api_stays(request):
    lang = request.GET.get("lang", request.lang)
    return JsonResponse({"stays": [{"slug": s.slug, "name": s.name, "kind": s.kind, "price_usd": s.price_usd, "rating": s.rating,
                                    "near": s.near.tr("name", lang) if s.near else None, "lat": s.lat, "lon": s.lon}
                                   for s in Stay.objects.select_related("near")]}, json_dumps_params={"ensure_ascii": False})


def api_health(request):
    return JsonResponse({"ok": True, "ai": ai.ai_enabled(), "places": Place.objects.count(), "stays": Stay.objects.count()})
