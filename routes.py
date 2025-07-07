"""
Modularized routes with proper error handling and logging.
"""
from flask import render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime, date
import traceback

from app import app
from extensions import db
from models import Project, Activity, Dependency, ProjectStatus, ActivityType
from forms import ProjectForm, ActivityForm, DependencyForm, ScheduleImportForm, FiveDAnalysisForm
from services.project_service import ProjectService
from services.activity_service import ActivityService
from services.analytics_service import AnalyticsService
from logger import log_error, log_activity, log_performance
import utils
import import_utils
import time

def login_required(f):
    """Login decorator with proper error handling."""
    def decorated_function(*args, **kwargs):
        try:
            # Simple session-based authentication
            if 'user_id' not in session:
                session['user_id'] = 'anonymous_user'  # Simple default for demo
            return f(*args, **kwargs)
        except Exception as e:
            log_error(e, f"Authentication error in {f.__name__}")
            flash('Authentication error occurred', 'error')
            return redirect(url_for('login'))
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login system with error handling."""
    try:
        if request.method == 'POST':
            username = request.form.get('username', 'demo_user')
            session['user_id'] = username
            session['logged_in'] = True
            log_activity(username, "User logged in")
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        
        return render_template('auth/login.html')
        
    except Exception as e:
        log_error(e, "Login error")
        flash('Login error occurred', 'error')
        return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user with proper cleanup."""
    try:
        user_id = session.get('user_id')
        session.clear()
        log_activity(user_id, "User logged out")
        flash('Logged out successfully', 'info')
        return redirect(url_for('login'))
        
    except Exception as e:
        log_error(e, "Logout error")
        session.clear()
        return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Enhanced dashboard with comprehensive metrics and error handling."""
    start_time = time.time()
    
    try:
        user_id = session.get('user_id')
        
        # Get dashboard metrics using service
        dashboard_metrics = AnalyticsService.calculate_dashboard_metrics()
        
        # Get projects and recent activities
        projects = ProjectService.get_all_projects(user_id)
        recent_activities = Activity.query.order_by(Activity.updated_at.desc()).limit(10).all()
        
        # Performance logging
        execution_time = time.time() - start_time
        log_performance('dashboard_load', execution_time, f"Projects: {len(projects)}")
        
        return render_template('index.html', 
                             projects=projects,
                             recent_activities=recent_activities,
                             metrics=dashboard_metrics,
                             total_projects=dashboard_metrics.get('total_projects', 0),
                             active_projects=dashboard_metrics.get('active_projects', 0),
                             total_activities=dashboard_metrics.get('total_activities', 0),
                             completed_activities=dashboard_metrics.get('completed_activities', 0),
                             avg_completion=dashboard_metrics.get('completion_rate', 0))
                             
    except Exception as e:
        log_error(e, "Dashboard loading error")
        flash('Error loading dashboard', 'error')
        return render_template('index.html', 
                             projects=[],
                             recent_activities=[],
                             metrics={},
                             total_projects=0,
                             active_projects=0,
                             total_activities=0,
                             completed_activities=0,
                             avg_completion=0)

@app.route('/projects')
@login_required
def projects():
    """List all projects with enhanced filtering and error handling."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_all_projects(user_id)
        
        return render_template('projects.html', projects=projects)
        
    except Exception as e:
        log_error(e, "Projects listing error")
        flash('Error loading projects', 'error')
        return render_template('projects.html', projects=[])

