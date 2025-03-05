# Use the official Python base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y cron dos2unix

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Add the cron job definition file to the /app directory
COPY ./crontab /app/crontab

# Ensure cron job file has proper permissions
RUN chmod 0644 /app/crontab

# Convert cron job file to Unix format
RUN dos2unix /app/crontab

# Apply the cron job
RUN crontab /app/crontab

# Expose the port the app will run on
EXPOSE 8000
