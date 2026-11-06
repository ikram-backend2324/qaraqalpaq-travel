from django.urls import path

from . import views as v

urlpatterns = [
    path("", v.home),
    path("stays/", v.stays),
    path("stays/<slug:slug>/", v.stay_detail),
    path("booked/<int:pk>/", v.booked),
    path("guides/", v.guides),
    path("places/", v.places),
    path("places/<slug:slug>/", v.place_detail),
    path("ar/<slug:slug>/", v.ar_view),
    path("craft/", v.craft),
    path("craft/<slug:slug>/", v.product_detail),
    path("cart/", v.cart_view),
    path("cart/add/<slug:slug>/", v.cart_add),
    path("cart/remove/<slug:slug>/", v.cart_remove),
    path("planner/", v.planner),
    path("partner/", v.partner),
    path("dashboard/", v.dashboard),
    path("about/", v.about),
    path("img/stay/<slug:slug>.svg", v.img_stay),
    path("img/place/<slug:slug>.svg", v.img_place),
    path("img/product/<slug:slug>.svg", v.img_product),
    path("img/hero.svg", v.img_hero),
    path("img/ar/<str:scene>/<str:layer>.svg", v.img_ar),
    path("api/plan/", v.api_plan),
    path("api/stays/", v.api_stays),
    path("api/health/", v.api_health),
]
