from django.urls import path
from .views import ServerMonitor, LiveDatabaseServerGraphData, LiveAPIServerGraphData, LiveDashboardServerGraphData, getServerStatus
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('', ServerMonitor, name='server_monitor'),
    path('monitor/get_db_data/', LiveDatabaseServerGraphData, name='get_db_data'),
    path('monitor/get_api_data/', LiveAPIServerGraphData, name='get_api_data'),
    path('monitor/get_dasboard_data/', LiveDashboardServerGraphData, name='get_dasboard_data'),
    path('monitor/get_server_status/<str:server_ip>/', getServerStatus, name='get_server_status'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
