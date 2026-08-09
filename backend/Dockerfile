# Small official Python image for the API container.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies before source code so Docker can reuse this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

# 0.0.0.0 makes the service reachable from outside the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
