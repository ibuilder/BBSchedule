# BBSchedule Enterprise Deployment Guide

## Overview

BBSchedule Enterprise Edition provides advanced security, compliance, monitoring, and integration capabilities for large-scale construction project management deployments.

## Enterprise Features

### 🔐 Security & Authentication
- **Multi-Factor Authentication (MFA)** with TOTP support
- **Role-Based Access Control (RBAC)** with granular permissions
- **JWT-based API authentication** with token revocation
- **Data encryption** at rest and in transit
- **Advanced session management** with Redis backend
- **Security headers** and CSP policies
- **Rate limiting** and DDoS protection

### 📊 Monitoring & Observability
- **Real-time metrics collection** with Prometheus
- **Performance monitoring** with response time tracking
- **System resource monitoring** (CPU, memory, disk)
- **Business metrics tracking** (projects, activities, KPIs)
- **Health checks** for Kubernetes deployments
- **Alerting system** with configurable thresholds
- **Log aggregation** with ELK stack

### 🔄 Scalability & Performance
- **Redis caching layer** for improved performance
- **Database connection pooling** with optimization
- **Auto-scaling recommendations** based on metrics
- **Load balancing** with session affinity
- **CDN integration** for static assets
- **Query optimization** with automated indexing

### 🔗 Enterprise Integrations
- **Procore Construction Management** sync
- **Autodesk Construction Cloud** BIM integration
- **PlanGrid** document management
- **Primavera Cloud** schedule import/export
- **Custom API gateway** with rate limiting
- **Webhook management** for real-time updates
- **Data synchronization** with external systems

### 📋 Compliance & Governance
- **SOX compliance** controls and audit trails
- **GDPR compliance** with data subject rights
- **Comprehensive audit logging** with retention policies
- **Data governance** with classification and retention
- **Compliance reporting** and dashboards
- **Automated compliance checks** and alerts

## Deployment Options

### 1. Docker Compose (Recommended for Small-Medium Deployments)

```bash
# Clone the repository
git clone <repository-url>
cd bbschedule-enterprise

# Copy environment template
cp .env.template .env

# Edit configuration
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Kubernetes (Recommended for Large-Scale Deployments)

```bash
# Create namespace
kubectl create namespace bbschedule-production

# Create secrets
kubectl create secret generic bbschedule-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  --from-literal=session-secret="..." \
  --from-literal=jwt-secret="..." \
  -n bbschedule-production

# Deploy application
kubectl apply -f kubernetes/ -n bbschedule-production

# Check deployment
kubectl get pods -n bbschedule-production
```

### 3. AWS ECS/Fargate

```bash
# Build and push image
docker build -t bbschedule:latest .
docker tag bbschedule:latest your-ecr-repo:latest
docker push your-ecr-repo:latest

# Deploy using ECS task definition
aws ecs update-service --cluster production --service bbschedule
```

## Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/bbschedule
REDIS_URL=redis://host:6379/0

# Security
SESSION_SECRET=<32-character-random-string>
JWT_SECRET_KEY=<32-character-random-string>
ENCRYPTION_KEY=<fernet-key>
DATA_ENCRYPTION_KEY=<fernet-key>

# External Integrations
PROCORE_API_KEY=<your-procore-key>
PROCORE_CLIENT_SECRET=<your-procore-secret>
AUTODESK_CLIENT_ID=<your-autodesk-id>
AUTODESK_CLIENT_SECRET=<your-autodesk-secret>
```

### SSL/TLS Configuration

```bash
# Generate SSL certificate (Let's Encrypt recommended)
certbot certonly --nginx -d bbschedule.yourdomain.com

# Or use your existing certificates
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

## Security Hardening

### 1. Network Security
- Use VPC with private subnets for application servers
- Configure security groups to allow only necessary traffic
- Implement Web Application Firewall (WAF)
- Use load balancer with SSL termination

### 2. Database Security
- Enable SSL connections to database
- Use strong passwords and rotate regularly
- Implement database firewall rules
- Enable audit logging

### 3. Application Security
- Enable all security headers
- Configure CSP policies
- Implement rate limiting
- Use secure session configuration

## Monitoring Setup

### 1. Prometheus Metrics
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'bbschedule'
    static_configs:
      - targets: ['bbschedule:5000']
    metrics_path: '/metrics/prometheus'
```

