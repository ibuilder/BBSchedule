#!/usr/bin/env python3
"""
Test script to verify the modularized codebase structure.
"""
import os
import sys

def test_imports():
    """Test all the modular imports work correctly."""
    print("Testing modular codebase imports...")
    
    try:
        # Test configuration
        from config import config, DevelopmentConfig
        print("✓ Config module imported successfully")
        
        # Test extensions
        from extensions import db, Base
        print("✓ Extensions module imported successfully")
        
        # Test logger
        from logger import setup_logging, log_error, log_activity
        print("✓ Logger module imported successfully")
        
        # Test services
        from services.project_service import ProjectService
        from services.activity_service import ActivityService
        from services.analytics_service import AnalyticsService
        print("✓ Service modules imported successfully")
        
        # Test main application
        from app import app, create_app
        print("✓ Main application imported successfully")
        
        # Test models
        from models import Project, Activity, ProjectStatus, ActivityType
        print("✓ Models imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ General error: {e}")
        return False

def test_services():
    """Test service methods are accessible."""
    print("\nTesting service layer functionality...")
    
    try:
        from services.project_service import ProjectService
        from services.activity_service import ActivityService
        from services.analytics_service import AnalyticsService
        
        # Check service methods exist
        assert hasattr(ProjectService, 'get_all_projects')
        assert hasattr(ProjectService, 'create_project')
        assert hasattr(ActivityService, 'get_activities_by_project')
        assert hasattr(AnalyticsService, 'calculate_dashboard_metrics')
        print("✓ Service methods are properly defined")
        
        return True
        
    except Exception as e:
        print(f"✗ Service test error: {e}")
        return False

def test_database_connection():
    """Test database connection in app context."""
    print("\nTesting database connection...")
    
    try:
        from app import app
        from extensions import db
        from models import Project
        
        with app.app_context():
            # Try a simple query
            count = Project.query.count()
            print(f"✓ Database connection successful. Projects count: {count}")
            return True
            
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("CONSTRUCTION SCHEDULER CODEBASE TEST")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run tests
    if not test_imports():
        all_tests_passed = False
    
    if not test_services():
        all_tests_passed = False
    
    if not test_database_connection():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - Codebase is properly modularized!")
    else:
        print("❌ SOME TESTS FAILED - Check the errors above")
    print("=" * 50)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)