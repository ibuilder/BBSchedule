"""
Load test data for the construction scheduling application
Creates realistic construction projects with activities, dependencies, and schedules
"""

from datetime import datetime, date, timedelta
from app import app, db
from models import (
    Project, Activity, Dependency, Schedule, Document, ScheduleMetrics,
    ProjectStatus, ActivityType, ScheduleType
)

def load_test_data():
    """Load comprehensive test data for the application"""
    
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Project 1: Office Building Construction
        project1 = Project(
            name="Downtown Office Complex",
            description="15-story commercial office building with underground parking",
            start_date=date(2024, 1, 15),
            end_date=date(2025, 8, 30),
            status=ProjectStatus.ACTIVE,
            total_sf=250000,
            floor_count=15,
            building_type="Commercial Office",
            location="Downtown Financial District",
            budget=25000000.00,
            created_at=datetime.utcnow()
        )
        
        # Project 2: Residential Development
        project2 = Project(
            name="Sunset Gardens Residential",
            description="Mixed-use residential development with 120 units",
            start_date=date(2024, 3, 1),
            end_date=date(2025, 12, 15),
            status=ProjectStatus.ACTIVE,
            total_sf=180000,
            floor_count=8,
            building_type="Residential",
            location="Sunset District",
            budget=18500000.00,
            created_at=datetime.utcnow()
        )
        
        # Project 3: Infrastructure Project
        project3 = Project(
            name="Highway Bridge Replacement",
            description="Replace aging highway bridge with modern structure",
            start_date=date(2024, 6, 1),
            end_date=date(2025, 5, 31),
            status=ProjectStatus.PLANNING,
            total_sf=45000,
            floor_count=1,
            building_type="Infrastructure",
            location="Highway 101 Mile Marker 25",
            budget=12000000.00,
            created_at=datetime.utcnow()
        )
        
        db.session.add_all([project1, project2, project3])
        db.session.flush()
        
        # Activities for Project 1 (Office Building)
        office_activities = [
            # Site Preparation Phase
            Activity(
                project_id=project1.id,
                name="Site Survey and Soil Testing",
                description="Comprehensive site survey and geotechnical soil analysis",
                activity_type=ActivityType.SITEWORK,
                duration=14,
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 28),
                progress=100,
                quantity=250000,
                unit="sq ft",
                production_rate=17857,
                resource_crew_size=4,
                cost_estimate=85000.00,
                actual_cost=82500.00,
                location_start=0.0,
                location_end=250000.0,
                notes="Soil bearing capacity confirmed at 4000 PSF"
            ),
            Activity(
                project_id=project1.id,
                name="Site Clearing and Demolition",
                description="Clear existing structures and prepare for excavation",
                activity_type=ActivityType.SITEWORK,
                duration=21,
                start_date=date(2024, 1, 29),
                end_date=date(2024, 2, 18),
                progress=100,
                quantity=50000,
                unit="sq ft",
                production_rate=2380,
                resource_crew_size=8,
                cost_estimate=125000.00,
                actual_cost=118000.00,
                location_start=0.0,
                location_end=50000.0
            ),
            Activity(
                project_id=project1.id,
                name="Excavation and Earthwork",
                description="Excavate for foundation and underground parking",
                activity_type=ActivityType.SITEWORK,
                duration=35,
                start_date=date(2024, 2, 19),
                end_date=date(2024, 3, 25),
                progress=100,
                quantity=45000,
                unit="cubic yards",
                production_rate=1285,
                resource_crew_size=12,
                cost_estimate=450000.00,
                actual_cost=465000.00,
                location_start=0.0,
                location_end=250000.0
            ),
            
            # Foundation Phase
            Activity(
                project_id=project1.id,
                name="Foundation Formwork and Rebar",
                description="Install foundation forms and reinforcement steel",
                activity_type=ActivityType.FOUNDATION,
                duration=28,
                start_date=date(2024, 3, 26),
                end_date=date(2024, 4, 22),
                progress=100,
                quantity=1200,
                unit="tons",
                production_rate=43,
                resource_crew_size=16,
                cost_estimate=280000.00,
                actual_cost=275000.00,
                location_start=0.0,
                location_end=250000.0
            ),
            Activity(
                project_id=project1.id,
                name="Foundation Concrete Pour",
                description="Pour foundation concrete and footings",
                activity_type=ActivityType.FOUNDATION,
                duration=14,
                start_date=date(2024, 4, 23),
                end_date=date(2024, 5, 6),
                progress=100,
                quantity=2800,
                unit="cubic yards",
                production_rate=200,
                resource_crew_size=20,
                cost_estimate=420000.00,
                actual_cost=410000.00,
                location_start=0.0,
                location_end=250000.0
            ),
            
            # Structural Phase
            Activity(
                project_id=project1.id,
                name="Structural Steel Erection",
                description="Erect structural steel frame for floors 1-5",
                activity_type=ActivityType.FRAMING,
                duration=42,
                start_date=date(2024, 5, 7),
                end_date=date(2024, 6, 17),
                progress=85,
                quantity=850,
                unit="tons",
                production_rate=20,
                resource_crew_size=14,
                cost_estimate=680000.00,
                actual_cost=590000.00,
                location_start=0.0,
                location_end=62500.0
            ),
            Activity(
                project_id=project1.id,
                name="Floor Deck Installation",
                description="Install metal decking and concrete floors 1-5",
                activity_type=ActivityType.FRAMING,
                duration=35,
                start_date=date(2024, 6, 18),
                end_date=date(2024, 7, 22),
                progress=70,
                quantity=62500,
                unit="sq ft",
                production_rate=1785,
                resource_crew_size=12,
                cost_estimate=375000.00,
                actual_cost=320000.00,
                location_start=0.0,
                location_end=62500.0
            ),
            
            # MEP Rough-in Phase
            Activity(
                project_id=project1.id,
                name="Electrical Rough-in Floors 1-5",
                description="Install electrical conduit, wiring, and panels",
                activity_type=ActivityType.ELECTRICAL,
                duration=28,
                start_date=date(2024, 7, 23),
                end_date=date(2024, 8, 19),
                progress=45,
                quantity=62500,
                unit="sq ft",
                production_rate=2232,
                resource_crew_size=8,
                cost_estimate=285000.00,
                actual_cost=180000.00,
                location_start=0.0,
                location_end=62500.0
            ),
            Activity(
                project_id=project1.id,
                name="Plumbing Rough-in Floors 1-5",
                description="Install plumbing pipes, fixtures rough-in",
                activity_type=ActivityType.PLUMBING,
                duration=25,
                start_date=date(2024, 8, 20),
                end_date=date(2024, 9, 13),
                progress=35,
                quantity=62500,
                unit="sq ft",
                production_rate=2500,
                resource_crew_size=6,
                cost_estimate=195000.00,
                actual_cost=125000.00,
                location_start=0.0,
                location_end=62500.0
            ),
            Activity(
                project_id=project1.id,
                name="HVAC Rough-in Floors 1-5",
                description="Install ductwork and HVAC equipment",
                activity_type=ActivityType.HVAC,
                duration=32,
                start_date=date(2024, 9, 14),
                end_date=date(2024, 10, 15),
                progress=25,
                quantity=62500,
                unit="sq ft",
                production_rate=1953,
                resource_crew_size=10,
                cost_estimate=385000.00,
                actual_cost=225000.00,
                location_start=0.0,
                location_end=62500.0
            )
        ]
        
        # Activities for Project 2 (Residential)
        residential_activities = [
            Activity(
                project_id=project2.id,
                name="Site Preparation",
                description="Site clearing and utilities preparation",
                activity_type=ActivityType.SITEWORK,
                duration=18,
                start_date=date(2024, 3, 1),
                end_date=date(2024, 3, 18),
                progress=100,
                quantity=180000,
                unit="sq ft",
                production_rate=10000,
                resource_crew_size=6,
                cost_estimate=95000.00,
                actual_cost=92000.00,
                location_start=0.0,
                location_end=180000.0
            ),
            Activity(
                project_id=project2.id,
                name="Foundation Work",
                description="Pour foundations for residential buildings",
                activity_type=ActivityType.FOUNDATION,
                duration=35,
                start_date=date(2024, 3, 19),
                end_date=date(2024, 4, 22),
                progress=100,
                quantity=1800,
                unit="cubic yards",
                production_rate=51,
                resource_crew_size=14,
                cost_estimate=285000.00,
                actual_cost=278000.00,
                location_start=0.0,
                location_end=180000.0
            ),
            Activity(
                project_id=project2.id,
                name="Framing - Buildings A & B",
                description="Wood frame construction for residential units",
                activity_type=ActivityType.FRAMING,
                duration=56,
                start_date=date(2024, 4, 23),
                end_date=date(2024, 6, 17),
                progress=75,
                quantity=90000,
                unit="sq ft",
                production_rate=1607,
                resource_crew_size=18,
                cost_estimate=485000.00,
                actual_cost=420000.00,
                location_start=0.0,
                location_end=90000.0
            ),
            Activity(
                project_id=project2.id,
                name="Roofing Installation",
                description="Install roofing systems on completed buildings",
                activity_type=ActivityType.ROOFING,
                duration=28,
                start_date=date(2024, 6, 18),
                end_date=date(2024, 7, 15),
                progress=60,
                quantity=22500,
                unit="sq ft",
                production_rate=803,
                resource_crew_size=8,
                cost_estimate=165000.00,
                actual_cost=135000.00,
                location_start=0.0,
                location_end=90000.0
            )
        ]
        
        # Activities for Project 3 (Bridge)
        bridge_activities = [
            Activity(
                project_id=project3.id,
                name="Environmental Impact Assessment",
                description="Complete environmental review and permitting",
                activity_type=ActivityType.OTHER,
                duration=45,
                start_date=date(2024, 6, 1),
                end_date=date(2024, 7, 15),
                progress=100,
                quantity=1,
                unit="project",
                production_rate=0.022,
                resource_crew_size=3,
                cost_estimate=125000.00,
                actual_cost=128000.00,
                location_start=0.0,
                location_end=1200.0
            ),
            Activity(
                project_id=project3.id,
                name="Bridge Demolition",
                description="Demolish existing bridge structure",
                activity_type=ActivityType.SITEWORK,
                duration=21,
                start_date=date(2024, 7, 16),
                end_date=date(2024, 8, 5),
                progress=80,
                quantity=850,
                unit="tons",
                production_rate=40,
                resource_crew_size=12,
                cost_estimate=385000.00,
                actual_cost=320000.00,
                location_start=0.0,
                location_end=1200.0
            ),
            Activity(
                project_id=project3.id,
                name="Foundation Piers",
                description="Install deep foundation piers for new bridge",
                activity_type=ActivityType.FOUNDATION,
                duration=42,
                start_date=date(2024, 8, 6),
                end_date=date(2024, 9, 16),
                progress=45,
                quantity=24,
                unit="piers",
                production_rate=0.57,
                resource_crew_size=16,
                cost_estimate=1250000.00,
                actual_cost=750000.00,
                location_start=0.0,
                location_end=1200.0
            )
        ]
        
        # Add all activities
        all_activities = office_activities + residential_activities + bridge_activities
        db.session.add_all(all_activities)
        db.session.flush()
        
        # Create Dependencies for Office Building
        office_deps = [
            # Site work sequence
            Dependency(
                predecessor_id=office_activities[0].id,  # Survey
                successor_id=office_activities[1].id,    # Clearing
                dependency_type='FS',
                lag_days=0
            ),
            Dependency(
                predecessor_id=office_activities[1].id,  # Clearing
                successor_id=office_activities[2].id,    # Excavation
                dependency_type='FS',
                lag_days=0
            ),
            # Foundation sequence
            Dependency(
                predecessor_id=office_activities[2].id,  # Excavation
                successor_id=office_activities[3].id,    # Foundation Formwork
                dependency_type='FS',
                lag_days=0
            ),
            Dependency(
                predecessor_id=office_activities[3].id,  # Foundation Formwork
                successor_id=office_activities[4].id,    # Foundation Pour
                dependency_type='FS',
                lag_days=0
            ),
            # Structural sequence
            Dependency(
                predecessor_id=office_activities[4].id,  # Foundation Pour
                successor_id=office_activities[5].id,    # Steel Erection
                dependency_type='FS',
                lag_days=7
            ),
            Dependency(
                predecessor_id=office_activities[5].id,  # Steel Erection
                successor_id=office_activities[6].id,    # Floor Deck
                dependency_type='SS',
                lag_days=14
            ),
            # MEP sequence
            Dependency(
                predecessor_id=office_activities[6].id,  # Floor Deck
                successor_id=office_activities[7].id,    # Electrical
                dependency_type='SS',
                lag_days=7
            ),
            Dependency(
                predecessor_id=office_activities[7].id,  # Electrical
                successor_id=office_activities[8].id,    # Plumbing
                dependency_type='SS',
                lag_days=5
            ),
            Dependency(
                predecessor_id=office_activities[8].id,  # Plumbing
                successor_id=office_activities[9].id,    # HVAC
                dependency_type='SS',
                lag_days=3
            )
        ]
        
        # Dependencies for Residential Project
        residential_deps = [
            Dependency(
                predecessor_id=residential_activities[0].id,  # Site Prep
                successor_id=residential_activities[1].id,    # Foundation
                dependency_type='FS',
                lag_days=0
            ),
            Dependency(
                predecessor_id=residential_activities[1].id,  # Foundation
                successor_id=residential_activities[2].id,    # Framing
                dependency_type='FS',
                lag_days=5
            ),
            Dependency(
                predecessor_id=residential_activities[2].id,  # Framing
                successor_id=residential_activities[3].id,    # Roofing
                dependency_type='SS',
                lag_days=21
            )
        ]
        
        # Dependencies for Bridge Project
        bridge_deps = [
            Dependency(
                predecessor_id=bridge_activities[0].id,  # Environmental
                successor_id=bridge_activities[1].id,    # Demolition
                dependency_type='FS',
                lag_days=0
            ),
            Dependency(
                predecessor_id=bridge_activities[1].id,  # Demolition
                successor_id=bridge_activities[2].id,    # Foundation Piers
                dependency_type='FS',
                lag_days=0
            )
        ]
        
        all_dependencies = office_deps + residential_deps + bridge_deps
        db.session.add_all(all_dependencies)
        
        # Create Schedules
        schedules = [
            Schedule(
                project_id=project1.id,
                name="Master Schedule - Office Complex",
                schedule_type=ScheduleType.GANTT,
                is_baseline=True,
                is_active=True
            ),
            Schedule(
                project_id=project1.id,
                name="Current Working Schedule",
                schedule_type=ScheduleType.GANTT,
                is_baseline=False,
                is_active=True
            ),
            Schedule(
                project_id=project2.id,
                name="Residential Linear Schedule",
                schedule_type=ScheduleType.LINEAR,
                is_baseline=True,
                is_active=True
            ),
            Schedule(
                project_id=project3.id,
                name="Bridge Construction Schedule",
                schedule_type=ScheduleType.GANTT,
                is_baseline=True,
                is_active=True
            )
        ]
        db.session.add_all(schedules)
        
        # Create Sample Schedule Metrics
        metrics = [
            ScheduleMetrics(
                project_id=project1.id,
                metric_date=date.today(),
                schedule_performance_index=0.92,
                cost_performance_index=1.05,
                planned_value=8500000.00,
                earned_value=7820000.00,
                actual_cost=7450000.00,
                activities_on_schedule=6,
                activities_delayed=4,
                critical_path_variance=-5.2,
                resource_utilization=87.5
            ),
            ScheduleMetrics(
                project_id=project2.id,
                metric_date=date.today(),
                schedule_performance_index=1.08,
                cost_performance_index=1.12,
                planned_value=1030000.00,
                earned_value=1112400.00,
                actual_cost=993200.00,
                activities_on_schedule=3,
                activities_delayed=1,
                critical_path_variance=2.8,
                resource_utilization=92.3
            ),
            ScheduleMetrics(
                project_id=project3.id,
                metric_date=date.today(),
                schedule_performance_index=0.85,
                cost_performance_index=0.95,
                planned_value=1760000.00,
                earned_value=1496000.00,
                actual_cost=1575789.00,
                activities_on_schedule=1,
                activities_delayed=2,
                critical_path_variance=-8.5,
                resource_utilization=78.9
            )
        ]
        db.session.add_all(metrics)
        
        db.session.commit()
        print("Test data loaded successfully!")
        print(f"Created {len([project1, project2, project3])} projects")
        print(f"Created {len(all_activities)} activities")
        print(f"Created {len(all_dependencies)} dependencies")
        print(f"Created {len(schedules)} schedules")
        print(f"Created {len(metrics)} schedule metrics")

if __name__ == "__main__":
    load_test_data()