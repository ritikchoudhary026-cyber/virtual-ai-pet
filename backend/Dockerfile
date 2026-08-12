# Python base image for the API container
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source code
COPY . .

EXPOSE 8000

# 0.0.0.0 makes the service reachable from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
