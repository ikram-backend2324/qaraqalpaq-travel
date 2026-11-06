from django.db import models

LANGS = ("qq", "uz", "ru", "en")


class I18nMixin:
    def tr(self, field, lang):
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_en", "")


class Place(I18nMixin, models.Model):
    KINDS = [("fortress", "fortress"), ("museum", "museum"), ("nature", "nature"), ("aral", "aral"), ("sacred", "sacred")]
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=20, choices=KINDS)
    name_qq = models.CharField(max_length=120)
    name_uz = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    era = models.CharField(max_length=80, blank=True)
    district = models.CharField(max_length=80, blank=True)
    lat = models.FloatField()
    lon = models.FloatField()
    desc_qq = models.TextField()
    desc_uz = models.TextField()
    desc_ru = models.TextField()
    desc_en = models.TextField()
    ar_scene = models.CharField(max_length=20, blank=True)  # fortress / aral / ""
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name_en


class Stay(I18nMixin, models.Model):
    KINDS = [("yurt", "yurt"), ("glamping", "glamping"), ("guesthouse", "guesthouse")]
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=20, choices=KINDS)
    name = models.CharField(max_length=120)
    near = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, related_name="stays")
    lat = models.FloatField()
    lon = models.FloatField()
    price_usd = models.PositiveIntegerField()
    capacity = models.PositiveSmallIntegerField(default=4)
    rating = models.FloatField(default=4.6)
    amenities = models.CharField(max_length=300, help_text="comma separated keys")
    desc_qq = models.TextField()
    desc_uz = models.TextField()
    desc_ru = models.TextField()
    desc_en = models.TextField()
    palette = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["price_usd"]

    def amenity_list(self):
        return [a.strip() for a in self.amenities.split(",") if a.strip()]

    def __str__(self):
        return self.name


class Service(I18nMixin, models.Model):
    KINDS = [("guide", "guide"), ("driver", "driver")]
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=10, choices=KINDS)
    name = models.CharField(max_length=120)
    languages = models.CharField(max_length=80)
    base = models.CharField(max_length=80)
    vehicle = models.CharField(max_length=80, blank=True)
    seats = models.PositiveSmallIntegerField(default=0)
    price_usd = models.PositiveIntegerField()
    rating = models.FloatField(default=4.7)
    spec_qq = models.CharField(max_length=200)
    spec_uz = models.CharField(max_length=200)
    spec_ru = models.CharField(max_length=200)
    spec_en = models.CharField(max_length=200)

    class Meta:
        ordering = ["kind", "price_usd"]

    def __str__(self):
        return self.name


class Product(I18nMixin, models.Model):
    CATS = [("embroidery", "embroidery"), ("carpet", "carpet"), ("silver", "silver"), ("ceramics", "ceramics")]
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=20, choices=CATS)
    name_qq = models.CharField(max_length=120)
    name_uz = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    artisan = models.CharField(max_length=120)
    origin = models.CharField(max_length=80)
    price_usd = models.PositiveIntegerField()
    ship_days = models.CharField(max_length=20, default="7-14")
    desc_qq = models.TextField()
    desc_uz = models.TextField()
    desc_ru = models.TextField()
    desc_en = models.TextField()
    palette = models.PositiveSmallIntegerField(default=0)
    stock = models.PositiveSmallIntegerField(default=5)

    class Meta:
        ordering = ["category", "price_usd"]

    def __str__(self):
        return self.name_en


class Booking(models.Model):
    STATUS = [("new", "new"), ("confirmed", "confirmed"), ("cancelled", "cancelled")]
    stay = models.ForeignKey(Stay, on_delete=models.CASCADE, null=True, blank=True, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True, related_name="bookings")
    name = models.CharField(max_length=120)
    contact = models.CharField(max_length=160)
    country = models.CharField(max_length=80, blank=True)
    date_from = models.DateField()
    date_to = models.DateField()
    guests = models.PositiveSmallIntegerField(default=2)
    extras = models.CharField(max_length=200, blank=True)
    total_usd = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Order(models.Model):
    name = models.CharField(max_length=120)
    contact = models.CharField(max_length=160)
    country = models.CharField(max_length=80)
    items = models.JSONField()
    total_usd = models.PositiveIntegerField()
    status = models.CharField(max_length=12, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PartnerLead(models.Model):
    KINDS = [("camp", "camp"), ("driver", "driver"), ("guide", "guide"), ("artisan", "artisan")]
    kind = models.CharField(max_length=10, choices=KINDS)
    name = models.CharField(max_length=120)
    contact = models.CharField(max_length=160)
    location = models.CharField(max_length=120)
    note = models.CharField(max_length=400, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PlanLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    lang = models.CharField(max_length=5)
    request = models.TextField()
    answer = models.TextField()
    model_used = models.CharField(max_length=80, blank=True)
