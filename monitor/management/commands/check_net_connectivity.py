from django.core.management.base import BaseCommand
import socket
from django.utils import timezone
from monitor.models import NetConnectivityLog

class Command(BaseCommand):
    help = "Check internet connectivity via the 10.x network and log uptime/downtime"

    def check_internet_on_10(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)

            # Replace with your actual server IP on the 10 network
            # sock.bind(("10.10.10.17", 0)) # This is to bind the request with a specific IP
            sock.connect(("8.8.8.8", 53))
            sock.close()
            return True
        except Exception:
            return False

    def handle(self, *args, **kwargs):
        net_status = self.check_internet_on_10()

        if net_status:
            # ✅ Internet available → check if we need to create a new log
            if not NetConnectivityLog.objects.filter(end_datetime__isnull=True).exists():
                NetConnectivityLog.objects.create(
                    start_datetime=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS("✅ Net UP → started new log"))
            else:
                self.stdout.write("✅ Net still UP → continuing current log")

        else:
            # ❌ Internet not available → close the last open log if exists
            last_log = NetConnectivityLog.objects.filter(end_datetime__isnull=True).last()
            if last_log:
                last_log.end_datetime = timezone.now()
                last_log.save(update_fields=["end_datetime"])
                self.stdout.write(self.style.ERROR("❌ Net DOWN → closed the log"))
            else:
                self.stdout.write("❌ Net still DOWN → no log open")
