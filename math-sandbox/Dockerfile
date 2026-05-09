FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CFLAGS="-O3 -mavx2"
ENV CXXFLAGS="-O3 -mavx2"

# Install build dependencies for compiling packages with AVX2
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash sandboxuser

# Set working directory
WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Ensure the sandbox user has permissions for the app directory
RUN chown -R sandboxuser:sandboxuser /app

# Switch to the non-root user
USER sandboxuser

# Expose port
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
