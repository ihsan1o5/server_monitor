from django import template
from datetime import datetime

register = template.Library()

@register.filter
def hours_since(value):
    if not value:
        return 0

    # Check if the value is a string and try to parse it
    if isinstance(value, str):
        try:
            # Adjust this format to match your input date string
            value = datetime.strptime(value, '%b %d, %Y, %I:%M %p')
        except ValueError:
            return 0  # Return 0 if the date string can't be parsed

    # Ensure value is a datetime object after parsing
    if isinstance(value, datetime):
        current_time = datetime.now()
        time_difference = (current_time - value).total_seconds() // 3600
        return int(time_difference)

    return 0