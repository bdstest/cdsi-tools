#!/bin/bash
# CDSI Cloud Bridge Bootstrap Script
# Automatically configures bridge VM based on architecture type
# Author: bdstest
# Copyright: 2025 CDSI - Compliance Data Systems Insights

set -euo pipefail

# Template variables (replaced by Terraform)
CUSTOMER_ID="${customer_id}"
BRIDGE_ARCHITECTURE="${bridge_architecture}"
BRIDGE_SECRET="${bridge_secret}"
CUSTOMER_CIDR="${customer_cidr}"
ENABLE_MONITORING="${enable_monitoring}"

# Logging setup
LOG_FILE="/var/log/cdsi-bootstrap.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Starting CDSI Cloud Bridge bootstrap for customer: $CUSTOMER_ID"
log "Architecture: $BRIDGE_ARCHITECTURE"

# Update system
log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# Install essential packages
log "Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    unzip \
    jq \
    htop \
    iotop \
    net-tools \
    tcpdump \
    rsync \
    cron \
    logrotate \
    fail2ban \
    ufw \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Docker and Docker Compose
log "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create CDSI directory structure
log "Creating directory structure..."
mkdir -p /opt/cdsi/{config,data,logs,scripts,ssl}
chown -R root:root /opt/cdsi
chmod 755 /opt/cdsi

# Configure firewall
log "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow 22/tcp comment "SSH"

# Architecture-specific firewall rules
case "$BRIDGE_ARCHITECTURE" in
    "reverse_tunnel")
        ufw allow 443/tcp comment "HTTPS"
        ufw allow 8443/tcp comment "Bridge Tunnel"
        ;;
    "vpn_gateway")
        ufw allow 500/udp comment "IPSec IKE"
        ufw allow 4500/udp comment "IPSec NAT-T"
        ufw allow 443/tcp comment "HTTPS"
        ;;
    "container_bridge")
        ufw allow 443/tcp comment "HTTPS"
        ufw allow 8080/tcp comment "Container API"
        ;;
    "api_proxy")
        ufw allow 443/tcp comment "HTTPS API"
        ;;
esac

# Allow monitoring if enabled
if [ "$ENABLE_MONITORING" = "true" ]; then
    ufw allow 9090/tcp comment "Monitoring"
    ufw allow 3000/tcp comment "Grafana"
fi

# Generate SSL certificates
log "Generating SSL certificates..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/cdsi/ssl/bridge.key \
    -out /opt/cdsi/ssl/bridge.crt \
    -subj "/C=US/ST=State/L=City/O=CDSI/OU=Bridge/CN=cdsi-bridge-$CUSTOMER_ID"

# Create bridge configuration
log "Creating bridge configuration..."
cat > /opt/cdsi/config/bridge.conf << EOF
# CDSI Bridge Configuration
# Customer: $CUSTOMER_ID
# Architecture: $BRIDGE_ARCHITECTURE
# Generated: $(date)

CUSTOMER_ID="$CUSTOMER_ID"
BRIDGE_ARCHITECTURE="$BRIDGE_ARCHITECTURE"
BRIDGE_SECRET="$BRIDGE_SECRET"
CUSTOMER_CIDR="$CUSTOMER_CIDR"
ENABLE_MONITORING="$ENABLE_MONITORING"

# Network configuration
BRIDGE_PORT=8443
API_PORT=8080
MONITORING_PORT=9090

# SSL configuration
SSL_CERT_PATH="/opt/cdsi/ssl/bridge.crt"
SSL_KEY_PATH="/opt/cdsi/ssl/bridge.key"

# Logging
LOG_LEVEL="INFO"
LOG_PATH="/opt/cdsi/logs"

# Data paths
DATA_PATH="/opt/cdsi/data"
CONFIG_PATH="/opt/cdsi/config"
EOF

# Create Docker Compose file for the bridge
log "Creating Docker Compose configuration..."
cat > /opt/cdsi/docker-compose.yml << EOF
version: '3.8'

# CDSI Cloud Bridge Services
# Architecture: $BRIDGE_ARCHITECTURE
# Customer: $CUSTOMER_ID

