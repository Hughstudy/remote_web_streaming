#!/bin/bash

# AI Web Agent - One Command Deployment Script

echo "🚀 Starting AI Web Agent All-in-One Container"
echo "============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Set default values
CONTAINER_NAME="ai-web-agent"
IMAGE_NAME="ai-web-agent:latest"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running again!"
    echo "   Required: OPENROUTER_API_KEY or OPENAI_API_KEY"
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing container..."
    docker stop $CONTAINER_NAME >/dev/null 2>&1
    docker rm $CONTAINER_NAME >/dev/null 2>&1
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

# Get the host IP for display
HOST_IP=$(hostname -I | awk '{print $1}')

# Run the container
echo "🏃 Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env \
    -p 3000:3000 \
    -p 8000:8000 \
    -p 5901:5901 \
    --privileged \
    --shm-size=2gb \
    -v /dev/shm:/dev/shm \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo ""
    echo "🌐 Access Points:"
    echo "   Web UI:     http://$HOST_IP:3000"
    echo "   API:        http://$HOST_IP:8000"
    echo "   VNC Viewer: $HOST_IP:5901 (password: webagent)"
    echo ""
    echo "📱 Quick Test Commands:"
    echo "   curl http://$HOST_IP:8000/"
    echo "   curl -X POST http://$HOST_IP:8000/task -H 'Content-Type: application/json' -d '{\"instruction\": \"Go to Google\"}'"
    echo ""
    echo "🔍 Container Logs:"
    echo "   docker logs -f $CONTAINER_NAME"
    echo ""
    echo "🛑 To Stop:"
    echo "   docker stop $CONTAINER_NAME"
else
    echo "❌ Failed to start container!"
    exit 1
fi