"""
Import utilities for external schedule files (.xer, .mpp, .xml)
Handles parsing and importing existing project schedules into the system
"""

import os
import xml.etree.ElementTree as ET
import xmltodict
import json
import openpyxl
import chardet
import re
from datetime import datetime, date, timedelta
from dateutil import parser
from app import db
from models import (
    Project, Activity, Dependency, ActivityType, ProjectStatus,
    ScheduleMetrics, HistoricalProject
)


class ScheduleImporter:
    """Base class for schedule importers"""
    
    def __init__(self):
        self.project = None
        self.activities = []
        self.dependencies = []
        self.errors = []
        self.warnings = []
        self.activity_mapping = {}  # Map external IDs to internal IDs
    
    def detect_encoding(self, file_path):
        """Detect file encoding"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'
    
    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return None
        
        try:
            # Handle common date formats
            if isinstance(date_str, str):
                # Remove timezone info for simplicity
                date_str = date_str.split('T')[0] if 'T' in date_str else date_str
                # Handle different date formats
                date_str = re.sub(r'[^\d\-\/\.]', '', date_str)
                return parser.parse(date_str).date()
            elif isinstance(date_str, datetime):
                return date_str.date()
            elif isinstance(date_str, date):
                return date_str
        except Exception as e:
            self.warnings.append(f"Could not parse date: {date_str} - {str(e)}")
            return None
    
    def map_activity_type(self, activity_type_str):
        """Map external activity types to internal enum"""
        if not activity_type_str:
            return ActivityType.CONSTRUCTION
        
        activity_type_str = activity_type_str.lower().strip()
        
        # Mapping dictionary for common activity types
        type_mapping = {
            'foundation': ActivityType.FOUNDATION,
            'concrete': ActivityType.FOUNDATION,
            'frame': ActivityType.FRAMING,
            'framing': ActivityType.FRAMING,
            'roof': ActivityType.ROOFING,
            'roofing': ActivityType.ROOFING,
            'electric': ActivityType.ELECTRICAL,
            'electrical': ActivityType.ELECTRICAL,
            'plumb': ActivityType.PLUMBING,
            'plumbing': ActivityType.PLUMBING,
            'hvac': ActivityType.HVAC,
            'mechanical': ActivityType.HVAC,
            'drywall': ActivityType.DRYWALL,
            'gypsum': ActivityType.DRYWALL,
            'floor': ActivityType.FLOORING,
            'flooring': ActivityType.FLOORING,
            'paint': ActivityType.PAINTING,
            'painting': ActivityType.PAINTING,
            'finish': ActivityType.FINISHING,
            'finishing': ActivityType.FINISHING,
            'site': ActivityType.SITEWORK,
            'sitework': ActivityType.SITEWORK,
            'excavation': ActivityType.SITEWORK,
            'earthwork': ActivityType.SITEWORK
        }
        
        # Check for partial matches
        for key, value in type_mapping.items():
            if key in activity_type_str:
                return value
        
        return ActivityType.CONSTRUCTION
    
    def validate_activity_data(self, activity_data):
        """Validate activity data before saving"""
        errors = []
        
        if not activity_data.get('name'):
            errors.append("Activity name is required")
        
        if not activity_data.get('duration') or activity_data['duration'] <= 0:
            errors.append("Activity duration must be positive")
        
        return errors
    
    def save_to_database(self):
        """Save imported data to database"""
        try:
            # Save project
            if self.project:
                db.session.add(self.project)
                db.session.flush()  # Get project ID
                
                # Save activities
                for activity_data in self.activities:
                    activity = Activity(
                        project_id=self.project.id,
                        name=activity_data.get('name', 'Unnamed Activity'),
                        description=activity_data.get('description', ''),
                        activity_type=activity_data.get('activity_type', ActivityType.CONSTRUCTION),
                        duration=activity_data.get('duration', 1),
                        start_date=activity_data.get('start_date'),
                        end_date=activity_data.get('end_date'),
                        progress=activity_data.get('progress', 0),
                        quantity=activity_data.get('quantity'),
                        unit=activity_data.get('unit'),
                        production_rate=activity_data.get('production_rate'),
                        resource_crew_size=activity_data.get('resource_crew_size'),
                        cost_estimate=activity_data.get('cost_estimate'),
                        actual_cost=activity_data.get('actual_cost'),
                        location_start=activity_data.get('location_start'),
                        location_end=activity_data.get('location_end'),
                        notes=activity_data.get('notes', '')
                    )
                    
                    db.session.add(activity)
                    db.session.flush()
                    
                    # Map external ID to internal ID
                    external_id = activity_data.get('external_id')
                    if external_id:
                        self.activity_mapping[external_id] = activity.id
                
                # Save dependencies
                for dep_data in self.dependencies:
                    predecessor_id = self.activity_mapping.get(dep_data.get('predecessor_external_id'))
                    successor_id = self.activity_mapping.get(dep_data.get('successor_external_id'))
                    
                    if predecessor_id and successor_id:
                        dependency = Dependency(
                            predecessor_id=predecessor_id,
                            successor_id=successor_id,
                            dependency_type=dep_data.get('dependency_type', 'FS'),
                            lag_days=dep_data.get('lag_days', 0)
                        )
                        db.session.add(dependency)
                
                db.session.commit()
                return self.project
                
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"Database save error: {str(e)}")
            raise e


class XERImporter(ScheduleImporter):
    """Primavera XER file importer"""
    
    def import_file(self, file_path):
        """Import XER file"""
        try:
            encoding = self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self._parse_xer_content(content)
            return self.save_to_database()
            
        except Exception as e:
            self.errors.append(f"XER import error: {str(e)}")
            raise e
    
    def _parse_xer_content(self, content):
        """Parse XER file content"""
        lines = content.split('\n')
        current_table = None
        headers = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            
            # Table definition
            if line.startswith('%T'):
                current_table = line.split('\t')[1] if '\t' in line else None
                headers = []
            
            # Column headers
            elif line.startswith('%F'):
                headers = line.split('\t')[1:] if '\t' in line else []
            
            # Data records
            elif line.startswith('%R') and current_table and headers:
                data_parts = line.split('\t')[1:] if '\t' in line else []
                if len(data_parts) >= len(headers):
                    record = dict(zip(headers, data_parts))
                    self._process_xer_record(current_table, record)
    
    def _process_xer_record(self, table_name, record):
        """Process individual XER record"""
        if table_name == 'PROJECT':
            self._process_project_record(record)
        elif table_name == 'TASK':
            self._process_task_record(record)
        elif table_name == 'TASKPRED':
            self._process_dependency_record(record)
    
    def _process_project_record(self, record):
        """Process project record from XER"""
        self.project = Project(
            name=record.get('proj_short_name', 'Imported Project'),
            description=record.get('proj_name', ''),
            start_date=self.parse_date(record.get('plan_start_date')),
            end_date=self.parse_date(record.get('plan_end_date')),
            status=ProjectStatus.PLANNING,
            created_by='XER Import'
        )
    
    def _process_task_record(self, record):
        """Process task/activity record from XER"""
        activity_data = {
            'external_id': record.get('task_id'),
            'name': record.get('task_name', 'Unnamed Task'),
            'description': record.get('task_notes', ''),
            'activity_type': self.map_activity_type(record.get('task_type')),
            'duration': int(float(record.get('target_drtn_hr_cnt', 8)) / 8) or 1,  # Convert hours to days
            'start_date': self.parse_date(record.get('act_start_date') or record.get('target_start_date')),
            'end_date': self.parse_date(record.get('act_end_date') or record.get('target_end_date')),
            'progress': float(record.get('phys_complete_pct', 0)),
            'cost_estimate': float(record.get('target_cost', 0)) if record.get('target_cost') else None,
            'actual_cost': float(record.get('act_reg_cost', 0)) if record.get('act_reg_cost') else None
        }
        
        # Validate and add activity
        validation_errors = self.validate_activity_data(activity_data)
        if validation_errors:
            self.errors.extend(validation_errors)
        else:
            self.activities.append(activity_data)
    
    def _process_dependency_record(self, record):
        """Process dependency record from XER"""
        dependency_data = {
            'predecessor_external_id': record.get('pred_task_id'),
            'successor_external_id': record.get('task_id'),
            'dependency_type': record.get('pred_type', 'FS'),
            'lag_days': int(float(record.get('lag_hr_cnt', 0)) / 8) if record.get('lag_hr_cnt') else 0
        }
        self.dependencies.append(dependency_data)


class MPPImporter(ScheduleImporter):
    """Microsoft Project MPP/XML file importer"""
    
    def import_file(self, file_path):
        """Import MPP/XML file"""
        try:
            if file_path.lower().endswith('.xml'):
                return self._parse_xml_file(file_path)
            else:
                # For .mpp files, we'd need python-msp library or convert to XML first
                self.errors.append("Direct MPP import not supported. Please export to XML format first.")
                raise ValueError("Direct MPP import not supported")
                
        except Exception as e:
            self.errors.append(f"MPP import error: {str(e)}")
            raise e
    
    def _parse_xml_file(self, file_path):
        """Parse Microsoft Project XML file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Define namespace
            namespace = {'ms': 'http://schemas.microsoft.com/project'}
            
            # Parse project info
            self._parse_project_info(root, namespace)
            
            # Parse tasks
            self._parse_tasks(root, namespace)
            
            # Parse assignments (if needed)
            self._parse_assignments(root, namespace)
            
            return self.save_to_database()
            
        except ET.ParseError as e:
            self.errors.append(f"XML parsing error: {str(e)}")
            raise e
    
    def _parse_project_info(self, root, namespace):
        """Parse project information from XML"""
        project_name = self._get_xml_text(root, './/ms:Name', namespace) or 'Imported Project'
        project_start = self._get_xml_text(root, './/ms:StartDate', namespace)
        project_finish = self._get_xml_text(root, './/ms:FinishDate', namespace)
        
        self.project = Project(
            name=project_name,
            description='Imported from Microsoft Project',
            start_date=self.parse_date(project_start),
            end_date=self.parse_date(project_finish),
            status=ProjectStatus.PLANNING,
            created_by='XML Import'
        )
    
    def _parse_tasks(self, root, namespace):
        """Parse tasks from XML"""
        tasks = root.findall('.//ms:Task', namespace)
        
        for task in tasks:
            task_id = self._get_xml_text(task, './ms:ID', namespace)
            task_name = self._get_xml_text(task, './ms:Name', namespace)
            
            # Skip summary tasks (they have subtasks)
            if not task_name or self._get_xml_text(task, './ms:Summary', namespace) == '1':
                continue
            
            activity_data = {
                'external_id': task_id,
                'name': task_name,
                'duration': self._parse_duration(self._get_xml_text(task, './ms:Duration', namespace)),
                'start_date': self.parse_date(self._get_xml_text(task, './ms:Start', namespace)),
                'end_date': self.parse_date(self._get_xml_text(task, './ms:Finish', namespace)),
                'progress': float(self._get_xml_text(task, './ms:PercentComplete', namespace) or 0),
                'cost_estimate': float(self._get_xml_text(task, './ms:Cost', namespace) or 0),
                'notes': self._get_xml_text(task, './ms:Notes', namespace) or ''
            }
            
            # Validate and add activity
            validation_errors = self.validate_activity_data(activity_data)
            if validation_errors:
                self.errors.extend([f"Task {task_name}: {error}" for error in validation_errors])
            else:
                self.activities.append(activity_data)
                
            # Parse predecessors
            predecessors = task.findall('.//ms:PredecessorLink', namespace)
            for pred in predecessors:
                pred_id = self._get_xml_text(pred, './ms:PredecessorUID', namespace)
                dep_type = self._get_xml_text(pred, './ms:Type', namespace) or '1'  # 1 = FS
                lag = self._get_xml_text(pred, './ms:Lag', namespace) or '0'
                
                # Convert dependency type
                type_mapping = {'0': 'FF', '1': 'FS', '2': 'SS', '3': 'SF'}
                dependency_type = type_mapping.get(dep_type, 'FS')
                
                dependency_data = {
                    'predecessor_external_id': pred_id,
                    'successor_external_id': task_id,
                    'dependency_type': dependency_type,
                    'lag_days': self._parse_duration(lag)
                }
                self.dependencies.append(dependency_data)
    
    def _parse_assignments(self, root, namespace):
        """Parse resource assignments from XML"""
        # This would parse resource assignments if needed
        # For now, we'll skip this as it's not essential for basic schedule import
        pass
    
    def _get_xml_text(self, element, path, namespace):
        """Get text from XML element with namespace support"""
        try:
            found = element.find(path, namespace)
            return found.text if found is not None else None
        except Exception:
            return None
    
    def _parse_duration(self, duration_text):
        """Parse Microsoft Project duration format"""
        if not duration_text:
            return 1
        
        try:
            # Remove 'PT' prefix and 'H' suffix for hours
            duration_text = duration_text.replace('PT', '').replace('H', '')
            hours = float(duration_text)
            return max(1, int(hours / 8))  # Convert to days, minimum 1 day
        except Exception:
            return 1


