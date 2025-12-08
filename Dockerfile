# OrcaSlicer API Dockerfile
FROM ubuntu:24.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    squashfs-tools \
    fuse \
    libfuse2 \
    libgl1 \
    libegl1 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libwebkit2gtk-4.1-0 \
    libjavascriptcoregtk-4.1-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libglib2.0-0 \
    libdbus-1-3 \
    libwayland-client0 \
    libwayland-egl1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Download and install OrcaSlicer
ARG ORCA_VERSION=2.3.1


# RUN curl -L https://github.com/OrcaSlicer/OrcaSlicer/releases/download/v${ORCA_VERSION}/OrcaSlicer_Linux_AppImage_Ubuntu2404_V${ORCA_VERSION}.AppImage -o OrcaSlicer.AppImage
RUN curl -o OrcaSlicer.AppImage -L "https://github.com/kldzj/orca-slicer-arm64/releases/download/v${ORCA_VERSION}-arm64/OrcaSlicer-${ORCA_VERSION}-arm64-linux.AppImage"
RUN chmod +x OrcaSlicer.AppImage
RUN ./OrcaSlicer.AppImage --appimage-extract

# Copy application code
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python3 -m venv .venv
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Create data directory
RUN mkdir -p /data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/.venv/bin/python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
