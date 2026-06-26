# Stage 1: Builder
FROM python:3.11-slim AS builder

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
FROM python:3.11-slim AS ephemeris_downloader

WORKDIR /ephemeris
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN curl -o de440.bsp https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440.bsp && \
    curl -o de421.bsp https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp

# Download Outfit variable font directly from google/fonts repository
RUN curl -sS -L -o Outfit-VariableFont_wght.ttf "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit%5Bwght%5D.ttf"


# Stage 3: Runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user
RUN useradd -m -s /bin/bash sandboxuser

# Install system fonts, emoji packages, and fontconfig
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    fonts-symbola \
    fontconfig && \
    rm -rf /var/lib/apt/lists/*

# Copy Outfit font from downloader
RUN mkdir -p /usr/share/fonts/truetype/outfit
COPY --from=ephemeris_downloader /ephemeris/Outfit-VariableFont_wght.ttf /usr/share/fonts/truetype/outfit/

# Update system font cache
RUN fc-cache -fv

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Create matplotlib config directory for sandboxuser
RUN mkdir -p /home/sandboxuser/.matplotlib && chown -R sandboxuser:sandboxuser /home/sandboxuser/.matplotlib

# Configure default fonts via matplotlibrc and prebuild matplotlib cache
# This layer is run before application code copy so it is cached in GHA when code changes
RUN echo "font.family: sans-serif" > /home/sandboxuser/.matplotlib/matplotlibrc && \
    echo "font.sans-serif: Outfit, Noto Sans CJK SC, Symbola, DejaVu Sans, Arial, Helvetica, sans-serif" >> /home/sandboxuser/.matplotlib/matplotlibrc && \
    echo "axes.unicode_minus: False" >> /home/sandboxuser/.matplotlib/matplotlibrc && \
    chown sandboxuser:sandboxuser /home/sandboxuser/.matplotlib/matplotlibrc && \
    MPLCONFIGDIR=/home/sandboxuser/.matplotlib python -c "import matplotlib.pyplot"

WORKDIR /app

# Copy ephemerides as an independent layer
COPY --from=ephemeris_downloader --chown=sandboxuser:sandboxuser /ephemeris/de440.bsp /ephemeris/de421.bsp /app/

# Copy application code
COPY --chown=sandboxuser:sandboxuser app/ /app/

# Switch to the non-root user
USER sandboxuser

EXPOSE 8000

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
