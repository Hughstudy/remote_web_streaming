FROM ubuntu:22.04

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python and Node.js
    python3.11 python3.11-venv python3-pip python3.11-dev \
    nodejs npm \
    # Browser automation
    wget gnupg ca-certificates procps \
    chromium-browser chromium-chromedriver \
    # VNC and GUI
    xvfb x11vnc fluxbox \
    xterm \
    # Network tools
    curl wget git \
    # Utilities
    supervisor nginx \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
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

# Install Node.js dependencies and build frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci

COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Copy nginx configuration for frontend
COPY <<EOF /etc/nginx/sites-available/frontend
server {
    listen 3000;
    root /app/frontend/build;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /etc/nginx/sites-available/frontend /etc/nginx/sites-enabled/

# Create supervisor configuration
COPY <<EOF /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true
user=root

[program:xvfb]
command=Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
autostart=true
autorestart=true
stdout_logfile=/var/log/xvfb.log
stderr_logfile=/var/log/xvfb_error.log

[program:fluxbox]
command=fluxbox -display :1
environment=DISPLAY=:1
autostart=true
autorestart=true
stdout_logfile=/var/log/fluxbox.log
stderr_logfile=/var/log/fluxbox_error.log

[program:x11vnc]
command=x11vnc -display :1 -forever -shared -rfbport 5901 -nopw -noxdamage -noxfixes -noxcomposite
environment=DISPLAY=:1
autostart=true
autorestart=true
stdout_logfile=/var/log/x11vnc.log
stderr_logfile=/var/log/x11vnc_error.log

[program:backend]
command=/app/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
directory=/app
environment=DISPLAY=:1,PATH="/app/venv/bin:%(ENV_PATH)s"
autostart=true
autorestart=true
stdout_logfile=/var/log/backend.log
stderr_logfile=/var/log/backend_error.log

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/var/log/nginx.log
stderr_logfile=/var/log/nginx_error.log
EOF

# Create startup script
COPY <<'EOF' /start.sh
#!/bin/bash

# Create necessary directories
mkdir -p /var/log /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# Wait a moment for services to initialize
echo "Starting AI Web Agent services..."

# Start supervisor (manages all services)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
EOF

RUN chmod +x /start.sh

# Set environment variables
ENV DISPLAY=:1
ENV BROWSER_HEADLESS=false
ENV VNC_PASSWORD=webagent
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose ports
# 3000: Frontend (Web UI)
# 8000: Backend API
# 5901: VNC Server
EXPOSE 3000 8000 5901

# Create .env file template
COPY <<EOF /app/.env
# AI API Configuration (Choose ONE)
# Option 1: OpenRouter + Gemini 2.5 Flash (Recommended)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Option 2: OpenAI (Alternative)
# OPENAI_API_KEY=your_openai_api_key_here

# System Configuration
DISPLAY=:1
BROWSER_HEADLESS=false
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
VNC_PASSWORD=webagent
VNC_PORT=5901
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ && curl -f http://localhost:3000/ || exit 1

# Start all services
CMD ["/start.sh"]