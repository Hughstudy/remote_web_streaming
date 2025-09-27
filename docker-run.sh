#!/bin/bash

# AI Web Agent - One Command Deployment Script

echo "🚀 Starting AI Web Agent All-in-One Container"
echo "============================================="

# Set default values
CONTAINER_NAME="ai-web-agent"
IMAGE_NAME="ai-web-agent:latest"

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
# Build docker run command with conditional .env file
DOCKER_RUN_CMD="docker run -d --name $CONTAINER_NAME"

# Add .env file if it exists
if [ -f ".env" ]; then
    DOCKER_RUN_CMD="$DOCKER_RUN_CMD --env-file .env"
fi

# Add environment variables and other options
DOCKER_RUN_CMD="$DOCKER_RUN_CMD \
    -e OPENAI_API_KEY \
    -e OPENAI_BASE_URL \
    -p 3000:3000 \
    -p 8000:8000 \
    -p 5901:5901 \
    --privileged \
    --shm-size=2gb \
    -v /dev/shm:/dev/shm \
    $IMAGE_NAME"

# Execute the command
eval $DOCKER_RUN_CMD

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