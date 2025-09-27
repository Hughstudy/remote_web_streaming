# AI Web Agent - Remote Streaming Architecture

## Project Overview

This project implements an **AI Web Agent** system that enables autonomous browser automation with real-time streaming capabilities. Users can give natural language instructions to an AI agent, which then controls a remote browser while streaming the visual output in real-time.

## Architecture Components

### 1. Backend (FastAPI + Python)
- **Main Application** (`backend/main.py`): FastAPI server with WebSocket support
- **WebSocket Manager** (`backend/websocket_manager.py`): Manages real-time client connections
- **Services Layer**:
  - `browser_service.py`: Browser automation using browser-use library
  - `ai_service.py`: AI decision making with OpenAI/OpenRouter APIs
  - `vnc_service.py`: VNC server management for remote display

### 2. Frontend (React + TypeScript)
- **Main App** (`frontend/src/App.tsx`): Main application interface
- **Components**:
  - `BrowserStream.tsx`: VNC client using noVNC for remote browser display
  - `TaskInput.tsx`: Natural language task input interface
  - `TaskHistory.tsx`: Display of current and past AI agent actions
- **Services**:
  - `websocket.service.ts`: WebSocket client for real-time communication
  - `api.service.ts`: HTTP API calls to backend

### 3. Browser Engine (browser-use + Playwright)
- **Browser Automation**: Uses browser-use library built on Playwright
- **AI Integration**: Connects browser actions to AI decision making
- **Screenshot Analysis**: Provides visual context to AI models

### 4. VNC Streaming Layer
- **Display Server**: Virtual display (Xvfb) for headless browser
- **VNC Server**: Streams browser display over VNC protocol
- **noVNC Client**: Web-based VNC client for frontend display

## Data Flow

1. **User Input**: User enters natural language instruction in frontend
2. **Task Creation**: Frontend sends task to backend via WebSocket
3. **AI Processing**: Backend uses OpenAI/OpenRouter to analyze task
4. **Browser Control**: AI agent controls browser using browser-use
5. **Visual Feedback**: VNC streams browser display to frontend
6. **Progress Updates**: WebSocket sends real-time step updates
7. **Task Completion**: Final results returned to user

## Technology Stack

### Backend Dependencies
```python
# Core framework
fastapi>=0.115.13          # Latest FastAPI with WebSocket support
uvicorn[standard]>=0.24.0  # ASGI server
websockets>=12.0           # WebSocket implementation

# Browser automation
browser-use>=0.1.18        # AI-powered browser automation
playwright>=1.48.0         # Browser engine

# AI/LLM integration
openai>=1.68.0            # OpenAI Python SDK with structured outputs
anthropic>=0.39.0         # Claude API support

# Utilities
python-dotenv>=1.0.0      # Environment variables
pydantic>=2.5.0           # Data validation
Pillow>=10.1.0            # Image processing
```

### Frontend Dependencies
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "@novnc/novnc": "^1.4.0",
  "socket.io-client": "^4.7.0",
  "axios": "^1.6.0",
  "tailwindcss": "^3.3.0"
}
```

## Environment Configuration

```bash
# AI API Keys
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key

# VNC Settings
VNC_PASSWORD=secure_password
VNC_PORT=5901
VNC_DISPLAY=:1

# Browser Settings
BROWSER_HEADLESS=false
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080

# Server Settings
API_HOST=0.0.0.0
API_PORT=8000
```

## Development Setup

1. **Clone and setup environment**:
```bash
git clone <repository>
cd remote-streaming
uv venv --python 3.11
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. **Install Python dependencies**:
```bash
uv pip install -r requirements.txt
uvx playwright install chromium --with-deps
```

3. **Setup frontend**:
```bash
cd frontend
npm install
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Start development servers**:
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm start
```

## API Endpoints

### HTTP Endpoints
- `GET /` - Health check
- `POST /task` - Create new AI task

### WebSocket Endpoints
- `ws://localhost:8000/ws` - Real-time task execution and updates

### WebSocket Message Types
```typescript
// Client to Server
{
  "type": "execute_task",
  "task_id": "uuid",
  "instruction": "Find flight prices to Tokyo"
}

// Server to Client
{
  "type": "step_update",
  "task_id": "uuid",
  "step_number": 1,
  "action": "navigate",
  "description": "Opening airline website..."
}
```

## Security Considerations

- API keys stored in environment variables
- VNC password protection
- CORS configured for frontend domain
- WebSocket connection validation
- Browser sandbox isolation

## Deployment

### Docker Support
- Dockerfile for backend service
- docker-compose.yml for full stack deployment
- VNC display configuration for containerized browsers

### Production Considerations
- Reverse proxy (nginx) for WebSocket handling
- SSL/TLS termination
- Browser resource limits
- VNC security hardening

## Testing Strategy

- Unit tests for services using pytest
- Browser automation tests with Playwright
- WebSocket connection testing
- End-to-end workflow validation

## Error Handling

- Graceful AI API failures with fallback responses
- Browser crash recovery and restart
- WebSocket reconnection logic
- VNC connection error handling

## Performance Optimization

- Browser resource pooling
- WebSocket message batching
- VNC frame rate optimization
- AI response caching for common patterns

# Current System Status and Issues

## Connection Status (Latest Update)

### ✅ RESOLVED ISSUES:
1. **VNC Connection**: VNC server working correctly on port 5901, websockify proxy on port 6901
2. **WebSocket Backend**: Backend WebSocket endpoint working at `ws://localhost:8000/ws`
3. **Nginx Proxy**: Successfully proxying WebSocket connections from port 3000 to 8000
4. **React Frontend Issues**: Completely bypassed by implementing bulletproof vanilla JavaScript frontend

