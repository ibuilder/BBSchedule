"""
Enhanced scheduling service for Gantt charts, critical path analysis, and resource optimization.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, deque
import json

from extensions import db
from models import Project, Activity, Dependency, ActivityType
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

class SchedulingService:
    """Advanced scheduling operations for construction projects."""
    
    @staticmethod
    def calculate_critical_path(project_id: int) -> Dict[str, Any]:
        """
        Calculate critical path using Critical Path Method (CPM).
        Returns critical path data with forward and backward pass calculations.
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}
            
            activities = Activity.query.filter_by(project_id=project_id).all()
            dependencies = Dependency.query.filter(
                Dependency.predecessor_id.in_([a.id for a in activities]),
                Dependency.successor_id.in_([a.id for a in activities])
            ).all()
            
            # Build network graph
            graph = SchedulingService._build_network_graph(activities, dependencies)
            
            # Forward pass - calculate Early Start (ES) and Early Finish (EF)
            forward_pass = SchedulingService._forward_pass(graph, activities)
            
            # Backward pass - calculate Late Start (LS) and Late Finish (LF)
            backward_pass = SchedulingService._backward_pass(graph, activities, forward_pass)
            
            # Calculate total float and identify critical path
            critical_path_data = SchedulingService._calculate_critical_path(
                activities, forward_pass, backward_pass
            )
            
            return {
                'project_id': project_id,
                'project_name': project.name,
                'critical_path': critical_path_data['critical_path'],
                'critical_activities': critical_path_data['critical_activities'],
                'project_duration': critical_path_data['project_duration'],
                'total_float': critical_path_data['total_float'],
                'schedule_performance': SchedulingService._calculate_schedule_performance(
                    activities, critical_path_data
                )
            }
            
        except Exception as e:
            logger.error(f"Critical path calculation error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _build_network_graph(activities: List[Activity], dependencies: List[Dependency]) -> Dict[int, Dict]:
        """Build network graph for CPM calculations."""
        graph = {}
        
        # Initialize nodes
        for activity in activities:
            graph[activity.id] = {
                'activity': activity,
                'predecessors': [],
                'successors': [],
                'duration': activity.duration or 0
            }
        
        # Add dependencies
        for dep in dependencies:
            if dep.predecessor_id in graph and dep.successor_id in graph:
                graph[dep.predecessor_id]['successors'].append(dep.successor_id)
                graph[dep.successor_id]['predecessors'].append(dep.predecessor_id)
        
        return graph
    
    @staticmethod
    def _forward_pass(graph: Dict[int, Dict], activities: List[Activity]) -> Dict[int, Dict]:
        """Calculate Early Start and Early Finish times."""
        forward_pass = {}
        
        # Initialize all activities
        for activity in activities:
            forward_pass[activity.id] = {
                'early_start': 0,
                'early_finish': 0,
                'calculated': False
            }
        
        # Topological sort and calculate ES/EF
        def calculate_forward(activity_id):
            if forward_pass[activity_id]['calculated']:
                return
                
            node = graph[activity_id]
            max_early_finish = 0
            
            # Calculate based on predecessors
            for pred_id in node['predecessors']:
                if not forward_pass[pred_id]['calculated']:
                    calculate_forward(pred_id)
                max_early_finish = max(max_early_finish, forward_pass[pred_id]['early_finish'])
            
            # Set early start and finish
            forward_pass[activity_id]['early_start'] = max_early_finish
            forward_pass[activity_id]['early_finish'] = max_early_finish + node['duration']
            forward_pass[activity_id]['calculated'] = True
        
        # Calculate for all activities
        for activity in activities:
            calculate_forward(activity.id)
        
        return forward_pass
    
    @staticmethod
    def _backward_pass(graph: Dict[int, Dict], activities: List[Activity], forward_pass: Dict[int, Dict]) -> Dict[int, Dict]:
        """Calculate Late Start and Late Finish times."""
        backward_pass = {}
        
        # Find project end time
        project_end = max(forward_pass[a.id]['early_finish'] for a in activities)
        
        # Initialize all activities
        for activity in activities:
            backward_pass[activity.id] = {
                'late_start': project_end,
                'late_finish': project_end,
                'calculated': False
            }
        
        # Calculate LS/LF in reverse order
        def calculate_backward(activity_id):
            if backward_pass[activity_id]['calculated']:
                return
                
            node = graph[activity_id]
            min_late_start = project_end
            
            # If no successors, this is an end activity
            if not node['successors']:
                backward_pass[activity_id]['late_finish'] = forward_pass[activity_id]['early_finish']
            else:
                # Calculate based on successors
                for succ_id in node['successors']:
                    if not backward_pass[succ_id]['calculated']:
                        calculate_backward(succ_id)
                    min_late_start = min(min_late_start, backward_pass[succ_id]['late_start'])
                backward_pass[activity_id]['late_finish'] = min_late_start
            
            # Set late start
            backward_pass[activity_id]['late_start'] = backward_pass[activity_id]['late_finish'] - node['duration']
            backward_pass[activity_id]['calculated'] = True
        
        # Calculate for all activities
        for activity in activities:
            calculate_backward(activity.id)
        
        return backward_pass
    
    @staticmethod
    def _calculate_critical_path(activities: List[Activity], forward_pass: Dict[int, Dict], backward_pass: Dict[int, Dict]) -> Dict[str, Any]:
        """Identify critical path and calculate float values."""
        critical_activities = []
        total_float = {}
        
        for activity in activities:
            # Calculate total float
            total_float[activity.id] = backward_pass[activity.id]['late_start'] - forward_pass[activity.id]['early_start']
            
            # Critical activities have zero float
            if total_float[activity.id] == 0:
                critical_activities.append({
                    'id': activity.id,
                    'name': activity.name,
                    'duration': activity.duration,
                    'early_start': forward_pass[activity.id]['early_start'],
                    'early_finish': forward_pass[activity.id]['early_finish'],
                    'late_start': backward_pass[activity.id]['late_start'],
                    'late_finish': backward_pass[activity.id]['late_finish']
                })
        
        # Find critical path sequence
        critical_path = SchedulingService._find_critical_path_sequence(critical_activities)
        
        # Calculate project duration
        project_duration = max(forward_pass[a.id]['early_finish'] for a in activities) if activities else 0
        
        return {
            'critical_path': critical_path,
            'critical_activities': critical_activities,
            'project_duration': project_duration,
            'total_float': total_float
        }
    
    @staticmethod
    def _find_critical_path_sequence(critical_activities: List[Dict]) -> List[int]:
        """Find the longest path through critical activities."""
        if not critical_activities:
            return []
        
        # Sort by early start time
        critical_activities.sort(key=lambda x: x['early_start'])
        return [activity['id'] for activity in critical_activities]
    
    @staticmethod
    def _calculate_schedule_performance(activities: List[Activity], critical_path_data: Dict) -> Dict[str, Any]:
        """Calculate schedule performance metrics."""
        if not activities:
            return {'schedule_performance_index': 0, 'schedule_variance': 0}
        
        total_planned_duration = sum(a.duration or 0 for a in activities)
        total_actual_duration = sum(a.duration or 0 for a in activities if a.progress == 100)
        
        # Schedule Performance Index (SPI)
        spi = (total_actual_duration / total_planned_duration) if total_planned_duration > 0 else 0
        
        # Schedule Variance
        schedule_variance = total_actual_duration - total_planned_duration
        
        return {
            'schedule_performance_index': round(spi, 2),
            'schedule_variance': schedule_variance,
            'critical_path_duration': critical_path_data.get('project_duration', 0),
            'total_activities': len(activities),
            'critical_activities_count': len(critical_path_data.get('critical_activities', []))
        }
    
    @staticmethod
    def get_gantt_chart_data(project_id: int) -> Dict[str, Any]:
        """
        Generate Gantt chart data for visualization.
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}
            
            activities = Activity.query.filter_by(project_id=project_id).all()
            dependencies = Dependency.query.filter(
                Dependency.predecessor_id.in_([a.id for a in activities]),
                Dependency.successor_id.in_([a.id for a in activities])
            ).all()
            
            # Get critical path data
            critical_path_data = SchedulingService.calculate_critical_path(project_id)
            critical_activity_ids = [a['id'] for a in critical_path_data.get('critical_activities', [])]
            
            # Build Gantt chart data structure
            gantt_data = []
            for activity in activities:
                # Calculate dates
                start_date = activity.start_date or datetime.now()
                end_date = activity.end_date or (start_date + timedelta(days=activity.duration or 1))
                
                gantt_data.append({
                    'id': activity.id,
                    'name': activity.name,
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'duration': activity.duration or 0,
                    'progress': activity.progress or 0,
                    'type': activity.activity_type.value if activity.activity_type else 'task',
                    'is_critical': activity.id in critical_activity_ids,
                    'location_start': activity.location_start,
                    'location_end': activity.location_end,
                    'dependencies': [
                        dep.predecessor_id for dep in dependencies 
                        if dep.successor_id == activity.id
                    ]
                })
            
            return {
                'project_id': project_id,
                'project_name': project.name,
                'gantt_data': gantt_data,
                'critical_path': critical_path_data,
                'project_start': project.start_date.isoformat() if project.start_date else None,
                'project_end': project.end_date.isoformat() if project.end_date else None
            }
            
        except Exception as e:
            logger.error(f"Gantt chart data generation error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def detect_resource_conflicts(project_id: int) -> Dict[str, Any]:
        """
        Detect resource conflicts and overlapping activities.
        """
        try:
            activities = Activity.query.filter_by(project_id=project_id).all()
            conflicts = []
            
            # Group activities by location and time
            for i, activity1 in enumerate(activities):
                for j, activity2 in enumerate(activities[i+1:], i+1):
                    conflict = SchedulingService._check_activity_conflict(activity1, activity2)
                    if conflict:
                        conflicts.append(conflict)
            
            # Resource utilization analysis
            resource_utilization = SchedulingService._calculate_resource_utilization(activities)
            
            return {
                'project_id': project_id,
                'conflicts': conflicts,
                'resource_utilization': resource_utilization,
                'recommendations': SchedulingService._generate_resource_recommendations(conflicts)
            }
            
        except Exception as e:
            logger.error(f"Resource conflict detection error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _check_activity_conflict(activity1: Activity, activity2: Activity) -> Optional[Dict]:
        """Check if two activities conflict in time and location."""
        # Check time overlap
        if not (activity1.start_date and activity1.end_date and 
                activity2.start_date and activity2.end_date):
            return None
            
        time_overlap = (activity1.start_date <= activity2.end_date and 
                       activity2.start_date <= activity1.end_date)
        
        if not time_overlap:
            return None
        
        # Check location overlap
        if (activity1.location_start is not None and activity1.location_end is not None and
            activity2.location_start is not None and activity2.location_end is not None):
            
            location_overlap = (activity1.location_start <= activity2.location_end and 
                              activity2.location_start <= activity1.location_end)
            
            if location_overlap:
                return {
                    'activity1_id': activity1.id,
                    'activity1_name': activity1.name,
                    'activity2_id': activity2.id,
                    'activity2_name': activity2.name,
                    'conflict_type': 'time_location',
                    'severity': 'high',
                    'time_overlap_days': (min(activity1.end_date, activity2.end_date) - 
                                         max(activity1.start_date, activity2.start_date)).days,
                    'location_overlap': {
                        'start': max(activity1.location_start, activity2.location_start),
                        'end': min(activity1.location_end, activity2.location_end)
                    }
                }
        
        return None
    
    @staticmethod
    def _calculate_resource_utilization(activities: List[Activity]) -> Dict[str, Any]:
        """Calculate resource utilization metrics."""
        daily_utilization = defaultdict(int)
        
        for activity in activities:
            if activity.start_date and activity.end_date and activity.resource_crew_size:
                current_date = activity.start_date
                while current_date <= activity.end_date:
                    daily_utilization[current_date.isoformat()] += activity.resource_crew_size
                    current_date += timedelta(days=1)
        
        # Calculate statistics
        utilization_values = list(daily_utilization.values()) if daily_utilization else [0]
        
        return {
            'peak_utilization': max(utilization_values),
            'average_utilization': sum(utilization_values) / len(utilization_values),
            'utilization_variance': SchedulingService._calculate_variance(utilization_values),
            'daily_utilization': dict(daily_utilization)
        }
    
    @staticmethod
    def _calculate_variance(values: List[int]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    @staticmethod
    def _generate_resource_recommendations(conflicts: List[Dict]) -> List[Dict]:
        """Generate recommendations for resolving resource conflicts."""
        recommendations = []
        
        for conflict in conflicts:
            if conflict['conflict_type'] == 'time_location':
                recommendations.append({
                    'type': 'schedule_adjustment',
                    'priority': 'high',
                    'description': f"Consider rescheduling {conflict['activity1_name']} or {conflict['activity2_name']} to avoid overlap",
                    'activities': [conflict['activity1_id'], conflict['activity2_id']]
                })
        
        return recommendations
    
    @staticmethod
    def get_timeline_view(project_id: int, view_type: str = 'weekly') -> Dict[str, Any]:
        """
        Generate timeline view data for different periods.
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}
            
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            # Determine date range based on view type
            if view_type == 'weekly':
                period_days = 7
            elif view_type == 'monthly':
                period_days = 30
            elif view_type == 'quarterly':
                period_days = 90
            else:
                period_days = 7
            
            # Build timeline data
            timeline_data = SchedulingService._build_timeline_data(activities, period_days)
            
            return {
                'project_id': project_id,
                'view_type': view_type,
                'timeline_data': timeline_data,
                'summary': SchedulingService._calculate_timeline_summary(activities, period_days)
            }
            
        except Exception as e:
            logger.error(f"Timeline view generation error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _build_timeline_data(activities: List[Activity], period_days: int) -> List[Dict]:
        """Build timeline data grouped by periods."""
        timeline_data = []
        
        if not activities:
            return timeline_data
        
        # Find project date range
        start_dates = [a.start_date for a in activities if a.start_date]
        end_dates = [a.end_date for a in activities if a.end_date]
        
        if not start_dates or not end_dates:
            return timeline_data
        
        project_start = min(start_dates)
        project_end = max(end_dates)
        
        # Create periods
        current_date = project_start
        period_num = 1
        
        while current_date <= project_end:
            period_end = current_date + timedelta(days=period_days)
            
            # Find activities in this period
            period_activities = []
            for activity in activities:
                if (activity.start_date and activity.end_date and
                    activity.start_date <= period_end and activity.end_date >= current_date):
                    period_activities.append({
                        'id': activity.id,
                        'name': activity.name,
                        'progress': activity.progress or 0,
                        'type': activity.activity_type.value if activity.activity_type else 'task'
                    })
            
            timeline_data.append({
                'period': period_num,
                'start_date': current_date.isoformat(),
                'end_date': period_end.isoformat(),
                'activities': period_activities,
                'activity_count': len(period_activities)
            })
            
            current_date = period_end
            period_num += 1
        
        return timeline_data
    
    @staticmethod
    def _calculate_timeline_summary(activities: List[Activity], period_days: int) -> Dict[str, Any]:
        """Calculate summary statistics for timeline view."""
        total_activities = len(activities)
        completed_activities = sum(1 for a in activities if a.progress == 100)
        in_progress_activities = sum(1 for a in activities if 0 < (a.progress or 0) < 100)
        
        return {
            'total_activities': total_activities,
            'completed_activities': completed_activities,
            'in_progress_activities': in_progress_activities,
            'completion_rate': (completed_activities / total_activities * 100) if total_activities > 0 else 0,
            'period_type': f"{period_days}-day periods"
        }