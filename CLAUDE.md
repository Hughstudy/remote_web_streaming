# AI Web Agent - Remote Streaming Architecture

## Project Overview

This project implements an **AI Web Agent** system that enables autonomous browser automation with real-time streaming capabilities. Users can give natural language instructions to an AI agent, which then controls a remote browser while streaming the visual output in real-time.

## Architecture Components

### 1. Backend (FastAPI + Python)
- **Main Application** (`backend/main.py`): FastAPI server with embedded frontend HTML
- **WebSocket Manager** (`backend/websocket_manager.py`): Manages real-time client connections
- **Services Layer**:
  - `browser_service.py`: Browser automation using browser-use library with Chrome debug port 9222
  - `ai_service.py`: AI decision making with OpenAI/OpenRouter APIs (Google Gemini fallback)
  - `vnc_service.py`: VNC server management for remote display (unused - Docker handles VNC directly)

### 2. Frontend (Embedded Vanilla JavaScript)
- **Embedded HTML**: Directly served by FastAPI at `/` endpoint
- **Vanilla JavaScript**: No React dependencies or build process
- **noVNC Integration**: ES6 modules loaded from `/novnc` static path
- **WebSocket Client**: Native browser WebSocket API
- **Zero Dependencies**: No npm packages or build tools required

### 3. Browser Engine (browser-use + Chrome)
- **Browser Automation**: Uses browser-use library with Playwright, connects to existing Chrome on port 9222
- **AI Integration**: Connects browser actions to AI decision making
- **Chrome Configuration**: Optimized for VNC environment with X11 display
- **Playwright Setup**: `cdp_url='http://localhost:9222'` for existing Chrome connection

### 4. VNC Streaming Layer
- **Display Server**: Xvfb virtual display :1 at 1920x1080x24
- **VNC Server**: x11vnc on port 5901 with no authentication
- **WebSocket Bridge**: websockify on port 6901 converts VNC to WebSocket
- **Browser Display**: Chrome runs on DISPLAY=:1 through Xvfb

## Data Flow

1. **User Input**: User enters natural language instruction in embedded frontend at port 8000
2. **Task Creation**: Frontend sends HTTP POST to `/task` with instruction
3. **AI Processing**: Backend uses OpenRouter (Google Gemini fall back) to analyze task
4. **Browser Control**: AI agent controls browser using browser-use + existing Chrome
5. **Visual Feedback**: VNC streams browser display (:1→5901→6901) to frontend via noVNC
6. **Progress Updates**: WebSocket on port 8000 sends real-time step updates
7. **Task Completion**: Final results returned to user

## Technology Stack

### Backend Dependencies
```python
# Core framework
fastapi>=0.115.13          # Latest FastAPI with WebSocket support
uvicorn[standard]>=0.24.0  # ASGI server
websockets>=12.0           # WebSocket implementation

# Browser automation
browser-use>=0.1.48        # AI-powered browser automation with Chrome debug
playwright>=1.48.0         # Browser engine (Chromium)

# AI/LLM integration
openai>=1.68.0            # OpenAI Python SDK with OpenRouter support
anthropic>=0.39.0         # Claude API support

# VNC/Streaming utilities
vncdotool>=1.2.0          # VNC client tools
Pillow>=10.1.0            # Image processing
```

### Frontend Dependencies
```json
{
  "novnc": "ES6 modules from /novnc static path",
  "javascript": "Native browser APIs - no build dependencies"
}
```

## Environment Configuration

### AI Settings
```bash
# Primary OpenRouter with Google Gemini fallback
OPENAI_API_KEY=your_openrouter_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
# Model selection: google/gemini-2.5-flash (OpenRouter) or gpt-4o (OpenAI)
```

### VNC Settings
```bash
VNC_PORT=5901              # Direct VNC server port
VNC_PASSWORD=webagent      # Optional password (currently disabled in Docker)
VNC_DISPLAY=:1             # Xvfb virtual display
BROWSER_WIDTH=1920         # Browser viewport width
BROWSER_HEIGHT=1080        # Browser viewport height
```

### Browser Configuration
```bash
BROWSER_HEADLESS=false     # Chrome runs in full GUI mode for VNC
CHROME_FLAGS=
  --remote-debugging-port=9222
  --window-size=1920,1080
  --no-sandbox
  --ozone-platform=x11
  --use-gl=swiftshader
```

## API Specifications

### HTTP Endpoints

#### Health Check
```http
GET /api/health
Response: {"status": "running", "message": "AI Web Agent API is active"}
```

#### Task Creation
```http
POST /task
Request: {"instruction": "AI task description"}
Response: {"task_id": "uuid", "status": "created"}
Error: {"error": "Another task is running", "status": "blocked"}
```

#### Task Execution (HTTP)
```http
POST /execute_task
Request: {"task_id": "uuid"}
Response: {"status": "execution_started", "message": "Connect to WebSocket for updates"}
```

