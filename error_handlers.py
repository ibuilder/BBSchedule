"""
Comprehensive error handling for production deployment
"""
import traceback
from flask import jsonify, render_template, request, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from security_middleware import log_security_event

def register_error_handlers(app):
    """Register comprehensive error handlers."""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 Bad Request errors."""
        current_app.logger.error(f"400 Bad Request: {request.url} - {error}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad Request',
                'message': 'The request could not be understood by the server.',
                'status_code': 400
            }), 400
        
        return render_template('error.html', 
                             error_code=400, 
                             error_message="Bad Request",
                             error_description="The request could not be understood."), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle 401 Unauthorized errors."""
        current_app.logger.warning(f"401 Unauthorized: {request.url} - {request.remote_addr}")
        log_security_event('unauthorized_access', {'url': request.url})
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required.',
                'status_code': 401
            }), 401
        
        return render_template('error.html', 
                             error_code=401, 
                             error_message="Unauthorized",
                             error_description="Please log in to access this resource."), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        current_app.logger.warning(f"403 Forbidden: {request.url} - {request.remote_addr}")
        log_security_event('forbidden_access', {'url': request.url})
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied.',
                'status_code': 403
            }), 403
        
        return render_template('error.html', 
                             error_code=403, 
                             error_message="Access Denied",
                             error_description="You don't have permission to access this resource."), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        current_app.logger.info(f"404 Not Found: {request.url}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.',
                'status_code': 404
            }), 404
        
        return render_template('error.html', 
                             error_code=404, 
                             error_message="Page Not Found",
                             error_description="The page you're looking for doesn't exist."), 404
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        """Handle 429 Too Many Requests errors."""
        current_app.logger.warning(f"429 Rate Limit: {request.url} - {request.remote_addr}")
        log_security_event('rate_limit_exceeded', {'url': request.url})
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Too Many Requests',
                'message': 'Rate limit exceeded. Please try again later.',
                'status_code': 429
            }), 429
        
        return render_template('error.html', 
                             error_code=429, 
                             error_message="Too Many Requests",
                             error_description="Please wait before making another request."), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server errors."""
        current_app.logger.error(f"500 Internal Server Error: {request.url}")
        current_app.logger.error(f"Error details: {traceback.format_exc()}")
        
        # Log the full error for debugging
        log_security_event('internal_server_error', {
            'url': request.url,
            'error': str(error),
            'traceback': traceback.format_exc()
        })
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.',
                'status_code': 500
            }), 500
        
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Internal Server Error",
                             error_description="Something went wrong on our end."), 500
    
    @app.errorhandler(503)
    def service_unavailable_error(error):
        """Handle 503 Service Unavailable errors."""
        current_app.logger.error(f"503 Service Unavailable: {request.url}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'The service is temporarily unavailable.',
                'status_code': 503
            }), 503
        
        return render_template('error.html', 
                             error_code=503, 
                             error_message="Service Unavailable",
                             error_description="The service is temporarily unavailable."), 503
    
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        """Handle database errors."""
        current_app.logger.error(f"Database Error: {str(error)}")
        current_app.logger.error(f"Database traceback: {traceback.format_exc()}")
        
        # Rollback any pending transactions
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Database Error',
                'message': 'A database error occurred.',
                'status_code': 500
            }), 500
        
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Database Error",
                             error_description="A database error occurred. Please try again."), 500
    
    @app.errorhandler(Exception)
    def general_exception_handler(error):
        """Handle any unhandled exceptions."""
        current_app.logger.error(f"Unhandled Exception: {str(error)}")
        current_app.logger.error(f"Exception traceback: {traceback.format_exc()}")
        
        # Log the error details
        log_security_event('unhandled_exception', {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'url': request.url,
            'traceback': traceback.format_exc()
        })
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.',
                'status_code': 500
            }), 500
        
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Internal Server Error",
                             error_description="An unexpected error occurred."), 500
    
    @app.errorhandler(HTTPException)
    def http_exception_handler(error):
        """Handle HTTP exceptions."""
        current_app.logger.error(f"HTTP Exception: {error.code} - {error.description}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': error.name,
                'message': error.description,
                'status_code': error.code
            }), error.code
        
        return render_template('error.html', 
                             error_code=error.code, 
                             error_message=error.name,
                             error_description=error.description), error.code