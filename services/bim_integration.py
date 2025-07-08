"""
BIM (Building Information Modeling) Integration Service
Provides 3D visualization and model integration capabilities
"""

import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from models import Project, Activity
from extensions import db
from logger import log_activity, log_performance

class BIMIntegrationService:
    """BIM integration service for 3D visualization and model management"""
    
    def __init__(self):
        self.supported_formats = ['ifc', 'rvt', 'dwg', 'skp', 'obj', 'gltf']
        self.viewer_configs = {
            'default': {
                'background_color': '#f8f9fa',
                'camera_position': [10, 10, 10],
                'lighting': 'ambient',
                'render_quality': 'medium'
            },
            'construction': {
                'background_color': '#e3f2fd',
                'camera_position': [15, 8, 12],
                'lighting': 'directional',
                'render_quality': 'high',
                'show_progress': True
            }
        }
    
    def generate_3d_timeline_visualization(self, project_id: int) -> Dict[str, Any]:
        """Generate 3D timeline visualization data for the project"""
        
        project = Project.query.get_or_404(project_id)
        activities = Activity.query.filter_by(project_id=project_id).order_by(Activity.start_date).all()
        
        # Generate 3D building representation
        building_components = self._generate_building_components(project, activities)
        
        # Create timeline data with 3D elements
        timeline_data = {
            'project_info': {
                'id': project.id,
                'name': project.name,
                'total_sf': project.total_sf,
                'floor_count': project.floor_count,
                'building_type': project.building_type
            },
            'scene_config': self.viewer_configs['construction'],
            'building_model': {
                'components': building_components,
                'total_components': len(building_components),
                'completion_percentage': self._calculate_3d_completion(activities)
            },
            'timeline_phases': self._generate_timeline_phases(activities),
            'construction_sequence': self._generate_construction_sequence(activities),
            'progress_visualization': self._generate_progress_visualization(activities),
            'generated_at': datetime.now().isoformat()
        }
        
        return timeline_data
    
    def _generate_building_components(self, project: Project, activities: List[Activity]) -> List[Dict[str, Any]]:
        """Generate 3D building components based on project activities"""
        
        components = []
        floor_height = 3.5  # meters
        
        # Foundation components
        foundation_activities = [a for a in activities if 'foundation' in a.name.lower() or 'excavation' in a.name.lower()]
        if foundation_activities:
            components.append({
                'id': 'foundation',
                'type': 'foundation',
                'name': 'Foundation & Basement',
                'geometry': {
                    'type': 'box',
                    'dimensions': [30, 20, 2],
                    'position': [0, -1, 0],
                    'color': '#8d6e63'
                },
                'activities': [a.id for a in foundation_activities],
                'progress': sum(a.progress for a in foundation_activities) / len(foundation_activities) if foundation_activities else 0,
                'phase': 'foundation'
            })
        
        # Floor/Structure components
        if project.floor_count:
            for floor in range(int(project.floor_count)):
                floor_activities = [a for a in activities if f'floor {floor+1}' in a.name.lower() or 'structural' in a.name.lower()]
                
                components.append({
                    'id': f'floor_{floor+1}',
                    'type': 'floor_structure',
                    'name': f'Floor {floor+1} Structure',
                    'geometry': {
                        'type': 'box',
                        'dimensions': [30, 20, 0.3],
                        'position': [0, floor * floor_height, 0],
                        'color': '#455a64'
                    },
                    'activities': [a.id for a in floor_activities],
                    'progress': sum(a.progress for a in floor_activities) / len(floor_activities) if floor_activities else 0,
                    'phase': 'structure'
                })
                
                # Walls for each floor
                components.append({
                    'id': f'walls_floor_{floor+1}',
                    'type': 'walls',
                    'name': f'Floor {floor+1} Walls',
                    'geometry': {
                        'type': 'walls',
                        'floor_level': floor * floor_height,
                        'height': floor_height - 0.3,
                        'color': '#e0e0e0'
                    },
                    'activities': [a.id for a in activities if 'wall' in a.name.lower() or 'framing' in a.name.lower()],
                    'progress': 0,
                    'phase': 'envelope'
                })
        
        # MEP Systems
        mep_activities = [a for a in activities if any(keyword in a.name.lower() for keyword in ['electrical', 'plumbing', 'hvac', 'mechanical'])]
        if mep_activities:
            components.append({
                'id': 'mep_systems',
                'type': 'mep',
                'name': 'MEP Systems',
                'geometry': {
                    'type': 'system_lines',
                    'color': '#ff9800',
                    'visibility': 'toggle'
                },
                'activities': [a.id for a in mep_activities],
                'progress': sum(a.progress for a in mep_activities) / len(mep_activities) if mep_activities else 0,
                'phase': 'mep'
            })
        
        # Finishing components
        finishing_activities = [a for a in activities if any(keyword in a.name.lower() for keyword in ['finish', 'paint', 'flooring', 'ceiling'])]
        if finishing_activities:
            components.append({
                'id': 'finishes',
                'type': 'finishes',
                'name': 'Interior Finishes',
                'geometry': {
                    'type': 'surface_materials',
                    'color': '#4caf50'
                },
                'activities': [a.id for a in finishing_activities],
                'progress': sum(a.progress for a in finishing_activities) / len(finishing_activities) if finishing_activities else 0,
                'phase': 'finishes'
            })
        
        return components
    
    def _generate_timeline_phases(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """Generate construction phases for timeline visualization"""
        
        phases = {
            'foundation': {'name': 'Foundation & Site Work', 'color': '#8d6e63', 'activities': []},
            'structure': {'name': 'Structural Work', 'color': '#455a64', 'activities': []},
            'envelope': {'name': 'Building Envelope', 'color': '#546e7a', 'activities': []},
            'mep': {'name': 'MEP Systems', 'color': '#ff9800', 'activities': []},
            'finishes': {'name': 'Interior Finishes', 'color': '#4caf50', 'activities': []},
            'sitework': {'name': 'Site Completion', 'color': '#689f38', 'activities': []}
        }
        
        for activity in activities:
            activity_name = activity.name.lower()
            
            if any(keyword in activity_name for keyword in ['foundation', 'excavation', 'site prep']):
                phases['foundation']['activities'].append(activity)
            elif any(keyword in activity_name for keyword in ['structural', 'concrete', 'steel', 'frame']):
                phases['structure']['activities'].append(activity)
            elif any(keyword in activity_name for keyword in ['roof', 'wall', 'window', 'envelope']):
                phases['envelope']['activities'].append(activity)
            elif any(keyword in activity_name for keyword in ['electrical', 'plumbing', 'hvac', 'mechanical']):
                phases['mep']['activities'].append(activity)
            elif any(keyword in activity_name for keyword in ['finish', 'paint', 'flooring', 'ceiling']):
                phases['finishes']['activities'].append(activity)
            else:
                phases['sitework']['activities'].append(activity)
        
        # Convert to timeline format
        timeline_phases = []
        for phase_key, phase_data in phases.items():
            if phase_data['activities']:
                activities_list = phase_data['activities']
                start_date = min(a.start_date for a in activities_list if a.start_date)
                end_date = max(a.end_date for a in activities_list if a.end_date) if any(a.end_date for a in activities_list) else None
                
                timeline_phases.append({
                    'id': phase_key,
                    'name': phase_data['name'],
                    'color': phase_data['color'],
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'activities': [a.id for a in activities_list],
                    'progress': sum(a.progress for a in activities_list) / len(activities_list),
                    'duration_days': sum(a.duration for a in activities_list)
                })
        
        return timeline_phases
    
    def _generate_construction_sequence(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """Generate construction sequence animation data"""
        
        sequence_steps = []
        sorted_activities = sorted(activities, key=lambda a: a.start_date if a.start_date else datetime.now().date())
        
        for i, activity in enumerate(sorted_activities):
            sequence_steps.append({
                'step': i + 1,
                'activity_id': activity.id,
                'activity_name': activity.name,
                'start_date': activity.start_date.isoformat() if activity.start_date else None,
                'duration': activity.duration,
                'animation': {
                    'type': 'progressive_build',
                    'duration_seconds': 2,
                    'easing': 'ease-in-out'
                },
                'camera_focus': self._get_activity_camera_focus(activity),
                'visibility_changes': {
                    'show': [f'component_{activity.id}'],
                    'highlight': [f'component_{activity.id}'],
                    'fade': []
                }
            })
        
        return sequence_steps
    
    def _generate_progress_visualization(self, activities: List[Activity]) -> Dict[str, Any]:
        """Generate progress visualization data"""
        
        total_activities = len(activities)
        completed_activities = len([a for a in activities if a.progress >= 100])
        in_progress_activities = len([a for a in activities if 0 < a.progress < 100])
        
        progress_data = {
            'overall_progress': sum(a.progress for a in activities) / total_activities if total_activities > 0 else 0,
            'phase_progress': {},
            'color_coding': {
                'not_started': '#e0e0e0',
                'in_progress': '#ff9800',
                'completed': '#4caf50',
                'delayed': '#f44336'
            },
            'statistics': {
                'total_activities': total_activities,
                'completed': completed_activities,
                'in_progress': in_progress_activities,
                'not_started': total_activities - completed_activities - in_progress_activities
            }
        }
        
        return progress_data
    
    def _calculate_3d_completion(self, activities: List[Activity]) -> float:
        """Calculate 3D model completion percentage"""
        if not activities:
            return 0.0
        
        total_progress = sum(a.progress for a in activities)
        return total_progress / len(activities)
    
    def _get_activity_camera_focus(self, activity: Activity) -> Dict[str, Any]:
        """Get camera focus point for activity visualization"""
        
        # Default camera positions for different activity types
        activity_name = activity.name.lower()
        
        if 'foundation' in activity_name:
            return {'position': [0, -2, 15], 'target': [0, -1, 0]}
        elif 'roof' in activity_name:
            return {'position': [0, 20, 15], 'target': [0, 15, 0]}
        elif 'floor' in activity_name:
            floor_num = 1  # Extract floor number if possible
            return {'position': [15, floor_num * 3.5, 15], 'target': [0, floor_num * 3.5, 0]}
        else:
            return {'position': [10, 10, 10], 'target': [0, 5, 0]}
    
    def generate_bim_viewer_config(self, project_id: int, viewer_type: str = 'construction') -> Dict[str, Any]:
        """Generate BIM viewer configuration"""
        
        config = self.viewer_configs.get(viewer_type, self.viewer_configs['default']).copy()
        
        # Add project-specific settings
        project = Project.query.get_or_404(project_id)
        
        config.update({
            'project_id': project_id,
            'project_name': project.name,
            'controls': {
                'pan': True,
                'zoom': True,
                'rotate': True,
                'timeline_scrub': True,
                'layer_toggle': True
            },
            'ui_elements': {
                'timeline': True,
                'phase_selector': True,
                'progress_indicator': True,
                'legend': True,
                'toolbar': True
            },
            'interaction': {
                'click_for_info': True,
                'hover_highlight': True,
                'selection_mode': 'single'
            },
            'performance': {
                'auto_lod': True,  # Level of Detail
                'frustum_culling': True,
                'instancing': True
            }
        })
        
        return config
    
    def export_3d_data(self, project_id: int, format_type: str = 'gltf') -> Dict[str, Any]:
        """Export 3D model data in specified format"""
        
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")
        
        timeline_data = self.generate_3d_timeline_visualization(project_id)
        
        export_data = {
            'format': format_type,
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'project_id': project_id,
            'metadata': timeline_data['project_info'],
            'model_data': timeline_data['building_model'],
            'animation_data': timeline_data['construction_sequence'],
            'download_url': f'/api/project/{project_id}/export_3d/{format_type}'
        }
        
        return export_data

# Global instance
bim_service = BIMIntegrationService()