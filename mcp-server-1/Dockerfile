FROM python:3.11-slim

WORKDIR /app

# Copy common package first
COPY common /app/common

# Copy requirements and install dependencies
COPY mcp-server-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp-server-1/app /app/app

# Create logs directory
RUN mkdir -p /app/logs

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
