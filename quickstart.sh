#!/bin/bash
# Quick start script for OrcaSlicer API

set -e

echo "🚀 OrcaSlicer API Quick Start"
echo "=============================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "   Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "   Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is installed"
echo ""

# Build the image
echo "📦 Building Docker image..."
docker build -t orcaslicer-api:latest . || {
    echo "❌ Build failed"
    exit 1
}

echo "✓ Build successful"
echo ""

# Start the service
echo "🚀 Starting OrcaSlicer API..."
docker-compose up -d || {
    echo "❌ Failed to start service"
    exit 1
}

echo "✓ Service started"
echo ""

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Check if service is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Service is ready!"
    echo ""
    echo "📍 Access Points:"
    echo "   API Base:    http://localhost:8000"
    echo "   Swagger UI:  http://localhost:8000/docs"
    echo "   ReDoc:       http://localhost:8000/redoc"
    echo "   Health:      http://localhost:8000/health"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Check health: curl http://localhost:8000/health"
    echo "   2. View docs: open http://localhost:8000/docs"
    echo "   3. Run example: python example_usage.py (requires example.stl)"
    echo ""
    echo "🛠️  Useful Commands:"
    echo "   View logs:   docker-compose logs -f"
    echo "   Stop:        docker-compose down"
    echo "   Restart:     docker-compose restart"
    echo ""
    echo "✅ OrcaSlicer API is running!"
else
    echo "❌ Service did not start properly"
    echo "   Check logs with: docker-compose logs"
    exit 1
fi
