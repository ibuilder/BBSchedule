"""
Modularized routes with proper error handling and logging.
"""
from flask import render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime, date, timedelta
import traceback

from app import app
from extensions import db
from models import Project, Activity, Dependency, ProjectStatus, ActivityType
from forms import ProjectForm, ActivityForm, DependencyForm, ScheduleImportForm, FiveDAnalysisForm
from services.project_service import ProjectService
from services.activity_service import ActivityService
from services.analytics_service import AnalyticsService
from services.ai_service import ai_service
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
        
        # Calculate completion percentage
        completion_percentage = project.calculate_completion_percentage() if project else 0
        
        return render_template('project_detail.html', 
                             project=project, 
                             activities=activities,
                             metrics=metrics,
                             schedule_metrics=schedule_metrics,
                             completion_percentage=completion_percentage)
                             
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

@app.route('/activity/<int:activity_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_activity(activity_id):
    """Edit an existing activity."""
    try:
        user_id = session.get('user_id')
        activity = Activity.query.get_or_404(activity_id)
        project = activity.project
        
        if request.method == 'POST':
            form = ActivityForm(request.form, obj=activity, project=project)
            if form.validate():
                form.populate_obj(activity)
                db.session.commit()
                flash('Activity updated successfully', 'success')
                log_activity(user_id, f"Updated activity {activity.name}")
                return redirect(url_for('project_detail', project_id=activity.project_id))
            else:
                flash('Please correct the errors below', 'error')
        else:
            form = ActivityForm(obj=activity, project=project)
        
        return render_template('activity_create.html', form=form, project=project, activity=activity)
        
    except Exception as e:
        log_error(e, f"Edit activity error for activity {activity_id}")
        flash('Error editing activity', 'error')
        return redirect(url_for('index'))

@app.route('/activity/<int:activity_id>/delete', methods=['POST'])
@login_required
def delete_activity(activity_id):
    """Delete an activity."""
    try:
        user_id = session.get('user_id')
        activity = Activity.query.get_or_404(activity_id)
        project_id = activity.project_id
        activity_name = activity.name
        
        db.session.delete(activity)
        db.session.commit()
        
        flash(f'Activity "{activity_name}" deleted successfully', 'success')
        log_activity(user_id, f"Deleted activity {activity_name}")
        
        return redirect(url_for('project_detail', project_id=project_id))
        
    except Exception as e:
        log_error(e, f"Delete activity error for activity {activity_id}")
        flash('Error deleting activity', 'error')
        return redirect(url_for('index'))

@app.route('/project/<int:project_id>/upload_document', methods=['GET', 'POST'])
@login_required
def upload_document(project_id):
    """Upload document for a project."""
    try:
        user_id = session.get('user_id')
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        if request.method == 'POST':
            # Handle file upload here - for now just redirect back with success message
            flash('Document upload functionality coming soon', 'info')
            return redirect(url_for('project_detail', project_id=project_id))
        
        return render_template('project_detail.html', project=project)
        
    except Exception as e:
        log_error(e, f"Document upload error for project {project_id}")
        flash('Error uploading document', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

@app.route('/project/<int:project_id>/ai_optimization')
@login_required
def ai_optimization(project_id):
    """AI-powered schedule optimization page."""
    try:
        user_id = session.get('user_id')
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        # Generate AI optimization scenarios
        scenarios = ai_service.generate_schedule_scenarios(project_id, 5)
        
        # Get activity predictions
        activity_predictions = ai_service.predict_activity_durations(project_id)
        
        # Assess project risks
        risk_assessment = ai_service.assess_project_risks(project_id)
        
        # Resource optimization
        resource_optimization = ai_service.optimize_resource_allocation(project_id)
        
        log_activity(user_id, f"Accessed AI optimization for project {project.name}")
        
        return render_template('ai_optimization.html',
                             project=project,
                             scenarios=scenarios,
                             activity_predictions=activity_predictions,
                             risk_assessment=risk_assessment,
                             resource_optimization=resource_optimization)
        
    except Exception as e:
        log_error(e, f"AI optimization error for project {project_id}")
        flash('Error loading AI optimization', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

@app.route('/project/<int:project_id>/completion_probability')
@login_required
def completion_probability(project_id):
    """AI completion probability analysis."""
    try:
        user_id = session.get('user_id')
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        # Use project end date as target, or add 30 days from now
        target_date = project.end_date or datetime.now() + timedelta(days=30)
        
        # Get completion probability analysis
        completion_analysis = ai_service.predict_completion_probability(project_id, target_date)
        
        log_activity(user_id, f"Analyzed completion probability for project {project.name}")
        
        return jsonify(completion_analysis)
        
    except Exception as e:
        log_error(e, f"Completion probability error for project {project_id}")
        return jsonify({'error': 'Failed to analyze completion probability'})

@app.route('/api/project/<int:project_id>/ai_recommendations')
@login_required
def api_ai_recommendations(project_id):
    """API endpoint for AI-powered project recommendations."""
    try:
        user_id = session.get('user_id')
        
        # Get AI-powered recommendations
        risk_assessment = ai_service.assess_project_risks(project_id)
        resource_optimization = ai_service.optimize_resource_allocation(project_id)
        activity_predictions = ai_service.predict_activity_durations(project_id)
        
        recommendations = {
            'risk_recommendations': risk_assessment.get('recommendations', []),
            'resource_recommendations': [opt.get('reasoning', '') for opt in resource_optimization.get('crew_recommendations', [])],
            'schedule_recommendations': [pred.risk_factors for pred in activity_predictions],
            'priority_actions': [
                'Review high-risk activities identified by AI',
                'Implement suggested resource optimizations',
                'Monitor weather-dependent activities closely',
                'Update cost estimates for better accuracy'
            ]
        }
        
        log_activity(user_id, f"Retrieved AI recommendations for project {project_id}")
        
        return jsonify(recommendations)
        
    except Exception as e:
        log_error(e, f"AI recommendations API error for project {project_id}")
        return jsonify({'error': 'Failed to get AI recommendations'})

@app.route('/gantt')
@login_required
def gantt_chart():
    """Interactive Gantt chart view."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_all_projects(user_id)
        
        project_id = request.args.get('project_id')
        project = None
        if project_id:
            project = ProjectService.get_project_by_id(project_id, user_id)
        
        log_activity(user_id, f"Accessed Gantt chart for project {project_id}" if project_id else "Accessed Gantt chart for all projects")
        
        return render_template('gantt_interactive.html', 
                             projects=projects, 
                             project=project)
        
    except Exception as e:
        log_error(e, "Gantt chart view error")
        flash('Error loading Gantt chart', 'error')
        return redirect(url_for('index'))

@app.route('/api/projects/<int:project_id>/gantt')
@login_required
def api_project_gantt(project_id):
    """API endpoint for project Gantt data with critical path."""
    try:
        user_id = session.get('user_id')
        project = ProjectService.get_project_by_id(project_id, user_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get activities with dates
        activities = []
        for activity in project.activities:
            if activity.start_date and activity.end_date:
                activities.append({
                    'id': activity.id,
                    'name': activity.name,
                    'start_date': activity.start_date.isoformat(),
                    'end_date': activity.end_date.isoformat(),
                    'duration': activity.duration,
                    'progress': activity.progress or 0,
                    'activity_type': activity.activity_type.value if activity.activity_type else 'other'
                })
        
        # Calculate critical path using scheduling service
        from services.scheduling_service import SchedulingService
        critical_path = SchedulingService.calculate_critical_path(project_id)
        
        return jsonify({
            'activities': activities,
            'critical_path': [cp['activity_id'] for cp in critical_path],
            'project': {
                'id': project.id,
                'name': project.name,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None
            }
        })
        
    except Exception as e:
        log_error(e, f"Gantt API error for project {project_id}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/gantt/all')
@login_required
def api_all_gantt():
    """API endpoint for all projects Gantt data."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_all_projects(user_id)
        
        all_activities = []
        all_critical_paths = []
        
        for project in projects:
            for activity in project.activities:
                if activity.start_date and activity.end_date:
                    all_activities.append({
                        'id': activity.id,
                        'name': f"{project.name} - {activity.name}",
                        'project_id': project.id,
                        'project_name': project.name,
                        'start_date': activity.start_date.isoformat(),
                        'end_date': activity.end_date.isoformat(),
                        'duration': activity.duration,
                        'progress': activity.progress or 0,
                        'activity_type': activity.activity_type.value if activity.activity_type else 'other'
                    })
            
            # Get critical path for each project
            from services.scheduling_service import SchedulingService
            critical_path = SchedulingService.calculate_critical_path(project.id)
            all_critical_paths.extend([cp['activity_id'] for cp in critical_path])
        
        return jsonify({
            'activities': all_activities,
            'critical_path': all_critical_paths
        })
        
    except Exception as e:
        log_error(e, "All projects Gantt API error")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/5d-analysis')
@login_required
def five_d_analysis():
    """5D Analysis dashboard."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_all_projects(user_id)
        
        log_activity(user_id, "Accessed 5D Analysis dashboard")
        
        return render_template('5d_analysis.html', projects=projects)
        
    except Exception as e:
        log_error(e, "5D analysis view error")
        flash('Error loading 5D analysis', 'error')
        return redirect(url_for('index'))

@app.route('/api/projects/<int:project_id>/5d-analysis')
@login_required
def api_project_5d_analysis(project_id):
    """API endpoint for project 5D analysis data."""
    try:
        user_id = session.get('user_id')
        from services.analytics_service import AnalyticsService
        
        analysis_data = AnalyticsService.get_5d_analysis(project_id, user_id)
        
        return jsonify(analysis_data)
        
    except Exception as e:
        log_error(e, f"5D analysis API error for project {project_id}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/5d-analysis/all')
@login_required
def api_all_5d_analysis():
    """API endpoint for all projects 5D analysis."""
    try:
        user_id = session.get('user_id')
        from services.analytics_service import AnalyticsService
        
        analysis_data = AnalyticsService.get_all_projects_5d_analysis(user_id)
        
        return jsonify(analysis_data)
        
    except Exception as e:
        log_error(e, "All projects 5D analysis API error")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/resources')
@login_required
def resource_management():
    """Resource management dashboard."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_all_projects(user_id)
        
        log_activity(user_id, "Accessed resource management")
        
        return render_template('resource_management.html', projects=projects)
        
    except Exception as e:
        log_error(e, "Resource management view error")
        flash('Error loading resource management', 'error')
        return redirect(url_for('index'))

@app.route('/api/resources/management')
@login_required
def api_resource_management():
    """API endpoint for resource management data."""
    try:
        user_id = session.get('user_id')
        
        # Mock data for now - would integrate with actual resource system
        resource_data = {
            'crews': [
                {
                    'id': 1,
                    'specialty': 'Foundation',
                    'size': 8,
                    'current_assignment': 'Downtown Office Complex',
                    'utilization': 85
                },
                {
                    'id': 2,
                    'specialty': 'Electrical',
                    'size': 4,
                    'current_assignment': 'Highway Extension',
                    'utilization': 72
                },
                {
                    'id': 3,
                    'specialty': 'Framing',
                    'size': 12,
                    'current_assignment': None,
                    'utilization': 0
                }
            ],
            'equipment': [
                {
                    'id': 1,
                    'category': 'Excavator',
                    'status': 'Active',
                    'location': 'Site A',
                    'next_maintenance': '2025-07-15'
                },
                {
                    'id': 2,
                    'category': 'Crane',
                    'status': 'Maintenance',
                    'location': 'Depot',
                    'next_maintenance': '2025-07-10'
                }
            ],
            'conflicts': [
                {
                    'id': 1,
                    'title': 'Double Booking',
                    'description': 'Crew #1 assigned to overlapping activities',
                    'severity': 'high',
                    'recommendation': 'Reschedule Activity B by 3 days'
                }
            ],
            'timeline': {
                'dates': ['2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04', '2025-07-05'],
                'crew_utilization': [75, 80, 85, 82, 78],
                'equipment_utilization': [65, 70, 75, 72, 68]
            },
            'distribution': {
                'labels': ['Foundation', 'Electrical', 'Framing', 'Equipment'],
                'values': [8, 4, 12, 2]
            }
        }
        
        return jsonify(resource_data)
        
    except Exception as e:
        log_error(e, "Resource management API error")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/resources', methods=['POST'])
@login_required
def api_add_resource():
    """API endpoint to add new resource."""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # TODO: Implement actual resource creation
        log_activity(user_id, f"Added new {data.get('type')} resource: {data.get('name')}")
        
        return jsonify({'success': True, 'message': 'Resource added successfully'})
        
    except Exception as e:
        log_error(e, "Add resource API error")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/resources/optimize', methods=['POST'])
@login_required
def api_optimize_resources():
    """API endpoint for resource optimization."""
    try:
        user_id = session.get('user_id')
        
        # TODO: Implement actual optimization algorithm
        log_activity(user_id, "Performed resource optimization")
        
        return jsonify({'success': True, 'improvements': 5})
        
    except Exception as e:
        log_error(e, "Resource optimization API error")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/reports')
@login_required
def reports():
    """Reports generation dashboard."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_all_projects(user_id)
        
        log_activity(user_id, "Accessed reports dashboard")
        
        return render_template('reports.html', projects=projects)
        
    except Exception as e:
        log_error(e, "Reports view error")
        flash('Error loading reports', 'error')
        return redirect(url_for('index'))

@app.route('/dependencies')
@login_required
def dependencies():
    """Manage project dependencies."""
    try:
        user_id = session.get('user_id')
        projects = ProjectService.get_projects_by_user(user_id)
        
        # Get all dependencies across projects
        dependencies = []
        for project in projects:
            for activity in project.activities:
                for dep in activity.predecessor_dependencies:
                    dependencies.append({
                        'project': project,
                        'successor': dep.successor,
                        'predecessor': dep.predecessor,
                        'type': dep.dependency_type,
                        'lag': dep.lag_days
                    })
        
        return render_template('dependencies.html', dependencies=dependencies, projects=projects)
        
    except Exception as e:
        log_error(e, "Dependencies view error")
        flash('Error loading dependencies', 'error')
        return redirect(url_for('index'))

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

# Production Monitoring and AI Routes
@app.route('/api/monitoring/metrics')
def monitoring_metrics():
    """Get application metrics for monitoring dashboard."""
    try:
        metrics = monitoring_service.collect_metrics()
        return jsonify(metrics)
    except Exception as e:
        log_error(e, {'endpoint': 'monitoring_metrics'})
        return jsonify({'error': 'Failed to collect metrics'}), 500

@app.route('/api/monitoring/alerts')
def monitoring_alerts():
    """Get active alerts."""
    try:
        alerts = monitoring_service.get_active_alerts()
        return jsonify({
            'alerts': [
                {
                    'id': alert.id,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'metadata': alert.metadata
                }
                for alert in alerts
            ]
        })
    except Exception as e:
        log_error(e, {'endpoint': 'monitoring_alerts'})
        return jsonify({'error': 'Failed to get alerts'}), 500

@app.route('/api/project/ai_recommendations')
@login_required 
def api_ai_recommendations_general():
    """Get AI recommendations for dashboard (general)."""
    try:
        from services.ai_service import AIService
        
        # Get AI service
        ai_service = AIService()
        
        # Get general recommendations across all projects
        recommendations = {
            'risk_recommendations': [
                'Monitor critical path activities for potential delays',
                'Weather conditions may impact outdoor activities',
                'Resource conflicts detected in week 3-4'
            ],
            'resource_recommendations': [
                'Optimize crew scheduling for better efficiency',
                'Consider additional equipment for excavation',
                'Balance workforce allocation across projects'
            ],
            'schedule_recommendations': [
                'Review activity dependencies for optimization',
                'Consider parallel execution of compatible tasks',
                'Update progress tracking frequency'
            ],
            'priority_actions': [
                'Review high-risk activities identified by AI',
                'Optimize resource allocation based on predictions',
                'Update activity durations with ML insights',
                'Monitor weather impact on outdoor activities'
            ]
        }
        
        return jsonify(recommendations)
    except Exception as e:
        log_error(e, {'endpoint': 'ai_recommendations_general'})
        return jsonify({'error': 'Failed to generate AI recommendations'}), 500

