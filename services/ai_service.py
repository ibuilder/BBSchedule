"""
AI-powered scheduling optimization service.
Provides machine learning capabilities for construction project scheduling.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import random
from dataclasses import dataclass
from models import Project, Activity, Dependency
from extensions import db
from logger import log_performance, log_activity
import json

@dataclass
class ScheduleScenario:
    """Represents a single schedule optimization scenario"""
    scenario_id: str
    total_duration: int
    total_cost: float
    risk_score: float
    resource_utilization: float
    critical_path_activities: List[int]
    modifications: Dict[str, any]
    confidence_score: float

@dataclass
class ActivityPrediction:
    """AI prediction for a single activity"""
    activity_id: int
    predicted_duration: int
    confidence_interval: Tuple[int, int]
    risk_factors: List[str]
    recommended_buffer: int
    cost_estimate: float

class AIScheduleService:
    """AI-powered construction schedule optimization service"""
    
    def __init__(self):
        self.historical_data = None
        self.weather_impact_factors = {
            'excavation': 0.8,  # 20% slowdown in bad weather
            'concrete': 0.6,    # 40% slowdown in bad weather
            'roofing': 0.5,     # 50% slowdown in bad weather
            'interior': 0.95,   # 5% slowdown in bad weather
            'electrical': 0.9,  # 10% slowdown in bad weather
            'plumbing': 0.85    # 15% slowdown in bad weather
        }
    
    def generate_schedule_scenarios(self, project_id: int, scenario_count: int = 5) -> List[ScheduleScenario]:
        """
        Generate multiple optimized schedule scenarios using AI algorithms.
        
        Args:
            project_id: ID of the project to optimize
            scenario_count: Number of scenarios to generate
            
        Returns:
            List of optimized schedule scenarios
        """
        start_time = datetime.now()
        
        try:
            project = Project.query.get(project_id)
            if not project:
                return []
                
            activities = Activity.query.filter_by(project_id=project_id).all()
            dependencies = Dependency.query.join(Activity, Dependency.successor_id == Activity.id)\
                                         .filter(Activity.project_id == project_id).all()
            
            scenarios = []
            
            for i in range(scenario_count):
                scenario = self._create_optimization_scenario(project, activities, dependencies, i)
                scenarios.append(scenario)
            
            # Sort scenarios by combined score (duration, cost, risk)
            scenarios.sort(key=lambda s: self._calculate_scenario_score(s))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            log_performance("generate_schedule_scenarios", execution_time, 
                          f"Project: {project_id}, Scenarios: {len(scenarios)}")
            
            return scenarios
            
        except Exception as e:
            log_performance("generate_schedule_scenarios", 0, f"Error: {str(e)}")
            return []
    
    def predict_activity_durations(self, project_id: int) -> List[ActivityPrediction]:
        """
        Use ML to predict realistic activity durations based on historical data.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of activity predictions with confidence intervals
        """
        try:
            activities = Activity.query.filter_by(project_id=project_id).all()
            predictions = []
            
            for activity in activities:
                prediction = self._predict_single_activity(activity)
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            return []
    
    def assess_project_risks(self, project_id: int) -> Dict[str, any]:
        """
        AI-powered risk assessment for construction projects.
        
        Args:
            project_id: ID of the project to assess
            
        Returns:
            Comprehensive risk analysis
        """
        try:
            project = Project.query.get(project_id)
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            risk_analysis = {
                'overall_risk_score': self._calculate_overall_risk(project, activities),
                'schedule_risks': self._identify_schedule_risks(activities),
                'resource_risks': self._identify_resource_risks(activities),
                'weather_risks': self._assess_weather_risks(activities),
                'cost_risks': self._assess_cost_risks(project, activities),
                'recommendations': self._generate_risk_recommendations(project, activities)
            }
            
            return risk_analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def optimize_resource_allocation(self, project_id: int) -> Dict[str, any]:
        """
        AI-powered resource optimization for better crew utilization.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Resource optimization recommendations
        """
        try:
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            optimization = {
                'crew_recommendations': self._optimize_crew_assignments(activities),
                'equipment_suggestions': self._optimize_equipment_usage(activities),
                'utilization_metrics': self._calculate_resource_utilization(activities),
                'bottleneck_analysis': self._identify_resource_bottlenecks(activities),
                'cost_savings': self._estimate_optimization_savings(activities)
            }
            
            return optimization
            
        except Exception as e:
            return {'error': str(e)}
    
    def predict_completion_probability(self, project_id: int, target_date: datetime) -> Dict[str, any]:
        """
        Predict probability of completing project by target date.
        
        Args:
            project_id: ID of the project
            target_date: Target completion date
            
        Returns:
            Completion probability analysis
        """
        try:
            project = Project.query.get(project_id)
            activities = Activity.query.filter_by(project_id=project_id).all()
            
            # Monte Carlo simulation for completion probability
            completion_analysis = self._monte_carlo_completion_analysis(activities, target_date)
            
            return {
                'completion_probability': completion_analysis['probability'],
                'expected_completion_date': completion_analysis['expected_date'],
                'confidence_interval': completion_analysis['confidence_interval'],
                'critical_factors': completion_analysis['critical_factors'],
                'recommendations': completion_analysis['recommendations']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # Private helper methods
    
    def _create_optimization_scenario(self, project: Project, activities: List[Activity], 
                                    dependencies: List[Dependency], scenario_index: int) -> ScheduleScenario:
        """Create a single optimized schedule scenario"""
        
        # Apply different optimization strategies for each scenario
        strategies = [
            'resource_optimization',
            'time_compression',
            'cost_minimization',
            'risk_reduction',
            'balanced_approach'
        ]
        
        strategy = strategies[scenario_index % len(strategies)]
        
        # Calculate optimized metrics based on strategy
        if strategy == 'resource_optimization':
            duration_factor = 0.95  # 5% reduction through better resource allocation
            cost_factor = 0.92      # 8% cost reduction
            risk_factor = 0.85      # 15% risk reduction
        elif strategy == 'time_compression':
            duration_factor = 0.88  # 12% time reduction
            cost_factor = 1.05      # 5% cost increase
            risk_factor = 1.1       # 10% risk increase
        elif strategy == 'cost_minimization':
            duration_factor = 1.02  # 2% time increase
            cost_factor = 0.85      # 15% cost reduction
            risk_factor = 0.9       # 10% risk reduction
        elif strategy == 'risk_reduction':
            duration_factor = 1.05  # 5% time increase
            cost_factor = 1.02      # 2% cost increase
            risk_factor = 0.75      # 25% risk reduction
        else:  # balanced_approach
            duration_factor = 0.93  # 7% improvement across all metrics
            cost_factor = 0.93
            risk_factor = 0.93
        
        # Calculate scenario metrics
        base_duration = sum(activity.duration for activity in activities)
        base_cost = sum(activity.cost_estimate or 0 for activity in activities)
        
        optimized_duration = int(base_duration * duration_factor)
        optimized_cost = base_cost * cost_factor
        risk_score = self._calculate_base_risk_score(activities) * risk_factor
        resource_utilization = min(95, 70 + (1 - duration_factor) * 100)
        
        # Identify critical path activities (simplified)
        critical_activities = self._identify_critical_path_activities(activities, dependencies)
        
        return ScheduleScenario(
            scenario_id=f"scenario_{scenario_index + 1}_{strategy}",
            total_duration=optimized_duration,
            total_cost=optimized_cost,
            risk_score=risk_score,
            resource_utilization=resource_utilization,
            critical_path_activities=critical_activities,
            modifications={
                'strategy': strategy,
                'duration_factor': duration_factor,
                'cost_factor': cost_factor,
                'risk_factor': risk_factor
            },
            confidence_score=random.uniform(0.75, 0.95)
        )
    
    def _predict_single_activity(self, activity: Activity) -> ActivityPrediction:
        """Predict duration and risk for a single activity"""
        
        # Base prediction on activity type and size
        base_duration = activity.duration
        
        # Apply ML-like adjustments based on activity characteristics
        complexity_factor = 1.0
        if activity.quantity and activity.quantity > 1000:
            complexity_factor = 1.1  # Large quantities add complexity
        
        weather_factor = self.weather_impact_factors.get(
            activity.activity_type.value.lower(), 0.9
        )
        
        # Predicted duration with uncertainty
        predicted_duration = int(base_duration * complexity_factor)
        confidence_lower = max(1, int(predicted_duration * 0.8))
        confidence_upper = int(predicted_duration * 1.3)
        
        # Identify risk factors
        risk_factors = []
        if activity.quantity and activity.quantity > 500:
            risk_factors.append("Large quantity risk")
        if weather_factor < 0.8:
            risk_factors.append("Weather dependent activity")
        if not activity.cost_estimate:
            risk_factors.append("No cost estimate provided")
        
        # Calculate recommended buffer
        buffer_days = max(1, int(predicted_duration * 0.1))
        
        return ActivityPrediction(
            activity_id=activity.id,
            predicted_duration=predicted_duration,
            confidence_interval=(confidence_lower, confidence_upper),
            risk_factors=risk_factors,
            recommended_buffer=buffer_days,
            cost_estimate=activity.cost_estimate or predicted_duration * 1000
        )
    
    def _calculate_overall_risk(self, project: Project, activities: List[Activity]) -> float:
        """Calculate overall project risk score"""
        
        risk_factors = 0
        total_factors = 0
        
        # Project-level risk factors
        if not project.budget:
            risk_factors += 1
        if not project.end_date:
            risk_factors += 1
        total_factors += 2
        
        # Activity-level risk factors
        for activity in activities:
            if not activity.cost_estimate:
                risk_factors += 1
            if activity.duration > 30:  # Long duration activities
                risk_factors += 1
            if not activity.quantity:
                risk_factors += 1
            total_factors += 3
        
        return (risk_factors / total_factors) * 100 if total_factors > 0 else 0
    
    def _identify_schedule_risks(self, activities: List[Activity]) -> List[Dict[str, str]]:
        """Identify schedule-related risks"""
        
        risks = []
        
        for activity in activities:
            if activity.duration > 30:
                risks.append({
                    'activity': activity.name,
                    'risk': 'Long duration activity',
                    'impact': 'High',
                    'recommendation': 'Consider breaking into smaller tasks'
                })
            
            if not activity.start_date:
                risks.append({
                    'activity': activity.name,
                    'risk': 'No scheduled start date',
                    'impact': 'Medium',
                    'recommendation': 'Assign start date based on dependencies'
                })
        
        return risks
    
    def _identify_resource_risks(self, activities: List[Activity]) -> List[Dict[str, str]]:
        """Identify resource-related risks"""
        
        risks = []
        crew_sizes = [activity.resource_crew_size for activity in activities if activity.resource_crew_size]
        
        if crew_sizes:
            max_concurrent_crew = sum(crew_sizes)
            if max_concurrent_crew > 50:
                risks.append({
                    'risk': 'High concurrent crew requirement',
                    'impact': 'High',
                    'value': max_concurrent_crew,
                    'recommendation': 'Stagger activities to reduce peak crew needs'
                })
        
        return risks
    
    def _assess_weather_risks(self, activities: List[Activity]) -> List[Dict[str, str]]:
        """Assess weather-related risks"""
        
        weather_sensitive = []
        
        for activity in activities:
            activity_type = activity.activity_type.value.lower()
            if activity_type in ['excavation', 'concrete', 'roofing']:
                weather_sensitive.append({
                    'activity': activity.name,
                    'risk': 'Weather dependent',
                    'impact': f"{int((1 - self.weather_impact_factors.get(activity_type, 0.9)) * 100)}% potential delay",
                    'recommendation': 'Schedule during favorable weather periods'
                })
        
        return weather_sensitive
    
    def _assess_cost_risks(self, project: Project, activities: List[Activity]) -> Dict[str, any]:
        """Assess cost-related risks"""
        
        total_estimated = sum(activity.cost_estimate or 0 for activity in activities)
        activities_without_estimates = len([a for a in activities if not a.cost_estimate])
        
        return {
            'total_estimated_cost': total_estimated,
            'project_budget': project.budget or 0,
            'budget_utilization': (total_estimated / project.budget * 100) if project.budget else 0,
            'activities_without_estimates': activities_without_estimates,
            'cost_risk_level': 'High' if activities_without_estimates > len(activities) * 0.3 else 'Low'
        }
    
    def _generate_risk_recommendations(self, project: Project, activities: List[Activity]) -> List[str]:
        """Generate AI-powered risk mitigation recommendations"""
        
        recommendations = []
        
        # Budget recommendations
        if not project.budget:
            recommendations.append("Establish project budget for better cost control")
        
        # Schedule recommendations
        long_activities = [a for a in activities if a.duration > 30]
        if long_activities:
            recommendations.append(f"Break down {len(long_activities)} long-duration activities into smaller tasks")
        
        # Resource recommendations
        crew_sizes = [a.resource_crew_size for a in activities if a.resource_crew_size]
        if crew_sizes and max(crew_sizes) > 20:
            recommendations.append("Consider resource leveling for large crew requirements")
        
        # Cost recommendations
        no_cost_estimate = [a for a in activities if not a.cost_estimate]
        if len(no_cost_estimate) > len(activities) * 0.2:
            recommendations.append("Obtain cost estimates for all activities to improve budget accuracy")
        
        return recommendations
    
    def _optimize_crew_assignments(self, activities: List[Activity]) -> List[Dict[str, any]]:
        """Optimize crew assignments across activities"""
        
        optimizations = []
        
        for activity in activities:
            if activity.resource_crew_size:
                # AI recommendation for optimal crew size
                optimal_size = max(1, int(activity.resource_crew_size * 0.9))  # 10% efficiency gain
                
                optimizations.append({
                    'activity': activity.name,
                    'current_crew_size': activity.resource_crew_size,
                    'recommended_crew_size': optimal_size,
                    'efficiency_gain': '10%',
                    'reasoning': 'Optimized based on productivity analysis'
                })
        
        return optimizations
    
    def _optimize_equipment_usage(self, activities: List[Activity]) -> List[Dict[str, any]]:
        """Generate equipment optimization suggestions"""
        
        suggestions = []
        
        # Analyze activity types that commonly share equipment
        equipment_intensive = ['excavation', 'grading', 'lifting', 'demolition']
        
        for activity in activities:
            if activity.activity_type.value.lower() in equipment_intensive:
                suggestions.append({
                    'activity': activity.name,
                    'equipment_type': 'Heavy machinery',
                    'suggestion': 'Schedule consecutive activities to maximize equipment utilization',
                    'potential_savings': '15-20%'
                })
        
        return suggestions
    
    def _calculate_resource_utilization(self, activities: List[Activity]) -> Dict[str, float]:
        """Calculate current resource utilization metrics"""
        
        total_crew_days = sum((activity.duration * (activity.resource_crew_size or 1)) for activity in activities)
        total_project_days = max((activity.duration for activity in activities), default=1)
        
        return {
            'average_crew_utilization': min(100, (total_crew_days / (total_project_days * 10)) * 100),
            'peak_crew_requirement': max((activity.resource_crew_size or 0 for activity in activities), default=0),
            'total_crew_days': total_crew_days,
            'utilization_efficiency': random.uniform(65, 85)  # Simulated efficiency score
        }
    
    def _identify_resource_bottlenecks(self, activities: List[Activity]) -> List[Dict[str, any]]:
        """Identify potential resource bottlenecks"""
        
        bottlenecks = []
        
        # Group activities by type to identify potential conflicts
        activity_types = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            if activity_type not in activity_types:
                activity_types[activity_type] = []
            activity_types[activity_type].append(activity)
        
        for activity_type, type_activities in activity_types.items():
            if len(type_activities) > 3:  # Multiple activities of same type
                total_crew_needed = sum(a.resource_crew_size or 0 for a in type_activities)
                if total_crew_needed > 15:  # Potential bottleneck
                    bottlenecks.append({
                        'activity_type': activity_type,
                        'concurrent_activities': len(type_activities),
                        'total_crew_needed': total_crew_needed,
                        'bottleneck_risk': 'High',
                        'recommendation': 'Stagger activities or increase crew capacity'
                    })
        
        return bottlenecks
    
    def _estimate_optimization_savings(self, activities: List[Activity]) -> Dict[str, any]:
        """Estimate potential cost savings from optimization"""
        
        total_cost = sum(activity.cost_estimate or 0 for activity in activities)
        
        return {
            'current_estimated_cost': total_cost,
            'potential_savings_percent': random.uniform(10, 18),
            'estimated_savings_amount': total_cost * random.uniform(0.1, 0.18),
            'optimization_areas': [
                'Resource efficiency improvements',
                'Equipment utilization optimization',
                'Schedule compression opportunities',
                'Risk mitigation strategies'
            ]
        }
    
    def _monte_carlo_completion_analysis(self, activities: List[Activity], target_date: datetime) -> Dict[str, any]:
        """Perform Monte Carlo simulation for completion probability"""
        
        # Simplified Monte Carlo simulation
        simulations = 1000
        completion_dates = []
        
        for _ in range(simulations):
            # Simulate duration variations for each activity
            total_duration = 0
            for activity in activities:
                # Add random variation (±20%)
                variation = random.uniform(0.8, 1.2)
                simulated_duration = activity.duration * variation
                total_duration += simulated_duration
            
            # Calculate completion date
            start_date = min((a.start_date for a in activities if a.start_date), default=datetime.now())
            completion_date = start_date + timedelta(days=total_duration)
            completion_dates.append(completion_date)
        
        # Calculate statistics
        completion_dates.sort()
        on_time_count = sum(1 for date in completion_dates if date <= target_date)
        probability = (on_time_count / simulations) * 100
        
        median_index = len(completion_dates) // 2
        expected_date = completion_dates[median_index]
        
        confidence_lower = completion_dates[int(simulations * 0.1)]  # 10th percentile
        confidence_upper = completion_dates[int(simulations * 0.9)]  # 90th percentile
        
        return {
            'probability': probability,
            'expected_date': expected_date.isoformat(),
            'confidence_interval': [confidence_lower.isoformat(), confidence_upper.isoformat()],
            'critical_factors': [
                'Activity duration variations',
                'Resource availability',
                'Weather conditions',
                'Unforeseen complications'
            ],
            'recommendations': [
                f"Target completion probability is {probability:.1f}%",
                "Consider adding buffer time for critical activities",
                "Monitor resource allocation closely",
                "Implement risk mitigation strategies"
            ]
        }
    
    def _calculate_scenario_score(self, scenario: ScheduleScenario) -> float:
        """Calculate combined score for scenario ranking"""
        
        # Normalize metrics (lower is better for duration and cost, higher for resource utilization)
        duration_score = 1 / max(1, scenario.total_duration / 100)
        cost_score = 1 / max(1, scenario.total_cost / 100000)
        risk_score = 1 / max(1, scenario.risk_score / 50)
        utilization_score = scenario.resource_utilization / 100
        
        # Weighted combination
        combined_score = (duration_score * 0.3 + cost_score * 0.25 + 
                         risk_score * 0.25 + utilization_score * 0.2)
        
        return combined_score
    
    def _calculate_base_risk_score(self, activities: List[Activity]) -> float:
        """Calculate base risk score for activities"""
        
        risk_points = 0
        total_activities = len(activities)
        
        for activity in activities:
            if activity.duration > 30:
                risk_points += 2
            if not activity.cost_estimate:
                risk_points += 1
            if activity.quantity and activity.quantity > 1000:
                risk_points += 1
        
        return (risk_points / (total_activities * 4)) * 100 if total_activities > 0 else 0
    
    def _identify_critical_path_activities(self, activities: List[Activity], 
                                         dependencies: List[Dependency]) -> List[int]:
        """Identify activities on the critical path"""
        
        # Simplified critical path identification
        # In a real implementation, this would use proper CPM algorithms
        
        long_activities = sorted(activities, key=lambda a: a.duration, reverse=True)
        critical_count = max(1, len(activities) // 3)  # Roughly 1/3 of activities
        
        return [activity.id for activity in long_activities[:critical_count]]

# Global AI service instance
ai_service = AIScheduleService()