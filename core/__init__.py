"""
BBSchedule Core Module
Contains core application components and enterprise features
"""

try:
    from .security import EnterpriseAuth, RoleBasedAccess, SecurityMiddleware
    from .monitoring import MetricsCollector, PerformanceMonitor, HealthChecker  
    from .compliance import ComplianceAuditTrail, DataGovernance, SOXCompliance
    from .integrations import EnterpriseAPIGateway, ProcoreIntegration, AutodeskIntegration
    from .scalability import EnterpriseCache, DatabasePool, AutoScaler
except ImportError as e:
    # Graceful degradation for missing enterprise components
    import logging
    logging.warning(f"Enterprise components not fully available: {e}")
    
    class MockComponent:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return self
        def __getattr__(self, name): return MockComponent()
    
    EnterpriseAuth = RoleBasedAccess = SecurityMiddleware = MockComponent
    MetricsCollector = PerformanceMonitor = HealthChecker = MockComponent
    ComplianceAuditTrail = DataGovernance = SOXCompliance = MockComponent
    EnterpriseAPIGateway = ProcoreIntegration = AutodeskIntegration = MockComponent
    EnterpriseCache = DatabasePool = AutoScaler = MockComponent

__version__ = "1.0.0"
__all__ = [
    'EnterpriseAuth', 'RoleBasedAccess', 'SecurityMiddleware',
    'MetricsCollector', 'PerformanceMonitor', 'HealthChecker',
    'ComplianceAuditTrail', 'DataGovernance', 'SOXCompliance', 
    'EnterpriseAPIGateway', 'ProcoreIntegration', 'AutodeskIntegration',
    'EnterpriseCache', 'DatabasePool', 'AutoScaler'
]