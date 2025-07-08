#!/usr/bin/env python3
"""
Simplified test suite to identify critical errors in BBSchedule
"""

import unittest
import os
import sys
from datetime import datetime, date, timedelta

# Set test environment before imports
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SESSION_SECRET'] = 'test-secret-key'
os.environ['TESTING'] = 'True'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app components
try:
    from app import create_app
    from extensions import db
    from models import Project, Activity, ProjectStatus, ActivityType
    print("✓ Successfully imported core models")
except ImportError as e:
    print(f"✗ Failed to import models: {e}")
    sys.exit(1)

try:
    from services.project_service import ProjectService
    from services.activity_service import ActivityService  
    from services.analytics_service import AnalyticsService
    print("✓ Successfully imported services")
except ImportError as e:
    print(f"✗ Failed to import services: {e}")
    sys.exit(1)

try:
    import utils
    print("✓ Successfully imported utils")
except ImportError as e:
    print(f"✗ Failed to import utils: {e}")
    sys.exit(1)

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False

class BasicTests(unittest.TestCase):
    """Basic functionality tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app.config.from_object(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create database tables
        db.create_all()
        
        # Create test project
        self.test_project = Project(
            name="Test Project",
            description="Test project for testing",
            start_date=date.today(),
            status=ProjectStatus.ACTIVE,
            budget=100000.0
        )
        db.session.add(self.test_project)
        db.session.commit()
        
        # Create test activity
        self.test_activity = Activity(
            project_id=self.test_project.id,
            name="Test Activity",
            activity_type=ActivityType.FOUNDATION,
            duration=10,
            progress=50,
            cost_estimate=10000.0
        )
        db.session.add(self.test_activity)
        db.session.commit()
    
    def tearDown(self):
        """Clean up"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_models_basic(self):
        """Test basic model functionality"""
        # Test project exists
        project = Project.query.first()
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "Test Project")
        
        # Test activity exists  
        activity = Activity.query.first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.name, "Test Activity")
        
        print("✓ Model tests passed")
    
    def test_service_methods(self):
        """Test service layer methods"""
        # Test ProjectService
        projects = ProjectService.get_all_projects()
        self.assertIsInstance(projects, list)
        self.assertGreater(len(projects), 0)
        
        # Test ActivityService  
        activities = ActivityService.get_project_activities(self.test_project.id)
        self.assertIsInstance(activities, list)
        self.assertGreater(len(activities), 0)
        
        # Test AnalyticsService
        metrics = AnalyticsService.calculate_dashboard_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_projects', metrics)
        
        analytics = AnalyticsService.get_project_analytics(self.test_project.id)
        self.assertIsInstance(analytics, dict)
        
        print("✓ Service tests passed")
    
    def test_routes_basic(self):
        """Test basic route functionality"""
        # Test index route
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Test health endpoint
        response = self.client.get('/health/ping')
        self.assertEqual(response.status_code, 200)
        
        # Test API endpoints
        response = self.client.get(f'/api/project/{self.test_project.id}/activities')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/api/dashboard/metrics')
        self.assertEqual(response.status_code, 200)
        
        print("✓ Route tests passed")
    
    def test_utils_basic(self):
        """Test utility functions"""
        activities = [self.test_activity]
        metrics = utils.calculate_schedule_metrics(self.test_project, activities)
        self.assertIsInstance(metrics, dict)
        self.assertIn('completion_percentage', metrics)
        
        print("✓ Utils tests passed")

def run_tests():
    """Run basic tests and report results"""
    print("=" * 60)
    print("BBSchedule - Basic Functionality Tests")
    print("=" * 60)
    
    # Run test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BasicTests)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, error in result.failures:
            print(f"- {test}: {error[:200]}...")
    
    if result.errors:
        print("\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}: {error[:200]}...")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)