from datetime import date, timedelta

from django.test import TestCase

from .models import Booking, Order
from .seed_data import seed


class Flows(TestCase):
    def setUp(self):
        seed()

    def test_pages(self):
        for lang in ("qq", "uz", "ru", "en"):
            for url in ("/", "/stays/", "/stays/topiraq-glamp/", "/guides/", "/places/", "/places/moynaq/",
                        "/ar/ayaz-qala/", "/ar/moynaq/", "/craft/", "/craft/kumis-bilezik/", "/cart/",
                        "/planner/", "/partner/", "/dashboard/", "/about/"):
                self.assertEqual(self.client.get(f"{url}?lang={lang}").status_code, 200, url)

    def test_booking_total(self):
        d1, d2 = date.today() + timedelta(days=5), date.today() + timedelta(days=8)
        r = self.client.post("/stays/qizilqum-juldizlari/", {"from": d1, "to": d2, "guests": 2, "guide": "guide-aziz",
                                                             "driver": "", "name": "A", "contact": "a@b.c"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Booking.objects.get().total_usd, 3 * (45 + 40))

    def test_bad_dates(self):
        d = date.today() + timedelta(days=5)
        r = self.client.post("/stays/qizilqum-juldizlari/", {"from": d, "to": d, "name": "A", "contact": "x"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_cart_order(self):
        self.client.post("/cart/add/kumis-bilezik/")
        self.client.post("/cart/add/kumis-bilezik/")
        self.client.post("/cart/", {"name": "B", "contact": "c", "country": "Japan"})
        self.assertEqual(Order.objects.get().total_usd, 2 * 90 + 25)

    def test_plan_fallback(self):
        r = self.client.post("/api/plan/", {"days": 2, "interests": ["aral"], "budget": "low", "lang": "qq"},
                             content_type="application/json")
        self.assertIn("kún", r.json()["plan"])

    def test_booked_page_private(self):
        d1, d2 = date.today() + timedelta(days=5), date.today() + timedelta(days=7)
        r = self.client.post("/stays/qizilqum-juldizlari/", {"from": d1, "to": d2, "guests": 2, "name": "A", "contact": "a@b.c"})
        self.assertEqual(self.client.get(r["Location"]).status_code, 200)
        from django.test import Client
        self.assertEqual(Client().get(r["Location"]).status_code, 404)

    def test_stock_decreases(self):
        from .models import Product
        before = Product.objects.get(slug="kumis-bilezik").stock
        self.client.post("/cart/add/kumis-bilezik/")
        self.client.post("/cart/", {"name": "B", "contact": "c", "country": "Japan"})
        self.assertEqual(Product.objects.get(slug="kumis-bilezik").stock, before - 1)

    def test_lang_switch_keeps_filters(self):
        html = self.client.get("/stays/?near=moynaq&lang=en").content.decode()
        self.assertIn("?near=moynaq&amp;lang=qq", html)
