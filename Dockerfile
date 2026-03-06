# python:3.11-slim supports linux/amd64 and linux/arm64 (Raspberry Pi)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# OS-level deps (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY pyproject.toml /app/
COPY src /app/src

# Install the project itself (editable-like, uses pyproject.toml)
RUN pip install --no-cache-dir .

# Expose the web dashboard port
EXPOSE 5048

# Run the app: Flask web server + hourly scheduler
CMD ["python", "-m", "src.app.main"]
