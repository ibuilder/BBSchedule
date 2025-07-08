"""
Database optimization and indexing for production performance
"""
from sqlalchemy import text, Index
from extensions import db
from models import Project, Activity, Dependency, Schedule, Document, ScheduleMetrics

def create_production_indexes():
    """Create database indexes for optimal production performance."""
    
    # Project indexes
    indexes = [
        # Project indexes for common queries
        Index('idx_project_status', Project.status),
        Index('idx_project_start_date', Project.start_date),
        Index('idx_project_end_date', Project.end_date),
        Index('idx_project_created_at', Project.created_at),
        Index('idx_project_building_type', Project.building_type),
        
        # Activity indexes for performance
        Index('idx_activity_project_id', Activity.project_id),
        Index('idx_activity_status', Activity.status),
        Index('idx_activity_start_date', Activity.start_date),
        Index('idx_activity_end_date', Activity.end_date),
        Index('idx_activity_type', Activity.activity_type),
        Index('idx_activity_progress', Activity.progress),
        Index('idx_activity_project_status', Activity.project_id, Activity.status),
        Index('idx_activity_date_range', Activity.start_date, Activity.end_date),
        
        # Dependency indexes
        Index('idx_dependency_predecessor', Dependency.predecessor_id),
        Index('idx_dependency_successor', Dependency.successor_id),
        Index('idx_dependency_type', Dependency.dependency_type),
        
        # Schedule indexes
        Index('idx_schedule_project_id', Schedule.project_id),
        Index('idx_schedule_type', Schedule.schedule_type),
        Index('idx_schedule_baseline', Schedule.is_baseline),
        Index('idx_schedule_created_at', Schedule.created_at),
        
        # Document indexes
        Index('idx_document_project_id', Document.project_id),
        Index('idx_document_type', Document.document_type),
        Index('idx_document_created_at', Document.created_at),
        
        # Metrics indexes
        Index('idx_metrics_project_id', ScheduleMetrics.project_id),
        Index('idx_metrics_date', ScheduleMetrics.date),
        Index('idx_metrics_project_date', ScheduleMetrics.project_id, ScheduleMetrics.date),
    ]
    
    # Create indexes that don't already exist
    for index in indexes:
        try:
            index.create(db.engine, checkfirst=True)
            print(f"Created index: {index.name}")
        except Exception as e:
            print(f"Index {index.name} already exists or error: {e}")

def optimize_database_settings():
    """Optimize PostgreSQL settings for production."""
    
    optimization_queries = [
        # Analyze tables for better query planning
        "ANALYZE projects;",
        "ANALYZE activities;",
        "ANALYZE dependencies;",
        "ANALYZE schedules;",
        "ANALYZE documents;",
        "ANALYZE schedule_metrics;",
        
        # Update statistics
        "UPDATE pg_stat_user_tables SET n_tup_ins = n_tup_ins;",
        
        # Vacuum analyze for performance
        "VACUUM ANALYZE;",
    ]
    
    for query in optimization_queries:
        try:
            db.session.execute(text(query))
            db.session.commit()
            print(f"Executed: {query}")
        except Exception as e:
            print(f"Error executing {query}: {e}")
            db.session.rollback()

def get_database_performance_stats():
    """Get database performance statistics."""
    
    stats_queries = {
        'table_sizes': """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as raw_size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY raw_size DESC;
        """,
        
        'index_usage': """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_tup_read,
                idx_tup_fetch,
                idx_scan
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC;
        """,
        
        'slow_queries': """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY total_time DESC
            LIMIT 10;
        """,
        
        'connection_stats': """
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity;
        """
    }
    
    results = {}
    for stat_name, query in stats_queries.items():
        try:
            result = db.session.execute(text(query)).fetchall()
            results[stat_name] = result
            print(f"Retrieved {stat_name}: {len(result)} rows")
        except Exception as e:
            print(f"Error getting {stat_name}: {e}")
            results[stat_name] = []
    
    return results

def cleanup_old_data():
    """Clean up old data that may impact performance."""
    
    cleanup_queries = [
        # Remove old schedule metrics (keep last 90 days)
        """
        DELETE FROM schedule_metrics 
        WHERE date < CURRENT_DATE - INTERVAL '90 days';
        """,
        
        # Remove orphaned documents
        """
        DELETE FROM documents 
        WHERE project_id NOT IN (SELECT id FROM projects);
        """,
        
        # Remove orphaned dependencies
        """
        DELETE FROM dependencies 
        WHERE predecessor_id NOT IN (SELECT id FROM activities)
        OR successor_id NOT IN (SELECT id FROM activities);
        """,
    ]
    
    for query in cleanup_queries:
        try:
            result = db.session.execute(text(query))
            db.session.commit()
            print(f"Cleanup query executed: {result.rowcount} rows affected")
        except Exception as e:
            print(f"Error in cleanup: {e}")
            db.session.rollback()

def backup_database():
    """Create database backup (requires pg_dump)."""
    import subprocess
    import os
    from datetime import datetime
    
    try:
        # Get database URL
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            print("DATABASE_URL not found")
            return False
        
        # Create backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        
        # Execute pg_dump
        cmd = f"pg_dump {db_url} > {backup_filename}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Database backup created: {backup_filename}")
            return True
        else:
            print(f"Backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Backup error: {e}")
        return False

def run_full_optimization():
    """Run complete database optimization."""
    print("Starting database optimization...")
    
    print("\n1. Creating production indexes...")
    create_production_indexes()
    
    print("\n2. Optimizing database settings...")
    optimize_database_settings()
    
    print("\n3. Cleaning up old data...")
    cleanup_old_data()
    
    print("\n4. Getting performance statistics...")
    stats = get_database_performance_stats()
    
    print("\n5. Creating backup...")
    backup_database()
    
    print("\nDatabase optimization completed!")
    return stats

if __name__ == "__main__":
    # Run optimization if called directly
    from app import create_app
    
    app = create_app()
    with app.app_context():
        run_full_optimization()