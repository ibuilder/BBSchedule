"""
Enterprise deployment configuration and Docker setup for BBSchedule
"""

import os
from datetime import datetime

# Docker configuration
DOCKERFILE_CONTENT = '''
# Multi-stage build for enterprise deployment
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libpq-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && groupadd -r bbschedule \\
    && useradd -r -g bbschedule bbschedule

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads static/uploads \\
    && chown -R bbschedule:bbschedule /app

# Switch to non-root user
USER bbschedule

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/health/ping || exit 1

# Expose port
EXPOSE 5000

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "5", "--preload", "main:app"]
'''

# Docker Compose for enterprise deployment
DOCKER_COMPOSE_CONTENT = '''
version: '3.8'

services:
  # Main application
  bbschedule:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://bbschedule:${DB_PASSWORD}@postgres:5432/bbschedule
      - REDIS_URL=redis://redis:6379/0
      - SESSION_SECRET=${SESSION_SECRET}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DEBUG=False
      - FLASK_ENV=production
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.bbschedule.rule=Host(`bbschedule.yourdomain.com`)"
      - "traefik.http.routers.bbschedule.entrypoints=websecure"
      - "traefik.http.routers.bbschedule.tls.certresolver=letsencrypt"
    networks:
      - bbschedule-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  # PostgreSQL database
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=bbschedule
      - POSTGRES_USER=bbschedule
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - bbschedule-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  # Redis for caching and sessions
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - bbschedule-network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - bbschedule
    restart: unless-stopped
    networks:
      - bbschedule-network

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped
    networks:
      - bbschedule-network

  # Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped
    networks:
      - bbschedule-network

  # Log aggregation with ELK stack
  elasticsearch:
    image: elasticsearch:8.6.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    restart: unless-stopped
    networks:
      - bbschedule-network

  logstash:
    image: logstash:8.6.0
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      - ./logs:/var/log/bbschedule
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch
    restart: unless-stopped
    networks:
      - bbschedule-network

  kibana:
    image: kibana:8.6.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped
    networks:
      - bbschedule-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  bbschedule-network:
    driver: bridge
'''

# Kubernetes deployment configuration
KUBERNETES_DEPLOYMENT = '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bbschedule
  namespace: production
  labels:
    app: bbschedule
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: bbschedule
  template:
    metadata:
      labels:
        app: bbschedule
        version: v1.0.0
    spec:
      serviceAccountName: bbschedule
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: bbschedule
        image: bbschedule:latest
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bbschedule-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: bbschedule-secrets
              key: redis-url
        - name: SESSION_SECRET
          valueFrom:
            secretKeyRef:
              name: bbschedule-secrets
              key: session-secret
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: bbschedule-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: uploads
          mountPath: /app/uploads
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: bbschedule-logs
      - name: uploads
        persistentVolumeClaim:
          claimName: bbschedule-uploads
---
apiVersion: v1
kind: Service
metadata:
  name: bbschedule-service
  namespace: production
spec:
  selector:
    app: bbschedule
  ports:
  - port: 80
    targetPort: 5000
    name: http
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bbschedule-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - bbschedule.yourdomain.com
    secretName: bbschedule-tls
  rules:
  - host: bbschedule.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bbschedule-service
            port:
              number: 80
'''

# Nginx configuration
NGINX_CONFIG = '''
events {
    worker_connections 1024;
}

http {
    upstream bbschedule {
        server bbschedule:5000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

    server {
        listen 80;
        server_name bbschedule.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name bbschedule.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://bbschedule;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login rate limiting
        location /auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://bbschedule;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Main application
        location / {
            proxy_pass http://bbschedule;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
'''

# Environment configuration
ENV_TEMPLATE = '''
# Database Configuration
DATABASE_URL=postgresql://username:password@host:5432/dbname
DB_PASSWORD=secure_password_here

# Security Configuration
SESSION_SECRET=generate_secure_session_secret_here
JWT_SECRET_KEY=generate_secure_jwt_secret_here
ENCRYPTION_KEY=generate_fernet_encryption_key_here
DATA_ENCRYPTION_KEY=generate_data_encryption_key_here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# External Integrations
PROCORE_API_KEY=your_procore_api_key
PROCORE_CLIENT_SECRET=your_procore_client_secret
PROCORE_BASE_URL=https://api.procore.com/rest/v1.0

AUTODESK_CLIENT_ID=your_autodesk_client_id
AUTODESK_CLIENT_SECRET=your_autodesk_client_secret

PLANGRID_API_KEY=your_plangrid_api_key

# Webhook Secrets
PROCORE_WEBHOOK_SECRET=generate_webhook_secret_here
AUTODESK_WEBHOOK_SECRET=generate_webhook_secret_here

# Monitoring
GRAFANA_PASSWORD=secure_grafana_password

# Email Configuration (for alerts)
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=alerts@yourdomain.com
SMTP_PASSWORD=smtp_password
SMTP_USE_TLS=True

# SSL Configuration
SSL_CERT_PATH=/path/to/ssl/cert.pem
SSL_KEY_PATH=/path/to/ssl/key.pem

# Deployment Configuration
DEPLOY_ENV=production
LOG_LEVEL=INFO
DEBUG=False
'''

def create_deployment_files():
    """Create all deployment configuration files"""
    
    files = {
        'Dockerfile': DOCKERFILE_CONTENT,
        'docker-compose.yml': DOCKER_COMPOSE_CONTENT,
        'kubernetes/deployment.yml': KUBERNETES_DEPLOYMENT,
        'nginx/nginx.conf': NGINX_CONFIG,
        '.env.template': ENV_TEMPLATE
    }
    
    # Create directories
    os.makedirs('kubernetes', exist_ok=True)
    os.makedirs('nginx', exist_ok=True)
    os.makedirs('monitoring/grafana/dashboards', exist_ok=True)
    os.makedirs('monitoring/grafana/datasources', exist_ok=True)
    os.makedirs('logging', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    # Write files
    for filename, content in files.items():
        with open(filename, 'w') as f:
            f.write(content.strip())
    
    print("Enterprise deployment files created successfully!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and fill in your configuration")
    print("2. Generate SSL certificates for production")
    print("3. Configure DNS for your domain")
    print("4. Run: docker-compose up -d")
    print("5. Access Grafana at http://localhost:3000 for monitoring")

if __name__ == "__main__":
    create_deployment_files()