class FiveDScheduleManager:
    """5D Schedule Management (Time + 3D + Cost + Resources)"""
    
    def __init__(self, project):
        self.project = project
        self.activities = project.activities
        self.dependencies = []
        for activity in self.activities:
            self.dependencies.extend(activity.predecessor_dependencies)
    
    def calculate_5d_metrics(self):
        """Calculate comprehensive 5D scheduling metrics"""
        return {
            'time_performance': self._calculate_time_performance(),
            'cost_performance': self._calculate_cost_performance(),
            'resource_utilization': self._calculate_resource_utilization(),
            'spatial_conflicts': self._detect_spatial_conflicts(),
            'productivity_analysis': self._analyze_productivity(),
            'risk_assessment': self._assess_risks()
        }
    
    def _calculate_time_performance(self):
        """Calculate time-based performance metrics"""
        total_duration = sum([a.duration for a in self.activities])
        completed_duration = sum([a.duration for a in self.activities if a.progress >= 100])
        
        return {
            'total_planned_duration': total_duration,
            'completed_duration': completed_duration,
            'schedule_adherence': (completed_duration / total_duration * 100) if total_duration > 0 else 0,
            'critical_path_variance': self._calculate_critical_path_variance()
        }
    
    def _calculate_cost_performance(self):
        """Calculate cost performance metrics"""
        total_estimate = sum([a.cost_estimate or 0 for a in self.activities])
        total_actual = sum([a.actual_cost or 0 for a in self.activities])
        
        return {
            'total_estimated_cost': total_estimate,
            'total_actual_cost': total_actual,
            'cost_variance': total_estimate - total_actual,
            'cost_variance_percentage': ((total_actual - total_estimate) / total_estimate * 100) if total_estimate > 0 else 0
        }
    
    def _calculate_resource_utilization(self):
        """Calculate resource utilization metrics"""
        total_crew_days = sum([(a.resource_crew_size or 0) * a.duration for a in self.activities])
        utilized_crew_days = sum([(a.resource_crew_size or 0) * a.duration * (a.progress / 100) for a in self.activities])
        
        return {
            'total_crew_days_planned': total_crew_days,
            'utilized_crew_days': utilized_crew_days,
            'resource_efficiency': (utilized_crew_days / total_crew_days * 100) if total_crew_days > 0 else 0
        }
    
    def _detect_spatial_conflicts(self):
        """Detect spatial/location conflicts between activities"""
        conflicts = []
        
        for i, activity1 in enumerate(self.activities):
            for activity2 in self.activities[i+1:]:
                if (activity1.location_start is not None and activity1.location_end is not None and
                    activity2.location_start is not None and activity2.location_end is not None):
                    
                    if (self._locations_overlap(activity1, activity2) and 
                        self._time_overlap(activity1, activity2)):
                        conflicts.append({
                            'activity1': activity1.name,
                            'activity2': activity2.name,
                            'conflict_type': 'spatial_temporal_overlap'
                        })
        
        return conflicts
    
    def _locations_overlap(self, activity1, activity2):
        """Check if two activities overlap in location"""
        return not (activity1.location_end < activity2.location_start or 
                   activity2.location_end < activity1.location_start)
    
    def _time_overlap(self, activity1, activity2):
        """Check if two activities overlap in time"""
        if not all([activity1.start_date, activity1.end_date, activity2.start_date, activity2.end_date]):
            return False
        
        return not (activity1.end_date < activity2.start_date or 
                   activity2.end_date < activity1.start_date)
    
    def _analyze_productivity(self):
        """Analyze productivity metrics"""
        productivity_metrics = []
        
        for activity in self.activities:
            if activity.production_rate and activity.quantity and activity.duration:
                planned_production = activity.production_rate * activity.duration
                actual_production = activity.quantity * (activity.progress / 100)
                
                productivity_metrics.append({
                    'activity_name': activity.name,
                    'planned_production': planned_production,
                    'actual_production': actual_production,
                    'productivity_ratio': (actual_production / planned_production) if planned_production > 0 else 0
                })
        
        return productivity_metrics
    
    def _assess_risks(self):
        """Assess project risks based on 5D data"""
        risks = []
        
        # Schedule risks
        overdue_count = len([a for a in self.activities if a.is_overdue()])
        if overdue_count > 0:
            risks.append({
                'type': 'schedule',
                'severity': 'high' if overdue_count > len(self.activities) * 0.2 else 'medium',
                'description': f'{overdue_count} activities are overdue'
            })
        
        # Cost risks
        over_budget_activities = [a for a in self.activities 
                                if a.cost_estimate and a.actual_cost and a.actual_cost > a.cost_estimate * 1.1]
        if over_budget_activities:
            risks.append({
                'type': 'cost',
                'severity': 'high' if len(over_budget_activities) > len(self.activities) * 0.1 else 'medium',
                'description': f'{len(over_budget_activities)} activities are over budget'
            })
        
        return risks
    
    def _calculate_critical_path_variance(self):
        """Calculate variance in critical path"""
        # This would implement critical path method (CPM) calculations
        # For now, return a simplified metric
        return 0


def import_schedule_file(file_path, project_name=None):
    """Main function to import schedule files"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.xer':
            importer = XERImporter()
        elif file_extension in ['.xml', '.mpp']:
            importer = MPPImporter()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Set custom project name if provided
        if project_name:
            project = importer.import_file(file_path)
            if project:
                project.name = project_name
                db.session.commit()
            return project
        else:
            return importer.import_file(file_path)
            
    except Exception as e:
        raise Exception(f"Import failed: {str(e)}")
    
    def map_activity_type(self, activity_type_str):
        """Map external activity types to internal enum"""
        type_mapping = {
            'foundation': ActivityType.FOUNDATION,
            'concrete': ActivityType.FOUNDATION,
            'excavation': ActivityType.SITEWORK,
            'framing': ActivityType.FRAMING,
            'frame': ActivityType.FRAMING,
            'structural': ActivityType.FRAMING,
            'roofing': ActivityType.ROOFING,
            'roof': ActivityType.ROOFING,
            'electrical': ActivityType.ELECTRICAL,
            'electric': ActivityType.ELECTRICAL,
            'plumbing': ActivityType.PLUMBING,
            'hvac': ActivityType.HVAC,
            'mechanical': ActivityType.HVAC,
            'drywall': ActivityType.DRYWALL,
            'gypsum': ActivityType.DRYWALL,
            'flooring': ActivityType.FLOORING,
            'floor': ActivityType.FLOORING,
            'painting': ActivityType.PAINTING,
            'paint': ActivityType.PAINTING,
            'finishing': ActivityType.FINISHING,
            'finish': ActivityType.FINISHING,
            'sitework': ActivityType.SITEWORK,
            'site': ActivityType.SITEWORK,
        }
        
        if not activity_type_str:
            return ActivityType.OTHER
        
        activity_type_lower = activity_type_str.lower()
        for key, value in type_mapping.items():
            if key in activity_type_lower:
                return value
        
        return ActivityType.OTHER
    
    def save_to_database(self):
        """Save imported data to database"""
        try:
            # Save project
            db.session.add(self.project)
            db.session.flush()  # Get project ID
            
            # Update activity project_ids
            for activity in self.activities:
                activity.project_id = self.project.id
            
            # Save activities
            db.session.add_all(self.activities)
            db.session.flush()  # Get activity IDs
            
            # Create ID mapping for dependencies
            activity_id_map = {}
            for activity in self.activities:
                # Use original external ID if available, otherwise use name
                external_id = getattr(activity, 'external_id', None) or activity.name
                activity_id_map[external_id] = activity.id
            
            # Save dependencies with mapped IDs
            valid_dependencies = []
            for dep in self.dependencies:
                if (dep.predecessor_id in activity_id_map and 
                    dep.successor_id in activity_id_map):
                    dep.predecessor_id = activity_id_map[dep.predecessor_id]
                    dep.successor_id = activity_id_map[dep.successor_id]
                    valid_dependencies.append(dep)
                else:
                    self.warnings.append(f"Skipping invalid dependency: {dep.predecessor_id} -> {dep.successor_id}")
            
            db.session.add_all(valid_dependencies)
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"Database error: {str(e)}")
            return False


class XERImporter(ScheduleImporter):
    """Primavera XER file importer"""
    
    def import_file(self, file_path):
        """Import XER file"""
        try:
            encoding = self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self._parse_xer_content(content)
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Error reading XER file: {str(e)}")
            return False
    
    def _parse_xer_content(self, content):
        """Parse XER file content"""
        lines = content.split('\n')
        current_table = None
        headers = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('%T'):
                # Table definition
                current_table = line.split('\t')[1] if len(line.split('\t')) > 1 else None
                headers = []
            elif line.startswith('%F'):
                # Field definition
                headers = line.split('\t')[1:]
            elif line.startswith('%R'):
                # Record data
                if current_table and headers:
                    data = line.split('\t')[1:]
                    record = dict(zip(headers, data))
                    self._process_xer_record(current_table, record)
    
    def _process_xer_record(self, table_name, record):
        """Process individual XER record"""
        if table_name == 'PROJECT':
            self._process_project_record(record)
        elif table_name == 'TASK':
            self._process_task_record(record)
        elif table_name == 'TASKPRED':
            self._process_dependency_record(record)
    
    def _process_project_record(self, record):
        """Process project record from XER"""
        if not self.project:  # Only process first project
            self.project = Project(
                name=record.get('proj_short_name', 'Imported Project'),
                description=record.get('proj_name', ''),
                start_date=self.parse_date(record.get('plan_start_date')) or date.today(),
                end_date=self.parse_date(record.get('plan_end_date')),
                status=ProjectStatus.PLANNING,
                created_at=datetime.utcnow()
            )
    
    def _process_task_record(self, record):
        """Process task/activity record from XER"""
        try:
            # Parse duration (usually in hours, convert to days)
            duration_hours = float(record.get('target_drtn_hr_cnt', 0) or 0)
            duration_days = max(1, int(duration_hours / 8))  # Assume 8-hour workday
            
            # Parse dates
            start_date = self.parse_date(record.get('act_start_date') or record.get('early_start_date'))
            end_date = self.parse_date(record.get('act_end_date') or record.get('early_end_date'))
            
            # Calculate progress
            remaining_hours = float(record.get('remain_drtn_hr_cnt', 0) or 0)
            progress = 0
            if duration_hours > 0:
                progress = max(0, min(100, int((duration_hours - remaining_hours) / duration_hours * 100)))
            
            activity = Activity(
                name=record.get('task_name', 'Unnamed Activity'),
                description=record.get('task_descr', ''),
                activity_type=self.map_activity_type(record.get('task_type')),
                duration=duration_days,
                start_date=start_date,
                end_date=end_date,
                progress=progress,
                cost_estimate=float(record.get('target_cost', 0) or 0),
                actual_cost=float(record.get('act_this_per_cost', 0) or 0),
                created_at=datetime.utcnow()
            )
            
            # Store external ID for dependency mapping
            activity.external_id = record.get('task_id')
            self.activities.append(activity)
            
        except Exception as e:
            self.warnings.append(f"Error processing task {record.get('task_name', 'Unknown')}: {str(e)}")
    
    def _process_dependency_record(self, record):
        """Process dependency record from XER"""
        try:
            dependency = Dependency(
                predecessor_id=record.get('pred_task_id'),  # Will be mapped later
                successor_id=record.get('task_id'),  # Will be mapped later
                dependency_type=record.get('pred_type', 'FS'),
                lag_days=int(float(record.get('lag_hr_cnt', 0) or 0) / 8),  # Convert hours to days
                created_at=datetime.utcnow()
            )
            self.dependencies.append(dependency)
        except Exception as e:
            self.warnings.append(f"Error processing dependency: {str(e)}")


class MPPImporter(ScheduleImporter):
    """Microsoft Project MPP file importer (via XML export)"""
    
    def import_file(self, file_path):
        """Import MPP/XML file"""
        try:
            # For MPP files, we expect them to be exported as XML
            if file_path.lower().endswith('.mpp'):
                self.errors.append("Direct MPP import not supported. Please export to XML format from Microsoft Project.")
                return False
            
            self._parse_xml_file(file_path)
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Error reading XML file: {str(e)}")
            return False
    
    def _parse_xml_file(self, file_path):
        """Parse Microsoft Project XML file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle namespace
            namespace = {'ms': 'http://schemas.microsoft.com/project'}
            if root.tag.startswith('{'):
                ns_uri = root.tag.split('}')[0][1:]
                namespace = {'ms': ns_uri}
            
            self._parse_project_info(root, namespace)
            self._parse_tasks(root, namespace)
            self._parse_assignments(root, namespace)
            
        except ET.ParseError as e:
            self.errors.append(f"XML parsing error: {str(e)}")
        except Exception as e:
            self.errors.append(f"Error parsing XML: {str(e)}")
    
    def _parse_project_info(self, root, namespace):
        """Parse project information from XML"""
        project_elem = root.find('.//ms:Project', namespace) or root
        
        name = self._get_xml_text(project_elem, './/ms:Name', namespace) or 'Imported Project'
        title = self._get_xml_text(project_elem, './/ms:Title', namespace)
        start_date = self._get_xml_text(project_elem, './/ms:StartDate', namespace)
        finish_date = self._get_xml_text(project_elem, './/ms:FinishDate', namespace)
        
        self.project = Project(
            name=title or name,
            description=self._get_xml_text(project_elem, './/ms:Subject', namespace) or '',
            start_date=self.parse_date(start_date) or date.today(),
            end_date=self.parse_date(finish_date),
            status=ProjectStatus.PLANNING,
            created_at=datetime.utcnow()
        )
    
    def _parse_tasks(self, root, namespace):
        """Parse tasks from XML"""
        tasks = root.findall('.//ms:Task', namespace)
        
        for task in tasks:
            try:
                task_id = self._get_xml_text(task, './/ms:UID', namespace)
                name = self._get_xml_text(task, './/ms:Name', namespace)
                
                # Skip summary tasks and null tasks
                if (self._get_xml_text(task, './/ms:Summary', namespace) == 'true' or
                    self._get_xml_text(task, './/ms:Null', namespace) == 'true' or
                    not name):
                    continue
                
                duration_text = self._get_xml_text(task, './/ms:Duration', namespace)
                duration_days = self._parse_duration(duration_text)
                
                start_date = self.parse_date(self._get_xml_text(task, './/ms:Start', namespace))
                finish_date = self.parse_date(self._get_xml_text(task, './/ms:Finish', namespace))
                
                # Calculate progress
                percent_complete = self._get_xml_text(task, './/ms:PercentComplete', namespace)
                progress = int(float(percent_complete or 0))
                
                # Get cost information
                cost = self._get_xml_text(task, './/ms:Cost', namespace)
                actual_cost = self._get_xml_text(task, './/ms:ActualCost', namespace)
                
                activity = Activity(
                    name=name,
                    description=self._get_xml_text(task, './/ms:Notes', namespace) or '',
                    activity_type=self.map_activity_type(name),
                    duration=duration_days,
                    start_date=start_date,
                    end_date=finish_date,
                    progress=progress,
                    cost_estimate=float(cost or 0),
                    actual_cost=float(actual_cost or 0),
                    created_at=datetime.utcnow()
                )
                
                activity.external_id = task_id
                self.activities.append(activity)
                
                # Parse predecessors
                predecessors = task.findall('.//ms:PredecessorLink', namespace)
                for pred in predecessors:
                    pred_uid = self._get_xml_text(pred, './/ms:PredecessorUID', namespace)
                    if pred_uid:
                        dependency = Dependency(
                            predecessor_id=pred_uid,  # Will be mapped later
                            successor_id=task_id,  # Will be mapped later
                            dependency_type='FS',  # Default to Finish-to-Start
                            lag_days=0,
                            created_at=datetime.utcnow()
                        )
                        self.dependencies.append(dependency)
                        
            except Exception as e:
                self.warnings.append(f"Error processing task {name}: {str(e)}")
    
    def _parse_assignments(self, root, namespace):
        """Parse resource assignments from XML"""
        assignments = root.findall('.//ms:Assignment', namespace)
        
        # Group assignments by task to calculate crew sizes
        task_resources = {}
        for assignment in assignments:
            task_uid = self._get_xml_text(assignment, './/ms:TaskUID', namespace)
            if task_uid:
                if task_uid not in task_resources:
                    task_resources[task_uid] = 0
                task_resources[task_uid] += 1
        
        # Update activities with crew size information
        for activity in self.activities:
            if hasattr(activity, 'external_id') and activity.external_id in task_resources:
                activity.resource_crew_size = task_resources[activity.external_id]
    
    def _get_xml_text(self, element, path, namespace):
        """Get text from XML element with namespace support"""
        elem = element.find(path, namespace)
        return elem.text if elem is not None else None
    
    def _parse_duration(self, duration_text):
        """Parse Microsoft Project duration format"""
        if not duration_text:
            return 1
        
        try:
            # Remove PT prefix and parse ISO 8601 duration
            if duration_text.startswith('PT'):
                duration_text = duration_text[2:]
            
            # Extract hours
            if 'H' in duration_text:
                hours = float(duration_text.split('H')[0])
                return max(1, int(hours / 8))  # Convert to days
            
            # If no hours, assume days
            if 'D' in duration_text:
                return max(1, int(float(duration_text.split('D')[0])))
            
            return 1
        except:
            return 1


class FiveDScheduleManager:
    """5D Schedule Management (Time + 3D + Cost + Resources)"""
    
    def __init__(self, project):
        self.project = project
        self.activities = Activity.query.filter_by(project_id=project.id).all()
    
    def calculate_5d_metrics(self):
        """Calculate 5D scheduling metrics"""
        metrics = {
            'time_performance': self._calculate_time_performance(),
            'cost_performance': self._calculate_cost_performance(),
            'resource_utilization': self._calculate_resource_utilization(),
            'spatial_conflicts': self._detect_spatial_conflicts(),
            'productivity_analysis': self._analyze_productivity(),
            'risk_assessment': self._assess_risks()
        }
        return metrics
    
    def _calculate_time_performance(self):
        """Calculate time-based performance metrics"""
        total_duration = sum(a.duration for a in self.activities)
        completed_duration = sum(a.duration * (a.progress / 100) for a in self.activities)
        
        return {
            'schedule_performance_index': completed_duration / total_duration if total_duration > 0 else 0,
            'total_duration': total_duration,
            'completed_duration': completed_duration,
            'remaining_duration': total_duration - completed_duration
        }
    
    def _calculate_cost_performance(self):
        """Calculate cost performance metrics"""
        planned_value = sum(a.cost_estimate or 0 for a in self.activities)
        earned_value = sum((a.cost_estimate or 0) * (a.progress / 100) for a in self.activities)
        actual_cost = sum(a.actual_cost or 0 for a in self.activities)
        
        return {
            'planned_value': planned_value,
            'earned_value': earned_value,
            'actual_cost': actual_cost,
            'cost_performance_index': earned_value / actual_cost if actual_cost > 0 else 0,
            'cost_variance': earned_value - actual_cost,
            'schedule_variance': earned_value - planned_value
        }
    
    def _calculate_resource_utilization(self):
        """Calculate resource utilization metrics"""
        total_crew_hours = sum((a.resource_crew_size or 0) * a.duration for a in self.activities)
        utilized_crew_hours = sum((a.resource_crew_size or 0) * a.duration * (a.progress / 100) for a in self.activities)
        
        return {
            'total_crew_hours': total_crew_hours,
            'utilized_crew_hours': utilized_crew_hours,
            'utilization_percentage': (utilized_crew_hours / total_crew_hours * 100) if total_crew_hours > 0 else 0,
            'peak_resource_demand': max((a.resource_crew_size or 0) for a in self.activities) if self.activities else 0
        }
    
    def _detect_spatial_conflicts(self):
        """Detect spatial/location conflicts between activities"""
        conflicts = []
        
        for i, activity1 in enumerate(self.activities):
            for activity2 in self.activities[i+1:]:
                if (activity1.location_start is not None and activity1.location_end is not None and
                    activity2.location_start is not None and activity2.location_end is not None):
                    
                    # Check for location overlap
                    if self._locations_overlap(activity1, activity2):
                        # Check for time overlap
                        if self._time_overlap(activity1, activity2):
                            conflicts.append({
                                'activity1': activity1.name,
                                'activity2': activity2.name,
                                'type': 'spatial_temporal_conflict',
                                'severity': 'high'
                            })
        
        return conflicts
    
    def _locations_overlap(self, activity1, activity2):
        """Check if two activities overlap in location"""
        a1_start = min(activity1.location_start, activity1.location_end)
        a1_end = max(activity1.location_start, activity1.location_end)
        a2_start = min(activity2.location_start, activity2.location_end)
        a2_end = max(activity2.location_start, activity2.location_end)
        
        return a1_start < a2_end and a2_start < a1_end
    
    def _time_overlap(self, activity1, activity2):
        """Check if two activities overlap in time"""
        if not all([activity1.start_date, activity1.end_date, activity2.start_date, activity2.end_date]):
            return False
        
        return activity1.start_date < activity2.end_date and activity2.start_date < activity1.end_date
    
    def _analyze_productivity(self):
        """Analyze productivity metrics"""
        production_activities = [a for a in self.activities if a.production_rate and a.quantity]
        
        if not production_activities:
            return {'average_productivity': 0, 'productivity_variance': 0}
        
        productivities = []
        for activity in production_activities:
            if activity.duration > 0 and activity.quantity > 0:
                actual_rate = activity.quantity / activity.duration
                expected_rate = activity.production_rate
                productivity = (actual_rate / expected_rate) if expected_rate > 0 else 0
                productivities.append(productivity)
        
        if productivities:
            avg_productivity = sum(productivities) / len(productivities)
            variance = sum((p - avg_productivity) ** 2 for p in productivities) / len(productivities)
        else:
            avg_productivity = variance = 0
        
        return {
            'average_productivity': avg_productivity,
            'productivity_variance': variance,
            'high_performing_activities': len([p for p in productivities if p > 1.1]),
            'underperforming_activities': len([p for p in productivities if p < 0.9])
        }
    
    def _assess_risks(self):
        """Assess project risks based on 5D data"""
        risks = []
        
        # Schedule risks
        delayed_activities = [a for a in self.activities if a.progress < 50 and a.start_date and a.start_date < date.today()]
        if delayed_activities:
            risks.append({
                'type': 'schedule_delay',
                'description': f'{len(delayed_activities)} activities behind schedule',
                'severity': 'high' if len(delayed_activities) > len(self.activities) * 0.2 else 'medium'
            })
        
        # Cost risks
        over_budget_activities = [a for a in self.activities if a.actual_cost and a.cost_estimate and a.actual_cost > a.cost_estimate * 1.1]
        if over_budget_activities:
            risks.append({
                'type': 'cost_overrun',
                'description': f'{len(over_budget_activities)} activities over budget',
                'severity': 'high' if len(over_budget_activities) > len(self.activities) * 0.15 else 'medium'
            })
        
        # Resource risks
        high_resource_activities = [a for a in self.activities if (a.resource_crew_size or 0) > 10]
        if high_resource_activities:
            risks.append({
                'type': 'resource_constraint',
                'description': f'{len(high_resource_activities)} activities require large crews',
                'severity': 'medium'
            })
        
        return risks


def import_schedule_file(file_path, project_name=None):
    """Main function to import schedule files"""
    file_ext = os.path.splitext(file_path.lower())[1]
    
    if file_ext == '.xer':
        importer = XERImporter()
    elif file_ext in ['.xml', '.mpp']:
        importer = MPPImporter()
    else:
        return None, ["Unsupported file format. Supported formats: .xer, .xml, .mpp"]
    
    success = importer.import_file(file_path)
    
    if success and importer.project:
        if project_name:
            importer.project.name = project_name
        
        if importer.save_to_database():
            return importer.project, importer.warnings
        else:
            return None, importer.errors
    else:
        return None, importer.errors