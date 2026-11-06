from django.contrib import admin

from .models import Booking, Order, PartnerLead, Place, PlanLog, Product, Service, Stay

for m in (Place, Stay, Service, Product, Booking, Order, PartnerLead, PlanLog):
    admin.site.register(m)
