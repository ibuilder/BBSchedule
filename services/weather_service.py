"""
Real-time Weather Integration Service
Provides weather-aware scheduling and risk assessment
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import Project, Activity
from extensions import db
from logger import log_activity, log_error

class WeatherService:
    """Weather integration service for schedule optimization"""
    
    def __init__(self):
        self.weather_impacts = {
            'clear': {'factor': 1.0, 'risk': 'low'},
            'cloudy': {'factor': 1.0, 'risk': 'low'},
            'light_rain': {'factor': 1.15, 'risk': 'medium'},
            'heavy_rain': {'factor': 1.4, 'risk': 'high'},
            'snow': {'factor': 1.6, 'risk': 'high'},
            'thunderstorm': {'factor': 2.0, 'risk': 'critical'},
            'extreme_heat': {'factor': 1.2, 'risk': 'medium'},
            'extreme_cold': {'factor': 1.3, 'risk': 'medium'},
            'high_wind': {'factor': 1.25, 'risk': 'medium'}
        }
        
        self.weather_sensitive_activities = [
            'excavation', 'concrete', 'roofing', 'siding', 'painting',
            'asphalt', 'landscaping', 'crane operations', 'welding'
        ]
    
    def get_weather_forecast(self, project_id: int, days: int = 14) -> Dict[str, Any]:
        """Get weather forecast for project location"""
        
        project = Project.query.get_or_404(project_id)
        
        # Simulate weather API call (replace with actual weather service)
        forecast_data = self._generate_realistic_forecast(project.location, days)
        
        return {
            'project_id': project_id,
            'location': project.location,
            'forecast_period': days,
            'generated_at': datetime.now().isoformat(),
            'daily_forecast': forecast_data,
            'weather_alerts': self._generate_weather_alerts(forecast_data),
            'schedule_recommendations': self._generate_schedule_recommendations(project_id, forecast_data)
        }
    
    def assess_weather_risk(self, project_id: int) -> Dict[str, Any]:
        """Assess weather risk for upcoming activities"""
        
        project = Project.query.get_or_404(project_id)
        activities = Activity.query.filter_by(project_id=project_id)\
                                 .filter(Activity.start_date >= datetime.now().date())\
                                 .order_by(Activity.start_date).all()
        
        forecast = self.get_weather_forecast(project_id, 14)
        risk_assessment = []
        
        for activity in activities:
            if activity.start_date:
                days_from_now = (activity.start_date - datetime.now().date()).days
                
                if 0 <= days_from_now < len(forecast['daily_forecast']):
                    weather_data = forecast['daily_forecast'][days_from_now]
                    
                    risk_level = self._calculate_activity_weather_risk(activity, weather_data)
                    
                    risk_assessment.append({
                        'activity_id': activity.id,
                        'activity_name': activity.name,
                        'start_date': activity.start_date.isoformat(),
                        'weather_condition': weather_data['condition'],
                        'risk_level': risk_level['level'],
                        'impact_factor': risk_level['factor'],
                        'recommendations': risk_level['recommendations'],
                        'alternative_dates': self._suggest_alternative_dates(activity, forecast)
                    })
        
        return {
            'project_id': project_id,
            'assessment_date': datetime.now().isoformat(),
            'activities_assessed': len(risk_assessment),
            'high_risk_activities': len([r for r in risk_assessment if r['risk_level'] == 'high']),
            'risk_details': risk_assessment,
            'overall_recommendations': self._generate_overall_recommendations(risk_assessment)
        }
    
    def optimize_schedule_for_weather(self, project_id: int) -> Dict[str, Any]:
        """Optimize project schedule based on weather forecast"""
        
        weather_risk = self.assess_weather_risk(project_id)
        activities = Activity.query.filter_by(project_id=project_id).all()
        
        optimization_results = {
            'project_id': project_id,
            'optimization_date': datetime.now().isoformat(),
            'original_schedule': len(activities),
            'optimized_activities': 0,
            'weather_adjustments': [],
            'estimated_time_savings': 0,
            'risk_reduction': 0
        }
        
        total_adjustments = 0
        time_savings = 0
        
        for risk_item in weather_risk['risk_details']:
            if risk_item['risk_level'] in ['high', 'critical']:
                activity = Activity.query.get(risk_item['activity_id'])
                
                if activity and risk_item['alternative_dates']:
                    best_date = risk_item['alternative_dates'][0]
                    original_duration = activity.duration
                    
                    # Calculate optimized duration
                    weather_factor = risk_item['impact_factor']
                    optimized_duration = int(original_duration / weather_factor)
                    
                    adjustment = {
                        'activity_id': activity.id,
                        'activity_name': activity.name,
                        'original_date': activity.start_date.isoformat() if activity.start_date else None,
                        'optimized_date': best_date['date'],
                        'original_duration': original_duration,
                        'optimized_duration': optimized_duration,
                        'time_saved': original_duration - optimized_duration,
                        'weather_condition_avoided': risk_item['weather_condition'],
                        'risk_reduction': weather_factor - 1.0
                    }
                    
                    optimization_results['weather_adjustments'].append(adjustment)
                    total_adjustments += 1
                    time_savings += adjustment['time_saved']
        
        optimization_results['optimized_activities'] = total_adjustments
        optimization_results['estimated_time_savings'] = time_savings
        optimization_results['risk_reduction'] = len([r for r in weather_risk['risk_details'] if r['risk_level'] == 'high'])
        
        return optimization_results
    
    def _generate_realistic_forecast(self, location: str, days: int) -> List[Dict[str, Any]]:
        """Generate realistic weather forecast data"""
        
        import random
        
        conditions = ['clear', 'cloudy', 'light_rain', 'heavy_rain', 'thunderstorm']
        temperatures = list(range(45, 85))  # Fahrenheit
        
        forecast = []
        base_date = datetime.now().date()
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            
            # Simulate seasonal and regional weather patterns
            condition = random.choice(conditions)
            temp = random.choice(temperatures)
            
            # Adjust for seasonal patterns
            month = date.month
            if month in [12, 1, 2]:  # Winter
                temp = max(20, temp - 20)
                if random.random() < 0.3:
                    condition = 'snow'
            elif month in [6, 7, 8]:  # Summer
                temp = min(95, temp + 15)
                if temp > 90 and random.random() < 0.2:
                    condition = 'extreme_heat'
            
            forecast.append({
                'date': date.isoformat(),
                'condition': condition,
                'temperature_high': temp,
                'temperature_low': temp - random.randint(10, 20),
                'humidity': random.randint(30, 90),
                'wind_speed': random.randint(5, 25),
                'precipitation_chance': random.randint(0, 100) if condition in ['light_rain', 'heavy_rain', 'thunderstorm'] else random.randint(0, 20)
            })
        
        return forecast
    
    def _generate_weather_alerts(self, forecast_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate weather alerts for severe conditions"""
        
        alerts = []
        
        for day_data in forecast_data:
            if day_data['condition'] in ['heavy_rain', 'thunderstorm', 'snow']:
                alerts.append({
                    'date': day_data['date'],
                    'severity': 'high',
                    'condition': day_data['condition'],
                    'message': f"Severe weather expected: {day_data['condition'].replace('_', ' ').title()}",
                    'recommendations': ['Reschedule outdoor activities', 'Secure equipment and materials', 'Review safety protocols']
                })
            elif day_data['condition'] == 'extreme_heat' or day_data['temperature_high'] > 90:
                alerts.append({
                    'date': day_data['date'],
                    'severity': 'medium',
                    'condition': 'extreme_heat',
                    'message': f"High temperature warning: {day_data['temperature_high']}°F",
                    'recommendations': ['Implement heat safety measures', 'Adjust work hours', 'Increase hydration breaks']
                })
            elif day_data['wind_speed'] > 20:
                alerts.append({
                    'date': day_data['date'],
                    'severity': 'medium',
                    'condition': 'high_wind',
                    'message': f"High wind warning: {day_data['wind_speed']} mph",
                    'recommendations': ['Suspend crane operations', 'Secure loose materials', 'Review fall protection']
                })
        
        return alerts
    
    def _generate_schedule_recommendations(self, project_id: int, forecast_data: List[Dict[str, Any]]) -> List[str]:
        """Generate schedule recommendations based on weather"""
        
        recommendations = []
        
        # Count weather conditions
        rain_days = len([d for d in forecast_data if 'rain' in d['condition']])
        severe_days = len([d for d in forecast_data if d['condition'] in ['heavy_rain', 'thunderstorm', 'snow']])
        
        if rain_days > 3:
            recommendations.append("Consider scheduling indoor activities during the next 2 weeks")
        
        if severe_days > 1:
            recommendations.append("High risk period detected - review critical path activities")
        
        # Identify good weather windows
        clear_days = [(i, d) for i, d in enumerate(forecast_data) if d['condition'] in ['clear', 'cloudy']]
        
        if len(clear_days) >= 3:
            start_day = clear_days[0][0]
            end_day = clear_days[-1][0]
            recommendations.append(f"Optimal weather window: Days {start_day+1}-{end_day+1} for critical outdoor work")
        
        recommendations.append("Enable automatic weather alerts for real-time schedule adjustments")
        
        return recommendations
    
    def _calculate_activity_weather_risk(self, activity: Activity, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weather risk for specific activity"""
        
        activity_name = activity.name.lower()
        weather_condition = weather_data['condition']
        
        # Check if activity is weather-sensitive
        is_sensitive = any(keyword in activity_name for keyword in self.weather_sensitive_activities)
        
        if not is_sensitive:
            return {
                'level': 'low',
                'factor': 1.0,
                'recommendations': ['No weather-related concerns']
            }
        
        weather_impact = self.weather_impacts.get(weather_condition, self.weather_impacts['clear'])
        
        # Additional risk factors
        risk_multiplier = 1.0
        
        if weather_data['wind_speed'] > 20:
            risk_multiplier += 0.2
        
        if weather_data['temperature_high'] > 90 or weather_data['temperature_low'] < 32:
            risk_multiplier += 0.1
        
        final_factor = weather_impact['factor'] * risk_multiplier
        
        if final_factor >= 1.5:
            risk_level = 'critical'
        elif final_factor >= 1.3:
            risk_level = 'high'
        elif final_factor >= 1.1:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        recommendations = []
        if risk_level in ['high', 'critical']:
            recommendations.extend([
                'Consider rescheduling to avoid weather delays',
                'Prepare weather protection measures',
                'Have backup indoor activities ready'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                'Monitor weather conditions closely',
                'Prepare contingency plans'
            ])
        
        return {
            'level': risk_level,
            'factor': final_factor,
            'recommendations': recommendations
        }
    
    def _suggest_alternative_dates(self, activity: Activity, forecast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest alternative dates with better weather"""
        
        alternatives = []
        current_date = activity.start_date
        
        for i, day_data in enumerate(forecast['daily_forecast']):
            if day_data['condition'] in ['clear', 'cloudy']:
                date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d').date()
                
                if date_obj != current_date:
                    alternatives.append({
                        'date': day_data['date'],
                        'condition': day_data['condition'],
                        'temperature': day_data['temperature_high'],
                        'suitability_score': self._calculate_date_suitability(day_data)
                    })
        
        # Sort by suitability score
        alternatives.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def _calculate_date_suitability(self, day_data: Dict[str, Any]) -> float:
        """Calculate suitability score for a date"""
        
        score = 100.0
        
        # Weather condition impact
        condition_scores = {
            'clear': 100,
            'cloudy': 90,
            'light_rain': 40,
            'heavy_rain': 10,
            'thunderstorm': 5,
            'snow': 15,
            'extreme_heat': 60,
            'extreme_cold': 60,
            'high_wind': 50
        }
        
        score = condition_scores.get(day_data['condition'], 70)
        
        # Temperature adjustments
        temp = day_data['temperature_high']
        if 60 <= temp <= 80:  # Ideal temperature range
            score += 10
        elif temp > 90 or temp < 32:
            score -= 20
        
        # Wind speed adjustments
        if day_data['wind_speed'] < 10:
            score += 5
        elif day_data['wind_speed'] > 20:
            score -= 15
        
        return max(0, min(100, score))
    
    def _generate_overall_recommendations(self, risk_assessment: List[Dict[str, Any]]) -> List[str]:
        """Generate overall recommendations for weather management"""
        
        high_risk_count = len([r for r in risk_assessment if r['risk_level'] == 'high'])
        total_activities = len(risk_assessment)
        
        recommendations = []
        
        if high_risk_count > total_activities * 0.3:
            recommendations.append("Consider major schedule restructuring due to high weather risk")
        
        if high_risk_count > 0:
            recommendations.append(f"{high_risk_count} activities have high weather risk - prioritize rescheduling")
        
        recommendations.extend([
            "Enable daily weather monitoring and alerts",
            "Implement flexible scheduling for weather-sensitive activities",
            "Maintain contingency plans for severe weather events",
            "Consider weather insurance for critical activities"
        ])
        
        return recommendations

# Global service instance
weather_service = WeatherService()