### 2. Grafana Dashboards
- System metrics dashboard
- Application performance dashboard
- Business metrics dashboard
- Security events dashboard

### 3. Alerting Rules
```yaml
# alerts.yml
groups:
  - name: bbschedule
    rules:
      - alert: HighResponseTime
        expr: response_time > 5
        for: 5m
        annotations:
          summary: High response time detected
```

## Backup and Disaster Recovery

### 1. Database Backups
```bash
# Automated daily backups
0 2 * * * pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip -c backup-20240101.sql.gz | psql $DATABASE_URL
```

### 2. File Backups
```bash
# Backup uploads and logs
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### 3. Disaster Recovery Plan
1. **RTO**: 4 hours (Recovery Time Objective)
2. **RPO**: 1 hour (Recovery Point Objective)
3. **Multi-region deployment** for high availability
4. **Automated failover** procedures
5. **Regular DR testing** quarterly

## Compliance Configuration

### 1. SOX Compliance
- Enable audit trail logging
- Configure segregation of duties
- Implement approval workflows
- Generate compliance reports

### 2. GDPR Compliance
- Configure consent management
- Implement data subject rights
- Enable data retention policies
- Setup privacy controls

### 3. Industry Standards
- **ISO 27001**: Information security management
- **SOC 2 Type II**: Security and availability
- **NIST Framework**: Cybersecurity controls

## Performance Optimization

### 1. Database Optimization
```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_activities_project_status ON activities(project_id, status);
CREATE INDEX CONCURRENTLY idx_projects_created_by_status ON projects(created_by, status);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM activities WHERE project_id = 1;
```

### 2. Caching Strategy
- **Redis**: Session data, frequently accessed data
- **CDN**: Static assets, images, documents
- **Application-level**: Query results, API responses

### 3. Auto-scaling Configuration
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bbschedule-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bbschedule
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Integration Setup

### 1. Procore Integration
```python
# Configure Procore API
PROCORE_CONFIG = {
    'base_url': 'https://api.procore.com/rest/v1.0',
    'client_id': os.environ['PROCORE_CLIENT_ID'],
    'client_secret': os.environ['PROCORE_CLIENT_SECRET'],
    'redirect_uri': 'https://your-domain.com/auth/procore/callback'
}
```

### 2. Autodesk Integration
```python
# Configure Autodesk Forge
AUTODESK_CONFIG = {
    'client_id': os.environ['AUTODESK_CLIENT_ID'],
    'client_secret': os.environ['AUTODESK_CLIENT_SECRET'],
    'scope': 'account:read data:read data:write'
}
```

## Maintenance Procedures

### 1. Regular Maintenance
- **Daily**: Check logs for errors
- **Weekly**: Review performance metrics
- **Monthly**: Update dependencies
- **Quarterly**: Security assessment

### 2. Update Procedures
```bash
# Rolling update with zero downtime
kubectl set image deployment/bbschedule bbschedule=bbschedule:v1.1.0
kubectl rollout status deployment/bbschedule

# Rollback if needed
kubectl rollout undo deployment/bbschedule
```

### 3. Health Monitoring
```bash
# Check application health
curl https://bbschedule.yourdomain.com/health/ready

# Check detailed health
curl -H "X-API-Key: your-api-key" \
  https://bbschedule.yourdomain.com/api/enterprise/health/detailed
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check for memory leaks in logs
   - Increase pod memory limits
   - Optimize database queries

2. **Slow Response Times**
   - Check database performance
   - Review cache hit rates
   - Analyze slow query logs

3. **Authentication Failures**
   - Verify JWT secret configuration
   - Check Redis connectivity
   - Review security logs

### Support Contacts

- **Technical Support**: support@bbschedule.com
- **Security Issues**: security@bbschedule.com
- **Emergency**: +1-800-BBSCHED

## License

BBSchedule Enterprise Edition
Copyright (c) 2024 BBSchedule Inc.
All rights reserved.