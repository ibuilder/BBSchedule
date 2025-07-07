from app import db
from datetime import datetime, date
from sqlalchemy import func
from enum import Enum

class ProjectStatus(Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ActivityType(Enum):
    FOUNDATION = "foundation"
    FRAMING = "framing"
    ROOFING = "roofing"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    DRYWALL = "drywall"
    FLOORING = "flooring"
    PAINTING = "painting"
    FINISHING = "finishing"
    SITEWORK = "sitework"
    CONSTRUCTION = "construction"
    OTHER = "other"

class ScheduleType(Enum):
    GANTT = "gantt"
    LINEAR = "linear"

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    total_sf = db.Column(db.Float)  # Total square footage
    floor_count = db.Column(db.Integer)
    building_type = db.Column(db.String(100))
    location = db.Column(db.String(200))
    budget = db.Column(db.Float)
    created_by = db.Column(db.String(100))
    
    # Linear scheduling fields
    linear_scheduling_enabled = db.Column(db.Boolean, default=False)
    project_start_station = db.Column(db.Float)  # Start chainage/station
    project_end_station = db.Column(db.Float)    # End chainage/station  
    station_units = db.Column(db.String(10), default='m')  # m, ft, km, mi
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='project', lazy=True, cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='project', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    def get_completion_percentage(self):
        """Calculate project completion percentage based on activities"""
        if not self.activities:
            return 0
        total_progress = sum([activity.progress or 0 for activity in self.activities])
        return total_progress / len(self.activities)
    
    def get_budget_utilization(self):
        """Calculate budget utilization percentage"""
        if not self.budget or self.budget == 0:
            return 0
        spent = sum([activity.actual_cost or 0 for activity in self.activities])
        return (spent / self.budget) * 100
    
    def get_overdue_activities(self):
        """Get list of overdue activities"""
        today = date.today()
        return [a for a in self.activities if a.end_date and a.end_date < today and a.progress < 100]
    
    def get_total_duration(self):
        """Calculate total project duration in days"""
        if not self.activities:
            return 0
        return sum(activity.duration for activity in self.activities)
    
    def get_project_length(self):
        """Get total project length for linear scheduling (max end location)"""
        if not self.activities:
            return 0
        locations = [a.location_end for a in self.activities if a.location_end is not None]
        return max(locations) if locations else 0
    
    def get_activities_by_location(self, start_station=None, end_station=None):
        """Get activities within a specific location range"""
        if start_station is None and end_station is None:
            return self.activities
        
        filtered = []
        for activity in self.activities:
            if activity.location_start is not None and activity.location_end is not None:
                activity_start = min(activity.location_start, activity.location_end)
                activity_end = max(activity.location_start, activity.location_end)
                
                if start_station is not None and activity_end < start_station:
                    continue
                if end_station is not None and activity_start > end_station:
                    continue
                filtered.append(activity)
        
        return filtered

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.Enum(ActivityType), default=ActivityType.CONSTRUCTION)
    duration = db.Column(db.Integer, nullable=False)  # Duration in days
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    progress = db.Column(db.Integer, default=0)  # Progress percentage 0-100
    
    # Quantity and production tracking
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))
    production_rate = db.Column(db.Float)  # Units per day
    
    # Resource tracking
    resource_crew_size = db.Column(db.Integer)
    
    # Cost tracking
    cost_estimate = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    
    # Location tracking (for linear scheduling)
    location_start = db.Column(db.Float)  # Start station/chainage
    location_end = db.Column(db.Float)    # End station/chainage
    
    # Additional fields
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predecessor_dependencies = db.relationship('Dependency', foreign_keys='Dependency.successor_id', backref='successor')
    successor_dependencies = db.relationship('Dependency', foreign_keys='Dependency.predecessor_id', backref='predecessor')
    
    def __repr__(self):
        return f'<Activity {self.name}>'
    
    def get_predecessor_ids(self):
        """Get list of predecessor activity IDs"""
        return [dep.predecessor_id for dep in self.predecessor_dependencies]
    
    def get_successor_ids(self):
        """Get list of successor activity IDs"""
        return [dep.successor_id for dep in self.successor_dependencies]
    
    def is_overdue(self):
        """Check if activity is overdue"""
        if not self.end_date:
            return False
        return self.end_date < date.today() and self.progress < 100
    
    def get_progress_status(self):
        """Get human-readable progress status"""
        if self.progress >= 100:
            return "Completed"
        elif self.progress > 0:
            return "In Progress"
        else:
            return "Not Started"

class Dependency(db.Model):
    __tablename__ = 'dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    predecessor_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    successor_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    dependency_type = db.Column(db.String(10), default='FS')  # FS, SS, FF, SF
    lag_days = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Dependency {self.predecessor_id} -> {self.successor_id}>'

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    schedule_type = db.Column(db.Enum(ScheduleType), default=ScheduleType.GANTT)
    is_baseline = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Schedule {self.name}>'

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.Integer)
    document_type = db.Column(db.String(50))  # plans, logistics, bim, other
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class ScheduleMetrics(db.Model):
    __tablename__ = 'schedule_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    metric_date = db.Column(db.Date, default=date.today)
    
    # Performance metrics
    planned_value = db.Column(db.Float, default=0)
    earned_value = db.Column(db.Float, default=0)
    actual_cost = db.Column(db.Float, default=0)
    
    # Calculated indices
    schedule_performance_index = db.Column(db.Float, default=0)  # SPI
    cost_performance_index = db.Column(db.Float, default=0)     # CPI
    
    # Activity counts
    total_activities = db.Column(db.Integer, default=0)
    completed_activities = db.Column(db.Integer, default=0)
    in_progress_activities = db.Column(db.Integer, default=0)
    overdue_activities = db.Column(db.Integer, default=0)
    
    # Additional metrics
    resource_utilization = db.Column(db.Float, default=0)
    critical_path_length = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScheduleMetrics {self.project_id} - {self.metric_date}>'

class HistoricalProject(db.Model):
    __tablename__ = 'historical_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    original_project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    project_data = db.Column(db.Text)  # JSON serialized project data
    snapshot_date = db.Column(db.DateTime, default=datetime.utcnow)
    snapshot_type = db.Column(db.String(50))  # baseline, milestone, final
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<HistoricalProject {self.original_project_id} - {self.snapshot_date}>'