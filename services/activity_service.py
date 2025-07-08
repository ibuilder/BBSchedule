"""
Activity-related business logic and operations.
"""
from datetime import datetime
from extensions import db
from models import Activity, ActivityType
from logger import log_error, log_activity

class ActivityService:
    """Service class for activity operations."""
    
    @staticmethod
    def get_project_activities(project_id, user_id=None):
        """Get all activities for a project (alias for backward compatibility)."""
        return ActivityService.get_activities_by_project(project_id, user_id)
    
    @staticmethod
    def get_activities_by_project(project_id, user_id=None):
        """Get all activities for a project."""
        try:
            activities = Activity.query.filter_by(project_id=project_id).all()
            log_activity(user_id, f"Retrieved activities for project {project_id}", f"Count: {len(activities)}")
            return activities
        except Exception as e:
            log_error(e, f"Failed to retrieve activities for project {project_id}")
            return []
    
    @staticmethod
    def get_activity_by_id(activity_id, user_id=None):
        """Get activity by ID with error handling."""
        try:
            activity = Activity.query.get_or_404(activity_id)
            log_activity(user_id, f"Retrieved activity {activity_id}", activity.name)
            return activity
        except Exception as e:
            log_error(e, f"Failed to retrieve activity {activity_id}")
            return None
    
    @staticmethod
    def get_overdue_activities(project_id, user_id=None):
        """Get overdue activities for a project."""
        try:
            from datetime import date
            activities = Activity.query.filter_by(project_id=project_id).all()
            overdue = [a for a in activities if a.end_date and a.end_date < date.today() and a.progress < 100]
            log_activity(user_id, f"Retrieved overdue activities for project {project_id}", f"Count: {len(overdue)}")
            return overdue
        except Exception as e:
            log_error(e, f"Failed to retrieve overdue activities for project {project_id}")
            return []
    
    @staticmethod
    def create_activity(project_id, form_data, user_id=None):
        """Create a new activity."""
        try:
            activity = Activity()
            activity.project_id = project_id
            activity.name = form_data.get('name')
            activity.description = form_data.get('description')
            activity.activity_type = ActivityType(form_data.get('activity_type', 'OTHER'))
            activity.duration = form_data.get('duration')
            activity.start_date = form_data.get('start_date')
            activity.end_date = form_data.get('end_date')
            activity.progress = form_data.get('progress', 0)
            activity.quantity = form_data.get('quantity')
            activity.unit = form_data.get('unit')
            activity.production_rate = form_data.get('production_rate')
            activity.resource_crew_size = form_data.get('resource_crew_size')
            activity.cost_estimate = form_data.get('cost_estimate')
            activity.actual_cost = form_data.get('actual_cost')
            activity.location_start = form_data.get('location_start')
            activity.location_end = form_data.get('location_end')
            activity.notes = form_data.get('notes')
            activity.created_at = datetime.utcnow()
            activity.updated_at = datetime.utcnow()
            
            db.session.add(activity)
            db.session.commit()
            
            log_activity(user_id, f"Created activity in project {project_id}", f"ID: {activity.id}, Name: {activity.name}")
            return activity
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to create activity in project {project_id}")
            raise
    
    @staticmethod
    def update_activity(activity_id, form_data, user_id=None):
        """Update an existing activity."""
        try:
            activity = Activity.query.get_or_404(activity_id)
            
            activity.name = form_data.get('name')
            activity.description = form_data.get('description')
            activity.activity_type = ActivityType(form_data.get('activity_type'))
            activity.duration = form_data.get('duration')
            activity.start_date = form_data.get('start_date')
            activity.end_date = form_data.get('end_date')
            activity.progress = form_data.get('progress', 0)
            activity.quantity = form_data.get('quantity')
            activity.unit = form_data.get('unit')
            activity.production_rate = form_data.get('production_rate')
            activity.resource_crew_size = form_data.get('resource_crew_size')
            activity.cost_estimate = form_data.get('cost_estimate')
            activity.actual_cost = form_data.get('actual_cost')
            activity.location_start = form_data.get('location_start')
            activity.location_end = form_data.get('location_end')
            activity.notes = form_data.get('notes')
            activity.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            log_activity(user_id, f"Updated activity {activity_id}", activity.name)
            return activity
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to update activity {activity_id}")
            raise
    
    @staticmethod
    def delete_activity(activity_id, user_id=None):
        """Delete an activity."""
        try:
            activity = Activity.query.get_or_404(activity_id)
            activity_name = activity.name
            
            db.session.delete(activity)
            db.session.commit()
            
            log_activity(user_id, f"Deleted activity {activity_id}", activity_name)
            return True
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to delete activity {activity_id}")
            raise
    
    @staticmethod
    def update_activity_progress(activity_id, progress, user_id=None):
        """Update activity progress percentage."""
        try:
            activity = Activity.query.get_or_404(activity_id)
            old_progress = activity.progress
            activity.progress = max(0, min(100, progress))  # Ensure 0-100 range
            activity.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            log_activity(user_id, f"Updated progress for activity {activity_id}", 
                        f"From {old_progress}% to {progress}%")
            return activity
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Failed to update progress for activity {activity_id}")
            raise
    
    @staticmethod
    def get_overdue_activities(project_id=None):
        """Get all overdue activities, optionally filtered by project."""
        try:
            query = Activity.query
            if project_id:
                query = query.filter_by(project_id=project_id)
            
            overdue = []
            for activity in query.all():
                if activity.is_overdue():
                    overdue.append(activity)
            
            return overdue
            
        except Exception as e:
            log_error(e, f"Failed to get overdue activities for project {project_id}")
            return []
    
    @staticmethod
    def get_activities_by_location_range(project_id, start_station, end_station):
        """Get activities within a specific location range."""
        try:
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            filtered_activities = []
            for activity in activities:
                if (activity.location_start is not None and activity.location_end is not None):
                    # Check if activity overlaps with the specified range
                    activity_start = min(activity.location_start, activity.location_end)
                    activity_end = max(activity.location_start, activity.location_end)
                    
                    # Check for overlap
                    if not (activity_end < start_station or activity_start > end_station):
                        filtered_activities.append(activity)
            
            return filtered_activities
            
        except Exception as e:
            log_error(e, f"Failed to get activities by location for project {project_id}")
            return []