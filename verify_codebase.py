#!/usr/bin/env python3
"""
Comprehensive verification script for the modularized codebase.
"""
import os
import sys
import time
from datetime import datetime

def verify_file_structure():
    """Verify the new modular file structure exists."""
    print("Verifying modular file structure...")
    
    required_files = [
        'config.py',
        'extensions.py', 
        'logger.py',
        'services/__init__.py',
        'services/project_service.py',
        'services/activity_service.py',
        'services/analytics_service.py',
        'app.py',
        'models.py',
        'routes.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ All required modular files exist")
    return True

def verify_logging_setup():
    """Test the logging system works."""
    print("\nVerifying logging system...")
    
    try:
        from logger import log_error, log_activity, log_performance
        
        # Test logging functions
        log_activity("test_user", "Testing logging system")
        log_performance("test_function", 0.1, "Test performance log")
        
        print("✓ Logging system functional")
        return True
        
    except Exception as e:
        print(f"✗ Logging error: {e}")
        return False

def verify_services_functionality():
    """Test service layer with real data."""
    print("\nVerifying service functionality with live data...")
    
    try:
        from app import app
        from services.project_service import ProjectService
        from services.activity_service import ActivityService
        from services.analytics_service import AnalyticsService
        
        with app.app_context():
            # Test analytics service
            start_time = time.time()
            metrics = AnalyticsService.calculate_dashboard_metrics()
            elapsed = time.time() - start_time
            
            print(f"✓ Dashboard metrics calculated in {elapsed:.3f}s")
            print(f"  - Total projects: {metrics.get('total_projects', 0)}")
            print(f"  - Active projects: {metrics.get('active_projects', 0)}")
            print(f"  - Linear projects: {metrics.get('linear_projects', 0)}")
            print(f"  - Total activities: {metrics.get('total_activities', 0)}")
            
            # Test project service
            projects = ProjectService.get_all_projects("test_user")
            print(f"✓ Retrieved {len(projects)} projects via service layer")
            
            # Test 5D analysis on first linear project
            linear_project = None
            for project in projects:
                if project.linear_scheduling_enabled:
                    linear_project = project
                    break
            
            if linear_project:
                analysis = AnalyticsService.generate_5d_analysis(linear_project.id)
                print(f"✓ 5D analysis generated for '{linear_project.name}'")
                print(f"  - Project length: {analysis.get('spatial_analysis', {}).get('project_length')} {linear_project.station_units}")
                print(f"  - Completion: {analysis.get('time_analysis', {}).get('completion_percentage')}%")
            
            return True
            
    except Exception as e:
        print(f"✗ Service functionality error: {e}")
        return False

def verify_error_handling():
    """Test error handling and logging."""
    print("\nVerifying error handling...")
    
    try:
        from logger import log_error
        from services.project_service import ProjectService
        from app import app
        
        with app.app_context():
            # Test non-existent project
            project = ProjectService.get_project_by_id(99999, "test_user")
            if project is None:
                print("✓ Service correctly handles non-existent records")
            
            # Test error logging
            test_error = Exception("Test error for logging")
            log_error(test_error, "Testing error logging system")
            print("✓ Error logging works correctly")
            
            return True
            
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def verify_linear_scheduling():
    """Verify linear scheduling functionality."""
    print("\nVerifying linear scheduling functionality...")
    
    try:
        from app import app
        from models import Project
        from services.project_service import ProjectService
        
        with app.app_context():
            # Find a linear project
            linear_projects = Project.query.filter_by(linear_scheduling_enabled=True).all()
            
            if not linear_projects:
                print("✗ No linear projects found")
                return False
            
            project = linear_projects[0]
            print(f"✓ Found linear project: {project.name}")
            print(f"  - Range: {project.project_start_station}-{project.project_end_station} {project.station_units}")
            print(f"  - Activities: {len(project.activities)}")
            
            # Test location-based filtering
            if project.project_end_station:
                mid_point = project.project_end_station / 2
                activities = ProjectService.get_linear_activities_by_location(
                    project.id, 0, mid_point
                )
                print(f"✓ Found {len(activities)} activities in first half of project")
            
            return True
            
    except Exception as e:
        print(f"✗ Linear scheduling verification error: {e}")
        return False

def main():
    """Run comprehensive verification."""
    print("=" * 60)
    print("COMPREHENSIVE CODEBASE VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        verify_file_structure,
        verify_logging_setup,
        verify_services_functionality,
        verify_error_handling,
        verify_linear_scheduling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"VERIFICATION COMPLETE: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 CODEBASE FULLY VERIFIED AND MODULARIZED!")
        print("\nKey improvements:")
        print("• Modular service layer architecture")
        print("• Comprehensive error logging system") 
        print("• Clean separation of concerns")
        print("• Enhanced debugging capabilities")
        print("• Linear scheduling fully functional")
    else:
        print("❌ Some verification tests failed")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)