#!/usr/bin/env python3
"""
Production readiness validation script for BBSchedule
Run this script to verify production deployment readiness
"""

import os
import sys
import time
import requests
from datetime import datetime

class ProductionValidator:
    """Validates production readiness of BBSchedule application."""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def log_check(self, name, status, message=""):
        """Log a check result."""
        self.checks.append({
            'name': name,
            'status': status,
            'message': message,
            'timestamp': datetime.now()
        })
        
        if status == 'PASS':
            self.passed += 1
            print(f"✅ {name}")
        else:
            self.failed += 1
            print(f"❌ {name}: {message}")
    
    def check_environment_variables(self):
        """Check required environment variables."""
        required_vars = [
            'DATABASE_URL',
            'SESSION_SECRET'
        ]
        
        for var in required_vars:
            if os.environ.get(var):
                self.log_check(f"Environment Variable: {var}", 'PASS')
            else:
                self.log_check(f"Environment Variable: {var}", 'FAIL', 
                             f"{var} is not set")
    
    def check_health_endpoints(self):
        """Check health endpoints."""
        endpoints = [
            ('/health/ping', 'Basic health check'),
            ('/health/ready', 'Readiness check'),
            ('/health/live', 'Liveness check'),
            ('/health/status', 'Status check'),
            ('/health/metrics', 'Metrics endpoint')
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_check(f"Health Endpoint: {endpoint}", 'PASS')
                else:
                    self.log_check(f"Health Endpoint: {endpoint}", 'FAIL',
                                 f"HTTP {response.status_code}")
            except requests.RequestException as e:
                self.log_check(f"Health Endpoint: {endpoint}", 'FAIL', str(e))
    
    def check_security_headers(self):
        """Check security headers."""
        try:
            response = requests.get(self.base_url, timeout=5)
            headers = response.headers
            
            security_headers = {
                'X-Frame-Options': 'Clickjacking protection',
                'X-Content-Type-Options': 'MIME sniffing protection',
                'X-XSS-Protection': 'XSS protection',
                'Content-Security-Policy': 'CSP protection',
                'Referrer-Policy': 'Referrer policy'
            }
            
            for header, description in security_headers.items():
                if header in headers:
                    self.log_check(f"Security Header: {header}", 'PASS')
                else:
                    self.log_check(f"Security Header: {header}", 'FAIL',
                                 f"Missing {description}")
        
        except requests.RequestException as e:
            self.log_check("Security Headers", 'FAIL', f"Cannot reach application: {e}")
    
    def check_database_performance(self):
        """Check database performance."""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health/ready", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                db_response_time = data.get('checks', {}).get('database', {}).get('response_time_ms', 0)
                
                if db_response_time < 500:
                    self.log_check("Database Performance", 'PASS',
                                 f"Response time: {db_response_time}ms")
                else:
                    self.log_check("Database Performance", 'FAIL',
                                 f"Slow response: {db_response_time}ms")
            else:
                self.log_check("Database Performance", 'FAIL',
                             f"Health check failed: HTTP {response.status_code}")
        
        except requests.RequestException as e:
            self.log_check("Database Performance", 'FAIL', str(e))
    
    def check_application_functionality(self):
        """Check core application functionality."""
        # Check dashboard
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                self.log_check("Dashboard Access", 'PASS')
            else:
                self.log_check("Dashboard Access", 'FAIL',
                             f"HTTP {response.status_code}")
        except requests.RequestException as e:
            self.log_check("Dashboard Access", 'FAIL', str(e))
        
        # Check API endpoints
        api_endpoints = [
            '/api/dashboard/metrics',
            '/api/monitoring/metrics',
            '/projects'
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 302]:  # 302 for redirects
                    self.log_check(f"API Endpoint: {endpoint}", 'PASS')
                else:
                    self.log_check(f"API Endpoint: {endpoint}", 'FAIL',
                                 f"HTTP {response.status_code}")
            except requests.RequestException as e:
                self.log_check(f"API Endpoint: {endpoint}", 'FAIL', str(e))
    
    def check_file_permissions(self):
        """Check file and directory permissions."""
        critical_paths = [
            ('uploads', 'Upload directory'),
            ('.', 'Application directory'),
        ]
        
        for path, description in critical_paths:
            if os.path.exists(path):
                if os.access(path, os.R_OK | os.W_OK):
                    self.log_check(f"File Permissions: {description}", 'PASS')
                else:
                    self.log_check(f"File Permissions: {description}", 'FAIL',
                                 "Directory not writable")
            else:
                self.log_check(f"File Permissions: {description}", 'FAIL',
                             "Directory does not exist")
    
    def check_logging_system(self):
        """Check logging system."""
        # Check if logs are being written
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Production validation test log")
            self.log_check("Logging System", 'PASS')
        except Exception as e:
            self.log_check("Logging System", 'FAIL', str(e))
    
    def run_all_checks(self):
        """Run all production readiness checks."""
        print("🚀 BBSchedule Production Readiness Validation")
        print("=" * 50)
        print(f"Testing application at: {self.base_url}")
        print(f"Started at: {datetime.now()}")
        print()
        
        # Run all checks
        self.check_environment_variables()
        self.check_health_endpoints()
        self.check_security_headers()
        self.check_database_performance()
        self.check_application_functionality()
        self.check_file_permissions()
        self.check_logging_system()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Total checks: {len(self.checks)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n🎉 All checks passed! Application is production-ready.")
            return True
        else:
            print(f"\n⚠️  {self.failed} checks failed. Review issues before deploying.")
            return False
    
    def generate_report(self, filename="production_validation_report.txt"):
        """Generate detailed validation report."""
        with open(filename, 'w') as f:
            f.write("BBSchedule Production Validation Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Application URL: {self.base_url}\n")
            f.write(f"Total Checks: {len(self.checks)}\n")
            f.write(f"Passed: {self.passed}\n")
            f.write(f"Failed: {self.failed}\n\n")
            
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            for check in self.checks:
                status_emoji = "✅" if check['status'] == 'PASS' else "❌"
                f.write(f"{status_emoji} {check['name']}: {check['status']}\n")
                if check['message']:
                    f.write(f"   Message: {check['message']}\n")
                f.write(f"   Time: {check['timestamp']}\n\n")
        
        print(f"📄 Detailed report saved to: {filename}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BBSchedule Production Validation')
    parser.add_argument('--url', default='http://localhost:5000',
                      help='Application URL to test (default: http://localhost:5000)')
    parser.add_argument('--report', action='store_true',
                      help='Generate detailed report file')
    
    args = parser.parse_args()
    
    validator = ProductionValidator(args.url)
    success = validator.run_all_checks()
    
    if args.report:
        validator.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()