from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Q, OuterRef, Subquery
from .models import ServerStatus, PhysicalServer, VirtualServer
from django.http import JsonResponse
from datetime import datetime
import json
from .utils import get_other_servers_data, get_five_latest_status_for_live_servers, format_db_data_with_flags

@login_required
def ServerMonitor(request):
    # Get count of virtual servers
    total_virtual_servers = VirtualServer.objects.all().count()

    # Get counts of physical servers
    physical_servers = PhysicalServer.objects.aggregate(
        total_count=Count('id'),
        cpu_count=Count('id', filter=Q(server_type='CPU')),
        silver_count=Count('id', filter=Q(server_type='Silver')),
        gold_count=Count('id', filter=Q(server_type='Gold')),
    )

    # Get production servers
    production_server_ids = VirtualServer.objects.filter(
        group='live'
    ).values_list('id', flat=True)

    production_servers_status = ServerStatus.objects.filter(
        server_id__in=production_server_ids
    ).order_by('-server_id','-timestamp').distinct('server')
    production_servers_status = list(production_servers_status.values('id', 'status', 'active_connections', 'timestamp', 'server__id', 'server__name', 'server__ip_address'))
    for status in production_servers_status:
        status['status'] = 1 if status['status'] else 0
        for key, value in status.items():
            if isinstance(value, datetime):
                status[key] = value.strftime('%Y-%m-%d %H:%M:%S')

    # Get other all type of servers data
    all_other_servers_status = get_other_servers_data()

    all_virtual_servers = VirtualServer.objects.all().values_list('name', 'ip_address', 'ram', 'hdd', 'group')

    context = {
        'physical_servers': physical_servers,
        'total_virtual_servers': total_virtual_servers,
        'production_servers_status': production_servers_status,
        'all_other_servers_status': all_other_servers_status,
        'all_virtual_servers': list(all_virtual_servers),
        'all_other_servers_status_json': json.dumps(all_other_servers_status),
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # context['physical_servers']['total_count'] = 3
        return JsonResponse(context)
    return render(request, 'server_monitor.html', context)

def LiveDatabaseServerGraphData(request):

    live_server_ids = VirtualServer.objects.filter(group='live', ip_address='10.10.10.15').values_list('id', flat=True)

    # Subquery to get the latest statuses for each server
    subquery = ServerStatus.objects.filter(
        server_id=OuterRef('server_id')
    ).order_by('-timestamp')

    latest_statuses = ServerStatus.objects.filter(
        server_id__in=live_server_ids,
        id__in=Subquery(subquery.values('id')[:1])  # Get the latest 5 statuses for each server
    ).order_by('server_id', '-timestamp').values_list('response_time', 'timestamp')
    print("latest_statuses =======================================================> ", latest_statuses)

    data_point = {
        'time': int(datetime.now().timestamp() * 1000),
        'value': latest_statuses[0][0]
    }

    
    return JsonResponse(data_point)

def LiveAPIServerGraphData(request):

    live_server_ids = VirtualServer.objects.filter(group='live', ip_address='10.10.10.16').values_list('id', flat=True)

    # Subquery to get the latest statuses for each server
    subquery = ServerStatus.objects.filter(
        server_id=OuterRef('server_id')
    ).order_by('-timestamp')

    latest_statuses = ServerStatus.objects.filter(
        server_id__in=live_server_ids,
        id__in=Subquery(subquery.values('id')[:1])  # Get the latest 5 statuses for each server
    ).order_by('server_id', '-timestamp').values_list('response_time', 'timestamp')
    print("latest_statuses =======================================================> ", latest_statuses)

    data_point = {
        'time': int(datetime.now().timestamp() * 1000),
        'value': latest_statuses[0][0]
    }

    
    return JsonResponse(data_point)

def LiveDashboardServerGraphData(request):

    live_server_ids = VirtualServer.objects.filter(group='live', ip_address='10.10.10.17').values_list('id', flat=True)

    # Subquery to get the latest statuses for each server
    subquery = ServerStatus.objects.filter(
        server_id=OuterRef('server_id')
    ).order_by('-timestamp')

    latest_statuses = ServerStatus.objects.filter(
        server_id__in=live_server_ids,
        id__in=Subquery(subquery.values('id')[:1])
    ).order_by('server_id', '-timestamp').values_list('response_time', 'timestamp')

    print("latest_statuses =======================================================> ", latest_statuses)

    data_point = {
        'time': int(datetime.now().timestamp() * 1000),
        'value': latest_statuses[0][0]
    }

    
    return JsonResponse(data_point)


def getServerStatus(request, server_ip):
    try:
        server = VirtualServer.objects.get(ip_address=server_ip)
        statuses = ServerStatus.objects.filter(server=server).order_by('-timestamp')[:10]
        status_data = [
            {
                'response_time': status.response_time,
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            for status in statuses
        ]
        return JsonResponse({'status_data': status_data})
    except VirtualServer.DoesNotExist:
        return JsonResponse({'error': 'Server not found'}, status=404)
