import requests
from django.core.management.base import BaseCommand
from django.db import connections
import os
import re, json

class Command(BaseCommand):
    help = "Send SMS to unsent records in the send_sms table"

    def handle(self, *args, **kwargs):
        query = """
            SELECT id, phone_number, sms, max_try
            FROM send_sms
            WHERE is_sent = false 
                AND sending_date_time <= now()
                AND max_try < 3;
        """

        update_query_success = """
            UPDATE send_sms
            SET is_sent = true, status_after_try = 'ok'
            WHERE id = %s
        """

        update_query_fail = """
            UPDATE send_sms
            SET max_try = max_try + 1, 
                status_after_try = CASE WHEN max_try + 1 >= 3 THEN 'failed' ELSE status_after_try END
            WHERE id = %s
        """

        api_url_template = os.getenv('SEND_SMS_API')
        api_params = {
            "user": "dhai_pakistan",
            "password": "oZmK9YpBS)3",
            "mask": "DHA 360",
        }

        with connections['default'].cursor() as cursor:
            cursor.execute(query)
            records = cursor.fetchall()

            print("total number of requests found => ", len(records))
            processed_records = []

            if records:
                for record in records:
                    sms_id, phone_number, message, max_try = record
                    phone_number = re.sub(r'\D', '', phone_number)
                    if phone_number.startswith('0'):
                        phone_number = '92' + phone_number[1:]

                    print("phone_number format => ", phone_number)
                    api_params.update({"to": phone_number, "message": message})

                    try:
                        response = requests.get(api_url_template, params=api_params)
                        response_data = response.json()

                        if response.status_code == 200 and response_data.get("Status") == "OK":
                            cursor.execute(update_query_success, [sms_id])
                            self.stdout.write(f"SMS sent successfully for ID {sms_id}")

                            processed_records.append(
                                {
                                    "mobile": record[1],
                                    "is_sent": True,
                                    "max_try": max_try + 1,
                                    "status_after_try": "ok"
                                })

                        else:
                            cursor.execute(update_query_fail, [sms_id])
                            processed_records.append(
                                {
                                    "mobile": record[1],
                                    "is_sent": False,
                                    "max_try": max_try + 1,
                                    "status_after_try": "failed"
                                })
                            self.stdout.write(f"Failed to send SMS for ID {sms_id}. Response: {response_data}")

                    except Exception as e:
                        cursor.execute(update_query_fail, [sms_id])
                        processed_records.append(
                            {
                                "mobile": record[1],
                                "is_sent": False,
                                "max_try": max_try + 1,
                                "status_after_try": "failed"
                            })
                        self.stdout.write(f"Error sending SMS for ID {sms_id}: {str(e)}")

                # Update the processed records in the DH360
                url = os.getenv('DH360_UPDATE_SMS_API')
                token = os.getenv('AUTH_TOKEN')
                headers = {
                    "Authorization": f"{token}",
                    "Content-Type": "application/json",
                }

                try:
                    response = requests.put(url, headers=headers, data=json.dumps(processed_records))

                    if response.status_code == 200:
                        print("DH360 API Response:", response.json())
                    else:
                        print("DH360 API Failed:", response.status_code, response.text)

                except requests.exceptions.RequestException as e:
                    print("An error occurred while updating DH360:", e)

            else:
                self.stdout.write("No records found to send SMS")


