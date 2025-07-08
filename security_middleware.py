"""
Security middleware for production deployment
"""
import os
from flask import request, current_app
from functools import wraps

class SecurityMiddleware:
    """Security middleware for production deployment."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        # Set security headers
        @app.after_request
        def set_security_headers(response):
            # Prevent clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # Prevent MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # XSS protection
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com "
                "https://cdn.replit.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net https://cdn.replit.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # HTTPS enforcement in production
            if not app.debug:
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
        
        # Rate limiting storage (in-memory for now, should use Redis in production)
        app.rate_limit_storage = {}
        
        # Add request ID for tracing
        @app.before_request
        def add_request_id():
            import uuid
            request.request_id = str(uuid.uuid4())[:8]
            current_app.logger.info(f"Request {request.request_id}: {request.method} {request.path}")

def rate_limit(max_requests=100, window_seconds=3600):
    """Rate limiting decorator."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Rate limiting key
            key = f"{client_ip}:{request.endpoint}"
            
            # Check rate limit
            import time
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Get current app's rate limit storage
            storage = current_app.rate_limit_storage
            
            # Clean old entries
            if key in storage:
                storage[key] = [timestamp for timestamp in storage[key] if timestamp > window_start]
            else:
                storage[key] = []
            
            # Check if limit exceeded
            if len(storage[key]) >= max_requests:
                current_app.logger.warning(f"Rate limit exceeded for {client_ip} on {request.endpoint}")
                return {'error': 'Rate limit exceeded. Please try again later.'}, 429
            
            # Add current request
            storage[key].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_https():
    """Middleware to enforce HTTPS in production."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.debug and not request.is_secure:
                return {'error': 'HTTPS required'}, 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_content_type(allowed_types=['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']):
    """Validate request content type."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_type = request.content_type
                if content_type:
                    content_type = content_type.split(';')[0].strip()
                
                if content_type not in allowed_types:
                    current_app.logger.warning(f"Invalid content type: {content_type}")
                    return {'error': 'Invalid content type'}, 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_filename(filename):
    """Sanitize uploaded filenames."""
    import re
    import os
    
    # Remove directory traversal attempts
    filename = os.path.basename(filename)
    
    # Remove special characters except dots, hyphens, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Limit filename length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def log_security_event(event_type, details=None):
    """Log security events for monitoring."""
    import json
    from datetime import datetime
    
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'client_ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
        'user_agent': request.headers.get('User-Agent', ''),
        'endpoint': request.endpoint,
        'method': request.method,
        'request_id': getattr(request, 'request_id', 'unknown'),
        'details': details or {}
    }
    
    current_app.logger.warning(f"Security Event: {json.dumps(event)}")