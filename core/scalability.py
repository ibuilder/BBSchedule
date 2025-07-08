"""
Enterprise scalability and performance optimization for BBSchedule
"""

import os
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import hashlib
import pickle
from flask import request, current_app
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import logging

# Performance logging
perf_logger = logging.getLogger('performance')

class EnterpriseCache:
    """Enterprise caching layer with Redis backend"""
    
    def __init__(self, redis_url=None, default_timeout=3600):
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.default_timeout = default_timeout
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis with enterprise configuration"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=100,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            perf_logger.info("Redis connection established")
        except Exception as e:
            perf_logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            perf_logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if self.redis_client:
                timeout = timeout or self.default_timeout
                serialized = json.dumps(value, default=str)
                return self.redis_client.setex(key, timeout, serialized)
            return False
        except Exception as e:
            perf_logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            return False
        except Exception as e:
            perf_logger.error(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            perf_logger.error(f"Cache invalidate error: {e}")
            return 0

def cache_result(timeout=3600, key_prefix="", invalidate_on=None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{_generate_cache_key(args, kwargs)}"
            
            # Try to get from cache
            cached_result = enterprise_cache.get(cache_key)
            if cached_result is not None:
                perf_logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            enterprise_cache.set(cache_key, result, timeout)
            perf_logger.debug(f"Cache miss, stored: {cache_key}")
            
            return result
        
        # Add cache invalidation method
        wrapper.invalidate_cache = lambda *args, **kwargs: enterprise_cache.delete(
            f"{key_prefix}:{func.__name__}:{_generate_cache_key(args, kwargs)}"
        )
        
        return wrapper
    return decorator

def _generate_cache_key(args, kwargs):
    """Generate consistent cache key from function arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

class DatabasePool:
    """Enterprise database connection pooling"""
    
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_connection_pool()
    
    def _setup_connection_pool(self):
        """Setup optimized connection pool"""
        engine_options = {
            'poolclass': pool.QueuePool,
            'pool_size': 20,           # Base connections
            'max_overflow': 30,        # Additional connections
            'pool_timeout': 30,        # Wait time for connection
            'pool_recycle': 3600,      # Recycle connections every hour
            'pool_pre_ping': True,     # Validate connections
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'BBSchedule-Enterprise'
            }
        }
        
        # PostgreSQL specific optimizations
        if 'postgresql' in self.database_url:
            engine_options['connect_args'].update({
                'options': '-c statement_timeout=30000'  # 30 second query timeout
            })
        
        self.engine = create_engine(self.database_url, **engine_options)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        perf_logger.info("Database connection pool initialized")
    
    def get_session(self):
        """Get database session from pool"""
        return self.SessionLocal()
    
    def get_pool_status(self):
        """Get connection pool status"""
        if self.engine and hasattr(self.engine.pool, 'status'):
            return {
                'size': self.engine.pool.size(),
                'checked_in': self.engine.pool.checkedin(),
                'checked_out': self.engine.pool.checkedout(),
                'overflow': self.engine.pool.overflow(),
                'invalid': self.engine.pool.invalid()
            }
        return {}

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_project_queries():
        """Optimize project-related database queries"""
        optimizations = [
            # Index suggestions
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_status ON projects(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_created_by ON projects(created_by);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activities_project_id ON activities(project_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activities_status ON activities(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activities_start_date ON activities(start_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activities_end_date ON activities(end_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dependencies_predecessor ON dependencies(predecessor_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dependencies_successor ON dependencies(successor_id);",
            
            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activities_project_status ON activities(project_id, status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activities_dates_range ON activities(start_date, end_date);",
        ]
        return optimizations
    
    @staticmethod
    def get_slow_query_recommendations():
        """Get recommendations for slow queries"""
        return [
            "Use SELECT with specific columns instead of SELECT *",
            "Add proper WHERE clause indexing",
            "Use LIMIT for pagination instead of fetching all records",
            "Consider query result caching for frequently accessed data",
            "Use database views for complex repeated queries",
            "Implement read replicas for reporting queries"
        ]

class LoadBalancer:
    """Application load balancing utilities"""
    
    def __init__(self):
        self.request_counts = {}
        self.response_times = {}
    
    def track_request(self, endpoint, response_time):
        """Track request for load analysis"""
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = 0
            self.response_times[endpoint] = []
        
        self.request_counts[endpoint] += 1
        self.response_times[endpoint].append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times[endpoint]) > 100:
            self.response_times[endpoint] = self.response_times[endpoint][-100:]
    
    def get_load_stats(self):
        """Get current load statistics"""
        stats = {}
        for endpoint in self.request_counts:
            response_times = self.response_times[endpoint]
            if response_times:
                stats[endpoint] = {
                    'request_count': self.request_counts[endpoint],
                    'avg_response_time': sum(response_times) / len(response_times),
                    'max_response_time': max(response_times),
                    'min_response_time': min(response_times)
                }
        return stats

class SessionManager:
    """Enterprise session management with Redis backend"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.session_timeout = timedelta(hours=8)  # Enterprise session timeout
    
    def create_session(self, user_id, user_data):
        """Create new user session"""
        session_id = os.urandom(32).hex()
        session_data = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        if self.redis_client:
            self.redis_client.setex(
                f"session:{session_id}",
                int(self.session_timeout.total_seconds()),
                json.dumps(session_data, default=str)
            )
        
        return session_id
    
    def get_session(self, session_id):
        """Get session data"""
        if self.redis_client:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                # Update last activity
                data['last_activity'] = datetime.utcnow().isoformat()
                self.redis_client.setex(
                    f"session:{session_id}",
                    int(self.session_timeout.total_seconds()),
                    json.dumps(data, default=str)
                )
                return data
        return None
    
    def invalidate_session(self, session_id):
        """Invalidate user session"""
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")

class AutoScaler:
    """Auto-scaling recommendations and utilities"""
    
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
    
    def analyze_scaling_needs(self):
        """Analyze current metrics to determine scaling needs"""
        metrics_summary = self.metrics.get_metrics_summary()
        
        recommendations = []
        
        # CPU scaling
        if 'cpu_usage' in metrics_summary:
            cpu_avg = metrics_summary['cpu_usage']['average']
            if cpu_avg > 80:
                recommendations.append({
                    'type': 'scale_up',
                    'reason': f'High CPU usage: {cpu_avg:.1f}%',
                    'metric': 'cpu_usage',
                    'value': cpu_avg
                })
            elif cpu_avg < 30:
                recommendations.append({
                    'type': 'scale_down',
                    'reason': f'Low CPU usage: {cpu_avg:.1f}%',
                    'metric': 'cpu_usage',
                    'value': cpu_avg
                })
        
        # Memory scaling
        if 'memory_usage' in metrics_summary:
            memory_avg = metrics_summary['memory_usage']['average']
            if memory_avg > 85:
                recommendations.append({
                    'type': 'scale_up',
                    'reason': f'High memory usage: {memory_avg:.1f}%',
                    'metric': 'memory_usage',
                    'value': memory_avg
                })
        
        # Response time scaling
        if 'response_time' in metrics_summary:
            response_avg = metrics_summary['response_time']['average']
            if response_avg > 2.0:
                recommendations.append({
                    'type': 'scale_up',
                    'reason': f'High response time: {response_avg:.2f}s',
                    'metric': 'response_time',
                    'value': response_avg
                })
        
        return recommendations

# Global enterprise components
enterprise_cache = EnterpriseCache()
query_optimizer = QueryOptimizer()
load_balancer = LoadBalancer()
auto_scaler = None  # Will be initialized with metrics collector

def init_enterprise_scalability(app, metrics_collector):
    """Initialize enterprise scalability components"""
    global auto_scaler
    auto_scaler = AutoScaler(metrics_collector)
    
    # Setup database pooling
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if database_url:
        db_pool = DatabasePool(database_url)
        app.db_pool = db_pool
    
    # Setup session management
    session_manager = SessionManager(enterprise_cache.redis_client)
    app.session_manager = session_manager
    
    perf_logger.info("Enterprise scalability components initialized")
    
    return {
        'cache': enterprise_cache,
        'db_pool': getattr(app, 'db_pool', None),
        'session_manager': session_manager,
        'load_balancer': load_balancer,
        'auto_scaler': auto_scaler
    }