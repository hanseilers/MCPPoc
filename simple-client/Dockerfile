FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_HOST=0.0.0.0
ENV SERVICE_PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app/main.py"]
