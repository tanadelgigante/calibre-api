FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application
COPY src/ .

# Set PYTHONPATH to include /app
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
