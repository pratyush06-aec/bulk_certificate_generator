# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is sent straight to terminal (unbuffered)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for Pillow and PyMuPDF if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the generated certificates directory exists and is writable
RUN mkdir -p /app/generated && chmod -R 777 /app/generated

# Expose port 8000 (Standard for FastAPI)
EXPOSE 8000

# Run alembic migrations before starting the application, then start uvicorn
# We bind to 0.0.0.0 so the container is accessible externally
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
