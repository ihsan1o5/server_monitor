from django.db import models

    
class PhysicalServer(models.Model):
    name = models.CharField(max_length=255)
    server_model = models.CharField(max_length=255, null=True, blank=True)
    specs = models.CharField(max_length=2455, null=True, blank=True)
    ram = models.CharField(max_length=50, null=True, blank=True)
    hdd = models.CharField(max_length=50, null=True, blank=True)
    server_type = models.CharField(max_length=100, default='CPU')
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.name

class VirtualServer(models.Model):
    name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=80)
    physical_server = models.ForeignKey(PhysicalServer, on_delete=models.CASCADE)
    processor = models.CharField(max_length=255, null=True, blank=True)
    ram = models.CharField(max_length=255, null=True, blank=True)
    hdd = models.CharField(max_length=255, null=True, blank=True)
    group = models.CharField(max_length=100, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ServerStatus(models.Model):
    server = models.ForeignKey(VirtualServer, on_delete=models.CASCADE)
    status = models.BooleanField()
    active_connections = models.IntegerField(default=0)
    response_time = models.FloatField(default=0.00)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.server.name
    

class ServerStatusHistory(models.Model):
    server = models.ForeignKey(VirtualServer, on_delete=models.CASCADE)
    down_datetime = models.DateTimeField(null=True, blank=True)
    up_datetime = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.server.name
    

class NetConnectivityLog(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Net from {self.start_datetime} to {self.end_datetime or 'still up'}"
