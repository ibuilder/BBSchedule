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
                             metrics=dashboard_metrics)
                             
    except Exception as e:
        log_error(e, "Dashboard loading error")
        flash('Error loading dashboard', 'error')
        return render_template('index.html', 
                             projects=[],
                             recent_activities=[],
                             metrics={})

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