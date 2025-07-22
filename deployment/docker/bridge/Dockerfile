# CDSI Cloud Bridge Container
# Multi-architecture container for hybrid deployments
# Author: bdstest
# Copyright: 2025 CDSI - Compliance Data Systems Insights

FROM python:3.11-slim-bullseye

# Metadata
LABEL maintainer="bdstest <consulting@getcdsi.com>"
LABEL version="1.0.0"
LABEL description="CDSI Cloud Bridge for hybrid deployments"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    jq \
    netcat \
    iputils-ping \
    dnsutils \
    openssl \
    ca-certificates \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r cdsi && useradd -r -g cdsi -d /app -s /bin/bash cdsi

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
COPY scripts/ /app/scripts/

# Copy configuration files
COPY docker/bridge/nginx.conf /etc/nginx/nginx.conf
COPY docker/bridge/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/bridge/entrypoint.sh /app/entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/{data,logs,ssl} \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /var/run/nginx \
    && touch /var/run/nginx/nginx.pid

# Set permissions
RUN chown -R cdsi:cdsi /app \
    && chmod +x /app/entrypoint.sh \
    && chmod +x /app/scripts/*.sh

# Generate self-signed SSL certificates
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /app/ssl/bridge.key \
    -out /app/ssl/bridge.crt \
    -subj "/C=US/ST=State/L=City/O=CDSI/OU=Bridge/CN=cdsi-bridge"

# Expose ports
EXPOSE 8443 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f -k https://localhost:8443/health || exit 1

# Switch to application user
USER cdsi

# Set environment variables
ENV PYTHONPATH=/app/src
ENV BRIDGE_PORT=8443
ENV API_PORT=8080
ENV MONITORING_PORT=9090

# Entry point
ENTRYPOINT ["/app/entrypoint.sh"]