"""
Enterprise integration and API management for BBSchedule
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from functools import wraps
import jwt
from flask import request, jsonify, current_app
import xml.etree.ElementTree as ET
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64

# Integration logging
integration_logger = logging.getLogger('integration')

@dataclass
class IntegrationConfig:
    """Configuration for external integrations"""
    name: str
    base_url: str
    api_key: str
    auth_type: str  # 'api_key', 'oauth2', 'jwt', 'basic'
    timeout: int = 30
    retry_count: int = 3
    rate_limit: int = 100  # requests per minute

class EnterpriseAPIGateway:
    """Enterprise API Gateway with rate limiting and authentication"""
    
    def __init__(self):
        self.integrations = {}
        self.rate_limits = {}
        self.api_keys = {}
        self.load_configurations()
    
    def load_configurations(self):
        """Load integration configurations from environment"""
        # Procore Integration
        if os.environ.get('PROCORE_API_KEY'):
            self.integrations['procore'] = IntegrationConfig(
                name='Procore',
                base_url=os.environ.get('PROCORE_BASE_URL', 'https://api.procore.com/rest/v1.0'),
                api_key=os.environ.get('PROCORE_API_KEY'),
                auth_type='oauth2'
            )
        
        # Autodesk Construction Cloud
        if os.environ.get('AUTODESK_CLIENT_ID'):
            self.integrations['autodesk'] = IntegrationConfig(
                name='Autodesk Construction Cloud',
                base_url='https://developer.api.autodesk.com',
                api_key=os.environ.get('AUTODESK_CLIENT_ID'),
                auth_type='oauth2'
            )
        
        # PlanGrid Integration
        if os.environ.get('PLANGRID_API_KEY'):
            self.integrations['plangrid'] = IntegrationConfig(
                name='PlanGrid',
                base_url='https://io.plangrid.com/api/v1',
                api_key=os.environ.get('PLANGRID_API_KEY'),
                auth_type='api_key'
            )
        
        # Primavera Cloud
        if os.environ.get('PRIMAVERA_API_KEY'):
            self.integrations['primavera'] = IntegrationConfig(
                name='Primavera Cloud',
                base_url='https://api.oraclecx.com/primavera/v1',
                api_key=os.environ.get('PRIMAVERA_API_KEY'),
                auth_type='oauth2'
            )
    
    def generate_api_key(self, client_name: str, permissions: List[str]) -> str:
        """Generate API key for external clients"""
        key_data = {
            'client_name': client_name,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        
        api_key = jwt.encode(
            key_data,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        self.api_keys[api_key] = key_data
        integration_logger.info(f"API key generated for {client_name}")
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate incoming API key"""
        try:
            payload = jwt.decode(
                api_key,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.utcnow() > expires_at:
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    def check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check rate limiting for API calls"""
        now = datetime.utcnow()
        minute_window = now.replace(second=0, microsecond=0)
        
        key = f"{client_id}:{endpoint}:{minute_window}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = 0
        
        self.rate_limits[key] += 1
        
        # Clean old entries
        cutoff = minute_window - timedelta(minutes=5)
        self.rate_limits = {
            k: v for k, v in self.rate_limits.items()
            if datetime.fromisoformat(k.split(':')[-1]) > cutoff
        }
        
        return self.rate_limits[key] <= 100  # 100 requests per minute

def require_api_key(permissions: List[str] = None):
    """Decorator to require valid API key for endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            key_data = api_gateway.validate_api_key(api_key)
            if not key_data:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Check permissions
            if permissions:
                user_permissions = key_data.get('permissions', [])
                if not any(perm in user_permissions for perm in permissions):
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Check rate limit
            client_name = key_data.get('client_name', 'unknown')
            if not api_gateway.check_rate_limit(client_name, request.endpoint):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add client info to request context
            request.api_client = key_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class ProcoreIntegration:
    """Integration with Procore construction management platform"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.access_token = None
        self.token_expires = None
    
    def authenticate(self):
        """Authenticate with Procore API"""
        # OAuth2 flow for Procore
        auth_url = f"{self.config.base_url}/oauth/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.config.api_key,
            'client_secret': os.environ.get('PROCORE_CLIENT_SECRET')
        }
        
        try:
            response = requests.post(auth_url, data=auth_data, timeout=self.config.timeout)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            integration_logger.info("Procore authentication successful")
            return True
            
        except Exception as e:
            integration_logger.error(f"Procore authentication failed: {e}")
            return False
    
    def sync_project(self, project_data: Dict) -> Dict:
        """Sync project data to Procore"""
        if not self._ensure_authenticated():
            return {'success': False, 'error': 'Authentication failed'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Transform BBSchedule project to Procore format
        procore_project = {
            'name': project_data['name'],
            'description': project_data.get('description', ''),
            'start_date': project_data.get('start_date'),
            'estimated_completion_date': project_data.get('end_date'),
            'project_type': 'Construction'
        }
        
        try:
            url = f"{self.config.base_url}/projects"
            response = requests.post(url, json=procore_project, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            integration_logger.info(f"Project synced to Procore: {result['id']}")
            
            return {'success': True, 'procore_id': result['id']}
            
        except Exception as e:
            integration_logger.error(f"Procore project sync failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def sync_activities(self, activities: List[Dict]) -> Dict:
        """Sync activities to Procore as work breakdown structure"""
        if not self._ensure_authenticated():
            return {'success': False, 'error': 'Authentication failed'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        synced_activities = []
        
        for activity in activities:
            procore_activity = {
                'name': activity['name'],
                'description': activity.get('description', ''),
                'start_date': activity.get('start_date'),
                'due_date': activity.get('end_date'),
                'percent_complete': activity.get('progress', 0)
            }
            
            try:
                url = f"{self.config.base_url}/work_breakdown_structure"
                response = requests.post(url, json=procore_activity, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                synced_activities.append(result['id'])
                
            except Exception as e:
                integration_logger.error(f"Activity sync failed: {e}")
        
        return {
            'success': True,
            'synced_count': len(synced_activities),
            'procore_ids': synced_activities
        }
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.utcnow() >= self.token_expires:
            return self.authenticate()
        return True

class AutodeskIntegration:
    """Integration with Autodesk Construction Cloud"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.access_token = None
        self.token_expires = None
    
    def authenticate(self):
        """Authenticate with Autodesk API"""
        auth_url = "https://developer.api.autodesk.com/authentication/v1/authenticate"
        
        auth_data = {
            'client_id': self.config.api_key,
            'client_secret': os.environ.get('AUTODESK_CLIENT_SECRET'),
            'grant_type': 'client_credentials',
            'scope': 'account:read data:read data:write'
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            integration_logger.info("Autodesk authentication successful")
            return True
            
        except Exception as e:
            integration_logger.error(f"Autodesk authentication failed: {e}")
            return False
    
    def get_bim_model_data(self, model_id: str) -> Dict:
        """Get BIM model data from Autodesk"""
        if not self._ensure_authenticated():
            return {'success': False, 'error': 'Authentication failed'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{model_id}/metadata"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            model_data = response.json()
            return {'success': True, 'data': model_data}
            
        except Exception as e:
            integration_logger.error(f"BIM model fetch failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.utcnow() >= self.token_expires:
            return self.authenticate()
        return True

class WebhookManager:
    """Manage incoming webhooks from external systems"""
    
    def __init__(self):
        self.webhook_secrets = {}
        self.load_webhook_configs()
    
    def load_webhook_configs(self):
        """Load webhook configurations"""
        # Procore webhook secret
        if os.environ.get('PROCORE_WEBHOOK_SECRET'):
            self.webhook_secrets['procore'] = os.environ.get('PROCORE_WEBHOOK_SECRET')
        
        # Autodesk webhook secret
        if os.environ.get('AUTODESK_WEBHOOK_SECRET'):
            self.webhook_secrets['autodesk'] = os.environ.get('AUTODESK_WEBHOOK_SECRET')
    
    def verify_webhook_signature(self, provider: str, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if provider not in self.webhook_secrets:
            return False
        
        secret = self.webhook_secrets[provider].encode()
        
        # Create HMAC signature
        import hmac
        expected_signature = hmac.new(
            secret,
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook(self, provider: str, event_type: str, payload: Dict) -> Dict:
        """Process incoming webhook"""
        integration_logger.info(f"Processing {provider} webhook: {event_type}")
        
        if provider == 'procore':
            return self._process_procore_webhook(event_type, payload)
        elif provider == 'autodesk':
            return self._process_autodesk_webhook(event_type, payload)
        
        return {'success': False, 'error': 'Unknown provider'}
    
    def _process_procore_webhook(self, event_type: str, payload: Dict) -> Dict:
        """Process Procore webhook events"""
        if event_type == 'project.updated':
            # Handle project updates from Procore
            project_id = payload.get('resource_id')
            # Update local project data
            pass
        elif event_type == 'task.completed':
            # Handle task completion from Procore
            pass
        
        return {'success': True}
    
    def _process_autodesk_webhook(self, event_type: str, payload: Dict) -> Dict:
        """Process Autodesk webhook events"""
        if event_type == 'model.updated':
            # Handle BIM model updates
            pass
        
        return {'success': True}

class DataSyncManager:
    """Manage bidirectional data synchronization"""
    
    def __init__(self):
        self.sync_jobs = {}
        self.last_sync_times = {}
    
    def schedule_sync(self, integration: str, sync_type: str, interval_hours: int = 1):
        """Schedule regular data synchronization"""
        sync_job = {
            'integration': integration,
            'sync_type': sync_type,
            'interval_hours': interval_hours,
            'last_run': None,
            'next_run': datetime.utcnow() + timedelta(hours=interval_hours)
        }
        
        job_id = f"{integration}_{sync_type}"
        self.sync_jobs[job_id] = sync_job
        
        integration_logger.info(f"Scheduled sync job: {job_id}")
        return job_id
    
    def run_sync_job(self, job_id: str) -> Dict:
        """Run a specific sync job"""
        if job_id not in self.sync_jobs:
            return {'success': False, 'error': 'Job not found'}
        
        job = self.sync_jobs[job_id]
        
        try:
            if job['integration'] == 'procore':
                result = self._sync_procore_data(job['sync_type'])
            elif job['integration'] == 'autodesk':
                result = self._sync_autodesk_data(job['sync_type'])
            else:
                result = {'success': False, 'error': 'Unknown integration'}
            
            # Update job status
            job['last_run'] = datetime.utcnow()
            job['next_run'] = datetime.utcnow() + timedelta(hours=job['interval_hours'])
            
            return result
            
        except Exception as e:
            integration_logger.error(f"Sync job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _sync_procore_data(self, sync_type: str) -> Dict:
        """Sync data with Procore"""
        # Implementation for Procore data sync
        return {'success': True, 'records_synced': 0}
    
    def _sync_autodesk_data(self, sync_type: str) -> Dict:
        """Sync data with Autodesk"""
        # Implementation for Autodesk data sync
        return {'success': True, 'records_synced': 0}

# Global integration components
api_gateway = EnterpriseAPIGateway()
webhook_manager = WebhookManager()
data_sync_manager = DataSyncManager()

def init_enterprise_integrations(app):
    """Initialize enterprise integrations"""
    
    # Initialize integrations based on available configurations
    integrations = {}
    
    if 'procore' in api_gateway.integrations:
        integrations['procore'] = ProcoreIntegration(api_gateway.integrations['procore'])
    
    if 'autodesk' in api_gateway.integrations:
        integrations['autodesk'] = AutodeskIntegration(api_gateway.integrations['autodesk'])
    
    app.integrations = integrations
    
    integration_logger.info(f"Initialized {len(integrations)} enterprise integrations")
    
    return {
        'api_gateway': api_gateway,
        'integrations': integrations,
        'webhook_manager': webhook_manager,
        'data_sync_manager': data_sync_manager
    }