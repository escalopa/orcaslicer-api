# OrcaSlicer API Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    curl \
    libgl1 \
    libegl1 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libwebkit2gtk-4.0-37 \
    libjavascriptcoregtk-4.0-18 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libglib2.0-0 \
    libdbus-1-3 \
    libwayland-client0 \
    libwayland-egl1 \
    libxrender1 \
    libxrandr2 \
    libxinerama1 \
    libxi6 \
    libxcursor1 \
    libfontconfig1 \
    libglu1-mesa \
    libxkbcommon0 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Download and install OrcaSlicer
ARG ORCA_VERSION=2.3.1

# Download OrcaSlicer AppImage with timeout
RUN curl --max-time 300 --connect-timeout 60 -L \
    "https://github.com/OrcaSlicer/OrcaSlicer/releases/download/v${ORCA_VERSION}/OrcaSlicer_Linux_AppImage_Ubuntu2404_V${ORCA_VERSION}.AppImage" \
    -o /usr/local/bin/orcaslicer \
    && chmod +x /usr/local/bin/orcaslicer \
    && echo "✓ OrcaSlicer v${ORCA_VERSION} installed successfully"

# Verify installation
RUN ls -lh /usr/local/bin/orcaslicer \
    && /usr/local/bin/orcaslicer --version || echo "Note: Version check may not work without display"

# Copy application code
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Create data directory
RUN mkdir -p /data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
