# Use a lightweight, secure Python 3.11 base image
FROM python:3.11-slim

# Set environment variables
# PYTHONUNBUFFERED=1 ensures console logs are printed and flushed immediately
# PYTHONDONTWRITEBYTECODE=1 prevents Python from writing .pyc files to the container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose no ports since this is a stdio-based CLI/orchestration application
# GEMINI_API_KEY should be passed as a runtime environment variable

# Set the default entrypoint to run the demo pipeline
ENTRYPOINT ["python", "run.py"]
