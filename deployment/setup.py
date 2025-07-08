#!/usr/bin/env python3
"""
Enterprise deployment script for BBSchedule
Automates the complete enterprise deployment process
"""

import os
import subprocess
import secrets
import string
from pathlib import Path
from cryptography.fernet import Fernet

def generate_secure_key(length=32):
    """Generate a secure random key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_fernet_key():
    """Generate Fernet encryption key"""
    return Fernet.generate_key().decode()

def create_enterprise_env():
    """Create enterprise .env file with secure defaults"""
    
    print("🔧 Generating enterprise environment configuration...")
    
    env_content = f"""# BBSchedule Enterprise Configuration
# Generated on {os.popen('date').read().strip()}

# Application Configuration
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Database Configuration (Update with your database details)
DATABASE_URL=postgresql://bbschedule:{generate_secure_key(16)}@localhost:5432/bbschedule_enterprise
DB_PASSWORD={generate_secure_key(24)}

# Security Configuration
SESSION_SECRET={generate_secure_key(32)}
JWT_SECRET_KEY={generate_secure_key(32)}
ENCRYPTION_KEY={generate_fernet_key()}
DATA_ENCRYPTION_KEY={generate_fernet_key()}

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# External API Integrations (Add your keys)
PROCORE_API_KEY=your_procore_api_key_here
PROCORE_CLIENT_SECRET=your_procore_client_secret_here
PROCORE_BASE_URL=https://api.procore.com/rest/v1.0

AUTODESK_CLIENT_ID=your_autodesk_client_id_here
AUTODESK_CLIENT_SECRET=your_autodesk_client_secret_here

PLANGRID_API_KEY=your_plangrid_api_key_here

PRIMAVERA_API_KEY=your_primavera_api_key_here

# Webhook Security
PROCORE_WEBHOOK_SECRET={generate_secure_key(32)}
AUTODESK_WEBHOOK_SECRET={generate_secure_key(32)}

# Monitoring Configuration
GRAFANA_PASSWORD={generate_secure_key(16)}

# Email Configuration (For alerts and notifications)
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=alerts@yourdomain.com
SMTP_PASSWORD=your_smtp_password_here
SMTP_USE_TLS=True

# Domain Configuration
DOMAIN_NAME=bbschedule.yourdomain.com

# Enterprise Features
ENTERPRISE_MODE=True
COMPLIANCE_ENABLED=True
AUDIT_LOGGING=True
ADVANCED_SECURITY=True

# File Upload Configuration
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=uploads

# Performance Configuration
WORKERS=4
WORKER_CONNECTIONS=1000
TIMEOUT=30

# Backup Configuration
BACKUP_RETENTION_DAYS=365
AUDIT_RETENTION_DAYS=2555
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Enterprise .env file created")
    print("⚠️  Please update the database URL and API keys in .env file")

