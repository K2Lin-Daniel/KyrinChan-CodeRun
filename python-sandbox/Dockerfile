# Stage 1: Builder
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CFLAGS="-O3 -mavx2"
ENV CXXFLAGS="-O3 -mavx2"

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install them into a virtual environment
COPY app/requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install requirements
# Using --no-cache-dir to avoid caching unnecessary downloads
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Stage 2: Ephemeris downloader
FROM python:3.11-slim as ephemeris_downloader

WORKDIR /ephemeris
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN curl -o de440.bsp https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440.bsp && \
    curl -o de421.bsp https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp


# Stage 3: Runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user
RUN useradd -m -s /bin/bash sandboxuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app/ /app/

# Ensure the sandbox user has permissions for the app directory
RUN chown -R sandboxuser:sandboxuser /app

# Copy ephemerides as an independent layer (after chown to prevent layer duplication)
COPY --from=ephemeris_downloader --chown=sandboxuser:sandboxuser /ephemeris /app/ephemeris

# Switch to the non-root user
USER sandboxuser

EXPOSE 8000

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
