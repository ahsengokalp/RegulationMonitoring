FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python 3.11 from deadsnakes and build tools
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   software-properties-common \
	   curl \
	   ca-certificates \
	&& add-apt-repository ppa:deadsnakes/ppa -y \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
	   python3.11 \
	   python3.11-venv \
	   python3.11-distutils \
	   build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Ensure pip for python3.11 is available
RUN python3.11 -m ensurepip --upgrade \
	&& python3.11 -m pip install --upgrade pip setuptools wheel

# Copy project files
COPY pyproject.toml /app/
COPY src /app/src
COPY README.md /app/

# Install project and dependencies
RUN python3.11 -m pip install --no-cache-dir .

# Expose the web dashboard port
EXPOSE 5048

# Run the app: web dashboard + hourly scheduler
CMD ["python3.11", "-m", "src.app.main"]
