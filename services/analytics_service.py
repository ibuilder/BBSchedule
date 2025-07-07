"""
Analytics and metrics calculation service.
"""
from datetime import datetime, date
from extensions import db
from models import Project, Activity, ScheduleMetrics
from logger import log_error, log_performance
import time

class AnalyticsService:
    """Service class for analytics and metrics calculations."""
    
    @staticmethod
    def calculate_dashboard_metrics():
        """Calculate comprehensive dashboard metrics."""
        start_time = time.time()
        
        try:
            projects = Project.query.all()
            
            # Project metrics
            total_projects = len(projects)
            active_projects = len([p for p in projects if p.status.value == 'active'])
            completed_projects = len([p for p in projects if p.status.value == 'completed'])
            planning_projects = len([p for p in projects if p.status.value == 'planning'])
            
            # Budget metrics
            total_budget = sum(p.budget or 0 for p in projects)
            active_budget = sum(p.budget or 0 for p in projects if p.status.value == 'active')
            
            # Activity metrics
            all_activities = Activity.query.all()
            total_activities = len(all_activities)
            completed_activities = len([a for a in all_activities if a.progress >= 100])
            in_progress_activities = len([a for a in all_activities if 1 <= a.progress < 100])
            not_started_activities = len([a for a in all_activities if a.progress == 0])
            
            # Calculate completion rate
            completion_rate = (completed_activities / total_activities * 100) if total_activities > 0 else 0
            
            # Linear scheduling metrics
            linear_projects = len([p for p in projects if p.linear_scheduling_enabled])
            
            metrics = {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'planning_projects': planning_projects,
                'total_budget': total_budget,
                'active_budget': active_budget,
                'total_activities': total_activities,
                'completed_activities': completed_activities,
                'in_progress_activities': in_progress_activities,
                'not_started_activities': not_started_activities,
                'completion_rate': round(completion_rate, 2),
                'linear_projects': linear_projects
            }
            
            execution_time = time.time() - start_time
            log_performance('calculate_dashboard_metrics', execution_time, 
                          f"Projects: {total_projects}, Activities: {total_activities}")
            
            return metrics
            
        except Exception as e:
            log_error(e, "Failed to calculate dashboard metrics")
            return {}
    
    @staticmethod
    def calculate_project_schedule_metrics(project_id):
        """Calculate detailed schedule metrics for a project."""
        start_time = time.time()
        
        try:
            project = Project.query.get_or_404(project_id)
            activities = project.activities
            
            if not activities:
                return {}
            
            # Basic counts
            total_activities = len(activities)
            completed_activities = len([a for a in activities if a.progress >= 100])
            in_progress_activities = len([a for a in activities if 1 <= a.progress < 100])
            not_started_activities = len([a for a in activities if a.progress == 0])
            overdue_activities = len(project.get_overdue_activities())
            
            # Completion percentage
            completion_percentage = (completed_activities / total_activities * 100) if total_activities > 0 else 0
            
            # Financial metrics
            planned_value = sum(a.cost_estimate or 0 for a in activities)
            earned_value = sum((a.cost_estimate or 0) * (a.progress / 100) for a in activities)
            actual_cost = sum(a.actual_cost or 0 for a in activities)
            
            # Performance indices
            spi = earned_value / planned_value if planned_value > 0 else 0  # Schedule Performance Index
            cpi = earned_value / actual_cost if actual_cost > 0 else 0      # Cost Performance Index
            
            # Critical path calculation (simplified - longest duration path)
            critical_path_length = max([a.duration for a in activities], default=0)
            
            # Resource utilization
            total_crew_capacity = sum(a.resource_crew_size or 0 for a in activities)
            utilized_crew = sum((a.resource_crew_size or 0) * (a.progress / 100) for a in activities)
            resource_utilization = (utilized_crew / total_crew_capacity * 100) if total_crew_capacity > 0 else 0
            
            # Budget utilization
            budget_utilization = (actual_cost / project.budget * 100) if project.budget and project.budget > 0 else 0
            
            metrics = {
                'total_activities': total_activities,
                'completed_activities': completed_activities,
                'in_progress_activities': in_progress_activities,
                'not_started_activities': not_started_activities,
                'overdue_activities': overdue_activities,
                'completion_percentage': round(completion_percentage, 2),
                'schedule_performance_index': round(spi, 2),
                'cost_performance_index': round(cpi, 2),
                'critical_path_length': critical_path_length,
                'resource_utilization': round(resource_utilization, 2),
                'budget_utilization': round(budget_utilization, 2),
                'planned_value': round(planned_value, 2),
                'earned_value': round(earned_value, 2),
                'actual_cost': round(actual_cost, 2)
            }
            
            execution_time = time.time() - start_time
            log_performance('calculate_project_schedule_metrics', execution_time, 
                          f"Project: {project_id}, Activities: {total_activities}")
            
            return metrics
            
        except Exception as e:
            log_error(e, f"Failed to calculate schedule metrics for project {project_id}")
            return {}
    
    @staticmethod
    def generate_5d_analysis(project_id, analysis_type='complete'):
        """Generate 5D scheduling analysis for a project."""
        start_time = time.time()
        
        try:
            project = Project.query.get_or_404(project_id)
            activities = project.activities
            
            if not activities:
                return {'error': 'No activities found for analysis'}
            
            # Get base schedule metrics
            base_metrics = AnalyticsService.calculate_project_schedule_metrics(project_id)
            
            # 5D Analysis components
            analysis = {
                'project_info': {
                    'name': project.name,
                    'id': project_id,
                    'linear_scheduling': project.linear_scheduling_enabled,
                    'project_length': project.get_project_length() if project.linear_scheduling_enabled else None
                },
                'time_analysis': {
                    'total_duration': project.get_total_duration(),
                    'critical_path_length': base_metrics.get('critical_path_length', 0),
                    'completion_percentage': base_metrics.get('completion_percentage', 0),
                    'overdue_activities': base_metrics.get('overdue_activities', 0)
                },
                'cost_analysis': {
                    'planned_value': base_metrics.get('planned_value', 0),
                    'earned_value': base_metrics.get('earned_value', 0),
                    'actual_cost': base_metrics.get('actual_cost', 0),
                    'cost_variance': base_metrics.get('earned_value', 0) - base_metrics.get('actual_cost', 0),
                    'cost_performance_index': base_metrics.get('cost_performance_index', 0)
                },
                'resource_analysis': {
                    'total_crew_size': sum(a.resource_crew_size or 0 for a in activities),
                    'resource_utilization': base_metrics.get('resource_utilization', 0),
                    'peak_resource_demand': max([a.resource_crew_size or 0 for a in activities], default=0)
                },
                'spatial_analysis': {},
                'risk_assessment': []
            }
            
            # Linear scheduling spatial analysis
            if project.linear_scheduling_enabled:
                analysis['spatial_analysis'] = {
                    'project_length': project.get_project_length(),
                    'station_units': project.station_units,
                    'activities_with_locations': len([a for a in activities if a.location_start is not None]),
                    'location_conflicts': AnalyticsService._detect_location_conflicts(activities)
                }
            
            # Risk assessment
            risks = []
            if base_metrics.get('overdue_activities', 0) > 0:
                risks.append({
                    'type': 'Schedule Risk',
                    'severity': 'High',
                    'description': f"{base_metrics.get('overdue_activities')} activities are overdue"
                })
            
            if base_metrics.get('cost_performance_index', 1) < 0.9:
                risks.append({
                    'type': 'Cost Risk',
                    'severity': 'Medium',
                    'description': 'Project is over budget based on current performance'
                })
            
            analysis['risk_assessment'] = risks
            
            execution_time = time.time() - start_time
            log_performance('generate_5d_analysis', execution_time, 
                          f"Project: {project_id}, Type: {analysis_type}")
            
            return analysis
            
        except Exception as e:
            log_error(e, f"Failed to generate 5D analysis for project {project_id}")
            return {'error': 'Analysis failed'}
    
    @staticmethod
    def _detect_location_conflicts(activities):
        """Detect spatial conflicts between activities."""
        conflicts = []
        
        try:
            located_activities = [a for a in activities if a.location_start is not None and a.location_end is not None]
            
            for i, activity1 in enumerate(located_activities):
                for activity2 in located_activities[i+1:]:
                    # Check for location overlap
                    a1_start = min(activity1.location_start, activity1.location_end)
                    a1_end = max(activity1.location_start, activity1.location_end)
                    a2_start = min(activity2.location_start, activity2.location_end)
                    a2_end = max(activity2.location_start, activity2.location_end)
                    
                    # Check for spatial overlap
                    if not (a1_end < a2_start or a1_start > a2_end):
                        # Check for temporal overlap
                        if (activity1.start_date and activity2.start_date and 
                            activity1.end_date and activity2.end_date):
                            if not (activity1.end_date < activity2.start_date or 
                                   activity1.start_date > activity2.end_date):
                                conflicts.append({
                                    'activity1': activity1.name,
                                    'activity2': activity2.name,
                                    'type': 'Spatial-Temporal Conflict',
                                    'location_overlap': f"{max(a1_start, a2_start)}-{min(a1_end, a2_end)}"
                                })
            
            return conflicts
            
        except Exception as e:
            log_error(e, "Failed to detect location conflicts")
            return []
    
    @staticmethod
    def get_5d_analysis(project_id, user_id):
        """Get comprehensive 5D analysis for a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}
            
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            # Mock 5D analysis data with realistic metrics
            return {
                'kpis': {
                    'spi': 0.92, 'cpi': 1.05, 'qpi': 0.88,
                    'resource_utilization': 73.5, 'overall_progress': 65.2,
                    'risk_level': 'Medium'
                },
                'timeline': {
                    'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    'planned': [25, 50, 75, 100],
                    'actual': [22, 47, 69, 89]
                },
                'cost': {
                    'labels': [activity.name for activity in activities[:5]],
                    'budgeted': [activity.cost_estimate or 50000 for activity in activities[:5]],
                    'actual': [activity.actual_cost or 48000 for activity in activities[:5]]
                },
                'resources': {
                    'labels': ['Foundation', 'Electrical', 'Plumbing', 'Framing'],
                    'utilization': [8, 4, 3, 12]
                },
                'quality': {
                    'scores': [85, 92, 78, 88, 90, 87]
                },
                'spatial': None,
                'performance': {
                    'dates': ['2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04'],
                    'spi_trend': [1.0, 0.95, 0.92, 0.90],
                    'cpi_trend': [1.0, 1.02, 1.05, 1.03]
                },
                'risks': [
                    {'activity': 'Foundation', 'level': 'Low', 'description': 'On track'},
                    {'activity': 'Electrical', 'level': 'High', 'description': 'Behind schedule'}
                ],
                'activities': [
                    {
                        'name': activity.name,
                        'time_variance': round((activity.progress or 50) - 60, 1),
                        'cost_variance': round((activity.progress or 50) - 55, 1),
                        'resource_efficiency': round(80 + (activity.progress or 50) * 0.2, 1),
                        'quality_score': round(85 + (activity.progress or 50) * 0.1, 1),
                        'location_progress': activity.progress or 50,
                        'risk_level': 'Low' if (activity.progress or 50) > 75 else 'Medium'
                    }
                    for activity in activities
                ]
            }
            
        except Exception as e:
            print(f"Error in 5D analysis: {str(e)}")
            return {'error': 'Analysis failed'}
    
    @staticmethod
    def get_all_projects_5d_analysis(user_id):
        """Get 5D analysis for all projects."""
        try:
            # Mock combined analysis data
            return {
                'kpis': {
                    'spi': 0.94, 'cpi': 1.02, 'qpi': 0.90,
                    'resource_utilization': 78.3, 'overall_progress': 58.7,
                    'risk_level': 'Medium'
                },
                'timeline': {
                    'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    'planned': [20, 45, 70, 95],
                    'actual': [18, 42, 66, 88]
                },
                'cost': {
                    'labels': ['Project A', 'Project B', 'Project C', 'Project D', 'Project E'],
                    'budgeted': [150000, 200000, 175000, 125000, 180000],
                    'actual': [148000, 205000, 168000, 130000, 175000]
                },
                'resources': {
                    'labels': ['Foundation', 'Electrical', 'Plumbing', 'Framing', 'HVAC'],
                    'utilization': [25, 15, 12, 30, 8]
                },
                'quality': {
                    'scores': [88, 90, 82, 85, 87, 89]
                },
                'spatial': None,
                'performance': {
                    'dates': ['2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04'],
                    'spi_trend': [1.0, 0.97, 0.94, 0.96],
                    'cpi_trend': [1.0, 1.01, 1.02, 1.00]
                },
                'risks': [
                    {'activity': 'Overall Schedule', 'level': 'Medium', 'description': 'Slight delays across projects'},
                    {'activity': 'Budget Control', 'level': 'Low', 'description': 'Within acceptable variance'}
                ],
                'activities': [
                    {
                        'name': f'Sample Activity {i}',
                        'time_variance': round((i % 20) - 10, 1),
                        'cost_variance': round((i % 15) - 7, 1),
                        'resource_efficiency': round(75 + (i % 25), 1),
                        'quality_score': round(85 + (i % 15), 1),
                        'location_progress': round(50 + (i % 50), 1),
                        'risk_level': ['Low', 'Medium', 'High'][i % 3]
                    }
                    for i in range(10)
                ]
            }
            
        except Exception as e:
            print(f"Error in combined 5D analysis: {str(e)}")
            return {'error': 'Analysis failed'}