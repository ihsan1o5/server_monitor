from django.contrib import admin
from .models import ServerStatus, PhysicalServer, VirtualServer


@admin.register(ServerStatus)
class ServerStatusAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ServerStatus._meta.fields]
    fields = ['server', 'status']


@admin.register(PhysicalServer)
class PhysicalServerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in  PhysicalServer._meta.fields]
    fields = ['name', 'server_model', 'specs', 'ram', 'hdd', 'server_type']

@admin.register(VirtualServer)
class VirtualServerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in VirtualServer._meta.fields]
    fields = ['name', 'ip_address', 'port', 'physical_server', 'processor', 'ram', 'hdd', 'group']


