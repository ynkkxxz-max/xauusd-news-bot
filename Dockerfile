FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to include /app and submodules
ENV PYTHONPATH="/app:/app/analyzers:/app/collectors:/app/formatters"
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
EXPOSE 10000

CMD ["python", "-u", "render_server.py"]
