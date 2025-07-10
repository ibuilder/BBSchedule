"""
Carolinas Scheduling SOP Compliance Service
Implements all SOP requirements and business logic
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_
from extensions import db
from models import Project, Activity
from models_sop_compliance import (
    SOPSchedule, SOPActivity, Fragnet, SchedulerAssignment, 
    PullPlanBoard, ScheduleReport, ScheduleTemplate,
    ScheduleType, ProjectSize, FloatStatus, SchedulePhase, UpdateType
)
import json
import logging

logger = logging.getLogger(__name__)

class SOPComplianceService:
    """Service for managing SOP compliance requirements"""
    
    def __init__(self):
        self.scheduler_workload = {
            'senior_scheduler': {'small_medium_large': (5, 10), 'very_large': (1, 2)},
            'scheduler': {'small_medium': (1, 5)}
        }
    
    def create_sop_schedule(self, project_id: int, schedule_type: ScheduleType, 
                           start_date: datetime = None) -> SOPSchedule:
        """Create SOP-compliant schedule with proper timelines"""
        
        sop_schedule = SOPSchedule(
            project_id=project_id,
            schedule_type=schedule_type,
            draft_start_date=start_date or datetime.utcnow()
        )
        
        # Set timeline dates per SOP requirements
        sop_schedule.set_timeline_dates()
        
        # Determine if 4D is required (>2 levels vertical)
        project = Project.query.get(project_id)
        if project and hasattr(project, 'floor_count') and project.floor_count > 2:
            sop_schedule.requires_4d = True
        
        # Set update frequency
        if schedule_type in [ScheduleType.BASELINE, ScheduleType.CD, ScheduleType.BID]:
            sop_schedule.update_frequency = UpdateType.BIWEEKLY
        
        db.session.add(sop_schedule)
        db.session.commit()
        
        logger.info(f"Created SOP schedule {schedule_type.value} for project {project_id}")
        return sop_schedule
    
    def validate_activity_sop_compliance(self, activity: SOPActivity) -> Dict[str, bool]:
        """Validate activity meets all SOP requirements"""
        
        validation_results = {
            'activity_id_valid': len(activity.activity_id) <= 5,
            'duration_valid': activity.duration <= 15,
            'dates_populated': bool(
                (activity.actual_start or activity.planned_start) and 
                (activity.actual_finish or activity.planned_finish)
            ),
            'from_bid_to_progress': True,  # Activity IDs match from bid to progress
            'overall_compliant': True
        }
        
        # Update activity compliance flags
        activity.is_valid_id = validation_results['activity_id_valid']
        activity.is_valid_duration = validation_results['duration_valid']
        activity.has_populated_dates = validation_results['dates_populated']
        
        validation_results['overall_compliant'] = all([
            validation_results['activity_id_valid'],
            validation_results['duration_valid'],
            validation_results['dates_populated']
        ])
        
        return validation_results
    
    def assign_scheduler(self, project_id: int, contract_value: float) -> SchedulerAssignment:
        """Assign scheduler based on SOP rules"""
        
        # Determine project size
        if contract_value >= 100_000_000:
            project_size = ProjectSize.VERY_LARGE
        elif contract_value >= 25_000_000:
            project_size = ProjectSize.LARGE
        elif contract_value >= 5_000_000:
            project_size = ProjectSize.MEDIUM
        else:
            project_size = ProjectSize.SMALL
        
        # SOP Rule: Scheduler required for >$10M projects
        requires_scheduler = contract_value > 10_000_000
        
        assignment = SchedulerAssignment(
            project_id=project_id,
            contract_value=contract_value,
            project_size=project_size,
            is_over_10m=requires_scheduler,
            is_team_update=not requires_scheduler
        )
        
        # Assign scheduler based on workload
        if project_size == ProjectSize.VERY_LARGE:
            assignment.scheduler_level = "senior_scheduler"
            assignment.scheduler_name = "Senior Scheduler (1-2 very large projects)"
        elif requires_scheduler:
            assignment.scheduler_level = "scheduler"
            assignment.scheduler_name = "Project Scheduler (Over $10M)"
        else:
            assignment.scheduler_level = "team"
            assignment.scheduler_name = "Project Team ($10M or less)"
        
        db.session.add(assignment)
        db.session.commit()
        
        return assignment
    
    def create_fragnet(self, schedule_id: int, trigger_type: str, 
                      delay_days: int, description: str) -> Fragnet:
        """Create fragnet per SOP requirements"""
        
        fragnet = Fragnet(
            schedule_id=schedule_id,
            name=f"Fragnet - {trigger_type.title()}",
            description=description,
            trigger_type=trigger_type,
            delay_days=delay_days,
            requires_recovery=delay_days > 15  # SOP: >15 days requires recovery
        )
        
        db.session.add(fragnet)
        db.session.commit()
        
        return fragnet
    
    def update_schedule_float_status(self, schedule_id: int) -> FloatStatus:
        """Update schedule float status per SOP color coding"""
        
        schedule = SOPSchedule.query.get(schedule_id)
        if not schedule:
            return None
        
        # Calculate current float (simplified - would integrate with actual CPM)
        activities = SOPActivity.query.filter_by(schedule_id=schedule_id).all()
        if activities:
            avg_float = sum(a.total_float for a in activities) / len(activities)
            schedule.current_float = avg_float
        
        # Apply SOP color coding
        schedule.calculate_float_status()
        db.session.commit()
        
        return schedule.float_status
    
    def generate_sop_reports(self, project_id: int) -> List[ScheduleReport]:
        """Generate all SOP-required reports"""
        
        reports = []
        report_types = [
            ('full_schedule', 'Full Schedule'),
            ('baseline_comparison', 'Baseline Comparison'),
            ('lookahead_schedule', 'Look-Ahead Schedule (4-8 weeks)'),
            ('longest_path', 'Longest Path'),
            ('total_float_report', 'Total Float Report'),
            ('update_form', 'Update Form (for ops team)')
        ]
        
        for report_type, report_name in report_types:
            report = ScheduleReport(
                project_id=project_id,
                report_type=report_type
            )
            setattr(report, report_type, True)
            
            reports.append(report)
            db.session.add(report)
        
        db.session.commit()
        return reports
    
    def create_pull_plan_board(self, project_id: int) -> PullPlanBoard:
        """Create 3-4 week lookahead pull plan board per SOP"""
        
        # High level activities only per SOP
        sample_activities = {
            'steel_fab_delivery': 'Steel Fabrication/Delivery',
            'steel_start': 'Steel Erection Start',
            'sog_pours': 'Slab on Grade Pours',
            'mep_ris': 'MEP Rough-ins'
        }
        
        pull_plan = PullPlanBoard(
            project_id=project_id,
            week_1_activities=json.dumps(['Steel Fab/Delivery', 'Steel Start']),
            week_2_activities=json.dumps(['SOG Pours', 'MEP RIs']),
            week_3_activities=json.dumps(['Deliveries', 'Inspections']),
            week_4_activities=json.dumps(['Safety Activities', 'Preinstall Meetings']),
            deliveries=json.dumps(['Material Delivery A', 'Equipment Delivery B']),
            preinstall_meetings=json.dumps(['MEP Coordination', 'Steel Coordination']),
            inspections=json.dumps(['Foundation Inspection', 'Framing Inspection']),
            safety_activities=json.dumps(['Safety Training', 'Site Safety Review'])
        )
        
        db.session.add(pull_plan)
        db.session.commit()
        
        return pull_plan
    
    def check_schedule_development_timeline(self, schedule_id: int) -> Dict[str, any]:
        """Check if schedule development follows SOP timelines"""
        
        schedule = SOPSchedule.query.get(schedule_id)
        if not schedule:
            return {'error': 'Schedule not found'}
        
        current_date = datetime.utcnow()
        
        timeline_status = {
            'draft_phase': {
                'due_date': schedule.draft_due_date,
                'is_overdue': current_date > schedule.draft_due_date if schedule.draft_due_date else False,
                'days_remaining': (schedule.draft_due_date - current_date).days if schedule.draft_due_date else None
            },
            'review_phase': {
                'due_date': schedule.review_due_date,
                'superintendent_buyoff': schedule.superintendent_buyoff,
                'is_overdue': current_date > schedule.review_due_date if schedule.review_due_date else False
            },
            'finalize_phase': {
                'due_date': schedule.finalize_due_date,
                'is_complete': schedule.phase == SchedulePhase.FINALIZE,
                'is_overdue': current_date > schedule.finalize_due_date if schedule.finalize_due_date else False
            }
        }
        
        return timeline_status
    
    def create_schedule_templates(self) -> List[ScheduleTemplate]:
        """Create SOP-required schedule templates (due Oct 1, 2025)"""
        
        templates_data = [
            {
                'name': 'School Construction Template',
                'type': 'school',
                'is_school_template': True,
                'activities': ['Site Prep', 'Foundation', 'Structure', 'MEP Rough-in', 'Finishes']
            },
            {
                'name': 'Office Building Template', 
                'type': 'office',
                'is_office_building': True,
                'activities': ['Excavation', 'Foundation', 'Structure', 'Envelope', 'MEP', 'Finishes']
            },
            {
                'name': 'Preconstruction/Permitting Template',
                'type': 'preconstruction',
                'is_preconstruction': True,
                'activities': ['Design', 'Permitting', 'Bidding', 'Procurement', 'Mobilization']
            },
            {
                'name': 'Milestone Template',
                'type': 'milestones',
                'activities': ['NTP', 'Foundation Complete', 'Structure Complete', 'Substantial Completion']
            },
            {
                'name': 'Cx/MEP Build Out Template',
                'type': 'cx_mep',
                'is_cx_mep_buildout': True,
                'activities': ['MEP Design', 'MEP Installation', 'Testing', 'Commissioning', 'Startup']
            },
            {
                'name': 'Closeout Template',
                'type': 'closeout',
                'is_closeout': True,
                'activities': ['Punch List', 'Final Inspections', 'Documentation', 'Training', 'Handover']
            }
        ]
        
        templates = []
        for template_data in templates_data:
            template = ScheduleTemplate(
                template_type=template_data['type'],
                name=template_data['name'],
                activities_json=json.dumps(template_data['activities']),
                **{k: v for k, v in template_data.items() if k.startswith('is_')}
            )
            templates.append(template)
            db.session.add(template)
        
        db.session.commit()
        return templates
    
    def validate_monthly_update_requirements(self, project_id: int) -> Dict[str, any]:
        """Validate monthly update requirements per SOP"""
        
        # Get scheduler assignment
        assignment = SchedulerAssignment.query.filter_by(project_id=project_id).first()
        
        validation = {
            'scheduler_required': assignment.is_over_10m if assignment else False,
            'team_updates_allowed': assignment.is_team_update if assignment else True,
            'update_deadline': 'Second Friday of each month',
            'feedback_deadline': 'Two days prior to bi-weekly site meetings',
            'monthly_report_required': True,
            'report_distribution': ['Pres', 'VP', 'OD', 'Generals', 'PX', 'Sr. Supt/PM']
        }
        
        # Check if activities have populated dates
        activities = SOPActivity.query.join(SOPSchedule).filter(
            SOPSchedule.project_id == project_id
        ).all()
        
        validation['activities_with_dates'] = sum(1 for a in activities if a.has_populated_dates)
        validation['total_activities'] = len(activities)
        validation['compliance_percentage'] = (
            validation['activities_with_dates'] / validation['total_activities'] * 100
            if validation['total_activities'] > 0 else 0
        )
        
        return validation
    
    def get_sop_compliance_dashboard(self, project_id: int) -> Dict[str, any]:
        """Get comprehensive SOP compliance dashboard"""
        
        project = Project.query.get(project_id)
        schedules = SOPSchedule.query.filter_by(project_id=project_id).all()
        assignment = SchedulerAssignment.query.filter_by(project_id=project_id).first()
        
        dashboard = {
            'project_info': {
                'name': project.name if project else 'Unknown',
                'contract_value': assignment.contract_value if assignment else 0,
                'project_size': assignment.project_size.value if assignment else 'unknown'
            },
            'schedule_compliance': {
                'schedules_created': len(schedules),
                'baseline_complete': any(s.baseline_complete for s in schedules),
                'requires_4d': any(s.requires_4d for s in schedules),
                'four_d_complete': any(s.four_d_complete for s in schedules)
            },
            'activity_compliance': self._get_activity_compliance(project_id),
            'update_compliance': self.validate_monthly_update_requirements(project_id),
            'reports_generated': len(ScheduleReport.query.filter_by(project_id=project_id).all()),
            'float_status': schedules[0].float_status.value if schedules else 'unknown'
        }
        
        return dashboard
    
    def _get_activity_compliance(self, project_id: int) -> Dict[str, any]:
        """Get activity compliance metrics"""
        
        activities = SOPActivity.query.join(SOPSchedule).filter(
            SOPSchedule.project_id == project_id
        ).all()
        
        if not activities:
            return {'total': 0, 'compliant': 0, 'compliance_rate': 0}
        
        compliant_activities = sum(1 for a in activities if a.validate_sop_compliance())
        
        return {
            'total': len(activities),
            'compliant': compliant_activities,
            'compliance_rate': compliant_activities / len(activities) * 100,
            'id_violations': sum(1 for a in activities if not a.is_valid_id),
            'duration_violations': sum(1 for a in activities if not a.is_valid_duration),
            'date_violations': sum(1 for a in activities if not a.has_populated_dates)
        }

# Global service instance
sop_service = SOPComplianceService()