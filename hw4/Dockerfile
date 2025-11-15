# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Set the PORT environment variable that Cloud Run will use
ENV PORT 8080

# Define the command to run your app using gunicorn
# This is the same command from your app.yaml's entrypoint
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