@app.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create a new project with comprehensive error handling."""
    form = ProjectForm()
    
    try:
        if form.validate_on_submit():
            user_id = session.get('user_id')
            
            # Use service to create project
            project = ProjectService.create_project(form.data, user_id)
            
            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('project_detail', project_id=project.id))
        
        return render_template('project_create.html', form=form, project=None)
        
    except Exception as e:
        log_error(e, f"Project creation error: {form.data if form else 'No form data'}")
        flash('Error creating project', 'error')
        return render_template('project_create.html', form=form, project=None)

@app.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    """View project details with comprehensive metrics."""
    try:
        user_id = session.get('user_id')
        
        # Get project using service
        project = ProjectService.get_project_by_id(project_id, user_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        # Get project metrics
        metrics = ProjectService.get_project_metrics(project_id)
        schedule_metrics = AnalyticsService.calculate_project_schedule_metrics(project_id)
        
        # Get activities using service
        activities = ActivityService.get_activities_by_project(project_id, user_id)
        
        return render_template('project_detail.html', 
                             project=project, 
                             activities=activities,
                             metrics=metrics,
                             schedule_metrics=schedule_metrics)
                             
    except Exception as e:
        log_error(e, f"Project detail error for project {project_id}")
        flash('Error loading project details', 'error')
        return redirect(url_for('projects'))

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit project details with error handling."""
    try:
        user_id = session.get('user_id')
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        form = ProjectForm(obj=project)
        
        if form.validate_on_submit():
            # Use service to update project
            updated_project = ProjectService.update_project(project_id, form.data, user_id)
            
            flash(f'Project "{updated_project.name}" updated successfully!', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('project_create.html', form=form, project=project)
        
    except Exception as e:
        log_error(e, f"Project edit error for project {project_id}")
        flash('Error updating project', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

@app.route('/projects/<int:project_id>/activities/create', methods=['GET', 'POST'])
@login_required
def create_activity(project_id):
    """Create a new activity with location support."""
    try:
        user_id = session.get('user_id')
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        form = ActivityForm(project=project)
        
        if form.validate_on_submit():
            # Use service to create activity
            activity = ActivityService.create_activity(project_id, form.data, user_id)
            
            flash(f'Activity "{activity.name}" created successfully!', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('activity_create.html', form=form, project=project)
        
    except Exception as e:
        log_error(e, f"Activity creation error for project {project_id}")
        flash('Error creating activity', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

@app.route('/import')
@login_required
def import_schedule():
    """Import schedule files placeholder."""
    try:
        flash('Import functionality coming soon!', 'info')
        return redirect(url_for('projects'))
    except Exception as e:
        log_error(e, "Import schedule error")
        return redirect(url_for('projects'))

@app.route('/calendar')
@login_required
def calendar_view():
    """Display calendar view of all activities."""
    try:
        user_id = session.get('user_id', 'anonymous_user')
        projects = ProjectService.get_all_projects(user_id)
        
        from datetime import datetime
        current_month = datetime.now().strftime('%B %Y')
        
        return render_template('calendar_view.html', 
                             projects=projects,
                             current_month=current_month)
    except Exception as e:
        log_error(e, "Calendar view error")
        flash('Error loading calendar', 'error')
        return redirect(url_for('index'))

# API Routes with proper error handling
@app.route('/api/dashboard/metrics')
@login_required
def api_dashboard_metrics():
    """API endpoint for real-time dashboard metrics."""
    try:
        metrics = AnalyticsService.calculate_dashboard_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        log_error(e, "API dashboard metrics error")
        return jsonify({'error': 'Failed to load metrics'}), 500

@app.route('/api/projects/<int:project_id>/5d-analysis')
@login_required
def api_5d_analysis(project_id):
    """API endpoint for 5D analysis with comprehensive error handling."""
    try:
        analysis_type = request.args.get('type', 'complete')
        analysis = AnalyticsService.generate_5d_analysis(project_id, analysis_type)
        
        return jsonify(analysis)
        
    except Exception as e:
        log_error(e, f"5D analysis error for project {project_id}")
        return jsonify({'error': 'Analysis failed'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    log_error(error, "Page not found")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with proper logging."""
    log_error(error, "Internal server error")
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions."""
    log_error(error, "Unhandled exception")
    db.session.rollback()
    flash('An unexpected error occurred', 'error')
    return render_template('500.html'), 500

# Calendar API endpoints
@app.route('/api/calendar/activities')
@login_required
def api_calendar_activities():
    """API endpoint for calendar activities."""
    try:
        user_id = session.get('user_id', 'anonymous_user')
        date_filter = request.args.get('date')
        project_filter = request.args.get('project_id')
        
        query = db.session.query(Activity, Project).join(Project)
        
        if project_filter:
            query = query.filter(Activity.project_id == project_filter)
            
        if date_filter:
            from datetime import datetime
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(
                Activity.start_date <= target_date,
                Activity.end_date >= target_date
            )
        
        results = query.all()
        
        activities = []
        for activity, project in results:
            activities.append({
                'id': activity.id,
                'name': activity.name,
                'project_id': project.id,
                'project_name': project.name,
                'start': activity.start_date.isoformat() if activity.start_date else None,
                'end': activity.end_date.isoformat() if activity.end_date else None,
                'progress': activity.progress or 0,
                'activity_type': activity.activity_type.value if activity.activity_type else 'task',
                'is_critical': False,  # TODO: Calculate from critical path
                'location_start': activity.location_start,
                'location_end': activity.location_end,
                'description': activity.description
            })
        
        return jsonify({'activities': activities})
        
    except Exception as e:
        log_error(e, "Calendar activities API error")
        return jsonify({'error': 'Failed to load calendar activities'}), 500

@app.route('/api/calendar/stats')
@login_required
def api_calendar_stats():
    """API endpoint for calendar statistics."""
    try:
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Activities this week
        activities_this_week = Activity.query.filter(
            Activity.start_date >= week_start,
            Activity.start_date <= week_end
        ).count()
        
        # Completed this week
        completed_this_week = Activity.query.filter(
            Activity.start_date >= week_start,
            Activity.start_date <= week_end,
            Activity.progress == 100
        ).count()
        
        # Overdue activities
        overdue_activities = Activity.query.filter(
            Activity.end_date < today,
            Activity.progress < 100
        ).count()
        
        # Upcoming deadlines (next 7 days)
        upcoming_end = today + timedelta(days=7)
        upcoming_deadlines = Activity.query.filter(
            Activity.end_date >= today,
            Activity.end_date <= upcoming_end,
            Activity.progress < 100
        ).count()
        
        return jsonify({
            'activities_this_week': activities_this_week,
            'completed_this_week': completed_this_week,
            'overdue_activities': overdue_activities,
            'upcoming_deadlines': upcoming_deadlines
        })
        
    except Exception as e:
        log_error(e, "Calendar stats API error")
        return jsonify({'error': 'Failed to load calendar stats'}), 500

@app.route('/api/activities/<int:activity_id>/complete', methods=['POST'])
@login_required
def api_complete_activity(activity_id):
    """API endpoint to mark activity as complete."""
    try:
        activity = Activity.query.get_or_404(activity_id)
        activity.progress = 100
        from datetime import datetime
        activity.updated_at = datetime.now()
        
        db.session.commit()
        
        log_activity(session.get('user_id', 'anonymous_user'), 
                    'completed_activity', 
                    f"Activity: {activity.name}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        log_error(e, f"Complete activity error for activity {activity_id}")
        db.session.rollback()
        return jsonify({'error': 'Failed to complete activity'}), 500

@app.route('/api/activities/create', methods=['POST'])
@login_required
def api_create_activity():
    """API endpoint to create new activity."""
    try:
        data = request.get_json()
        
        from datetime import datetime, timedelta
        
        activity = Activity(
            name=data['name'],
            description=data.get('description'),
            project_id=data['project_id'],
            activity_type=ActivityType(data.get('activity_type', 'task')),
            duration=int(data.get('duration', 1)),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            progress=0
        )
        
        # Calculate end date
        if activity.start_date and activity.duration:
            activity.end_date = activity.start_date + timedelta(days=activity.duration)
        
        db.session.add(activity)
        db.session.commit()
        
        log_activity(session.get('user_id', 'anonymous_user'),
                    'created_activity',
                    f"Activity: {activity.name}")
        
        return jsonify({'success': True, 'activity_id': activity.id})
        
    except Exception as e:
        log_error(e, "Create activity API error")
        db.session.rollback()
        return jsonify({'error': 'Failed to create activity'}), 500