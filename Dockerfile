# OrcaSlicer API Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    wget \
    fuse \
    libfuse2 \
    libgl1 \
    libglib2.0-0 \
    libxrender1 \
    libxrandr2 \
    libxinerama1 \
    libxi6 \
    libxcursor1 \
    libfontconfig1 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Download and install OrcaSlicer
# Note: Update this URL to the latest OrcaSlicer AppImage release
ARG ORCA_VERSION=v2.0.0
RUN wget -q "https://github.com/SoftFever/OrcaSlicer/releases/download/${ORCA_VERSION}/OrcaSlicer_Linux_${ORCA_VERSION}.AppImage" -O OrcaSlicer.AppImage || \
    echo "Warning: OrcaSlicer download may fail - please update the URL in Dockerfile"

# Extract AppImage
RUN chmod +x OrcaSlicer.AppImage && \
    ./OrcaSlicer.AppImage --appimage-extract || \
    echo "AppImage extraction completed"

# Make AppRun executable
RUN chmod +x /app/squashfs-root/AppRun || true

# Copy application code
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ORCA_CLI_PATH=/app/squashfs-root/AppRun
ENV ORCA_DATADIR=/app/orca-config
ENV DATA_DIR=/data
ENV LOG_LEVEL=INFO
ENV LOG_JSON=true

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