#### VNC Information
```http
GET /vnc_info
Response: {
  "type": "vnc_info",
  "data": {
    "host": "localhost",
    "port": 5901,
    "ws_url": "ws://localhost:6901"
  }
}
```

### WebSocket Message Formats

#### Client to Server
```json
{"type": "execute_task", "task_id": "uuid"}
{"type": "get_vnc_info"}
```

#### Server to Client
```json
{"type": "task_created", "task_id": "uuid", "instruction": "task"}
{"type": "task_execution_started", "task_id": "uuid"}
{"type": "step_update", "step_number": 1, "action": "navigate", "description": "..."}
{"type": "task_complete", "task_id": "uuid", "status": "completed"}
{"type": "error", "message": "error description"}
```

## Port Configuration

### Core Service Ports
```
Port 8000: FastAPI Backend (HTTP + WebSocket + Frontend)
├── HTTP APIs (/task, /execute_task, /api/health, /vnc_info)
├── WebSocket (ws://localhost:8000/ws)
├── Embedded frontend HTML at /
└── Static noVNC files at /novnc

Port 5901: VNC Server (x11vnc)
├── Direct VNC protocol
├── Connects to Xvfb display :1
└── No authentication configured

Port 6901: WebSocket VNC Proxy (websockify)
├── Converts VNC to WebSocket
├── Frontend connects via ws://localhost:6901
└── Bridges noVNC client to VNC server

Port 9222: Chrome Debug Port
├── Used by browser-use library
├── Remote debugging interface
└── Required for Playwright connection
```

### Internal Process Chain
```
Chrome Browser → DISPLAY=:1 → Xvfb:1 → x11vnc:5901 → websockify:6901 → Frontend noVNC
```

## Development Setup

### Docker Deployment (Recommended)
```bash
# Build and run with single command
docker build -t ai-web-agent .
docker run -d -p 8000:8000 -p 6901:6901 \
  -e OPENAI_API_KEY="$OPENROUTER_API_KEY" \
  -e OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
  ai-web-agent
```

### Manual Development Setup
```bash
# Clone and setup environment
git clone <repository>
cd remote-streaming
uv venv --python 3.11
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt
uvx playwright install chromium --with-deps

# Start services (in separate terminals)
cd backend && uvicorn main:app --reload
# VNC and Chrome are handled by Docker or manual setup
```

## Current Architecture Status

### ✅ Working Components
1. **Embedded Frontend**: Vanilla JavaScript served directly by FastAPI
2. **VNC Streaming**: Real-time browser visualization via websockify
3. **WebSocket APIs**: Real-time task progress updates
4. **Task Execution**: AI-driven browser automation with concurrency control
5. **Docker Deployment**: Single-container deployment with VNC environment

### 🔧 Configuration Changes Required
1. **VNC Password**: Add password protection for production (currently disabled)
2. **Port Simplification**: Single port 8000 handles everything
3. **Chrome Debug Port**: Ensure port 9222 is accessible for browser-use

### 🎯 Key Architecture Decisions
- **Embedded Frontend**: Eliminates React build complexity and dependencies
- **Single Port Design**: Port 8000 serves APIs, WebSocket, and frontend HTML
- **VNC Integration**: Direct Chrome running on virtual display with streamable output
- **Zero Frontend Dependencies**: Pure vanilla JavaScript with ES6 modules
- **Chrome Debug Port**: browser-use connects to existing Chrome instance for reliability

## Security Considerations
- **VNC Access**: Currently no password for demonstration (use -nopw flag)
- **CORS**: Configured for all origins (development only)
- **API Keys**: Environment variable based configuration
- **Chrome Sandbox**: Disabled for Docker compatibility

## Performance Optimization
- **Browser Resource Pooling**: Single Chrome instance for all tasks
- **VNC Frame Optimization**: Disabled damage tracking for better performance
- **WebSocket Efficiency**: Direct connection with no proxy overhead
- **Embedded Frontend**: No build process or static file serving delays

## Error Handling
- **Task Concurrency**: Backend blocks new tasks while one is running
- **VNC Connection**: Graceful fallback if websockify fails
- **Browser Recovery**: Chrome instance persistence with CDP connection
- **WebSocket Resilience**: Automatic reconnection handling in frontend

## Testing Strategy
```bash
# Test all components in sequence
curl http://localhost:8000/api/health                              # Health check
curl http://localhost:8000/vnc_info                              # VNC info
curl -X POST http://localhost:8000/task -d '{"instruction":"test"}' # Task creation
# Then connect WebSocket for task execution and VNC for visual feedback
```

## Deployment Commands
```bash
# Production deployment with proper port mapping
docker run -d --name ai-web-agent \
  -p 8000:8000 -p 6901:6901 \
  -e OPENAI_API_KEY="$OPENROUTER_API_KEY" \
  -e OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
  ai-web-agent

# Access points:
# Main Interface: http://localhost:8000/
# API Health: http://localhost:8000/api/health
# VNC WebSocket: ws://localhost:6901
```