### 🔧 CURRENT ISSUE:
**Task Execution Error**: User receives "error" response when submitting tasks via bulletproof frontend.

**Root Cause**: Frontend was sending both `task_id` and `instruction` in WebSocket message, but backend expects:
1. First: Create task via HTTP POST `/api/task` with `{"instruction": "task description"}`
2. Then: Execute via WebSocket with `{"type": "execute_task", "task_id": "returned_id"}`

**Fix Applied**: Modified `submitTask()` function in Dockerfile to use correct two-step process.

### 🚀 BULLETPROOF FRONTEND IMPLEMENTATION:
- **Location**: Embedded directly in Dockerfile (lines 51-214)
- **Approach**: Vanilla JavaScript/HTML/CSS - no build process, no dependencies
- **Features**: WebSocket connection, VNC display via noVNC, task submission, real-time logging
- **Reliability**: Works from fresh Docker build with zero external dependencies

### 🐳 DOCKER DEPLOYMENT:
- **Build**: `docker build -t ai-web-agent .`
- **Run**: Environment variables should be read from host environment
  ```bash
  docker run -d --name ai-web-agent \
    -p 3000:3000 -p 8000:8000 -p 5901:5901 -p 6901:6901 \
    -e OPENAI_API_KEY="$OPENROUTER_API_KEY" \
    -e OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
    ai-web-agent
  ```

### 📋 TASK EXECUTION WORKFLOW:
1. **Frontend**: POST `/api/task` → `{"instruction": "user task"}`
2. **Backend**: Returns `{"task_id": "uuid", "instruction": "user task"}`
3. **Frontend**: WebSocket send `{"type": "execute_task", "task_id": "uuid"}`
4. **Backend**: Executes task using browser-use + AI agent
5. **Real-time**: WebSocket streams progress updates to frontend
6. **VNC**: Browser actions visible in real-time via noVNC client

### 🔒 TASK CONCURRENCY CONTROL:
- **Implemented**: Backend blocks new tasks if one is already running
- **Location**: `backend/services/ai_service.py` - `current_running_task` tracking
- **Behavior**: Returns error if task submitted while another is executing

### 🛠 DEBUGGING APPROACH USED:
1. **Layer-by-layer testing**: VNC → websockify → nginx → WebSocket → frontend
2. **Direct WebSocket testing**: Used curl and Python scripts to verify backend
3. **Root cause analysis**: React JSX runtime issues preventing frontend execution
4. **Bulletproof replacement**: Eliminated all complex dependencies

### 🎯 ULTRA-SIMPLIFIED SINGLE-PORT ARCHITECTURE:

#### 🚀 EVERYTHING ON PORT 8000 - NO PROXIES, NO COMPLEXITY!

#### 1. EMBEDDED FRONTEND (FastAPI serves HTML)
```
Frontend URL: http://localhost:8000/
HTML: Embedded directly in FastAPI endpoint - no static files!
```

#### 2. DIRECT HTTP APIs (no proxy)
```
Health Check:
  GET http://localhost:8000/api/health
  Response: {"status": "running", "message": "AI Web Agent API is active"}

VNC Info:
  GET http://localhost:8000/vnc_info
  Response: {"type": "vnc_info", "data": {"ws_url": "ws://localhost:6901", ...}}

Task Creation:
  POST http://localhost:8000/task
  Payload: {"instruction": "search iPhone"}
  Response: {"task_id": "uuid", "status": "created"}

Task Execution:
  POST http://localhost:8000/execute_task
  Payload: {"task_id": "uuid"}
  Response: {"status": "execution_started", "message": "Connect to WebSocket for updates"}
```

#### 3. DIRECT WEBSOCKET (no proxy) - REAL-TIME STREAMING
```
WebSocket: ws://localhost:8000/ws
Purpose: Real-time task progress updates
Messages:
  - Frontend→Backend: {"type": "execute_task", "task_id": "uuid"}
  - Backend→Frontend: {"type": "step_update", "step_number": 1, "description": "..."}
  - Backend→Frontend: {"type": "task_complete", "task_id": "uuid"}
```

#### 4. DIRECT VNC CONNECTION (no proxy)
```
VNC WebSocket URL: ws://localhost:6901
Direct Connection: Browser → websockify:6901 → x11vnc:5901
```

#### 5. INTERNAL VNC CHAIN (unchanged)
```
Browser (in container) → DISPLAY=:1 → Xvfb:1 → x11vnc:5901 → websockify:6901
```

#### 🔍 ULTRA-SIMPLE CONNECTION TEST PLAN:
1. 📋 Test embedded frontend: `curl http://localhost:8000/`
2. 📋 Test health check: `curl http://localhost:8000/api/health`
3. 📋 Test VNC info: `curl http://localhost:8000/vnc_info`
4. 📋 Test task creation: `curl -X POST http://localhost:8000/task -H 'Content-Type: application/json' -d '{"instruction":"test"}'`
5. 📋 Test WebSocket streaming: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" ws://localhost:8000/ws`
6. 📋 Test VNC WebSocket: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" ws://localhost:6901`

#### 🎯 ULTRA-SIMPLIFIED ARCHITECTURE BENEFITS:
- ✅ Single port 8000 for everything (frontend + APIs + WebSocket)
- ✅ No nginx proxy complexity
- ✅ No static files or build process
- ✅ Embedded HTML in FastAPI
- ✅ Direct connections - no path translation
- ✅ Zero configuration issues
- ✅ Maximum reliability and simplicity
