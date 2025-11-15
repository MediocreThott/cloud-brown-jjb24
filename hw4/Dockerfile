# File: Dockerfile

# Use an official lightweight Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container first. This helps with
# Docker's layer caching, making future builds faster.
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code into the container
COPY . .

# Cloud Run will set this environment variable for you. Your app must
# listen on this port.
ENV PORT 8080

# Command to run the application using the Gunicorn web server.
# 'app:app' means: in the file app.py, find the Flask object named app.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
