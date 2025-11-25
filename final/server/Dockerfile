# 1. Start with a lean, official Python base image.
FROM python:3.9-slim

# 2. Set the working directory inside the container.
WORKDIR /app

# 3. Copy the file that lists our dependencies.
COPY requirements.txt .

# 4. Install the dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of our server's source code.
COPY . .

# 6. Expose the port that gunicorn will run on.
EXPOSE 8080

# 7. Define the command to run when the container starts.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "server:app"]