#!/bin/bash
# CDSI Bridge Container Entrypoint
# Author: bdstest
# Copyright: 2025 CDSI - Compliance Data Systems Insights

set -euo pipefail

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Starting CDSI Cloud Bridge..."

# Environment variables with defaults
export CUSTOMER_ID=${CUSTOMER_ID:-"demo"}
export BRIDGE_ARCHITECTURE=${BRIDGE_ARCHITECTURE:-"reverse_tunnel"}
export BRIDGE_SECRET=${BRIDGE_SECRET:-"$(openssl rand -hex 32)"}
export CUSTOMER_CIDR=${CUSTOMER_CIDR:-"10.0.0.0/16"}
export SSL_CERT_PATH=${SSL_CERT_PATH:-"/app/ssl/bridge.crt"}
export SSL_KEY_PATH=${SSL_KEY_PATH:-"/app/ssl/bridge.key"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

log "Configuration:"
log "  Customer ID: $CUSTOMER_ID"
log "  Architecture: $BRIDGE_ARCHITECTURE"
log "  Customer CIDR: $CUSTOMER_CIDR"
log "  SSL Cert: $SSL_CERT_PATH"

# Create runtime configuration
cat > /app/config/runtime.yaml << EOF
bridge:
  customer_id: "$CUSTOMER_ID"
  architecture: "$BRIDGE_ARCHITECTURE"
  secret: "$BRIDGE_SECRET"
  customer_cidr: "$CUSTOMER_CIDR"
  
network:
  bridge_port: $BRIDGE_PORT
  api_port: $API_PORT
  monitoring_port: $MONITORING_PORT
  
ssl:
  cert_path: "$SSL_CERT_PATH"
  key_path: "$SSL_KEY_PATH"
  
logging:
  level: "$LOG_LEVEL"
  path: "/app/logs"
  
data:
  path: "/app/data"
  
timestamp: "$(date -Iseconds)"
EOF

# Generate nginx configuration based on architecture
log "Configuring nginx for architecture: $BRIDGE_ARCHITECTURE"

case "$BRIDGE_ARCHITECTURE" in
    "reverse_tunnel")
        # Reverse tunnel configuration
        cat > /etc/nginx/nginx.conf << 'NGINX_EOF'
user www-data;
worker_processes auto;
pid /var/run/nginx/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Logging
    access_log /app/logs/nginx-access.log;
    error_log /app/logs/nginx-error.log;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;
    
    upstream bridge_backend {
        server localhost:8080;
    }
    
    # HTTPS server
    server {
        listen 8443 ssl http2;
        server_name _;
        
        ssl_certificate /app/ssl/bridge.crt;
        ssl_certificate_key /app/ssl/bridge.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        
        # WebSocket tunnel endpoint
        location /tunnel {
            proxy_pass http://bridge_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 86400;
        }
        
        # API endpoints
        location /api/ {
            proxy_pass http://bridge_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            proxy_pass http://bridge_backend;
            proxy_set_header Host $host;
            access_log off;
        }
        
        # Metrics endpoint
        location /metrics {
            proxy_pass http://bridge_backend;
            proxy_set_header Host $host;
            access_log off;
        }
        
        # Default response
        location / {
            return 200 'CDSI Bridge Active';
            add_header Content-Type text/plain;
        }
    }
}
NGINX_EOF
        ;;
        
    "container_bridge")
        # Container bridge configuration  
        cat > /etc/nginx/nginx.conf << 'NGINX_EOF'
user www-data;
worker_processes auto;
pid /var/run/nginx/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    access_log /app/logs/nginx-access.log;
    error_log /app/logs/nginx-error.log;
    
    upstream api_backend {
        server localhost:8080;
    }
    
    # HTTP server for container communication
    server {
        listen 8443 ssl;
        server_name _;
        
        ssl_certificate /app/ssl/bridge.crt;
        ssl_certificate_key /app/ssl/bridge.key;
        
        # Container API
        location /container/ {
            proxy_pass http://api_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        
        # Health check
        location /health {
            proxy_pass http://api_backend/health;
            access_log off;
        }
    }
}
NGINX_EOF
        ;;
        
    *)
        # Default API proxy configuration
        cat > /etc/nginx/nginx.conf << 'NGINX_EOF'
