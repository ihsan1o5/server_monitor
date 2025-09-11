from django.core.management.base import BaseCommand
from monitor.utils import check_server_status
from django.db import connection, transaction


class Command(BaseCommand):
    help = """ Checks the status of servers and updates the database """

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            check_server_status()
        self.stdout.write(self.style.SUCCESS('Successfully checked all servers.'))

        connection.close()