def setup_directories():
    """Create necessary directories for enterprise deployment"""
    
    print("📁 Setting up enterprise directory structure...")
    
    directories = [
        'logs',
        'uploads',
        'backups',
        'monitoring/grafana/dashboards',
        'monitoring/grafana/datasources',
        'monitoring/prometheus',
        'nginx/ssl',
        'kubernetes',
        'database',
        'logging',
        'static/uploads',
        'templates/enterprise'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created")

def create_docker_files():
    """Create Docker deployment files"""
    
    print("🐳 Creating Docker deployment files...")
    
    # Run the deployment script
    exec(open('enterprise_deployment.py').read())
    
    print("✅ Docker files created")

def setup_ssl_certificates():
    """Setup SSL certificate configuration"""
    
    print("🔒 Setting up SSL certificate configuration...")
    
    # Create self-signed certificate for development
    ssl_script = """
# Create self-signed certificate for development/testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=CA/L=San Francisco/O=BBSchedule/CN=localhost"
"""
    
    with open('setup_ssl.sh', 'w') as f:
        f.write(ssl_script)
    
    os.chmod('setup_ssl.sh', 0o755)
    
    print("✅ SSL setup script created (run ./setup_ssl.sh)")
    print("⚠️  For production, use Let's Encrypt or your CA-signed certificates")

def create_database_init():
    """Create database initialization script"""
    
    print("🗄️  Creating database initialization...")
    
    db_init = """
-- BBSchedule Enterprise Database Initialization
-- Creates enterprise-specific extensions and configurations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enterprise audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Create enterprise configuration table
CREATE TABLE IF NOT EXISTS enterprise_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default enterprise settings
INSERT INTO enterprise_config (key, value) VALUES
    ('compliance_enabled', 'true'),
    ('audit_retention_days', '2555'),
    ('data_retention_days', '2190'),
    ('security_level', 'high'),
    ('integration_enabled', 'true')
ON CONFLICT (key) DO NOTHING;

-- Create enterprise indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_enterprise ON projects(status, created_at, created_by);
CREATE INDEX IF NOT EXISTS idx_activities_enterprise ON activities(project_id, status, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_audit_enterprise ON audit.audit_events(timestamp, user_id, action);

-- Set up enterprise database configuration
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Create enterprise user for monitoring
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bbschedule_monitor') THEN
        CREATE ROLE bbschedule_monitor WITH LOGIN PASSWORD 'monitor_password_here';
        GRANT CONNECT ON DATABASE bbschedule TO bbschedule_monitor;
        GRANT USAGE ON SCHEMA public TO bbschedule_monitor;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO bbschedule_monitor;
        GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO bbschedule_monitor;
        GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO bbschedule_monitor;
    END IF;
END
$$;
"""
    
    with open('database/init.sql', 'w') as f:
        f.write(db_init)
    
    print("✅ Database initialization script created")

def create_monitoring_config():
    """Create monitoring configuration files"""
    
    print("📊 Creating monitoring configuration...")
    
    # Prometheus configuration
    prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'bbschedule'
    static_configs:
      - targets: ['bbschedule:5000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 30s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
"""
    
    with open('monitoring/prometheus.yml', 'w') as f:
        f.write(prometheus_config)
    
    # Grafana datasource
    grafana_datasource = """
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"""
    
    with open('monitoring/grafana/datasources/prometheus.yml', 'w') as f:
        f.write(grafana_datasource)
    
    print("✅ Monitoring configuration created")

def create_backup_scripts():
    """Create automated backup scripts"""
    
    print("💾 Creating backup scripts...")
    
    backup_script = """#!/bin/bash
# BBSchedule Enterprise Backup Script

set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="$BACKUP_DIR/database_backup_$DATE.sql.gz"
FILES_BACKUP_FILE="$BACKUP_DIR/files_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
pg_dump $DATABASE_URL | gzip > $DB_BACKUP_FILE

# Files backup
echo "Creating files backup..."
tar -czf $FILES_BACKUP_FILE uploads/ logs/ --exclude='logs/*.log'

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DB_BACKUP_FILE, $FILES_BACKUP_FILE"
"""
    
    with open('backup.sh', 'w') as f:
        f.write(backup_script)
    
    os.chmod('backup.sh', 0o755)
    
    # Cron setup script
    cron_script = """#!/bin/bash
# Setup automated backups

# Add backup job to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/bbschedule/backup.sh") | crontab -

echo "Automated backup scheduled for 2 AM daily"
"""
    
    with open('setup_cron.sh', 'w') as f:
        f.write(cron_script)
    
    os.chmod('setup_cron.sh', 0o755)
    
    print("✅ Backup scripts created")

def create_deployment_checklist():
    """Create enterprise deployment checklist"""
    
    print("📋 Creating deployment checklist...")
    
    checklist = """# BBSchedule Enterprise Deployment Checklist

## Pre-Deployment
- [ ] Server infrastructure provisioned (CPU: 4+ cores, RAM: 8+ GB, Disk: 100+ GB SSD)
- [ ] Domain name configured and DNS records set
- [ ] SSL certificates obtained (Let's Encrypt or CA-signed)
- [ ] Database server setup (PostgreSQL 14+)
- [ ] Redis server setup for caching and sessions
- [ ] Load balancer configured (if using multiple instances)

## Security Configuration
- [ ] Generated secure environment variables (.env file)
- [ ] Updated database credentials with strong passwords
- [ ] Configured firewall rules (only necessary ports open)
- [ ] SSL/TLS certificates installed and configured
- [ ] Security headers enabled in web server
- [ ] Rate limiting configured

## Application Deployment
- [ ] Updated .env file with production configuration
- [ ] Built Docker images or prepared application files
- [ ] Database migrations executed
- [ ] Static files collected and served by web server
- [ ] Application health checks passing

## External Integrations
- [ ] Procore API credentials configured and tested
- [ ] Autodesk Construction Cloud integration setup
- [ ] PlanGrid integration configured
- [ ] Webhook endpoints configured and secured
- [ ] API rate limits and quotas verified

## Monitoring Setup
- [ ] Prometheus metrics collection enabled
- [ ] Grafana dashboards imported and configured
- [ ] Alert rules configured for critical metrics
- [ ] Log aggregation setup (ELK stack or similar)
- [ ] Health check endpoints configured

## Backup and Recovery
- [ ] Automated database backups configured
- [ ] File system backups scheduled
- [ ] Backup retention policies implemented
- [ ] Disaster recovery plan documented and tested
- [ ] Data restore procedures verified

## Compliance Configuration
- [ ] Audit logging enabled and configured
- [ ] Data retention policies implemented
- [ ] GDPR compliance features configured
- [ ] SOX compliance controls enabled
- [ ] Security event monitoring activated

## Performance Optimization
- [ ] Database indexes created and optimized
- [ ] Redis caching layer configured
- [ ] CDN setup for static assets
- [ ] Database connection pooling configured
- [ ] Application performance monitoring enabled

## Post-Deployment Verification
- [ ] Application accessible via configured domain
- [ ] User authentication working correctly
- [ ] All major features tested and functional
- [ ] API endpoints responding correctly
- [ ] Monitoring dashboards showing data
- [ ] Backup scripts executed successfully
- [ ] Load testing completed with acceptable performance

## Documentation
- [ ] Deployment configuration documented
- [ ] Administrator accounts created and documented
- [ ] Emergency procedures documented
- [ ] User training materials prepared
- [ ] System maintenance procedures documented

## Go-Live
- [ ] DNS cutover completed
- [ ] User notifications sent
- [ ] Support team briefed
- [ ] Monitoring alerts active
- [ ] Initial system health verified

## Notes
Date deployed: _______________
Deployed by: _________________
Version: ____________________
Special configurations: ______
"""
    
    with open('DEPLOYMENT_CHECKLIST.md', 'w') as f:
        f.write(checklist)
    
    print("✅ Deployment checklist created")

def main():
    """Main deployment setup function"""
    
    print("🚀 BBSchedule Enterprise Deployment Setup")
    print("=" * 50)
    
    try:
        setup_directories()
        create_enterprise_env()
        create_docker_files()
        setup_ssl_certificates()
        create_database_init()
        create_monitoring_config()
        create_backup_scripts()
        create_deployment_checklist()
        
        print("\n" + "=" * 50)
        print("✅ Enterprise deployment setup completed!")
        print("\nNext Steps:")
        print("1. Review and update .env file with your specific configuration")
        print("2. Obtain SSL certificates for production use")
        print("3. Update docker-compose.yml with your domain name")
        print("4. Configure external API credentials in .env")
        print("5. Run: docker-compose up -d")
        print("6. Follow the deployment checklist in DEPLOYMENT_CHECKLIST.md")
        print("\nFor detailed instructions, see ENTERPRISE_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())