user www-data;
worker_processes auto;
pid /var/run/nginx/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    access_log /app/logs/nginx-access.log;
    error_log /app/logs/nginx-error.log;
    
    upstream api_backend {
        server localhost:8080;
    }
    
    server {
        listen 8443 ssl;
        server_name _;
        
        ssl_certificate /app/ssl/bridge.crt;
        ssl_certificate_key /app/ssl/bridge.key;
        
        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
NGINX_EOF
        ;;
esac

# Validate nginx configuration
log "Validating nginx configuration..."
nginx -t

# Create supervisor configuration
log "Configuring supervisor..."
cat > /etc/supervisor/conf.d/supervisord.conf << EOF
[supervisord]
nodaemon=true
user=root
logfile=/app/logs/supervisord.log
pidfile=/var/run/supervisord.pid

[program:nginx]
command=nginx -g "daemon off;"
autorestart=true
stdout_logfile=/app/logs/nginx-stdout.log
stderr_logfile=/app/logs/nginx-stderr.log
user=root

[program:bridge-api]
command=python3 -m src.bridge.api_server
directory=/app
autorestart=true
stdout_logfile=/app/logs/bridge-api-stdout.log
stderr_logfile=/app/logs/bridge-api-stderr.log
user=cdsi
environment=PYTHONPATH="/app/src"

[program:bridge-tunnel]
command=python3 -m src.bridge.tunnel_server
directory=/app
autorestart=true
stdout_logfile=/app/logs/bridge-tunnel-stdout.log
stderr_logfile=/app/logs/bridge-tunnel-stderr.log
user=cdsi
environment=PYTHONPATH="/app/src"

[program:metrics-exporter]
command=python3 -m src.bridge.metrics_exporter
directory=/app
autorestart=true
stdout_logfile=/app/logs/metrics-stdout.log
stderr_logfile=/app/logs/metrics-stderr.log
user=cdsi
environment=PYTHONPATH="/app/src"

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
EOF

# Create bridge application stub (placeholder for now)
log "Creating bridge application..."
mkdir -p /app/src/bridge

cat > /app/src/bridge/api_server.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
CDSI Bridge API Server
Author: bdstest
"""

import asyncio
import json
import logging
from datetime import datetime
from aiohttp import web, WSMsgType
import yaml
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeAPIServer:
    def __init__(self):
        self.config = self._load_config()
        self.app = web.Application()
        self._setup_routes()
        
    def _load_config(self):
        """Load runtime configuration"""
        try:
            with open('/app/config/runtime.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _setup_routes(self):
        """Setup API routes"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/status', self.get_status)
        self.app.router.add_get('/metrics', self.get_metrics)
        self.app.router.add_post('/api/v1/tunnel', self.handle_tunnel_request)
        self.app.router.add_get('/tunnel', self.websocket_handler)
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'customer_id': self.config.get('bridge', {}).get('customer_id', 'unknown')
        })
    
    async def get_status(self, request):
        """Status endpoint"""
        return web.json_response({
            'bridge': {
                'status': 'active',
                'customer_id': self.config.get('bridge', {}).get('customer_id'),
                'architecture': self.config.get('bridge', {}).get('architecture'),
                'uptime': 'running'
            },
            'timestamp': datetime.now().isoformat()
        })
    
    async def get_metrics(self, request):
        """Prometheus metrics endpoint"""
        metrics = [
            '# HELP cdsi_bridge_status Bridge status (1=up, 0=down)',
            '# TYPE cdsi_bridge_status gauge',
            'cdsi_bridge_status{customer_id="' + self.config.get('bridge', {}).get('customer_id', 'unknown') + '"} 1',
            '',
            '# HELP cdsi_connections_total Total connections',
            '# TYPE cdsi_connections_total counter', 
            'cdsi_connections_total 0',
            ''
        ]
        return web.Response(text='\n'.join(metrics), content_type='text/plain')
    
    async def handle_tunnel_request(self, request):
        """Handle tunnel API requests"""
        return web.json_response({
            'message': 'Tunnel request received',
            'customer_id': self.config.get('bridge', {}).get('customer_id'),
            'timestamp': datetime.now().isoformat()
        })
    
    async def websocket_handler(self, request):
        """WebSocket tunnel handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        logger.info(f"WebSocket connection established for customer: {self.config.get('bridge', {}).get('customer_id')}")
        
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                logger.info(f"Received message: {data}")
                
                # Echo response for now
                await ws.send_text(json.dumps({
                    'type': 'response',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }))
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
        
        logger.info("WebSocket connection closed")
        return ws
    
    async def start_server(self):
        """Start the API server"""
        port = int(os.environ.get('API_PORT', 8080))
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"Bridge API server started on port {port}")
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            pass
        finally:
            await runner.cleanup()

if __name__ == '__main__':
    server = BridgeAPIServer()
    asyncio.run(server.start_server())
PYTHON_EOF

# Create tunnel server stub
cat > /app/src/bridge/tunnel_server.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
CDSI Bridge Tunnel Server
Author: bdstest
"""

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TunnelServer:
    def __init__(self):
        self.running = False
        
    async def start(self):
        """Start tunnel server"""
        logger.info("Starting CDSI Tunnel Server...")
        self.running = True
        
        while self.running:
            # Tunnel server logic here
            await asyncio.sleep(30)
            logger.info(f"Tunnel server heartbeat: {datetime.now()}")
    
    def stop(self):
        """Stop tunnel server"""
        self.running = False

