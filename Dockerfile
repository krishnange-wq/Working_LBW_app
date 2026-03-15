# Use 3.10-slim (NOT 3.1)
FROM python:3.10-slim

# Install system tools for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Tell Render to use port 10000
ENV PORT=10000
EXPOSE 10000

# Start the server
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "flask_api:app"]