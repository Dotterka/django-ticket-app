from django.core.management.base import BaseCommand

from tickets.models import Order

class Command(BaseCommand):
    help = 'Expires orders that have passed their expiration time'

    def handle(self, *args, **kwargs):
        Order.expire_all_orders()