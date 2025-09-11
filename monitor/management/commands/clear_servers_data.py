from django.core.management.base import BaseCommand
from monitor.utils import clear_server_status_data
from django.db import transaction, connection



class Command(BaseCommand):
    help = """ Clear Server Status data from ServerStatus Model """

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            clear_server_status_data()
        self.stdout.write(self.style.SUCCESS('Successfully cleared old data.'))

        connection.close()

