# Use an official Python runtime as a parent image
#Build refresh
FROM python:3.11-slim

# Install system dependencies for OpenCV and video processing
# Install system dependencies for OpenCV and video processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Cloud Run sets the PORT environment variable.
# We use Gunicorn to handle production-grade Flask serving.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 600 flask_api:app