FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (no snap chromium - we'll use Playwright's)
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3-pip python3.11-dev \
    wget gnupg ca-certificates procps \
    xvfb x11vnc websockify \
    xterm x11-utils \
    curl wget git \
    libnss3 libatk-bridge2.0-0 libdrm2 libgtk-3-0 libgbm1 \
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

# Download noVNC from GitHub (proper ES6 modules)
RUN cd /app && \
    wget -O novnc.tar.gz https://github.com/novnc/noVNC/archive/refs/tags/v1.4.0.tar.gz && \
    tar -xzf novnc.tar.gz && \
    mv noVNC-1.4.0 novnc && \
    rm novnc.tar.gz

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

# Start Chrome with debug port (CRUCIAL: This makes browser visible in VNC)
echo "Starting Chrome with debug port..."
export DISPLAY=:1
# Find Playwright's Chromium using the reliable Python method
CHROMIUM_PATH=$(/app/venv/bin/python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.executable_path); p.stop()")

if [ -n "$CHROMIUM_PATH" ]; then
    echo "Found Chrome/Chromium at: $CHROMIUM_PATH"
    # Launch Chrome with debug port and VNC-optimized flags
    $CHROMIUM_PATH \
        --remote-debugging-port=9222 \
        --remote-debugging-address=0.0.0.0 \
        --no-sandbox \
        --disable-dbus \
        --disable-dev-shm-usage \
        --disable-gpu \
        --disable-extensions \
        --disable-web-security \
        --disable-features=VizDisplayCompositor \
        --window-size=1920,1080 \
        --ozone-platform=x11 \
        --use-gl=swiftshader \
        --disable-software-rasterizer \
        --disable-blink-features=AutomationControlled \
        --no-first-run \
        --no-default-browser-check \
        --disable-backgrounding-occluded-windows \
        --disable-renderer-backgrounding \
        --disable-background-timer-throttling \
        --disable-ipc-flooding-protection \
        --user-data-dir=/tmp/chrome-user-data \
        about:blank &
    sleep 5
    echo "Chrome started with debug port 9222"
else
    echo "ERROR: No Chrome/Chromium found!"
fi

# Start backend (with DISPLAY=:1 so it connects to VNC display)
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