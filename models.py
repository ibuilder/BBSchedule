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
    OTHER = "other"

class ScheduleType(Enum):
    GANTT = "gantt"
    LINEAR = "linear"

class Project(db.Model):
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='project', lazy=True, cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='project', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    def get_completion_percentage(self):
        if not self.activities:
            return 0
        completed_activities = sum(1 for activity in self.activities if activity.progress == 100)
        return (completed_activities / len(self.activities)) * 100
    
    def get_total_duration(self):
        if not self.activities:
            return 0
        return sum(activity.duration for activity in self.activities)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.Enum(ActivityType), default=ActivityType.OTHER)
    duration = db.Column(db.Integer, nullable=False)  # Duration in days
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    progress = db.Column(db.Integer, default=0)  # Progress percentage
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))
    production_rate = db.Column(db.Float)  # Units per day
    resource_crew_size = db.Column(db.Integer)
    cost_estimate = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Linear scheduling specific fields
    location_start = db.Column(db.Float)  # Start location/station
    location_end = db.Column(db.Float)    # End location/station
    
    # Relationships
    predecessors = db.relationship('Dependency', foreign_keys='Dependency.successor_id', backref='successor_activity', lazy=True)
    successors = db.relationship('Dependency', foreign_keys='Dependency.predecessor_id', backref='predecessor_activity', lazy=True)
    
    def __repr__(self):
        return f'<Activity {self.name}>'
    
    def get_predecessor_ids(self):
        return [dep.predecessor_id for dep in self.predecessors]
    
    def get_successor_ids(self):
        return [dep.successor_id for dep in self.successors]

class Dependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    predecessor_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    successor_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    dependency_type = db.Column(db.String(20), default='FS')  # FS, SS, FF, SF
    lag_days = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Dependency {self.predecessor_id} -> {self.successor_id}>'

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    schedule_type = db.Column(db.Enum(ScheduleType), nullable=False)
    is_baseline = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Schedule {self.name}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer)
    document_type = db.Column(db.String(50))  # 'plans', 'logistics', 'bim', 'other'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class ScheduleMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    metric_date = db.Column(db.Date, default=date.today)
    
    # Performance metrics
    schedule_performance_index = db.Column(db.Float)  # SPI
    cost_performance_index = db.Column(db.Float)      # CPI
    planned_value = db.Column(db.Float)               # PV
    earned_value = db.Column(db.Float)                # EV
    actual_cost = db.Column(db.Float)                 # AC
    
    # Quality metrics
    activities_on_schedule = db.Column(db.Integer)
    activities_delayed = db.Column(db.Integer)
    critical_path_variance = db.Column(db.Float)
    resource_utilization = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScheduleMetrics {self.project_id} - {self.metric_date}>'

# Historical data for AI learning
class HistoricalProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    building_type = db.Column(db.String(100))
    total_sf = db.Column(db.Float)
    floor_count = db.Column(db.Integer)
    actual_duration = db.Column(db.Integer)
    planned_duration = db.Column(db.Integer)
    final_cost = db.Column(db.Float)
    planned_cost = db.Column(db.Float)
    completion_date = db.Column(db.Date)
    
    # Key performance indicators
    schedule_variance = db.Column(db.Float)
    cost_variance = db.Column(db.Float)
    quality_score = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HistoricalProject {self.name}>'
