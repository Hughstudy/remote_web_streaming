# AI Web Agent - Remote Streaming

An autonomous AI agent that can control web browsers remotely with real-time streaming capabilities.

## Architecture

- **Backend**: FastAPI with WebSocket support
- **Browser Automation**: browser-use library (Playwright-based)
- **AI Engine**: OpenRouter/Gemini for decision making
- **Streaming**: VNC for remote browser display
- **Frontend**: React with noVNC integration

## Project Structure

```
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── docker/           # Docker configurations
└── requirements.txt   # Python dependencies
```

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker installed on your system
- OpenRouter API key (for Gemini 2.5 Flash model)

### One-Command Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd remote-streaming

# Set your API key in environment (or use .env file)
export OPENAI_API_KEY="your_openrouter_api_key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# Build and run everything with one command
bash docker-run.sh
```

The script will:
1. Check if Docker is installed
2. Create `.env` file from template if it doesn't exist
3. Build the Docker image with all dependencies
4. Run the container with all services (backend, frontend, VNC)

### Access Your Application
Once the container is running:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **VNC Viewer**: localhost:5901 (password: `webagent`)

### Quick Test
```bash
# Test the API
curl http://localhost:8000/

# Send a task to the AI agent
curl -X POST http://localhost:8000/task \
  -H 'Content-Type: application/json' \
  -d '{"instruction": "Go to Google and search for AI news"}'
```

### Managing the Container
```bash
# View logs
docker logs -f ai-web-agent

# Stop the container
docker stop ai-web-agent

# Restart with new changes
bash docker-run.sh
```

## Manual Development Setup

If you prefer to run without Docker:

1. Install Python dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `cd frontend && npm install`
3. Start backend: `cd backend && uvicorn main:app --reload`
4. Start frontend: `cd frontend && npm start`

## Environment Variables

Create a `.env` file or set environment variables:

```bash
# AI API Configuration (OpenRouter with Gemini 2.5 Flash)
OPENAI_API_KEY=your_openrouter_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# VNC Configuration
VNC_PASSWORD=webagent
VNC_PORT=5901

# Browser Configuration
BROWSER_HEADLESS=false
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
```