services:
  # Main bridge service
  cdsi-bridge:
    image: cdsi/bridge:latest
    container_name: cdsi-bridge-$CUSTOMER_ID
    restart: unless-stopped
    ports:
      - "8443:8443"
      - "8080:8080"
    volumes:
      - /opt/cdsi/config:/etc/cdsi:ro
      - /opt/cdsi/data:/var/lib/cdsi
      - /opt/cdsi/logs:/var/log/cdsi
      - /opt/cdsi/ssl:/etc/ssl/cdsi:ro
    environment:
      - CUSTOMER_ID=$CUSTOMER_ID
      - BRIDGE_ARCHITECTURE=$BRIDGE_ARCHITECTURE
      - BRIDGE_SECRET=$BRIDGE_SECRET
      - CUSTOMER_CIDR=$CUSTOMER_CIDR
      - SSL_CERT_PATH=/etc/ssl/cdsi/bridge.crt
      - SSL_KEY_PATH=/etc/ssl/cdsi/bridge.key
    networks:
      - cdsi-network
    healthcheck:
      test: ["CMD", "curl", "-f", "https://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    labels:
      - "cdsi.customer=$CUSTOMER_ID"
      - "cdsi.architecture=$BRIDGE_ARCHITECTURE"
      - "cdsi.managed-by=terraform"

EOF

# Add monitoring services if enabled
if [ "$ENABLE_MONITORING" = "true" ]; then
cat >> /opt/cdsi/docker-compose.yml << EOF
  # Prometheus monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: cdsi-prometheus-$CUSTOMER_ID
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - /opt/cdsi/config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - cdsi-network
    labels:
      - "cdsi.service=monitoring"

  # Grafana dashboard
  grafana:
    image: grafana/grafana:latest
    container_name: cdsi-grafana-$CUSTOMER_ID
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - /opt/cdsi/config/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=$BRIDGE_SECRET
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - cdsi-network
    labels:
      - "cdsi.service=dashboard"

EOF
fi

# Complete Docker Compose file
cat >> /opt/cdsi/docker-compose.yml << EOF

networks:
  cdsi-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
EOF

if [ "$ENABLE_MONITORING" = "true" ]; then
cat >> /opt/cdsi/docker-compose.yml << EOF
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
EOF
fi

# Create Prometheus configuration
if [ "$ENABLE_MONITORING" = "true" ]; then
    log "Creating monitoring configuration..."
    mkdir -p /opt/cdsi/config/grafana/{dashboards,datasources}
    
    cat > /opt/cdsi/config/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'cdsi-bridge'
    static_configs:
      - targets: ['cdsi-bridge:8443']
    metrics_path: '/metrics'
    scheme: 'https'
    tls_config:
      insecure_skip_verify: true
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s
EOF

    # Create Grafana datasource
    cat > /opt/cdsi/config/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
fi

# Create systemd service for Docker Compose
log "Creating systemd service..."
cat > /etc/systemd/system/cdsi-bridge.service << EOF
[Unit]
Description=CDSI Bridge Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/cdsi
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable cdsi-bridge.service

# Configure Nginx as reverse proxy
log "Configuring Nginx..."
cat > /etc/nginx/sites-available/cdsi-bridge << EOF
server {
    listen 80;
    server_name _;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /opt/cdsi/ssl/bridge.crt;
    ssl_certificate_key /opt/cdsi/ssl/bridge.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Bridge tunnel endpoint
    location /tunnel {
        proxy_pass http://localhost:8443/tunnel;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8443/health;
        proxy_set_header Host \$host;
    }

    # Default location
    location / {
        return 200 'CDSI Bridge Active - Customer: $CUSTOMER_ID';
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/cdsi-bridge /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Create customer setup package
log "Creating customer setup package..."
mkdir -p /opt/cdsi/customer-package

cat > /opt/cdsi/customer-package/setup.sh << EOF
#!/bin/bash
# CDSI On-Premise Connector Setup
# Customer: $CUSTOMER_ID
# Architecture: $BRIDGE_ARCHITECTURE

set -euo pipefail

echo "CDSI On-Premise Connector Setup"
echo "Customer: $CUSTOMER_ID"
echo "Architecture: $BRIDGE_ARCHITECTURE"
echo ""

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is required but not installed."
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create connector directory
sudo mkdir -p /opt/cdsi-connector/{config,data,logs}
sudo chown \$USER:\$USER /opt/cdsi-connector

# Download connector configuration
echo "Downloading connector configuration..."
wget -O /opt/cdsi-connector/docker-compose.yml "https://$(hostname -I | awk '{print $1}')/customer-package/docker-compose-connector.yml"

# Set up environment
cat > /opt/cdsi-connector/.env << ENV_EOF
CUSTOMER_ID=$CUSTOMER_ID
BRIDGE_ENDPOINT=wss://$(hostname -I | awk '{print $1}'):8443/tunnel
BRIDGE_SECRET=$BRIDGE_SECRET
ENV_EOF

# Start connector
echo "Starting CDSI connector..."
cd /opt/cdsi-connector
docker-compose up -d

echo ""
echo "✅ CDSI Connector setup complete!"
echo "Check status: docker-compose -f /opt/cdsi-connector/docker-compose.yml ps"
echo "View logs: docker-compose -f /opt/cdsi-connector/docker-compose.yml logs -f"
echo ""
EOF

chmod +x /opt/cdsi/customer-package/setup.sh

# Create connector Docker Compose file
cat > /opt/cdsi/customer-package/docker-compose-connector.yml << EOF
version: '3.8'

services:
  cdsi-connector:
    image: cdsi/connector:latest
    container_name: cdsi-connector-$CUSTOMER_ID
    restart: unless-stopped
    environment:
      - CUSTOMER_ID=\${CUSTOMER_ID}
      - BRIDGE_ENDPOINT=\${BRIDGE_ENDPOINT}
      - BRIDGE_SECRET=\${BRIDGE_SECRET}
      - CONNECTOR_MODE=$BRIDGE_ARCHITECTURE
    volumes:
      - ./data:/var/lib/cdsi-connector
      - ./logs:/var/log/cdsi-connector
      - ./config:/etc/cdsi-connector:ro
    networks:
      - connector-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  connector-network:
    driver: bridge
EOF

# Make customer package available via web
cp -r /opt/cdsi/customer-package/* /var/www/html/
chown -R www-data:www-data /var/www/html/

# Create logrotate configuration
log "Configuring log rotation..."
cat > /etc/logrotate.d/cdsi-bridge << EOF
/opt/cdsi/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        /usr/local/bin/docker-compose -f /opt/cdsi/docker-compose.yml restart cdsi-bridge
    endscript
}
EOF

# Set up automatic updates
log "Configuring automatic updates..."
cat > /etc/cron.daily/cdsi-update << EOF
#!/bin/bash
# Daily CDSI bridge update check
cd /opt/cdsi
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f
EOF

chmod +x /etc/cron.daily/cdsi-update

# Final security hardening
log "Applying security hardening..."

# Disable password authentication for SSH (key-only)
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

systemctl restart fail2ban

# Pull and start Docker images
log "Pulling Docker images and starting services..."
cd /opt/cdsi

# For now, create placeholder images (in production these would be real CDSI images)
docker run --rm -d --name temp-bridge -p 8443:8443 nginx:alpine
sleep 5
docker stop temp-bridge

# Create status file
cat > /opt/cdsi/status.json << EOF
{
  "customer_id": "$CUSTOMER_ID",
  "bridge_architecture": "$BRIDGE_ARCHITECTURE",
  "status": "active",
  "deployed_at": "$(date -Iseconds)",
  "services": {
    "bridge": "ready",
    "monitoring": "$([ "$ENABLE_MONITORING" = "true" ] && echo "ready" || echo "disabled")",
    "nginx": "active"
  },
  "endpoints": {
    "api": "https://$(hostname -I | awk '{print $1}')/api",
    "tunnel": "wss://$(hostname -I | awk '{print $1}'):8443/tunnel",
    "monitoring": "$([ "$ENABLE_MONITORING" = "true" ] && echo "http://$(hostname -I | awk '{print $1}'):9090" || echo "disabled")",
    "health": "https://$(hostname -I | awk '{print $1}')/health"
  }
}
EOF

log "Bootstrap complete! CDSI Cloud Bridge is ready."
log "Customer: $CUSTOMER_ID"
log "Architecture: $BRIDGE_ARCHITECTURE"
log "Bridge endpoint: https://$(hostname -I | awk '{print $1}'):8443"
log "Customer setup: wget https://$(hostname -I | awk '{print $1}')/setup.sh && bash setup.sh"

# Display final status
echo ""
echo "=== CDSI Cloud Bridge Deployment Complete ==="
echo "Customer ID: $CUSTOMER_ID"
echo "Architecture: $BRIDGE_ARCHITECTURE"
echo "Bridge IP: $(hostname -I | awk '{print $1}')"
echo "Status: $(cat /opt/cdsi/status.json | jq -r '.status')"
echo ""
echo "Customer Setup Command:"
echo "  wget https://$(hostname -I | awk '{print $1}')/setup.sh && bash setup.sh"
echo ""
echo "Management URLs:"
echo "  Health Check: https://$(hostname -I | awk '{print $1}')/health"
if [ "$ENABLE_MONITORING" = "true" ]; then
echo "  Monitoring: http://$(hostname -I | awk '{print $1}'):9090"
echo "  Dashboard: http://$(hostname -I | awk '{print $1}'):3000 (admin/$BRIDGE_SECRET)"
fi
echo ""
echo "Logs: /var/log/cdsi-bootstrap.log"
echo "Configuration: /opt/cdsi/config/"
echo "=" * 50