from celery import shared_task
from .management.commands.check_servers import check_server_status
from .management.commands.clear_servers_data import clear_server_status_data
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_servers():
    logger.info("Executing Task!")
    check_server_status()


@shared_task
def clear_old_server_status():
    logger.info("Executing task for clearing old data!")
    clear_server_status_data()


# @shared_task
# def send_sms_alert():
#     logger.info("Executing task for sending SMS alerts!")
#     try:
#         # Call the management command 'send_sms' directly
#         call_command('send_sms')
#     except Exception as e:
#         logger.error(f"Error while sending SMS: {str(e)}")
