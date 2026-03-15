# 1. Use Python 3.9 as the base
FROM python:3.10-slim

# 2. Install system libraries needed for OpenCV on Linux
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code (main.py, flask_api.py, etc.)
COPY . .

# 6. Run the app using Gunicorn (Production server)
# This is much more stable than app.run()
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "flask_api:app"]