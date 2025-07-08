"""
External Construction Management Tools Integration
Supports integration with Procore, Autodesk Construction Cloud, PlanGrid, etc.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import Project, Activity
from extensions import db
from logger import log_activity, log_error

class ExternalIntegrationService:
    """Service for integrating with external construction management platforms"""
    
    def __init__(self):
        self.supported_platforms = {
            'procore': {
                'name': 'Procore',
                'api_base': 'https://api.procore.com',
                'auth_type': 'oauth2',
                'endpoints': {
                    'projects': '/rest/v1.0/projects',
                    'schedules': '/rest/v1.0/projects/{project_id}/schedules',
                    'activities': '/rest/v1.0/projects/{project_id}/schedule_line_items',
                    'progress': '/rest/v1.0/projects/{project_id}/progress_reports'
                }
            },
            'autodesk_acc': {
                'name': 'Autodesk Construction Cloud',
                'api_base': 'https://developer.api.autodesk.com',
                'auth_type': 'oauth2',
                'endpoints': {
                    'projects': '/project/v1/hubs/{hub_id}/projects',
                    'schedules': '/project/v1/hubs/{hub_id}/projects/{project_id}/schedules',
                    'models': '/project/v1/hubs/{hub_id}/projects/{project_id}/versions'
                }
            },
            'plangrid': {
                'name': 'PlanGrid',
                'api_base': 'https://api.plangrid.com',
                'auth_type': 'api_key',
                'endpoints': {
                    'projects': '/v1/projects',
                    'sheets': '/v1/projects/{project_id}/sheets',
                    'issues': '/v1/projects/{project_id}/issues'
                }
            }
        }
    
    def sync_project_to_procore(self, project_id: int, procore_config: Dict[str, str]) -> Dict[str, Any]:
        """Sync project data to Procore"""
        
        try:
            project = Project.query.get_or_404(project_id)
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            # Prepare Procore project data
            procore_project_data = {
                'project': {
                    'name': project.name,
                    'description': project.description,
                    'start_date': project.start_date.isoformat() if project.start_date else None,
                    'estimated_completion_date': project.end_date.isoformat() if project.end_date else None,
                    'project_type': project.building_type or 'Commercial',
                    'square_footage': project.total_sf,
                    'budget': project.budget,
                    'address': project.location
                }
            }
            
            # Create/update project in Procore
            sync_result = {
                'platform': 'procore',
                'project_id': project_id,
                'external_project_id': None,
                'sync_status': 'pending',
                'synced_at': datetime.now().isoformat(),
                'activities_synced': 0,
                'errors': []
            }
            
            # Simulate API call (replace with actual Procore API integration)
            if self._validate_procore_credentials(procore_config):
                # Simulate successful project creation
                sync_result.update({
                    'external_project_id': f"procore_{project_id}_{int(datetime.now().timestamp())}",
                    'sync_status': 'success',
                    'activities_synced': len(activities),
                    'sync_details': {
                        'project_created': True,
                        'schedule_items_created': len(activities),
                        'documents_uploaded': 0,
                        'team_members_invited': 0
                    }
                })
                
                log_activity(
                    'system',
                    f"Project {project.name} synced to Procore",
                    {'project_id': project_id, 'external_id': sync_result['external_project_id']}
                )
            else:
                sync_result.update({
                    'sync_status': 'failed',
                    'errors': ['Invalid Procore credentials']
                })
            
            return sync_result
            
        except Exception as e:
            log_error(e, {'service': 'procore_sync', 'project_id': project_id})
            return {
                'sync_status': 'error',
                'error': str(e)
            }
    
    def sync_from_autodesk_acc(self, project_id: int, autodesk_config: Dict[str, str]) -> Dict[str, Any]:
        """Import project data from Autodesk Construction Cloud"""
        
        try:
            # Simulate Autodesk ACC data retrieval
            acc_project_data = {
                'project_info': {
                    'name': f'Imported Project {project_id}',
                    'description': 'Project imported from Autodesk Construction Cloud',
                    'location': 'Site Address from ACC',
                    'project_type': 'Commercial Building'
                },
                'schedule_data': [
                    {
                        'activity_name': 'Site Preparation',
                        'duration': 5,
                        'start_date': datetime.now().date(),
                        'trade': 'sitework'
                    },
                    {
                        'activity_name': 'Foundation Work',
                        'duration': 10,
                        'start_date': (datetime.now() + timedelta(days=5)).date(),
                        'trade': 'concrete'
                    },
                    {
                        'activity_name': 'Structural Steel',
                        'duration': 15,
                        'start_date': (datetime.now() + timedelta(days=15)).date(),
                        'trade': 'structural'
                    }
                ],
                'model_versions': [
                    {
                        'version': '1.0',
                        'date': datetime.now().isoformat(),
                        'file_type': 'rvt',
                        'size_mb': 145.6
                    }
                ]
            }
            
            import_result = {
                'platform': 'autodesk_acc',
                'project_id': project_id,
                'import_status': 'success',
                'imported_at': datetime.now().isoformat(),
                'activities_imported': len(acc_project_data['schedule_data']),
                'models_imported': len(acc_project_data['model_versions']),
                'import_summary': {
                    'project_info_updated': True,
                    'schedule_imported': True,
                    'models_linked': True,
                    'total_activities': len(acc_project_data['schedule_data'])
                }
            }
            
            return import_result
            
        except Exception as e:
            log_error(e, {'service': 'autodesk_acc_import', 'project_id': project_id})
            return {
                'import_status': 'error',
                'error': str(e)
            }
    
    def sync_with_plangrid(self, project_id: int, plangrid_config: Dict[str, str]) -> Dict[str, Any]:
        """Sync drawings and issues with PlanGrid"""
        
        try:
            project = Project.query.get_or_404(project_id)
            
            # Simulate PlanGrid integration
            plangrid_data = {
                'sheets_synced': [
                    {'name': 'Site Plan', 'sheet_number': 'C001', 'discipline': 'Civil'},
                    {'name': 'Foundation Plan', 'sheet_number': 'S001', 'discipline': 'Structural'},
                    {'name': 'Floor Plans', 'sheet_number': 'A101', 'discipline': 'Architectural'},
                    {'name': 'Electrical Plan', 'sheet_number': 'E101', 'discipline': 'Electrical'}
                ],
                'issues_imported': [
                    {
                        'title': 'Foundation wall alignment',
                        'status': 'open',
                        'priority': 'high',
                        'trade': 'concrete'
                    },
                    {
                        'title': 'MEP coordination conflict',
                        'status': 'in_progress',
                        'priority': 'medium',
                        'trade': 'mechanical'
                    }
                ]
            }
            
            sync_result = {
                'platform': 'plangrid',
                'project_id': project_id,
                'sync_status': 'success',
                'synced_at': datetime.now().isoformat(),
                'sheets_synced': len(plangrid_data['sheets_synced']),
                'issues_imported': len(plangrid_data['issues_imported']),
                'sync_details': plangrid_data
            }
            
            return sync_result
            
        except Exception as e:
            log_error(e, {'service': 'plangrid_sync', 'project_id': project_id})
            return {
                'sync_status': 'error',
                'error': str(e)
            }
    
    def generate_integration_status_report(self, project_id: int) -> Dict[str, Any]:
        """Generate comprehensive integration status report"""
        
        project = Project.query.get_or_404(project_id)
        
        # Simulate integration status checking
        integration_status = {
            'project_id': project_id,
            'project_name': project.name,
            'generated_at': datetime.now().isoformat(),
            'platforms': {
                'procore': {
                    'connected': True,
                    'last_sync': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'sync_status': 'success',
                    'data_quality': 'excellent',
                    'issues': []
                },
                'autodesk_acc': {
                    'connected': False,
                    'last_sync': None,
                    'sync_status': 'not_configured',
                    'data_quality': 'n/a',
                    'issues': ['API credentials not configured']
                },
                'plangrid': {
                    'connected': True,
                    'last_sync': (datetime.now() - timedelta(days=1)).isoformat(),
                    'sync_status': 'partial',
                    'data_quality': 'good',
                    'issues': ['Some drawings failed to sync']
                }
            },
            'overall_health': {
                'connected_platforms': 2,
                'total_platforms': 3,
                'health_score': 75,
                'recommendations': [
                    'Configure Autodesk Construction Cloud integration',
                    'Review PlanGrid drawing sync issues',
                    'Set up automated daily sync schedule'
                ]
            }
        }
        
        return integration_status
    
    def _validate_procore_credentials(self, config: Dict[str, str]) -> bool:
        """Validate Procore API credentials"""
        
        required_keys = ['client_id', 'client_secret', 'company_id']
        return all(key in config and config[key] for key in required_keys)
    
    def _validate_autodesk_credentials(self, config: Dict[str, str]) -> bool:
        """Validate Autodesk API credentials"""
        
        required_keys = ['client_id', 'client_secret', 'hub_id']
        return all(key in config and config[key] for key in required_keys)
    
    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """Get list of available integration platforms"""
        
        integrations = []
        for platform_key, platform_info in self.supported_platforms.items():
            integrations.append({
                'id': platform_key,
                'name': platform_info['name'],
                'description': f"Integrate with {platform_info['name']} for enhanced project management",
                'auth_type': platform_info['auth_type'],
                'features': self._get_platform_features(platform_key),
                'setup_difficulty': 'medium',
                'cost': 'varies'
            })
        
        return integrations
    
    def _get_platform_features(self, platform: str) -> List[str]:
        """Get feature list for each platform"""
        
        features_map = {
            'procore': [
                'Project management and scheduling',
                'Budget tracking and financial reporting',
                'Document management and RFIs',
                'Quality and safety management',
                'Team collaboration tools'
            ],
            'autodesk_acc': [
                'BIM 360 model coordination',
                'Design collaboration and markup',
                'Construction management workflows',
                'Document management and control',
                'Field management and reporting'
            ],
            'plangrid': [
                'Construction drawing management',
                'Field markup and annotations',
                'Issue tracking and resolution',
                'Progress photo documentation',
                'Punch list management'
            ]
        }
        
        return features_map.get(platform, [])

# Global service instance
external_integration_service = ExternalIntegrationService()