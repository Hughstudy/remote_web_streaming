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

## Getting Started

1. Install Python dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `cd frontend && npm install`
3. Start backend: `cd backend && uvicorn main:app --reload`
4. Start frontend: `cd frontend && npm start`

## Environment Variables

Create a `.env` file with **ONE** of these AI API options:

**Option 1: OpenRouter + Gemini 2.5 Flash (Recommended)**
```bash
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
VNC_PASSWORD=your_vnc_password
```

**Option 2: OpenAI (Alternative)**
```bash
OPENAI_API_KEY=your_openai_key_here
VNC_PASSWORD=your_vnc_password
```