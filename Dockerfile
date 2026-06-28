# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Default command runs the API
CMD ["uvicorn", "4leafclover-dataops:app", "--host", "0.0.0.0", "--port", "8080"]
