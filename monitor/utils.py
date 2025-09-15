from django.db import connections, close_old_connections
from django.db.models import Q, Func, F, Value, CharField, OuterRef, Subquery
from .models import ServerStatus, VirtualServer, ServerStatusHistory
import socket
from django.utils import timezone
import time
from datetime import datetime
import requests


def check_server_status():
    close_old_connections()
    print("Started checking server's status: ")
    servers = VirtualServer.objects.all()
    status_data = []
    history_data = []

    for server in servers:
        try:
            
            start_time = time.time()
            
            # Use HTTP request if server group is 'gis'
            if server.group.lower() == 'gis':
                url = f"http://{server.ip_address}:{server.port}"
                response = requests.get(url, timeout=2)
                status = response.ok  # True if status code is 200-299
            else:
                sock = socket.create_connection((server.ip_address, server.port), timeout=2)
                status = True
                sock.close()

            response_time = round((time.time() - start_time) * 1000, 2)

            # Adjust response time if it's less than 1
            if response_time < 1:
                response_time = int(round(response_time * 10, 0))

        except (socket.timeout, socket.error, requests.RequestException):
            print("Connection error On IP => ", server.ip_address, " Error is => ",  socket.error)
            status = False
            response_time = 0.00

        status_data.append(
            ServerStatus(
                server=server, 
                status=status, 
                response_time=response_time
            )
        )

        if not status:
            # Server is down, insert a new history entry if there isn’t an open down record
            if not ServerStatusHistory.objects.filter(server=server, up_datetime__isnull=True).exists():
                history_data.append(ServerStatusHistory(server=server, down_datetime=timezone.now()))
        else:
            # Server is up, update last down record with up_datetime if exists
            # ServerStatusHistory.objects.filter(server=server, up_datetime__isnull=True).update(up_datetime=time.strftime('%Y-%m-%d %H:%M:%S'))
            ServerStatusHistory.objects.filter(server=server, up_datetime__isnull=True).update(up_datetime=timezone.now())


    ServerStatus.objects.bulk_create(
        status_data
    )
    if history_data:
        ServerStatusHistory.objects.bulk_create(history_data)

    close_old_connections()

def clear_server_status_data():
    latest_100_records = ServerStatus.objects.order_by('-id').values_list('id', flat=True)[:100]
    ServerStatus.objects.exclude(id__in=latest_100_records).delete()

# get active sessions from dashboard DB
def get_users_connected(server):
    """
    Get the number of active users currently logged into the Django app using raw SQL.
    """
    active_connections = 0
    if server.ip_address == '10.10.10.17':
        with connections['dashboard'].cursor() as cursor:
            now = timezone.now()
            cursor.execute("""
                SELECT COUNT(*) FROM django_session
                WHERE expire_date >= %s;
            """, [now])
            active_connections = cursor.fetchone()[0]

    elif server.ip_address == '10.10.10.15':
        with connections['dashboard'].cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(pid)
                FROM pg_stat_activity 
                WHERE datname = 'dahsboard_login_new';
            """)
            active_connections = cursor.fetchone()[0]
        return active_connections
        
    return active_connections


def get_other_servers_data():

    # Get all servers other then production
    virtual_servers = VirtualServer.objects.filter(~Q(group='live'))

    servers_data = {}
    for server in virtual_servers:
        # Get the latest status entry for the current server
        latest_status = ServerStatus.objects.filter(server=server).order_by('-timestamp').first()

        if latest_status:
            # Check if the server is currently down
            if not latest_status.status:
                # Get the first time the server went down, continuosly
                # We want all statuses starting form the most recent 'UP'
                most_recent_up = ServerStatus.objects.filter(server=server, status=True).order_by('-timestamp').first()

                if most_recent_up:
                    # Find the first down status since the last 'UP'
                    first_down_since_up = ServerStatus.objects.filter(
                        server=server, status=False, timestamp__gt=most_recent_up.timestamp
                    ).order_by('timestamp').first()
                else:
                    # No 'UP' status found, meaning the server is down continuously from the earliest 'DOWN'
                    first_down_since_up = ServerStatus.objects.filter(
                        server=server, status=False
                    ).order_by('timestamp').first()

                # Get the latest 10 entries for the down server
                latest_statuses = ServerStatus.objects.filter(server=server).annotate(
                    formatted_timestamp=Func(
                        F('timestamp'),
                        Value('Mon DD, YYYY, HH:MI AM'),
                        function='to_char',
                        output_field=CharField()
                    )
                ).order_by('-timestamp')[:10]
                latest_statuses = list(latest_statuses.values('id', 'status', 'formatted_timestamp'))
                latest_statuses.sort(key=lambda x: x['id'])

                # Add the down time entry to the server's data
                server_info = {
                    'physical_server_specs': {
                        'name': server.physical_server.name,
                        'model': server.physical_server.server_model,
                        'specs': server.physical_server.specs,
                    },
                    'server': {
                        'name': server.name,
                        'ip_address': server.ip_address
                    },
                    'latest_status': {
                        'status': latest_status.status,
                        'timestamp': latest_status.timestamp.strftime('%b %d, %Y, %I:%M %p')
                    },
                    'first_down_time': first_down_since_up.timestamp.strftime('%b %d, %Y, %I:%M %p') if first_down_since_up else None,
                    'latest_10_entries': latest_statuses
                }
            else:
                # Get the latest 10 entries for the down server
                latest_statuses = ServerStatus.objects.filter(server=server).annotate(
                    formatted_timestamp=Func(
                        F('timestamp'),
                        Value('Mon DD, YYYY, HH:MI AM'),
                        function='to_char',
                        output_field=CharField()
                    )
                ).order_by('-timestamp')[:10]
                latest_statuses = list(latest_statuses.values('id', 'status', 'formatted_timestamp'))
                latest_statuses.sort(key=lambda x: x['id'])

                # If the server is up, no need to find downtime
                server_info = {
                    'physical_server_specs': {
                        'model': server.physical_server.server_model,
                        'specs': server.physical_server.specs,
                    },
                    'server': {
                        'name': server.name,
                        'ip_address': server.ip_address
                    },
                    'latest_status': {
                        'status': latest_status.status,
                        'timestamp': latest_status.timestamp.strftime('%b %d, %Y, %I:%M %p')
                    },
                    'first_down_time': None,
                    'latest_10_entries': latest_statuses
                }

            if server.group not in servers_data:
                servers_data[server.group] = []
            servers_data[server.group].append(server_info)
    
    return servers_data

def format_db_data_with_flags(data):
    for obj in data:
        obj['status'] = 1 if obj['status'] else 0
        for key, value in obj.items():
            if isinstance(value, datetime):
                obj[key] = value.strftime('%Y-%m-%d %H:%M:%S')

    return data

def get_five_latest_status_for_live_servers():
    # Get the IDs of virtual servers in the 'live' group
    live_server_ids = VirtualServer.objects.filter(group='live', ip_address='10.10.10.15').values_list('id', flat=True)

    # Subquery to get the latest statuses for each server
    subquery = ServerStatus.objects.filter(
        server_id=OuterRef('server_id')
    ).order_by('-timestamp')

    latest_statuses = ServerStatus.objects.filter(
        server_id__in=live_server_ids,
        id__in=Subquery(subquery.values('id')[:5])  # Get the latest 5 statuses for each server
    ).order_by('server_id', '-timestamp')

    status_list = []

    for status in latest_statuses:
        status_list.append()
    print("last status => ", latest_statuses)

    return latest_statuses


