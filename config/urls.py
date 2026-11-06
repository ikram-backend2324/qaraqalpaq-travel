from django.contrib import admin
from django.http import HttpResponse
from django.views.generic.base import RedirectView
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", lambda r: HttpResponse("User-agent: *\nDisallow: /admin/\nDisallow: /cart/\nDisallow: /booked/\n", content_type="text/plain")),
    path("favicon.ico", RedirectView.as_view(url="/static/img/logo.svg", permanent=True)),
    path("", include("travel.urls")),
]
