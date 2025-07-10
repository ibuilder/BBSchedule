"""
Carolinas Scheduling SOP Compliance Models
Additional models to ensure BBSchedule meets all SOP requirements
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from extensions import db
import enum

class ScheduleType(enum.Enum):
    """Schedule types per SOP requirements"""
    PRE_AWARD = "pre_award"  # Excel with marketing help
    AP = "ap"  # Award Package - Excel
    SD = "sd"  # Schematic Design - Excel or P6
    DD = "dd"  # Design Development - P6
    CD = "cd"  # Construction Documents - P6
    BID = "bid"  # Bid Schedule - P6
    BASELINE = "baseline"  # Baseline Schedule - P6
    AS_BUILT = "as_built"  # Final As-Built Schedule

class ProjectSize(enum.Enum):
    """Project size categories for scheduler assignment"""
    SMALL = "small"  # <$5M
    MEDIUM = "medium"  # $5M-$25M
    LARGE = "large"  # $25M-$100M
    VERY_LARGE = "very_large"  # >$100M

class FloatStatus(enum.Enum):
    """Float status categories per SOP"""
    POSITIVE = "positive"  # Green - Positive float
    YELLOW = "yellow"  # Yellow - 0 to -15 days
    RED = "red"  # Red - More than -15 days

class SchedulePhase(enum.Enum):
    """Schedule development phases per SOP"""
    DRAFT = "draft"  # 2 weeks for scheduler
    REVIEW = "review"  # 1 week for project team
    FINALIZE = "finalize"  # 1 week to finalize

class UpdateType(enum.Enum):
    """Schedule update types"""
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"

class SOPSchedule(db.Model):
    """Enhanced schedule model to meet SOP requirements"""
    __tablename__ = 'sop_schedules'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # SOP Schedule Type
    schedule_type = Column(SQLEnum(ScheduleType), nullable=False)
    phase = Column(SQLEnum(SchedulePhase), default=SchedulePhase.DRAFT)
    
    # Timeline requirements
    draft_start_date = Column(DateTime)
    draft_due_date = Column(DateTime)  # 2 weeks from start
    review_start_date = Column(DateTime)
    review_due_date = Column(DateTime)  # 1 week from review start
    finalize_start_date = Column(DateTime)
    finalize_due_date = Column(DateTime)  # 1 week from finalize start
    
    # Compliance tracking
    superintendent_buyoff = Column(Boolean, default=False)
    baseline_complete = Column(Boolean, default=False)
    weather_days_included = Column(Boolean, default=False)
    holidays_included = Column(Boolean, default=False)
    work_constraints_included = Column(Boolean, default=False)
    
    # Update tracking
    update_frequency = Column(SQLEnum(UpdateType), default=UpdateType.BIWEEKLY)
    last_update_date = Column(DateTime)
    next_update_date = Column(DateTime)
    
    # Float analysis
    float_status = Column(SQLEnum(FloatStatus))
    current_float = Column(Float, default=0.0)
    
    # 4D requirements
    requires_4d = Column(Boolean, default=False)  # >2 levels vertical
    four_d_complete = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")
    activities = relationship("SOPActivity", back_populates="schedule", cascade="all, delete-orphan")
    fragnets = relationship("Fragnet", back_populates="schedule", cascade="all, delete-orphan")
    
    def calculate_float_status(self):
        """Calculate float status per SOP requirements"""
        if self.current_float > 0:
            self.float_status = FloatStatus.POSITIVE
        elif self.current_float >= -15:
            self.float_status = FloatStatus.YELLOW
        else:
            self.float_status = FloatStatus.RED
    
    def set_timeline_dates(self):
        """Set timeline dates per SOP requirements"""
        if self.draft_start_date:
            self.draft_due_date = self.draft_start_date + timedelta(weeks=2)
            self.review_start_date = self.draft_due_date
            self.review_due_date = self.review_start_date + timedelta(weeks=1)
            self.finalize_start_date = self.review_due_date
            self.finalize_due_date = self.finalize_start_date + timedelta(weeks=1)

class SOPActivity(db.Model):
    """Activities enhanced for SOP compliance"""
    __tablename__ = 'sop_activities'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('sop_schedules.id'), nullable=False)
    activity_id = Column(String(5), nullable=False)  # Max 5 characters per SOP
    
    name = Column(String(200), nullable=False)
    duration = Column(Integer, nullable=False)  # Max 15 days per SOP
    
    # SOP required date fields
    actual_start = Column(DateTime)  # AS
    actual_finish = Column(DateTime)  # AF
    planned_start = Column(DateTime)  # PS
    planned_finish = Column(DateTime)  # PF
    
    # SOP tracking requirements
    is_critical_path = Column(Boolean, default=False)
    total_float = Column(Float, default=0.0)
    free_float = Column(Float, default=0.0)
    
    # Validation per SOP
    is_valid_id = Column(Boolean, default=True)  # Activity ID validation
    is_valid_duration = Column(Boolean, default=True)  # Duration <= 15 days
    has_populated_dates = Column(Boolean, default=False)  # No blank dates
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedule = relationship("SOPSchedule", back_populates="activities")
    
    def validate_sop_compliance(self):
        """Validate activity meets SOP requirements"""
        # Activity ID validation (max 5 characters)
        self.is_valid_id = len(self.activity_id) <= 5
        
        # Duration validation (max 15 days)
        self.is_valid_duration = self.duration <= 15
        
        # Date population validation
        self.has_populated_dates = all([
            self.actual_start or self.planned_start,
            self.actual_finish or self.planned_finish
        ])
        
        return self.is_valid_id and self.is_valid_duration and self.has_populated_dates

class Fragnet(db.Model):
    """Fragnets/Impacts per SOP requirements"""
    __tablename__ = 'fragnets'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('sop_schedules.id'), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Fragnet triggers per SOP
    trigger_type = Column(String(50))  # design_revision, stop_work, weather_event, etc.
    
    # Impact tracking
    delay_days = Column(Integer, default=0)
    cost_impact = Column(Float, default=0.0)
    
    # Recovery schedule trigger
    requires_recovery = Column(Boolean, default=False)  # >15 days delay
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    schedule = relationship("SOPSchedule", back_populates="fragnets")

class SchedulerAssignment(db.Model):
    """Scheduler assignments per SOP workload requirements"""
    __tablename__ = 'scheduler_assignments'
    
    id = Column(Integer, primary_key=True)
    scheduler_name = Column(String(100), nullable=False)
    scheduler_level = Column(String(50))  # senior_scheduler, scheduler
    
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    contract_value = Column(Float)
    project_size = Column(SQLEnum(ProjectSize))
    
    # Assignment rules per SOP
    is_over_10m = Column(Boolean, default=False)  # Scheduler required
    is_team_update = Column(Boolean, default=False)  # Team updates for <=10M
    
    assigned_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")

class PullPlanBoard(db.Model):
    """Pull planning boards per SOP requirements"""
    __tablename__ = 'pull_plan_boards'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # 3-4 week lookahead per SOP
    week_1_activities = Column(Text)  # JSON of activities
    week_2_activities = Column(Text)
    week_3_activities = Column(Text)
    week_4_activities = Column(Text)
    
    # High level activities only per SOP
    deliveries = Column(Text)  # JSON
    preinstall_meetings = Column(Text)  # JSON
    inspections = Column(Text)  # JSON
    safety_activities = Column(Text)  # JSON
    
    # Display format options per SOP
    format_type = Column(String(20), default="whiteboard")  # whiteboard, logistics_plan
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")

class ScheduleReport(db.Model):
    """Schedule reports per SOP requirements"""
    __tablename__ = 'schedule_reports'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # Report types per SOP
    report_type = Column(String(50))  # full, baseline_comparison, lookahead, etc.
    
    # SOP required reports
    full_schedule = Column(Boolean, default=False)
    baseline_comparison = Column(Boolean, default=False)
    lookahead_schedule = Column(Boolean, default=False)  # 4-8 weeks
    longest_path = Column(Boolean, default=False)
    total_float_report = Column(Boolean, default=False)
    update_form = Column(Boolean, default=False)
    
    # Monthly reporting requirements
    is_monthly_report = Column(Boolean, default=False)
    sent_to_owner = Column(Boolean, default=False)
    
    # Status tracking per SOP color coding
    baseline_complete = Column(Boolean, default=False)
    thirty_sixty_ninety = Column(String(20))  # status
    on_schedule_status = Column(String(20))  # green/yellow/red
    pull_planning_status = Column(String(20))
    
    generated_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")

class ScheduleTemplate(db.Model):
    """Schedule templates per SOP requirements (due Oct 1, 2025)"""
    __tablename__ = 'schedule_templates'
    
    id = Column(Integer, primary_key=True)
    
    # Template types per SOP
    template_type = Column(String(50), nullable=False)  # school, office, preconstruction, etc.
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Template content
    activities_json = Column(Text)  # JSON of template activities
    milestones_json = Column(Text)  # JSON of template milestones
    
    # SOP template categories
    is_school_template = Column(Boolean, default=False)
    is_office_building = Column(Boolean, default=False)
    is_preconstruction = Column(Boolean, default=False)
    is_closeout = Column(Boolean, default=False)
    is_cx_mep_buildout = Column(Boolean, default=False)
    
    created_date = Column(DateTime, default=datetime.utcnow)
    target_completion = Column(DateTime, default=lambda: datetime(2025, 10, 1))  # Oct 1, 2025

# Add relationships to existing Project model
def enhance_project_model():
    """Add SOP-required relationships to existing Project model"""
    # This would be added to the existing Project model in models.py
    # project.sop_schedules = relationship("SOPSchedule", back_populates="project")
    pass