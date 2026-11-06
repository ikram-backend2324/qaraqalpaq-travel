from django.core.management.base import BaseCommand

from travel.seed_data import seed


class Command(BaseCommand):
    help = "Load the demo catalogue"

    def handle(self, *a, **k):
        self.stdout.write(self.style.SUCCESS("places=%s stays=%s services=%s products=%s" % seed()))
