FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3-pip python3.11-dev \
    wget gnupg ca-certificates procps \
    chromium-browser chromium-chromedriver \
    xvfb x11vnc websockify \
    xterm x11-utils \
    curl wget git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy Python requirements and install
COPY requirements.txt .
RUN uv venv --python 3.11 /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN uv pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy backend code
COPY backend/ ./backend/

# Create simple startup script (NO SUPERVISOR)
COPY <<'EOF' /start.sh
#!/bin/bash
echo "🚀 Starting AI Web Agent (simple mode)"

# Clean up
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# Start Xvfb (virtual display)
echo "Starting Xvfb..."
Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
sleep 3

# Start x11vnc (VNC server)
echo "Starting x11vnc..."
x11vnc -display :1 -forever -shared -rfbport 5901 -nopw -noxdamage -noxfixes -noxcomposite -noxrecord &
sleep 2

# Start websockify (WebSocket proxy)
echo "Starting websockify..."
websockify 6901 localhost:5901 &
sleep 2

# Start backend (with DISPLAY=:1 so browser runs on VNC display)
echo "Starting backend..."
export DISPLAY=:1
exec /app/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /start.sh

# Environment
ENV DISPLAY=:1
ENV BROWSER_HEADLESS=false
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose ports
EXPOSE 8000 5901 6901

# Create .env template
COPY <<EOF /app/.env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
DISPLAY=:1
BROWSER_HEADLESS=false
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["/start.sh"]