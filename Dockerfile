# Base image
FROM python:3.12-slim

# Install PostgreSQL client and development headers
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .  
RUN pip install -r requirements.txt

# Copy the rest of the Django app code to the container
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the port Django will run on
EXPOSE 8000

# Command to run migrations and then start the Gunicorn server
# CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 server_monitor.wsgi:application"]

CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 8 --timeout 100 server_monitor.wsgi:application"]

# Copy the entrypoint.sh script
# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

# Use the entrypoint.sh script
# ENTRYPOINT ["/entrypoint.sh"]
