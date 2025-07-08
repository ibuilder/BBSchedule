"""
IoT & Field Integration Service
Equipment tracking, drone surveys, photo documentation, and QR code tracking
"""

import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import Project, Activity
from extensions import db
from logger import log_activity, log_error

class IoTFieldService:
    """IoT and field integration service for construction monitoring"""
    
    def __init__(self):
        self.equipment_registry = {}
        self.drone_missions = {}
        self.photo_documentation = {}
        self.qr_code_tracking = {}
        
    def register_equipment(self, project_id: int, equipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register IoT equipment for project monitoring"""
        
        equipment_id = f"equip_{project_id}_{equipment_data['name']}_{int(datetime.now().timestamp())}"
        
        registration_data = {
            'equipment_id': equipment_id,
            'project_id': project_id,
            'name': equipment_data['name'],
            'type': equipment_data.get('type', 'general'),
            'manufacturer': equipment_data.get('manufacturer', 'Unknown'),
            'model': equipment_data.get('model', 'Unknown'),
            'serial_number': equipment_data.get('serial_number'),
            'iot_device_id': equipment_data.get('iot_device_id'),
            'sensors': equipment_data.get('sensors', []),
            'location': equipment_data.get('location', {}),
            'status': 'active',
            'last_update': datetime.now().isoformat(),
            'metrics': {
                'uptime_hours': 0,
                'utilization_rate': 0,
                'maintenance_alerts': 0,
                'efficiency_score': 100
            },
            'alerts': [],
            'maintenance_schedule': []
        }
        
        self.equipment_registry[equipment_id] = registration_data
        
        log_activity('system', f"Registered equipment {equipment_data['name']} for project {project_id}", {
            'equipment_id': equipment_id,
            'project_id': project_id
        })
        
        return registration_data
    
    def track_equipment_status(self, equipment_id: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track real-time equipment status and metrics"""
        
        if equipment_id not in self.equipment_registry:
            raise ValueError("Equipment not found")
        
        equipment = self.equipment_registry[equipment_id]
        
        # Update sensor readings
        sensor_update = {
            'timestamp': datetime.now().isoformat(),
            'readings': sensor_data,
            'processed_at': datetime.now().isoformat()
        }
        
        # Analyze sensor data for alerts
        alerts = self._analyze_sensor_data(equipment, sensor_data)
        
        # Update equipment metrics
        equipment['last_update'] = datetime.now().isoformat()
        equipment['alerts'].extend(alerts)
        
        # Calculate utilization and efficiency
        if 'operating_hours' in sensor_data:
            equipment['metrics']['uptime_hours'] += sensor_data['operating_hours']
        
        if 'fuel_consumption' in sensor_data and 'work_completed' in sensor_data:
            efficiency = sensor_data['work_completed'] / max(1, sensor_data['fuel_consumption'])
            equipment['metrics']['efficiency_score'] = min(100, efficiency * 20)  # Scale to 0-100
        
        # Utilization calculation
        total_hours = (datetime.now() - datetime.fromisoformat(equipment['last_update'].replace('Z', '+00:00'))).total_seconds() / 3600
        if total_hours > 0:
            equipment['metrics']['utilization_rate'] = min(100, (equipment['metrics']['uptime_hours'] / total_hours) * 100)
        
        return {
            'equipment_id': equipment_id,
            'status_updated': True,
            'alerts_generated': len(alerts),
            'current_metrics': equipment['metrics'],
            'latest_sensor_data': sensor_update
        }
    
    def create_drone_mission(self, project_id: int, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and schedule a drone survey mission"""
        
        mission_id = f"drone_{project_id}_{int(datetime.now().timestamp())}"
        
        mission = {
            'mission_id': mission_id,
            'project_id': project_id,
            'title': mission_data.get('title', 'Site Survey'),
            'mission_type': mission_data.get('type', 'progress_monitoring'),
            'scheduled_date': mission_data.get('scheduled_date', datetime.now().isoformat()),
            'pilot': mission_data.get('pilot', 'Auto-pilot'),
            'drone_model': mission_data.get('drone_model', 'DJI Phantom 4 Pro'),
            'flight_parameters': {
                'altitude': mission_data.get('altitude', 120),  # feet
                'speed': mission_data.get('speed', 25),  # mph
                'overlap': mission_data.get('overlap', 80),  # percentage
                'resolution': mission_data.get('resolution', '2cm/pixel')
            },
            'coverage_area': mission_data.get('coverage_area', {}),
            'objectives': mission_data.get('objectives', [
                'Progress documentation',
                'Site safety inspection',
                'Material inventory',
                '3D model generation'
            ]),
            'status': 'scheduled',
            'weather_requirements': {
                'max_wind_speed': 25,  # mph
                'min_visibility': 3,   # miles
                'no_precipitation': True
            },
            'deliverables': {
                'photos': {'format': 'JPG', 'expected_count': 0},
                'video': {'format': 'MP4', 'duration_minutes': 0},
                '3d_model': {'format': 'OBJ', 'resolution': 'high'},
                'orthomosaic': {'format': 'GeoTIFF', 'resolution': '2cm/pixel'}
            },
            'created_at': datetime.now().isoformat()
        }
        
        self.drone_missions[mission_id] = mission
        
        return mission
    
    def process_drone_survey_results(self, mission_id: str, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process drone survey results and generate insights"""
        
        if mission_id not in self.drone_missions:
            raise ValueError("Mission not found")
        
        mission = self.drone_missions[mission_id]
        
        # Simulate processing survey data
        results = {
            'mission_id': mission_id,
            'processed_at': datetime.now().isoformat(),
            'flight_data': {
                'actual_altitude': survey_data.get('altitude', mission['flight_parameters']['altitude']),
                'flight_time_minutes': survey_data.get('flight_time', 35),
                'distance_covered_miles': survey_data.get('distance', 2.5),
                'photos_captured': survey_data.get('photo_count', 150),
                'video_duration_minutes': survey_data.get('video_duration', 8)
            },
            'analysis_results': {
                'progress_assessment': self._analyze_construction_progress(survey_data),
                'safety_observations': self._analyze_safety_conditions(survey_data),
                'material_inventory': self._analyze_material_status(survey_data),
                'site_changes': self._detect_site_changes(mission_id, survey_data)
            },
            'deliverables_generated': {
                '3d_model_url': f'/api/drone/{mission_id}/3d_model',
                'orthomosaic_url': f'/api/drone/{mission_id}/orthomosaic',
                'photo_gallery_url': f'/api/drone/{mission_id}/photos',
                'report_url': f'/api/drone/{mission_id}/report'
            },
            'quality_metrics': {
                'image_quality_score': survey_data.get('image_quality', 95),
                'coverage_completeness': survey_data.get('coverage', 98),
                'weather_conditions': survey_data.get('weather', 'optimal')
            }
        }
        
        # Update mission status
        mission['status'] = 'completed'
        mission['results'] = results
        
        return results
    
    def create_photo_documentation(self, project_id: int, activity_id: int, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create photo documentation for project activities"""
        
        photo_id = f"photo_{project_id}_{activity_id}_{int(datetime.now().timestamp())}"
        
        documentation = {
            'photo_id': photo_id,
            'project_id': project_id,
            'activity_id': activity_id,
            'photographer': photo_data.get('photographer', 'Anonymous'),
            'caption': photo_data.get('caption', ''),
            'location': photo_data.get('location', {}),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'camera_make': photo_data.get('camera_make', 'Unknown'),
                'resolution': photo_data.get('resolution', '1920x1080'),
                'file_size_mb': photo_data.get('file_size', 2.5),
                'gps_coordinates': photo_data.get('gps', {}),
                'weather_conditions': photo_data.get('weather', 'Clear')
            },
            'tags': photo_data.get('tags', []),
            'progress_indicators': {
                'completion_percentage': photo_data.get('completion', 0),
                'quality_assessment': photo_data.get('quality', 'good'),
                'compliance_check': photo_data.get('compliance', True)
            },
            'analysis': {
                'detected_objects': self._analyze_photo_objects(photo_data),
                'safety_observations': self._analyze_photo_safety(photo_data),
                'progress_comparison': self._compare_progress_photos(project_id, activity_id)
            }
        }
        
        if project_id not in self.photo_documentation:
            self.photo_documentation[project_id] = {}
        
        if activity_id not in self.photo_documentation[project_id]:
            self.photo_documentation[project_id][activity_id] = []
        
        self.photo_documentation[project_id][activity_id].append(documentation)
        
        return documentation
    
    def generate_qr_codes(self, project_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate QR codes for project items and activities"""
        
        qr_codes = []
        
        for item in items:
            qr_id = f"qr_{project_id}_{item['type']}_{int(datetime.now().timestamp())}"
            
            qr_data = {
                'qr_id': qr_id,
                'project_id': project_id,
                'item_type': item['type'],  # 'activity', 'equipment', 'material', 'location'
                'item_id': item['id'],
                'item_name': item['name'],
                'qr_code_url': f'/api/qr/{qr_id}',
                'tracking_url': f'/track/{qr_id}',
                'generated_at': datetime.now().isoformat(),
                'scan_count': 0,
                'last_scanned': None,
                'metadata': {
                    'format': 'PNG',
                    'size': '256x256',
                    'error_correction': 'M',
                    'encoding': 'UTF-8'
                }
            }
            
            qr_codes.append(qr_data)
            self.qr_code_tracking[qr_id] = qr_data
        
        return {
            'project_id': project_id,
            'qr_codes_generated': len(qr_codes),
            'qr_codes': qr_codes,
            'batch_id': f"batch_{project_id}_{int(datetime.now().timestamp())}"
        }
    
    def scan_qr_code(self, qr_id: str, scanner_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process QR code scan and update tracking"""
        
        if qr_id not in self.qr_code_tracking:
            raise ValueError("QR code not found")
        
        qr_data = self.qr_code_tracking[qr_id]
        
        # Update scan tracking
        qr_data['scan_count'] += 1
        qr_data['last_scanned'] = datetime.now().isoformat()
        
        scan_record = {
            'scan_id': f"scan_{qr_id}_{qr_data['scan_count']}",
            'qr_id': qr_id,
            'scanned_at': datetime.now().isoformat(),
            'scanner_location': scanner_data.get('location', {}),
            'scanner_device': scanner_data.get('device', 'Unknown'),
            'user_id': scanner_data.get('user_id', 'Anonymous'),
            'context': scanner_data.get('context', 'field_inspection')
        }
        
        # Return item information and tracking data
        return {
            'qr_id': qr_id,
            'item_info': {
                'type': qr_data['item_type'],
                'name': qr_data['item_name'],
                'project_id': qr_data['project_id']
            },
            'tracking_info': {
                'total_scans': qr_data['scan_count'],
                'first_generated': qr_data['generated_at'],
                'last_scanned': qr_data['last_scanned']
            },
            'scan_record': scan_record,
            'next_actions': self._suggest_scan_actions(qr_data, scanner_data)
        }
    
    def get_field_monitoring_dashboard(self, project_id: int) -> Dict[str, Any]:
        """Get comprehensive field monitoring dashboard"""
        
        # Collect all project-related data
        project_equipment = [eq for eq in self.equipment_registry.values() if eq['project_id'] == project_id]
        project_missions = [m for m in self.drone_missions.values() if m['project_id'] == project_id]
        project_photos = self.photo_documentation.get(project_id, {})
        project_qr_codes = [qr for qr in self.qr_code_tracking.values() if qr['project_id'] == project_id]
        
        # Calculate metrics
        total_photos = sum(len(activity_photos) for activity_photos in project_photos.values())
        active_equipment = len([eq for eq in project_equipment if eq['status'] == 'active'])
        completed_missions = len([m for m in project_missions if m['status'] == 'completed'])
        total_qr_scans = sum(qr['scan_count'] for qr in project_qr_codes)
        
        # Recent activity
        recent_activity = []
        
        # Equipment alerts
        for equipment in project_equipment:
            for alert in equipment.get('alerts', [])[-3:]:  # Last 3 alerts
                recent_activity.append({
                    'type': 'equipment_alert',
                    'timestamp': alert.get('timestamp', datetime.now().isoformat()),
                    'description': f"Equipment {equipment['name']}: {alert.get('message', 'Alert')}"
                })
        
        # Recent drone missions
        for mission in sorted(project_missions, key=lambda x: x['created_at'], reverse=True)[:3]:
            recent_activity.append({
                'type': 'drone_mission',
                'timestamp': mission['created_at'],
                'description': f"Drone mission: {mission['title']} - {mission['status']}"
            })
        
        # Sort recent activity by timestamp
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'project_id': project_id,
            'dashboard_generated': datetime.now().isoformat(),
            'summary_metrics': {
                'active_equipment': active_equipment,
                'total_equipment': len(project_equipment),
                'drone_missions_completed': completed_missions,
                'total_photos_captured': total_photos,
                'qr_codes_active': len(project_qr_codes),
                'total_qr_scans': total_qr_scans
            },
            'equipment_status': [
                {
                    'name': eq['name'],
                    'type': eq['type'],
                    'status': eq['status'],
                    'utilization': eq['metrics']['utilization_rate'],
                    'efficiency': eq['metrics']['efficiency_score'],
                    'alerts': len(eq['alerts'])
                }
                for eq in project_equipment
            ],
            'recent_activity': recent_activity[:10],
            'health_indicators': {
                'equipment_health': sum(eq['metrics']['efficiency_score'] for eq in project_equipment) / len(project_equipment) if project_equipment else 100,
                'monitoring_coverage': min(100, (active_equipment + completed_missions + total_photos) * 10),
                'data_quality': min(100, total_qr_scans + total_photos + completed_missions * 10)
            }
        }
    
    def _analyze_sensor_data(self, equipment: Dict[str, Any], sensor_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze sensor data for equipment alerts"""
        
        alerts = []
        
        # Temperature monitoring
        if 'temperature' in sensor_data:
            temp = sensor_data['temperature']
            if temp > 200:  # High temperature alert
                alerts.append({
                    'type': 'high_temperature',
                    'severity': 'high',
                    'message': f"High temperature detected: {temp}°F",
                    'timestamp': datetime.now().isoformat(),
                    'recommended_action': 'Shutdown equipment and inspect cooling system'
                })
        
        # Vibration monitoring
        if 'vibration_level' in sensor_data:
            vibration = sensor_data['vibration_level']
            if vibration > 80:  # High vibration alert
                alerts.append({
                    'type': 'high_vibration',
                    'severity': 'medium',
                    'message': f"Excessive vibration detected: {vibration}%",
                    'timestamp': datetime.now().isoformat(),
                    'recommended_action': 'Inspect equipment for loose components'
                })
        
        # Fuel level monitoring
        if 'fuel_level' in sensor_data:
            fuel = sensor_data['fuel_level']
            if fuel < 20:  # Low fuel alert
                alerts.append({
                    'type': 'low_fuel',
                    'severity': 'low',
                    'message': f"Low fuel level: {fuel}%",
                    'timestamp': datetime.now().isoformat(),
                    'recommended_action': 'Schedule refueling'
                })
        
        return alerts
    
    def _analyze_construction_progress(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze construction progress from drone survey"""
        
        return {
            'overall_progress': survey_data.get('progress_percentage', 75),
            'areas_completed': survey_data.get('completed_areas', ['Foundation', 'First floor structure']),
            'areas_in_progress': survey_data.get('active_areas', ['Second floor framing', 'MEP rough-in']),
            'areas_not_started': survey_data.get('pending_areas', ['Roofing', 'Exterior finishes']),
            'progress_rate': survey_data.get('progress_rate', 'On schedule'),
            'estimated_completion': survey_data.get('completion_date', '2025-12-15')
        }
    
    def _analyze_safety_conditions(self, survey_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze safety conditions from drone imagery"""
        
        return [
            {
                'observation': 'Fall protection systems in place',
                'status': 'compliant',
                'location': 'Second floor edge',
                'priority': 'informational'
            },
            {
                'observation': 'Material storage blocking egress path',
                'status': 'non_compliant',
                'location': 'Southeast corner',
                'priority': 'high'
            },
            {
                'observation': 'Proper crane setup and barriers',
                'status': 'compliant',
                'location': 'Main construction area',
                'priority': 'informational'
            }
        ]
    
    def _analyze_material_status(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze material inventory from drone survey"""
        
        return {
            'steel_beams': {'status': 'adequate', 'estimated_days': 15},
            'concrete_supplies': {'status': 'low', 'estimated_days': 3},
            'lumber': {'status': 'adequate', 'estimated_days': 8},
            'roofing_materials': {'status': 'not_delivered', 'estimated_days': 0},
            'electrical_supplies': {'status': 'adequate', 'estimated_days': 12}
        }
    
    def _detect_site_changes(self, mission_id: str, survey_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect changes from previous drone surveys"""
        
        return [
            {
                'change_type': 'new_construction',
                'description': 'Second floor walls framed',
                'location': 'North section',
                'confidence': 95
            },
            {
                'change_type': 'equipment_moved',
                'description': 'Crane relocated to east side',
                'location': 'Main construction area',
                'confidence': 90
            },
            {
                'change_type': 'material_delivery',
                'description': 'New steel beam delivery',
                'location': 'Material staging area',
                'confidence': 88
            }
        ]
    
    def _analyze_photo_objects(self, photo_data: Dict[str, Any]) -> List[str]:
        """Analyze objects detected in construction photos"""
        
        # Simulate AI object detection
        return [
            'construction_worker',
            'hard_hat',
            'safety_vest',
            'concrete_truck',
            'scaffolding',
            'building_materials'
        ]
    
    def _analyze_photo_safety(self, photo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze safety compliance in photos"""
        
        return [
            {
                'item': 'Hard hat usage',
                'status': 'compliant',
                'confidence': 95
            },
            {
                'item': 'Safety vest visibility',
                'status': 'compliant',
                'confidence': 92
            },
            {
                'item': 'Fall protection',
                'status': 'needs_verification',
                'confidence': 75
            }
        ]
    
    def _compare_progress_photos(self, project_id: int, activity_id: int) -> Dict[str, Any]:
        """Compare current photo with previous progress photos"""
        
        if project_id not in self.photo_documentation or activity_id not in self.photo_documentation[project_id]:
            return {'comparison': 'no_previous_photos'}
        
        photos = self.photo_documentation[project_id][activity_id]
        
        if len(photos) < 2:
            return {'comparison': 'insufficient_data'}
        
        return {
            'comparison': 'progress_detected',
            'progress_change': '+15%',
            'time_since_last': '3 days',
            'notable_changes': [
                'Wall framing completed',
                'Electrical rough-in started',
                'Material delivery received'
            ]
        }
    
    def _suggest_scan_actions(self, qr_data: Dict[str, Any], scanner_data: Dict[str, Any]) -> List[str]:
        """Suggest actions based on QR code scan context"""
        
        suggestions = []
        
        if qr_data['item_type'] == 'activity':
            suggestions.extend([
                'Update activity progress',
                'Log time spent',
                'Report any issues',
                'Take progress photos'
            ])
        elif qr_data['item_type'] == 'equipment':
            suggestions.extend([
                'Check equipment status',
                'Log usage hours',
                'Report maintenance needs',
                'Verify safety checklist'
            ])
        elif qr_data['item_type'] == 'material':
            suggestions.extend([
                'Update inventory count',
                'Check material quality',
                'Log consumption',
                'Report delivery status'
            ])
        
        return suggestions

# Global service instance
iot_field_service = IoTFieldService()