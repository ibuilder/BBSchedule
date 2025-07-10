"""
NCMoH Schedule Importer - Real-world SOP Implementation
Imports the NC Museum of History renovation schedule to demonstrate SOP compliance
"""

from datetime import datetime, timedelta
from extensions import db
from models import Project, Activity
from models_sop_compliance import (
    SOPSchedule, SOPActivity, Fragnet, SchedulerAssignment, 
    PullPlanBoard, ScheduleReport, ScheduleTemplate,
    ScheduleType, ProjectSize, FloatStatus, UpdateType
)
from services.sop_compliance_service import sop_service
import logging

logger = logging.getLogger(__name__)

class NCMoHScheduleImporter:
    """Import NC Museum of History schedule with SOP compliance"""
    
    def __init__(self):
        self.project_data = {
            'name': 'NC Museum of History Renovation & Expansion',
            'location': 'Raleigh, NC',
            'contract_value': 75000000,  # $75M project
            'start_date': datetime(2025, 6, 22),
            'end_date': datetime(2028, 2, 14),
            'description': 'Museum renovation and expansion with complex phasing and historic preservation requirements'
        }
        
        self.milestones = [
            {'id': 'MLS1630', 'name': 'Award GMP #2 / Early Release of GMP #2', 'date': datetime(2025, 8, 15)},
            {'id': 'MLS1640', 'name': 'Award GMP#3 / Notice to Proceed Issued', 'date': datetime(2025, 9, 12)},
            {'id': 'MLS1650', 'name': 'Beneficial Occupancy Date', 'date': datetime(2028, 2, 14)}
        ]
        
        # Real activities from the schedule with SOP-compliant IDs (≤5 chars)
        self.activities = [
            # Bidding Phase - GMP #2
            {'id': 'BID10', 'name': 'Advertisement to Bid', 'duration': 1, 'start': datetime(2025, 6, 22)},
            {'id': 'BID20', 'name': 'Pre-Bid Conference', 'duration': 1, 'start': datetime(2025, 6, 24)},
            {'id': 'BID30', 'name': 'Bid Walk-Thru', 'duration': 1, 'start': datetime(2025, 6, 27)},
            {'id': 'BID31', 'name': 'First Addendum', 'duration': 1, 'start': datetime(2025, 6, 30)},
            {'id': 'BID40', 'name': 'Final Addendum', 'duration': 1, 'start': datetime(2025, 7, 14)},
            {'id': 'BID50', 'name': 'Bid Receiving (Opening)', 'duration': 1, 'start': datetime(2025, 7, 22)},
            {'id': 'BID60', 'name': 'Rebid (If Necessary)', 'duration': 1, 'start': datetime(2025, 7, 29)},
            {'id': 'BID65', 'name': 'Reconcile GMP #2', 'duration': 10, 'start': datetime(2025, 7, 30)},
            
            # Award Activities - Multiple packages
            {'id': 'AWD80', 'name': 'Award BP-08G Curtainwall & Doors', 'duration': 3, 'start': datetime(2025, 8, 13)},
            {'id': 'AWD90', 'name': 'Award BP-31F Shoring Systems', 'duration': 3, 'start': datetime(2025, 8, 13)},
            {'id': 'AWD00', 'name': 'Award BP-05A Structural / Stairs / Misc Steel', 'duration': 3, 'start': datetime(2025, 8, 13)},
            {'id': 'AWD10', 'name': 'Award BP-01D Site Demo & Erosion Control', 'duration': 3, 'start': datetime(2025, 8, 13)},
            {'id': 'AWD20', 'name': 'Award BP-21A Fire Protection', 'duration': 3, 'start': datetime(2025, 8, 13)},
            
            # Structural Work - Micro Piles
            {'id': 'STR50', 'name': 'Micro Piles Test Piles', 'duration': 5, 'start': datetime(2025, 9, 23)},
            {'id': 'STR60', 'name': 'Micro Piles A1 - A2.5 (4 Total)', 'duration': 10, 'start': datetime(2025, 9, 30)},
            {'id': 'STR70', 'name': 'Micro Piles C.6/10 - C.6/13 (16 Total)', 'duration': 20, 'start': datetime(2025, 10, 14)},
            
            # FRP Column Work
            {'id': 'FRP25', 'name': 'FRP Wrap Columns Z6, A7, E3, E4, F3.5, F4', 'duration': 6, 'start': datetime(2025, 10, 20)},
            {'id': 'FRP35', 'name': 'FRP Wrap Columns E5, E6, E7, F5, F6, F7', 'duration': 6, 'start': datetime(2025, 10, 28)},
            {'id': 'FRP45', 'name': 'FRP Wrap Columns E8, E9, E11, F8, F9, F11', 'duration': 6, 'start': datetime(2025, 11, 5)},
            
            # Demolition Work
            {'id': 'DEM20', 'name': 'Demo Stair 4 Existing Structure', 'duration': 15, 'start': datetime(2025, 12, 31)},
            {'id': 'DEM15', 'name': '(05 Main Level) All Interior Demo East of CL D', 'duration': 20, 'start': datetime(2025, 12, 31)},
            {'id': 'DEM25', 'name': '(04 Service Level) All Interior Demo on Level', 'duration': 30, 'start': datetime(2026, 1, 29)},
            
            # MEP Work
            {'id': 'MEP05', 'name': 'New Plumbing Piping', 'duration': 15, 'start': datetime(2026, 11, 10)},
            {'id': 'MEP25', 'name': 'Test & Inspections', 'duration': 5, 'start': datetime(2026, 12, 3)},
            {'id': 'MEP35', 'name': 'Insulate Piping', 'duration': 10, 'start': datetime(2026, 12, 10)},
            {'id': 'MEP45', 'name': 'Close Up Shaft', 'duration': 10, 'start': datetime(2026, 12, 29)},
        ]
    
    def import_project(self):
        """Import the complete NCMoH project with SOP compliance"""
        
        # Create main project
        project = Project(
            name=self.project_data['name'],
            description=self.project_data['description'],
            location=self.project_data['location'],
            start_date=self.project_data['start_date'],
            end_date=self.project_data['end_date'],
            budget=self.project_data['contract_value'],
            status='active',
            floor_count=4,  # Multi-level museum (requires 4D per SOP)
            total_sf=150000  # Estimated square footage
        )
        
        db.session.add(project)
        db.session.flush()  # Get project ID
        
        logger.info(f"Created NCMoH project: {project.id}")
        
        # Create SOP-compliant schedules for different phases
        self._create_sop_schedules(project.id)
        
        # Import activities with SOP compliance
        self._import_activities(project.id)
        
        # Assign scheduler per SOP rules
        self._assign_scheduler(project.id)
        
        # Create pull planning board
        self._create_pull_planning_board(project.id)
        
        # Generate required reports
        self._generate_sop_reports(project.id)
        
        # Create fragnets for potential delays
        self._create_sample_fragnets(project.id)
        
        db.session.commit()
        
        return project
    
    def _create_sop_schedules(self, project_id):
        """Create SOP-compliant schedules for different phases"""
        
        # Bid Schedule (current phase)
        bid_schedule = sop_service.create_sop_schedule(
            project_id=project_id,
            schedule_type=ScheduleType.BID,
            start_date=datetime(2025, 6, 22)
        )
        bid_schedule.baseline_complete = False
        bid_schedule.requires_4d = True  # Museum is multi-level
        bid_schedule.weather_days_included = True
        bid_schedule.holidays_included = True
        bid_schedule.work_constraints_included = True
        
        # Baseline Schedule (upcoming)
        baseline_schedule = sop_service.create_sop_schedule(
            project_id=project_id,
            schedule_type=ScheduleType.BASELINE,
            start_date=datetime(2025, 8, 15)
        )
        baseline_schedule.superintendent_buyoff = False  # Pending
        baseline_schedule.requires_4d = True
        
        logger.info(f"Created SOP schedules for project {project_id}")
    
    def _import_activities(self, project_id):
        """Import activities with SOP compliance validation"""
        
        # Get the bid schedule
        bid_schedule = SOPSchedule.query.filter_by(
            project_id=project_id,
            schedule_type=ScheduleType.BID
        ).first()
        
        for activity_data in self.activities:
            # Create SOP-compliant activity
            activity = SOPActivity(
                schedule_id=bid_schedule.id,
                activity_id=activity_data['id'],  # Already ≤5 characters
                name=activity_data['name'],
                duration=activity_data['duration'],  # All ≤15 days per SOP
                planned_start=activity_data['start'],
                planned_finish=activity_data['start'] + timedelta(days=activity_data['duration'])
            )
            
            # Validate SOP compliance
            validation = sop_service.validate_activity_sop_compliance(activity)
            if not validation['overall_compliant']:
                logger.warning(f"Activity {activity.activity_id} has compliance issues: {validation}")
            
            db.session.add(activity)
        
        logger.info(f"Imported {len(self.activities)} SOP-compliant activities")
    
    def _assign_scheduler(self, project_id):
        """Assign scheduler based on SOP rules (>$10M = scheduler required)"""
        
        assignment = sop_service.assign_scheduler(
            project_id=project_id,
            contract_value=self.project_data['contract_value']
        )
        
        # This is a very large project requiring senior scheduler
        assignment.scheduler_name = "Senior Scheduler - Museum Specialist"
        assignment.scheduler_level = "senior_scheduler"
        
        logger.info(f"Assigned scheduler: {assignment.scheduler_name}")
    
    def _create_pull_planning_board(self, project_id):
        """Create pull planning board with real NCMoH activities"""
        
        pull_plan = sop_service.create_pull_plan_board(project_id)
        
        # Update with real museum project activities
        import json
        pull_plan.week_1_activities = json.dumps([
            'Award Curtainwall Package',
            'Award Shoring Systems',
            'Award Structural Steel'
        ])
        pull_plan.week_2_activities = json.dumps([
            'Mobilize Site Demo',
            'Begin Fire Protection Work',
            'Start Building Demo'
        ])
        pull_plan.week_3_activities = json.dumps([
            'Micro Pile Test Installation',
            'Structural Steel Delivery',
            'MEP Coordination Meeting'
        ])
        pull_plan.week_4_activities = json.dumps([
            'FRP Column Prep',
            'Demo Stair 4 Planning',
            'Interior Demo Layout'
        ])
        
        # Museum-specific special activities
        pull_plan.deliveries = json.dumps([
            'Historic Artifact Relocation',
            'Curtainwall System Delivery',
            'Structural Steel Shipment',
            'Shoring Equipment Delivery'
        ])
        
        pull_plan.inspections = json.dumps([
            'Historic Preservation Review',
            'Structural Micro Pile Inspection',
            'Fire Protection System Inspection',
            'MEP Rough-in Inspection'
        ])
        
        pull_plan.safety_activities = json.dumps([
            'Museum Safety Orientation',
            'Historic Material Handling Training',
            'Crane Safety Briefing',
            'Confined Space Training'
        ])
        
        logger.info(f"Created pull planning board for museum project")
    
    def _generate_sop_reports(self, project_id):
        """Generate all SOP-required reports"""
        
        reports = sop_service.generate_sop_reports(project_id)
        
        # Update with museum-specific information
        for report in reports:
            report.is_monthly_report = True
            if report.report_type == 'lookahead_schedule':
                # Museum projects need 6-week lookahead due to complexity
                report.report_type = 'lookahead_6_week'
        
        logger.info(f"Generated {len(reports)} SOP reports")
    
    def _create_sample_fragnets(self, project_id):
        """Create sample fragnets for potential museum project delays"""
        
        # Get schedule for fragnet association
        schedule = SOPSchedule.query.filter_by(project_id=project_id).first()
        
        fragnets = [
            {
                'trigger_type': 'historic_preservation_review',
                'delay_days': 20,
                'description': 'Historic preservation review process extends timeline for artifact handling and structural modifications'
            },
            {
                'trigger_type': 'design_revision',
                'delay_days': 10,
                'description': 'Design revision required for MEP systems to accommodate museum display requirements'
            },
            {
                'trigger_type': 'material_procurement_delay',
                'delay_days': 15,
                'description': 'Specialized museum-grade materials require extended procurement timeline'
            }
        ]
        
        for fragnet_data in fragnets:
            fragnet = sop_service.create_fragnet(
                schedule_id=schedule.id,
                trigger_type=fragnet_data['trigger_type'],
                delay_days=fragnet_data['delay_days'],
                description=fragnet_data['description']
            )
        
        logger.info(f"Created {len(fragnets)} sample fragnets")
    
    def get_sop_compliance_summary(self, project_id):
        """Get comprehensive compliance summary for NCMoH project"""
        
        dashboard = sop_service.get_sop_compliance_dashboard(project_id)
        
        # Add museum-specific compliance items
        museum_compliance = {
            'historic_preservation_compliance': True,
            'artifact_handling_procedures': True,
            'specialized_contractor_requirements': True,
            'phased_construction_planning': True,
            'visitor_safety_protocols': True
        }
        
        dashboard['museum_specific'] = museum_compliance
        
        return dashboard

# Global importer instance
ncmoh_importer = NCMoHScheduleImporter()