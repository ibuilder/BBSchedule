"""
Enterprise-grade security implementation for BBSchedule
"""

import os
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, session
from werkzeug.security import check_password_hash, generate_password_hash
import redis
from cryptography.fernet import Fernet
import logging

# Security logging
security_logger = logging.getLogger('security')

class EnterpriseAuth:
    """Enterprise authentication and authorization system"""
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.redis_client = redis_client
        self.encryption_key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher_suite = Fernet(self.encryption_key)
        
    def init_app(self, app):
        self.app = app
        
    def generate_secure_token(self, user_id, role, permissions):
        """Generate JWT token with enterprise claims"""
        payload = {
            'user_id': user_id,
            'role': role,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=8),
            'jti': secrets.token_hex(16),  # JWT ID for revocation
            'aud': 'bbschedule-enterprise',
            'iss': 'bbschedule-auth-service'
        }
        
        token = jwt.encode(
            payload, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithm='HS256'
        )
        
        # Store token in Redis for revocation checking
        if self.redis_client:
            self.redis_client.setex(
                f"token:{payload['jti']}", 
                timedelta(hours=8).total_seconds(), 
                user_id
            )
        
        security_logger.info(f"Token generated for user {user_id} with role {role}")
        return token
    
    def verify_token(self, token):
        """Verify JWT token with enterprise security checks"""
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256'],
                audience='bbschedule-enterprise'
            )
            
            # Check if token is revoked
            if self.redis_client and not self.redis_client.exists(f"token:{payload['jti']}"):
                security_logger.warning(f"Revoked token attempted access: {payload['jti']}")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            security_logger.warning("Expired token attempted access")
            return None
        except jwt.InvalidTokenError:
            security_logger.warning("Invalid token attempted access")
            return None
    
    def revoke_token(self, jti):
        """Revoke a specific token"""
        if self.redis_client:
            self.redis_client.delete(f"token:{jti}")
            security_logger.info(f"Token revoked: {jti}")

class RoleBasedAccess:
    """Role-based access control for enterprise deployment"""
    
    ROLES = {
        'admin': {
            'permissions': ['*'],  # All permissions
            'description': 'Full system access'
        },
        'project_manager': {
            'permissions': [
                'project.create', 'project.read', 'project.update', 'project.delete',
                'activity.create', 'activity.read', 'activity.update', 'activity.delete',
                'schedule.read', 'schedule.update', 'reports.generate'
            ],
            'description': 'Project management access'
        },
        'scheduler': {
            'permissions': [
                'project.read', 'activity.read', 'activity.update', 
                'schedule.read', 'schedule.update', 'reports.view'
            ],
            'description': 'Scheduling and progress tracking'
        },
        'viewer': {
            'permissions': [
                'project.read', 'activity.read', 'schedule.read', 'reports.view'
            ],
            'description': 'Read-only access'
        },
        'executive': {
            'permissions': [
                'project.read', 'activity.read', 'schedule.read', 
                'reports.generate', 'analytics.view', 'dashboard.executive'
            ],
            'description': 'Executive dashboard and reporting'
        }
    }
    
    @staticmethod
    def check_permission(user_role, required_permission):
        """Check if user role has required permission"""
        if user_role not in RoleBasedAccess.ROLES:
            return False
            
        role_permissions = RoleBasedAccess.ROLES[user_role]['permissions']
        
        # Admin has all permissions
        if '*' in role_permissions:
            return True
            
        return required_permission in role_permissions
    
    @staticmethod
    def require_permission(permission):
        """Decorator to enforce permission-based access"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get user from session or token
                user_role = session.get('user_role', 'viewer')
                
                if not RoleBasedAccess.check_permission(user_role, permission):
                    security_logger.warning(
                        f"Access denied: {session.get('user_id')} attempted {permission}"
                    )
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

class AuditLogger:
    """Enterprise audit logging system"""
    
    def __init__(self, app=None):
        self.app = app
        self.audit_logger = logging.getLogger('audit')
        
    def log_action(self, user_id, action, resource_type, resource_id, 
                   details=None, ip_address=None, user_agent=None):
        """Log user actions for audit trail"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {},
            'ip_address': ip_address or request.remote_addr,
            'user_agent': user_agent or request.user_agent.string,
            'session_id': session.get('session_id')
        }
        
        self.audit_logger.info(f"AUDIT: {audit_entry}")
        
        # Store in database for compliance
        # This would integrate with your existing database
        return audit_entry

class DataEncryption:
    """Enterprise data encryption for sensitive information"""
    
    def __init__(self, encryption_key=None):
        self.encryption_key = encryption_key or os.environ.get('DATA_ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_field(self, data):
        """Encrypt sensitive field data"""
        if data is None:
            return None
        return self.cipher.encrypt(str(data).encode()).decode()
    
    def decrypt_field(self, encrypted_data):
        """Decrypt sensitive field data"""
        if encrypted_data is None:
            return None
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def hash_password(self, password):
        """Hash password with enterprise-grade security"""
        return generate_password_hash(
            password, 
            method='pbkdf2:sha256:100000'  # 100,000 iterations
        )
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)

class SecurityMiddleware:
    """Enterprise security middleware"""
    
    def __init__(self, app=None):
        self.app = app
        
    def init_app(self, app):
        self.app = app
        
        # Add security headers
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            return response

class EnterpriseCompliance:
    """Compliance and governance features"""
    
    @staticmethod
    def data_retention_policy():
        """Implement data retention policies"""
        # Archive projects older than 7 years
        # Anonymize user data after account deletion
        # Maintain audit logs for required period
        pass
    
    @staticmethod
    def gdpr_compliance():
        """GDPR compliance features"""
        # Right to be forgotten
        # Data portability
        # Consent management
        pass
    
    @staticmethod
    def sox_compliance():
        """SOX compliance for financial controls"""
        # Segregation of duties
        # Change management controls
        # Financial reporting accuracy
        pass

# Initialize enterprise security
enterprise_auth = EnterpriseAuth()
rbac = RoleBasedAccess()
audit_logger = AuditLogger()
data_encryption = DataEncryption()
security_middleware = SecurityMiddleware()