if __name__ == '__main__':
    server = TunnelServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        server.stop()
PYTHON_EOF

# Create metrics exporter stub
cat > /app/src/bridge/metrics_exporter.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
CDSI Bridge Metrics Exporter
Author: bdstest
"""

import asyncio
import logging
from datetime import datetime
import psutil
import json

logger = logging.getLogger(__name__)

class MetricsExporter:
    def __init__(self):
        self.running = False
        
    async def collect_metrics(self):
        """Collect system and application metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            },
            'bridge': {
                'status': 'active',
                'connections': 0
            }
        }
    
    async def start(self):
        """Start metrics collection"""
        logger.info("Starting CDSI Metrics Exporter...")
        self.running = True
        
        while self.running:
            try:
                metrics = await self.collect_metrics()
                
                # Write metrics to file for Prometheus scraping
                with open('/app/data/metrics.json', 'w') as f:
                    json.dump(metrics, f, indent=2)
                
                await asyncio.sleep(15)  # Collect every 15 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Stop metrics collection"""
        self.running = False

if __name__ == '__main__':
    exporter = MetricsExporter()
    try:
        asyncio.run(exporter.start())
    except KeyboardInterrupt:
        exporter.stop()
PYTHON_EOF

# Create __init__.py files
touch /app/src/__init__.py
touch /app/src/bridge/__init__.py

# Set ownership and permissions
chown -R cdsi:cdsi /app/src
chown -R cdsi:cdsi /app/data
chown -R cdsi:cdsi /app/logs

# Create status file
cat > /app/data/bridge-status.json << EOF
{
  "customer_id": "$CUSTOMER_ID",
  "architecture": "$BRIDGE_ARCHITECTURE",
  "status": "starting",
  "started_at": "$(date -Iseconds)",
  "container": true,
  "endpoints": {
    "api": "http://localhost:8080",
    "bridge": "https://localhost:8443",
    "health": "https://localhost:8443/health"
  }
}
EOF

chown cdsi:cdsi /app/data/bridge-status.json

log "Starting supervisor to manage all services..."

# Update status to running
sed -i 's/"starting"/"running"/' /app/data/bridge-status.json

# Start supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf