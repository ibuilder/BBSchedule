"""
Project-related business logic and operations.
"""
from datetime import datetime, date
from extensions import db
from models import Project, Activity, ProjectStatus
from logger import log_error, log_activity
import traceback

class ProjectService:
    """Service class for project operations."""
    
    @staticmethod
    def get_all_projects(user_id=None):
        """Get all projects with optional user filtering."""
        try:
            projects = Project.query.all()
            log_activity(user_id, "Retrieved all projects", f"Count: {len(projects)}")
            return projects
        except Exception as e:
            log_error(e, "Failed to retrieve projects")
            return []
    
    @staticmethod
    def get_project_by_id(project_id, user_id=None):
        """Get project by ID with error handling."""
        try:
            project = Project.query.get_or_404(project_id)
            log_activity(user_id, f"Retrieved project {project_id}", project.name)
            return project
        except Exception as e:
            log_error(e, f"Failed to retrieve project {project_id}")
            return None
    
    @staticmethod
    def create_project(form_data, user_id=None):
        """Create a new project from form data."""
        try:
            project = Project()
            project.name = form_data.get('name')
            project.description = form_data.get('description')
            project.start_date = form_data.get('start_date')
            project.end_date = form_data.get('end_date')
            project.status = ProjectStatus(form_data.get('status', 'PLANNING'))
            project.total_sf = form_data.get('total_sf')
            project.floor_count = form_data.get('floor_count')
            project.building_type = form_data.get('building_type')
            project.location = form_data.get('location')
            project.budget = form_data.get('budget')
            
            # Linear scheduling fields
            project.linear_scheduling_enabled = form_data.get('linear_scheduling') == 'true'
            project.project_start_station = form_data.get('project_start_station')
            project.project_end_station = form_data.get('project_end_station')
            project.station_units = form_data.get('station_units', 'm')
            
            project.created_by = user_id
            project.created_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            
            db.session.add(project)
            db.session.commit()
            
            log_activity(user_id, "Created project", f"ID: {project.id}, Name: {project.name}")
            return project
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to create project: {form_data.get('name', 'Unknown')}")
            raise
    
    @staticmethod
    def update_project(project_id, form_data, user_id=None):
        """Update an existing project."""
        try:
            project = Project.query.get_or_404(project_id)
            
            project.name = form_data.get('name')
            project.description = form_data.get('description')
            project.start_date = form_data.get('start_date')
            project.end_date = form_data.get('end_date')
            project.status = ProjectStatus(form_data.get('status'))
            project.total_sf = form_data.get('total_sf')
            project.floor_count = form_data.get('floor_count')
            project.building_type = form_data.get('building_type')
            project.location = form_data.get('location')
            project.budget = form_data.get('budget')
            
            # Linear scheduling fields
            project.linear_scheduling_enabled = form_data.get('linear_scheduling') == 'true'
            project.project_start_station = form_data.get('project_start_station')
            project.project_end_station = form_data.get('project_end_station')
            project.station_units = form_data.get('station_units', 'm')
            
            project.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            log_activity(user_id, f"Updated project {project_id}", project.name)
            return project
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to update project {project_id}")
            raise
    
    @staticmethod
    def delete_project(project_id, user_id=None):
        """Delete a project and all associated data."""
        try:
            project = Project.query.get_or_404(project_id)
            project_name = project.name
            
            db.session.delete(project)
            db.session.commit()
            
            log_activity(user_id, f"Deleted project {project_id}", project_name)
            return True
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to delete project {project_id}")
            raise
    
    @staticmethod
    def get_project_metrics(project_id):
        """Get comprehensive project metrics."""
        try:
            project = Project.query.get_or_404(project_id)
            
            metrics = {
                'completion_percentage': project.get_completion_percentage(),
                'budget_utilization': project.get_budget_utilization(),
                'total_duration': project.get_total_duration(),
                'overdue_activities': len(project.get_overdue_activities()),
                'total_activities': len(project.activities),
                'linear_length': project.get_project_length() if project.linear_scheduling_enabled else None
            }
            
            return metrics
            
        except Exception as e:
            log_error(e, f"Failed to get metrics for project {project_id}")
            return {}
    
    @staticmethod
    def get_linear_activities_by_location(project_id, start_station=None, end_station=None):
        """Get activities within a location range for linear projects."""
        try:
            project = Project.query.get_or_404(project_id)
            
            if not project.linear_scheduling_enabled:
                return []
            
            return project.get_activities_by_location(start_station, end_station)
            
        except Exception as e:
            log_error(e, f"Failed to get linear activities for project {project_id}")
            return []