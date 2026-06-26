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

# Create directory for custom static fonts
RUN mkdir -p fonts

# Download static Outfit fonts (to avoid variable font incompatibility in matplotlib)
RUN curl -sS -L -o fonts/Outfit-Regular.ttf "https://cdn.jsdelivr.net/fontsource/fonts/outfit@latest/latin-400-normal.ttf" && \
    curl -sS -L -o fonts/Outfit-Bold.ttf "https://cdn.jsdelivr.net/fontsource/fonts/outfit@latest/latin-700-normal.ttf"

# Download static Noto Sans SC Chinese fonts (to avoid TTC packaging issues in matplotlib)
RUN curl -sS -L -o fonts/NotoSansSC-Regular.ttf "https://cdn.jsdelivr.net/fontsource/fonts/noto-sans-sc@latest/chinese-simplified-400-normal.ttf" && \
    curl -sS -L -o fonts/NotoSansSC-Bold.ttf "https://cdn.jsdelivr.net/fontsource/fonts/noto-sans-sc@latest/chinese-simplified-700-normal.ttf"

# Download static Symbola font directly for vector-based emoji fallback
RUN curl -sS -L -o fonts/Symbola.ttf "https://github.com/zhm/symbola/raw/master/fonts/Symbola.ttf"


# Stage 3: Runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user
RUN useradd -m -s /bin/bash sandboxuser

# Install fontconfig and lightweight Chinese font
RUN apt-get update && \
    apt-get install -y --no-install-recommends fontconfig fonts-wqy-microhei && \
    rm -rf /var/lib/apt/lists/*

# Copy custom fonts from downloader
COPY --from=ephemeris_downloader /ephemeris/fonts /usr/share/fonts/truetype/custom

# Update system font cache
RUN fc-cache -fv

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy custom fonts to matplotlib's internal font directory
RUN cp /usr/share/fonts/truetype/custom/*.ttf $(python -c "import os, matplotlib; print(os.path.join(os.path.dirname(matplotlib.matplotlib_fname()), 'fonts', 'ttf'))")

# Create matplotlib config directory for sandboxuser
RUN mkdir -p /home/sandboxuser/.matplotlib && chown -R sandboxuser:sandboxuser /home/sandboxuser/.matplotlib

# Configure default fonts via matplotlibrc and prebuild matplotlib cache
# This layer is run before application code copy so it is cached in GHA when code changes
RUN echo "font.family: sans-serif" > /home/sandboxuser/.matplotlib/matplotlibrc && \
    echo "font.sans-serif: Outfit, Noto Sans SC, WenQuanYi Micro Hei, Symbola, DejaVu Sans, Arial, Helvetica, sans-serif" >> /home/sandboxuser/.matplotlib/matplotlibrc && \
    echo "axes.unicode_minus: False" >> /home/sandboxuser/.matplotlib/matplotlibrc && \
    python -c "import matplotlib; import shutil; shutil.rmtree(matplotlib.get_cachedir(), ignore_errors=True)" && \
    MPLCONFIGDIR=/home/sandboxuser/.matplotlib python -c "import matplotlib.pyplot" && \
    chown -R sandboxuser:sandboxuser /home/sandboxuser/.matplotlib

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
