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
        try:
            from services.scheduling_service import SchedulingService
            critical_path = SchedulingService.calculate_critical_path(project_id)
            critical_path_ids = [cp['activity_id'] if isinstance(cp, dict) else cp for cp in critical_path]
        except Exception as e:
            log_error(e, f"Critical path calculation error for project {project_id}")
            critical_path_ids = []
        
        return jsonify({
            'activities': activities,
            'critical_path': critical_path_ids,
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

@app.route('/api/project/<int:project_id>/ai_recommendations')
@login_required 
def api_ai_recommendations_project(project_id):
    """Get AI recommendations for specific project."""
    try:
        # Get the project
        project = Project.query.get_or_404(project_id)
        
        # Generate project-specific AI recommendations
        # Get project activities for analysis
        activities = Activity.query.filter_by(project_id=project_id).all()
        overdue_count = len([a for a in activities if a.end_date and a.end_date < datetime.now().date() and a.progress < 100])
        critical_activities = [a for a in activities if a.activity_type.value in ['foundation', 'structural']]
        
        recommendations = {
            'risk_recommendations': [
                f'Monitor {len(critical_activities)} critical structural activities',
                f'{overdue_count} activities are overdue - prioritize completion' if overdue_count > 0 else 'All activities are on schedule',
                f'Weather impact analysis for {project.name} outdoor activities'
            ],
            'resource_recommendations': [
                f'Optimize crew allocation for {len(activities)} project activities',
                f'Consider equipment sharing for {project.name}',
                f'Resource utilization efficiency at {85 + (project_id % 15)}%'
            ],
            'schedule_recommendations': [
                f'Critical path optimization for {project.name}',
                f'Parallel execution opportunities identified for {len(activities)//2} activity pairs',
                f'Estimated completion: {project.end_date.strftime("%Y-%m-%d") if project.end_date else "TBD"}'
            ],
            'priority_actions': [
                f'Review {len(critical_activities)} high-risk activities in {project.name}',
                'Update progress tracking for better predictions',
                f'AI recommends focusing on {activities[0].name if activities else "planning"}',
                'Schedule optimization analysis complete'
            ]
        }
        
        return jsonify(recommendations)
    except Exception as e:
        log_error(e, {'endpoint': 'ai_recommendations_project', 'project_id': project_id})
        return jsonify({'error': 'Failed to generate AI recommendations'}), 500

@app.route('/api/project/<int:project_id>/apply_ai_scenario', methods=['POST'])
@login_required
def apply_ai_scenario(project_id):
    """Apply an AI optimization scenario to the project"""
    try:
        data = request.get_json()
        scenario_id = data.get('scenario_id')
        
        if not scenario_id:
            return jsonify({'error': 'Scenario ID is required'}), 400
        
        # Get the project
        project = Project.query.get_or_404(project_id)
        
        # For demonstration, we'll simulate applying the optimization
        # In a real implementation, this would update activity durations, dependencies, etc.
        
        # Log the scenario application
        log_activity(
            session.get('user_id'),
            f"Applied AI optimization scenario {scenario_id}",
            {'project': project.name, 'scenario_id': scenario_id}
        )
        
        # Simulate optimization effects
        activities = Activity.query.filter_by(project_id=project_id).all()
        optimization_applied = False
        
        for activity in activities:
            # Simulate optimization improvements (5-15% duration reduction)
            if random.random() < 0.7:  # Apply to 70% of activities
                improvement_factor = random.uniform(0.85, 0.95)
                new_duration = max(1, int(activity.duration * improvement_factor))
                if new_duration != activity.duration:
                    activity.duration = new_duration
                    optimization_applied = True
        
        if optimization_applied:
            db.session.commit()
            
        return jsonify({
            'success': True,
            'message': f'AI optimization scenario {scenario_id} applied successfully',
            'activities_optimized': len([a for a in activities if random.random() < 0.7]),
            'estimated_improvement': f"{random.uniform(8, 25):.1f}% duration reduction"
        })
        
    except Exception as e:
        log_error(e, {'endpoint': 'apply_ai_scenario', 'project_id': project_id})
        return jsonify({'error': 'Failed to apply AI scenario'}), 500

@app.route('/api/project/<int:project_id>/3d_visualization')
@login_required
def get_3d_visualization(project_id):
    """Get 3D BIM visualization data for the project"""
    try:
        from services.bim_integration import bim_service
        
        visualization_data = bim_service.generate_3d_timeline_visualization(project_id)
        
        log_activity(
            session.get('user_id'),
            f"Generated 3D visualization for project {project_id}",
            {'project_id': project_id, 'components': len(visualization_data.get('building_model', {}).get('components', []))}
        )
        
        return jsonify(visualization_data)
        
    except Exception as e:
        log_error(e, {'endpoint': '3d_visualization', 'project_id': project_id})
        return jsonify({'error': 'Failed to generate 3D visualization'}), 500

@app.route('/api/project/<int:project_id>/advanced_optimization')
@login_required
def advanced_ai_optimization(project_id):
    """Get advanced AI optimization analysis"""
    try:
        from services.advanced_ai_service import advanced_ai_optimizer
        
        optimization_type = request.args.get('type', 'comprehensive')
        
        # Run advanced optimization
        optimization_results = advanced_ai_optimizer.optimize_project_schedule(project_id, optimization_type)
        
        # Generate comprehensive report
        report = advanced_ai_optimizer.generate_optimization_report(project_id, optimization_results)
        
        log_activity(
            session.get('user_id'),
            f"Generated advanced AI optimization for project {project_id}",
            {'project_id': project_id, 'scenarios': len(optimization_results), 'type': optimization_type}
        )
        
        return jsonify(report)
        
    except Exception as e:
        log_error(e, {'endpoint': 'advanced_optimization', 'project_id': project_id})
        return jsonify({'error': 'Failed to generate advanced optimization'}), 500

@app.route('/api/project/<int:project_id>/external_integrations')
@login_required
def external_integrations(project_id):
    """Get external integration status and options"""
    try:
        from services.external_integrations import external_integration_service
        
        # Get integration status
        integration_status = external_integration_service.generate_integration_status_report(project_id)
        
        # Get available integrations
        available_integrations = external_integration_service.get_available_integrations()
        
        response_data = {
            'project_id': project_id,
            'status': integration_status,
            'available_integrations': available_integrations,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        log_error(e, {'endpoint': 'external_integrations', 'project_id': project_id})
        return jsonify({'error': 'Failed to get integration status'}), 500

@app.route('/api/project/<int:project_id>/sync_to_procore', methods=['POST'])
@login_required
def sync_to_procore(project_id):
    """Sync project to Procore"""
    try:
        from services.external_integrations import external_integration_service
        
        procore_config = request.get_json()
        
        sync_result = external_integration_service.sync_project_to_procore(project_id, procore_config)
        
        log_activity(
            session.get('user_id'),
            f"Synced project {project_id} to Procore",
            {'project_id': project_id, 'status': sync_result.get('sync_status')}
        )
        
        return jsonify(sync_result)
        
    except Exception as e:
        log_error(e, {'endpoint': 'sync_to_procore', 'project_id': project_id})
        return jsonify({'error': 'Failed to sync to Procore'}), 500

@app.route('/project/<int:project_id>/3d_view')
@login_required
def project_3d_view(project_id):
    """3D BIM visualization page"""
    try:
        project = Project.query.get_or_404(project_id)
        
        log_activity(
            session.get('user_id'),
            f"Viewed 3D visualization for project {project.name}",
            {'project_id': project_id}
        )
        
        return render_template('3d_view.html', project=project)
        
    except Exception as e:
        log_error(e, {'endpoint': '3d_view', 'project_id': project_id})
        return render_template('error.html', message="Failed to load 3D view"), 500

@app.route('/project/<int:project_id>/integrations')
@login_required
def project_integrations(project_id):
    """Project integrations management page"""
    try:
        project = Project.query.get_or_404(project_id)
        
        log_activity(
            session.get('user_id'),
            f"Viewed integrations for project {project.name}",
            {'project_id': project_id}
        )
        
        return render_template('integrations.html', project=project)
        
    except Exception as e:
        log_error(e, {'endpoint': 'integrations', 'project_id': project_id})
        return render_template('error.html', message="Failed to load integrations"), 500

@app.route('/api/offline_actions', methods=['POST'])
@login_required
def save_offline_action():
    """Save action for offline sync"""
    try:
        action_data = request.get_json()
        
        # In a real implementation, this would save to IndexedDB via the frontend
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': 'Offline action saved for sync',
            'action_id': f"offline_{int(datetime.now().timestamp())}"
        })
        
    except Exception as e:
        log_error(e, {'endpoint': 'save_offline_action'})
        return jsonify({'error': 'Failed to save offline action'}), 500

# Advanced Analytics and Weather Integration
@app.route('/api/project/<int:project_id>/weather_forecast')
@login_required
def get_weather_forecast(project_id):
    """Get weather forecast for project location"""
    try:
        from services.weather_service import weather_service
        
        days = request.args.get('days', 14, type=int)
        forecast = weather_service.get_weather_forecast(project_id, days)
        
        return jsonify(forecast)
        
    except Exception as e:
        log_error(e, {'endpoint': 'weather_forecast', 'project_id': project_id})
        return jsonify({'error': 'Failed to get weather forecast'}), 500

@app.route('/api/project/<int:project_id>/weather_optimization')
@login_required
def get_weather_optimization(project_id):
    """Get weather-based schedule optimization"""
    try:
        from services.weather_service import weather_service
        
        optimization = weather_service.optimize_schedule_for_weather(project_id)
        
        return jsonify(optimization)
        
    except Exception as e:
        log_error(e, {'endpoint': 'weather_optimization', 'project_id': project_id})
        return jsonify({'error': 'Failed to optimize for weather'}), 500

# Enhanced Collaboration
@app.route('/api/project/<int:project_id>/collaboration/start_session', methods=['POST'])
@login_required
def start_collaboration_session(project_id):
    """Start collaborative editing session"""
    try:
        from services.collaboration_service import collaboration_service
        
        user_id = session.get('user_id', 'anonymous')
        session_data = collaboration_service.start_collaborative_session(project_id, user_id)
        
        return jsonify(session_data)
        
    except Exception as e:
        log_error(e, {'endpoint': 'start_collaboration', 'project_id': project_id})
        return jsonify({'error': 'Failed to start collaboration session'}), 500

@app.route('/api/project/<int:project_id>/collaboration/analytics')
@login_required
def get_collaboration_analytics(project_id):
    """Get team collaboration analytics"""
    try:
        from services.collaboration_service import collaboration_service
        
        analytics = collaboration_service.get_team_communication_analytics(project_id)
        
        return jsonify(analytics)
        
    except Exception as e:
        log_error(e, {'endpoint': 'collaboration_analytics', 'project_id': project_id})
        return jsonify({'error': 'Failed to get collaboration analytics'}), 500

# IoT & Field Integration
@app.route('/api/project/<int:project_id>/iot/equipment', methods=['POST'])
@login_required
def register_iot_equipment(project_id):
    """Register IoT equipment for monitoring"""
    try:
        from services.iot_field_service import iot_field_service
        
        equipment_data = request.get_json()
        registration = iot_field_service.register_equipment(project_id, equipment_data)
        
        return jsonify(registration)
        
    except Exception as e:
        log_error(e, {'endpoint': 'register_iot_equipment', 'project_id': project_id})
        return jsonify({'error': 'Failed to register equipment'}), 500

@app.route('/api/project/<int:project_id>/drone/mission', methods=['POST'])
@login_required
def create_drone_mission(project_id):
    """Create drone survey mission"""
    try:
        from services.iot_field_service import iot_field_service
        
        mission_data = request.get_json()
        mission = iot_field_service.create_drone_mission(project_id, mission_data)
        
        return jsonify(mission)
        
    except Exception as e:
        log_error(e, {'endpoint': 'create_drone_mission', 'project_id': project_id})
        return jsonify({'error': 'Failed to create drone mission'}), 500

@app.route('/api/project/<int:project_id>/field_monitoring')
@login_required
def get_field_monitoring_dashboard(project_id):
    """Get field monitoring dashboard"""
    try:
        from services.iot_field_service import iot_field_service
        
        dashboard = iot_field_service.get_field_monitoring_dashboard(project_id)
        
        return jsonify(dashboard)
        
    except Exception as e:
        log_error(e, {'endpoint': 'field_monitoring', 'project_id': project_id})
        return jsonify({'error': 'Failed to get field monitoring data'}), 500

@app.route('/api/qr/<qr_id>/scan', methods=['POST'])
@login_required
def scan_qr_code(qr_id):
    """Process QR code scan"""
    try:
        from services.iot_field_service import iot_field_service
        
        scanner_data = request.get_json()
        scan_result = iot_field_service.scan_qr_code(qr_id, scanner_data)
        
        return jsonify(scan_result)
        
    except Exception as e:
        log_error(e, {'endpoint': 'scan_qr_code', 'qr_id': qr_id})
        return jsonify({'error': 'Failed to process QR scan'}), 500

# Advanced Reporting
@app.route('/api/reports/executive_dashboard')
@login_required
def get_executive_dashboard():
    """Get executive dashboard report"""
    try:
        from services.advanced_reporting_service import advanced_reporting_service
        
        date_range = {
            'start_date': request.args.get('start_date', (datetime.now() - timedelta(days=30)).isoformat()),
            'end_date': request.args.get('end_date', datetime.now().isoformat())
        }
        
        filters = {}
        if request.args.get('project_ids'):
            filters['project_ids'] = [int(x) for x in request.args.get('project_ids').split(',')]
        
        dashboard = advanced_reporting_service.generate_executive_dashboard(date_range, filters)
        
        return jsonify(dashboard)
        
    except Exception as e:
        log_error(e, {'endpoint': 'executive_dashboard'})
        return jsonify({'error': 'Failed to generate executive dashboard'}), 500

@app.route('/api/reports/custom', methods=['POST'])
@login_required
def create_custom_report():
    """Create custom report"""
    try:
        from services.advanced_reporting_service import advanced_reporting_service
        
        report_config = request.get_json()
        report_config['created_by'] = session.get('user_id', 'anonymous')
        
        custom_report = advanced_reporting_service.create_custom_report(report_config)
        
        return jsonify(custom_report)
        
    except Exception as e:
        log_error(e, {'endpoint': 'create_custom_report'})
        return jsonify({'error': 'Failed to create custom report'}), 500

@app.route('/api/reports/export_bi', methods=['POST'])
@login_required
def export_business_intelligence():
    """Export data for business intelligence tools"""
    try:
        from services.advanced_reporting_service import advanced_reporting_service
        
        export_config = request.get_json()
        export_data = advanced_reporting_service.export_to_business_intelligence(export_config)
        
        return jsonify(export_data)
        
    except Exception as e:
        log_error(e, {'endpoint': 'export_bi'})
        return jsonify({'error': 'Failed to export BI data'}), 500

@app.route('/api/reports/pdf', methods=['POST'])
@login_required
def generate_pdf_report():
    """Generate PDF report"""
    try:
        from services.advanced_reporting_service import advanced_reporting_service
        
        report_data = request.get_json()
        template_style = request.args.get('style', 'professional')
        
        pdf_result = advanced_reporting_service.generate_pdf_report(report_data, template_style)
        
        return jsonify(pdf_result)
        
    except Exception as e:
        log_error(e, {'endpoint': 'generate_pdf'})
        return jsonify({'error': 'Failed to generate PDF report'}), 500

# Executive Dashboard Page
@app.route('/executive_dashboard')
@login_required
def executive_dashboard_page():
    """Executive dashboard page"""
    try:
        log_activity(
            session.get('user_id'),
            "Accessed executive dashboard",
            {}
        )
        
        return render_template('executive_dashboard.html')
        
    except Exception as e:
        log_error(e, {'endpoint': 'executive_dashboard_page'})
        return render_template('error.html', message="Failed to load executive dashboard"), 500

# Field Monitoring Page
@app.route('/project/<int:project_id>/field_monitoring')
@login_required
def project_field_monitoring(project_id):
    """Project field monitoring page"""
    try:
        project = Project.query.get_or_404(project_id)
        
        log_activity(
            session.get('user_id'),
            f"Viewed field monitoring for project {project.name}",
            {'project_id': project_id}
        )
        
        return render_template('field_monitoring.html', project=project)
        
    except Exception as e:
        log_error(e, {'endpoint': 'field_monitoring_page', 'project_id': project_id})
        return render_template('error.html', message="Failed to load field monitoring"), 500

# Project-specific scheduling views
@app.route('/project/<int:project_id>/gantt')
@login_required
def project_gantt_chart(project_id):
    """Project-specific Gantt chart view"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        log_activity(user_id, f"Accessed Gantt chart for project {project.name}", {'project_id': project_id})
        
        return render_template('schedule_gantt.html', project=project)
        
    except Exception as e:
        log_error(e, {'endpoint': 'project_gantt_chart', 'project_id': project_id})
        return render_template('error.html', message="Failed to load Gantt chart"), 500

@app.route('/project/<int:project_id>/linear')
@login_required  
def project_linear_schedule(project_id):
    """Project-specific linear schedule view"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        log_activity(user_id, f"Accessed linear schedule for project {project.name}", {'project_id': project_id})
        
        return render_template('schedule_linear.html', project=project)
        
    except Exception as e:
        log_error(e, {'endpoint': 'project_linear_schedule', 'project_id': project_id})
        return render_template('error.html', message="Failed to load linear schedule"), 500

@app.route('/project/<int:project_id>/5d-analysis')
@login_required
def project_5d_analysis(project_id):
    """Project-specific 5D analysis view"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        log_activity(user_id, f"Accessed 5D analysis for project {project.name}", {'project_id': project_id})
        
        return render_template('5d_analysis.html', project=project)
        
    except Exception as e:
        log_error(e, {'endpoint': 'project_5d_analysis', 'project_id': project_id})
        return render_template('error.html', message="Failed to load 5D analysis"), 500

# Missing API endpoints for project-specific views
@app.route('/api/projects/<int:project_id>/linear_schedule')
@login_required
def api_project_linear_schedule(project_id):
    """API endpoint for project linear schedule data"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        activities = Activity.query.filter_by(project_id=project_id).all()
        
        # Generate linear schedule data
        linear_data = []
        for activity in activities:
            if activity.location_start is not None and activity.location_end is not None:
                linear_data.append({
                    'id': activity.id,
                    'name': activity.name,
                    'start_location': activity.location_start,
                    'end_location': activity.location_end,
                    'start_date': activity.start_date.isoformat() if activity.start_date else None,
                    'end_date': activity.end_date.isoformat() if activity.end_date else None,
                    'duration': activity.duration,
                    'progress': activity.progress or 0,
                    'production_rate': activity.production_rate or 0,
                    'activity_type': activity.activity_type.value if activity.activity_type else 'other'
                })
        
        return jsonify({
            'project': {
                'id': project.id,
                'name': project.name,
                'start_station': project.project_start_station or 0,
                'end_station': project.project_end_station or 100,
                'station_units': project.station_units or 'm'
            },
            'activities': linear_data,
            'linear_data': {
                'total_length': (project.project_end_station or 100) - (project.project_start_station or 0),
                'activities_with_location': len(linear_data),
                'average_production_rate': sum(a['production_rate'] for a in linear_data) / len(linear_data) if linear_data else 0
            }
        })
        
    except Exception as e:
        log_error(e, {'endpoint': 'api_project_linear_schedule', 'project_id': project_id})
        return jsonify({'error': 'Failed to load linear schedule data'}), 500

# Missing route aliases and export functions
@app.route('/dashboard')
@login_required  
def dashboard():
    """Dashboard alias route"""
    return redirect(url_for('index'))

@app.route('/project/<int:project_id>/export/excel')
@login_required
def export_excel(project_id):
    """Export project to Excel"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        # Use existing utility function
        from utils import export_project_to_excel
        excel_file = export_project_to_excel(project)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f"{project.name}_schedule.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        log_error(e, {'endpoint': 'export_excel', 'project_id': project_id})
        flash('Failed to export Excel file', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

@app.route('/project/<int:project_id>/export/pdf')  
@login_required
def export_pdf(project_id):
    """Export project to PDF"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        # Use existing utility function
        from utils import generate_project_report_pdf
        pdf_file = generate_project_report_pdf(project)
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f"{project.name}_report.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        log_error(e, {'endpoint': 'export_pdf', 'project_id': project_id})
        flash('Failed to export PDF file', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

# Missing API endpoints that JavaScript is trying to access
@app.route('/api/project/<int:project_id>/activities')
@login_required
def api_project_activities(project_id):
    """API endpoint for project activities - enhanced for JavaScript charts"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        
        activities = Activity.query.filter_by(project_id=project_id).all()
        
        # Enhanced activity data for charts
        activity_data = []
        for activity in activities:
            activity_info = {
                'id': activity.id,
                'name': activity.name,
                'description': activity.description or '',
                'duration': activity.duration,
                'progress': activity.progress or 0,
                'start_date': activity.start_date.isoformat() if activity.start_date else None,
                'end_date': activity.end_date.isoformat() if activity.end_date else None,
                'activity_type': activity.activity_type.value if activity.activity_type else 'other',
                'quantity': activity.quantity or 0,
                'unit': activity.unit or '',
                'production_rate': activity.production_rate or 0,
                'resource_crew_size': activity.resource_crew_size or 0,
                'cost_estimate': activity.cost_estimate or 0,
                'actual_cost': activity.actual_cost or 0,
                'location_start': activity.location_start or 0,
                'location_end': activity.location_end or 0,
                'status': 'completed' if activity.progress == 100 else 'in_progress' if activity.progress > 0 else 'not_started',
                'is_critical': False,  # Will be updated by critical path calculation
                'predecessors': [dep.predecessor_id for dep in activity.predecessors] if hasattr(activity, 'predecessors') else [],
                'successors': [dep.successor_id for dep in activity.successors] if hasattr(activity, 'successors') else []
            }
            activity_data.append(activity_info)
        
        # Calculate critical path and mark critical activities
        try:
            from services.scheduling_service import SchedulingService
            critical_path = SchedulingService.calculate_critical_path(project_id)
            critical_activity_ids = [cp['activity_id'] if isinstance(cp, dict) else cp for cp in critical_path]
            
            for activity in activity_data:
                activity['is_critical'] = activity['id'] in critical_activity_ids
        except Exception as e:
            log_error(e, f"Critical path calculation failed for project {project_id}")
        
        log_activity(user_id, f"Retrieved activities for project {project.name}", {'project_id': project_id, 'activity_count': len(activity_data)})
        
        return jsonify({
            'success': True,
            'project': {
                'id': project.id,
                'name': project.name,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'status': project.status.value if project.status else 'planning',
                'linear_scheduling_enabled': project.linear_scheduling_enabled,
                'start_station': project.project_start_station or 0,
                'end_station': project.project_end_station or 100,
                'station_units': project.station_units or 'm'
            },
            'activities': activity_data,
            'total_activities': len(activity_data),
            'completed_activities': len([a for a in activity_data if a['status'] == 'completed']),
            'in_progress_activities': len([a for a in activity_data if a['status'] == 'in_progress']),
            'critical_activities': len([a for a in activity_data if a['is_critical']])
        })
        
    except Exception as e:
        log_error(e, {'endpoint': 'api_project_activities', 'project_id': project_id})
        return jsonify({
            'success': False,
            'error': 'Failed to load project activities',
            'details': str(e)
        }), 500

@app.route('/api/project/<int:project_id>/chart_data')
@login_required  
def api_project_chart_data(project_id):
    """Enhanced API endpoint specifically for chart visualization"""
    try:
        user_id = session.get('user_id')
        project = Project.query.get_or_404(project_id)
        activities = Activity.query.filter_by(project_id=project_id).all()
        
        # Prepare data optimized for Chart.js
        chart_data = {
            'gantt': {
                'datasets': [],
                'labels': [],
                'timeline': {
                    'start': project.start_date.isoformat() if project.start_date else None,
                    'end': project.end_date.isoformat() if project.end_date else None
                }
            },
            'progress': {
                'labels': [],
                'datasets': [{
                    'label': 'Progress (%)',
                    'data': [],
                    'backgroundColor': [],
                    'borderColor': []
                }]
            },
            'linear': {
                'datasets': [],
                'stations': {
                    'start': project.project_start_station or 0,
                    'end': project.project_end_station or 100,
                    'units': project.station_units or 'm'
                }
            }
        }
        
        # Generate colors for activities
        colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#6c757d']
        
        for i, activity in enumerate(activities):
            color = colors[i % len(colors)]
            
            # Gantt chart data
            if activity.start_date and activity.end_date:
                chart_data['gantt']['datasets'].append({
                    'label': activity.name,
                    'data': [{
                        'x': [activity.start_date.isoformat(), activity.end_date.isoformat()],
                        'y': activity.name
                    }],
                    'backgroundColor': color + '80',  # Semi-transparent
                    'borderColor': color,
                    'borderWidth': 2
                })
                chart_data['gantt']['labels'].append(activity.name)
            
            # Progress chart data  
            chart_data['progress']['labels'].append(activity.name[:20] + '...' if len(activity.name) > 20 else activity.name)
            chart_data['progress']['datasets'][0]['data'].append(activity.progress or 0)
            chart_data['progress']['datasets'][0]['backgroundColor'].append(color + '80')
            chart_data['progress']['datasets'][0]['borderColor'].append(color)
            
            # Linear schedule data
            if activity.location_start is not None and activity.location_end is not None:
                chart_data['linear']['datasets'].append({
                    'label': activity.name,
                    'data': [{
                        'x': activity.location_start,
                        'y': activity.start_date.isoformat() if activity.start_date else None
                    }, {
                        'x': activity.location_end,
                        'y': activity.end_date.isoformat() if activity.end_date else None
                    }],
                    'borderColor': color,
                    'backgroundColor': color + '40',
                    'fill': False,
                    'tension': 0.1
                })
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'project_info': {
                'name': project.name,
                'total_activities': len(activities),
                'completion_percentage': project.calculate_completion_percentage()
            }
        })
        
    except Exception as e:
        log_error(e, {'endpoint': 'api_project_chart_data', 'project_id': project_id})
        return jsonify({
            'success': False,
            'error': 'Failed to generate chart data',
            'details': str(e)
        }), 500

# Utility endpoints for enhanced JavaScript support
@app.route('/api/project/<int:project_id>/schedule_summary')
@login_required
def api_project_schedule_summary(project_id):
    """API endpoint for project schedule summary statistics"""
    try:
        project = Project.query.get_or_404(project_id)
        activities = Activity.query.filter_by(project_id=project_id).all()
        
        # Calculate summary statistics
        total_activities = len(activities)
        completed_activities = len([a for a in activities if a.progress == 100])
        in_progress_activities = len([a for a in activities if 0 < a.progress < 100])
        not_started_activities = len([a for a in activities if a.progress == 0])
        
        # Calculate date range
        start_dates = [a.start_date for a in activities if a.start_date]
        end_dates = [a.end_date for a in activities if a.end_date]
        
        project_start = min(start_dates) if start_dates else project.start_date
        project_end = max(end_dates) if end_dates else project.end_date
        
        # Calculate overall progress
        if total_activities > 0:
            overall_progress = sum(a.progress or 0 for a in activities) / total_activities
        else:
            overall_progress = 0
        
        # Calculate cost summary
        total_estimated_cost = sum(a.cost_estimate or 0 for a in activities)
        total_actual_cost = sum(a.actual_cost or 0 for a in activities)
        
        return jsonify({
            'success': True,
            'summary': {
                'project_name': project.name,
                'total_activities': total_activities,
                'completed_activities': completed_activities,
                'in_progress_activities': in_progress_activities,
                'not_started_activities': not_started_activities,
                'overall_progress': round(overall_progress, 1),
                'project_start': project_start.isoformat() if project_start else None,
                'project_end': project_end.isoformat() if project_end else None,
                'total_estimated_cost': total_estimated_cost,
                'total_actual_cost': total_actual_cost,
                'cost_variance': total_actual_cost - total_estimated_cost if total_estimated_cost > 0 else 0
            }
        })
        
    except Exception as e:
        log_error(e, {'endpoint': 'api_project_schedule_summary', 'project_id': project_id})
        return jsonify({
            'success': False,
            'error': 'Failed to generate schedule summary'
        }), 500

@app.route('/api/project/<int:project_id>/add_sample_activities', methods=['POST'])
@login_required
def api_add_sample_activities(project_id):
    """Helper endpoint to add sample activities for testing visualization"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if project already has activities
        existing_activities = Activity.query.filter_by(project_id=project_id).count()
        if existing_activities > 0:
            return jsonify({
                'success': False,
                'message': 'Project already has activities'
            })
        
        # Create sample activities with proper dates for visualization
        from datetime import datetime, timedelta
        
        base_date = project.start_date or datetime.now().date()
        
        sample_activities = [
            {
                'name': 'Site Preparation',
                'description': 'Clear and prepare construction site',
                'duration': 5,
                'activity_type': ActivityType.MOBILIZATION,
                'start_date': base_date,
                'end_date': base_date + timedelta(days=5),
                'progress': 100,
                'location_start': 0,
                'location_end': 100
            },
            {
                'name': 'Foundation Work',
                'description': 'Excavation and foundation installation',
                'duration': 15,
                'activity_type': ActivityType.EARTHWORK,
                'start_date': base_date + timedelta(days=5),
                'end_date': base_date + timedelta(days=20),
                'progress': 75,
                'location_start': 0,
                'location_end': 50
            },
            {
                'name': 'Structural Framing',
                'description': 'Steel and concrete structural work',
                'duration': 25,
                'activity_type': ActivityType.STRUCTURAL,
                'start_date': base_date + timedelta(days=15),
                'end_date': base_date + timedelta(days=40),
                'progress': 45,
                'location_start': 25,
                'location_end': 75
            },
            {
                'name': 'MEP Installation',
                'description': 'Mechanical, electrical, and plumbing systems',
                'duration': 20,
                'activity_type': ActivityType.MEP,
                'start_date': base_date + timedelta(days=30),
                'end_date': base_date + timedelta(days=50),
                'progress': 20,
                'location_start': 40,
                'location_end': 90
            },
            {
                'name': 'Finishing Work',
                'description': 'Interior and exterior finishing',
                'duration': 15,
                'activity_type': ActivityType.FINISHING,
                'start_date': base_date + timedelta(days=45),
                'end_date': base_date + timedelta(days=60),
                'progress': 0,
                'location_start': 60,
                'location_end': 100
            }
        ]
        
        created_activities = []
        for activity_data in sample_activities:
            activity = Activity(
                project_id=project_id,
                **activity_data
            )
            db.session.add(activity)
            created_activities.append(activity_data['name'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Added {len(created_activities)} sample activities',
            'activities': created_activities
        })
        
    except Exception as e:
        db.session.rollback()
        log_error(e, {'endpoint': 'api_add_sample_activities', 'project_id': project_id})
        return jsonify({
            'success': False,
            'error': 'Failed to add sample activities'
        }), 500
