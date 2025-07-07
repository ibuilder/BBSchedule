import os
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.utils import secure_filename
from app import app, db
from models import Project, Activity, Dependency, Schedule, Document, ScheduleMetrics, ProjectStatus, ActivityType, ScheduleType
from forms import ProjectForm, ActivityForm, ScheduleForm, DocumentUploadForm, DependencyForm, ScheduleImportForm, FiveDAnalysisForm
from utils import calculate_schedule_metrics, export_schedule_to_excel, generate_schedule_pdf
from import_utils import import_schedule_file, FiveDScheduleManager
from datetime import datetime, date, timedelta
import json
import pandas as pd
from io import BytesIO
import uuid
from functools import wraps

# Session management and authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login system"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper password hashing)
        if username and password:
            session['user_id'] = str(uuid.uuid4())
            session['username'] = username
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Please enter both username and password.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Dashboard showing project overview and key metrics"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    projects = Project.query.all()
    
    # Calculate enhanced dashboard metrics
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.status == ProjectStatus.ACTIVE])
    completed_projects = len([p for p in projects if p.status == ProjectStatus.COMPLETED])
    planning_projects = len([p for p in projects if p.status == ProjectStatus.PLANNING])
    
    # Calculate project budget metrics
    total_budget = sum([p.budget or 0 for p in projects])
    active_budget = sum([p.budget or 0 for p in projects if p.status == ProjectStatus.ACTIVE])
    
    # Get recent activities with enhanced data
    recent_activities = Activity.query.order_by(Activity.updated_at.desc()).limit(10).all()
    
    # Calculate activity completion metrics
    total_activities = Activity.query.count()
    completed_activities = Activity.query.filter(Activity.progress >= 100).count()
    in_progress_activities = Activity.query.filter(Activity.progress.between(1, 99)).count()
    not_started_activities = Activity.query.filter(Activity.progress == 0).count()
    
    # Overall project health score
    if total_activities > 0:
        completion_rate = (completed_activities / total_activities) * 100
    else:
        completion_rate = 0
    
    return render_template('index.html', 
                         projects=projects,
                         total_projects=total_projects,
                         active_projects=active_projects,
                         completed_projects=completed_projects,
                         planning_projects=planning_projects,
                         recent_activities=recent_activities,
                         total_budget=total_budget,
                         active_budget=active_budget,
                         total_activities=total_activities,
                         completed_activities=completed_activities,
                         in_progress_activities=in_progress_activities,
                         not_started_activities=not_started_activities,
                         completion_rate=completion_rate,
                         username=session.get('username', 'User'))

@app.route('/projects')
@login_required
def projects():
    """List all projects with enhanced filtering and sorting"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    
    query = Project.query
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter(Project.status == ProjectStatus(status_filter))
    
    # Apply sorting
    if sort_by == 'name':
        if order == 'desc':
            query = query.order_by(Project.name.desc())
        else:
            query = query.order_by(Project.name.asc())
    elif sort_by == 'start_date':
        if order == 'desc':
            query = query.order_by(Project.start_date.desc())
        else:
            query = query.order_by(Project.start_date.asc())
    elif sort_by == 'budget':
        if order == 'desc':
            query = query.order_by(Project.budget.desc().nulls_last())
        else:
            query = query.order_by(Project.budget.asc().nulls_last())
    
    projects = query.all()
    
    # Calculate project completion percentages
    for project in projects:
        activities = Activity.query.filter_by(project_id=project.id).all()
        if activities:
            total_progress = sum([activity.progress for activity in activities])
            project.completion_percentage = total_progress / len(activities)
        else:
            project.completion_percentage = 0
    
    return render_template('projects.html', 
                         projects=projects,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         order=order)

@app.route('/project/create', methods=['GET', 'POST'])
def create_project():
    """Create a new project"""
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            status=ProjectStatus(form.status.data),
            total_sf=form.total_sf.data,
            floor_count=form.floor_count.data,
            building_type=form.building_type.data,
            location=form.location.data,
            budget=form.budget.data
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('project_create.html', form=form)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """View project details"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    schedules = Schedule.query.filter_by(project_id=project_id).all()
    documents = Document.query.filter_by(project_id=project_id).all()
    
    # Calculate project metrics
    completion_percentage = project.get_completion_percentage()
    total_duration = project.get_total_duration()
    
    return render_template('project_detail.html', 
                         project=project,
                         activities=activities,
                         schedules=schedules,
                         documents=documents,
                         completion_percentage=completion_percentage,
                         total_duration=total_duration)

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit project details"""
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.status = ProjectStatus(form.status.data)
        project.total_sf = form.total_sf.data
        project.floor_count = form.floor_count.data
        project.building_type = form.building_type.data
        project.location = form.location.data
        project.budget = form.budget.data
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('project_create.html', form=form, project=project)

@app.route('/project/<int:project_id>/activity/create', methods=['GET', 'POST'])
def create_activity(project_id):
    """Create a new activity for a project"""
    project = Project.query.get_or_404(project_id)
    form = ActivityForm()
    
    if form.validate_on_submit():
        activity = Activity(
            project_id=project_id,
            name=form.name.data,
            description=form.description.data,
            activity_type=ActivityType(form.activity_type.data),
            duration=form.duration.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            progress=form.progress.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            production_rate=form.production_rate.data,
            resource_crew_size=form.resource_crew_size.data,
            cost_estimate=form.cost_estimate.data,
            actual_cost=form.actual_cost.data,
            location_start=form.location_start.data,
            location_end=form.location_end.data,
            notes=form.notes.data
        )
        db.session.add(activity)
        db.session.commit()
        flash('Activity created successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project_id))
    
    return render_template('activity_create.html', form=form, project=project)

@app.route('/activity/<int:activity_id>/edit', methods=['GET', 'POST'])
def edit_activity(activity_id):
    """Edit activity details"""
    activity = Activity.query.get_or_404(activity_id)
    form = ActivityForm(obj=activity)
    
    if form.validate_on_submit():
        activity.name = form.name.data
        activity.description = form.description.data
        activity.activity_type = ActivityType(form.activity_type.data)
        activity.duration = form.duration.data
        activity.start_date = form.start_date.data
        activity.end_date = form.end_date.data
        activity.progress = form.progress.data
        activity.quantity = form.quantity.data
        activity.unit = form.unit.data
        activity.production_rate = form.production_rate.data
        activity.resource_crew_size = form.resource_crew_size.data
        activity.cost_estimate = form.cost_estimate.data
        activity.actual_cost = form.actual_cost.data
        activity.location_start = form.location_start.data
        activity.location_end = form.location_end.data
        activity.notes = form.notes.data
        activity.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Activity updated successfully!', 'success')
        return redirect(url_for('project_detail', project_id=activity.project_id))
    
    return render_template('activity_create.html', form=form, activity=activity)

@app.route('/project/<int:project_id>/dependencies', methods=['GET', 'POST'])
def manage_dependencies(project_id):
    """Manage activity dependencies"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    dependencies = Dependency.query.join(Activity, Dependency.predecessor_id == Activity.id).filter(Activity.project_id == project_id).all()
    
    form = DependencyForm()
    form.predecessor_id.choices = [(a.id, a.name) for a in activities]
    form.successor_id.choices = [(a.id, a.name) for a in activities]
    
    if form.validate_on_submit():
        if form.predecessor_id.data == form.successor_id.data:
            flash('An activity cannot depend on itself!', 'error')
        else:
            dependency = Dependency(
                predecessor_id=form.predecessor_id.data,
                successor_id=form.successor_id.data,
                dependency_type=form.dependency_type.data,
                lag_days=form.lag_days.data
            )
            db.session.add(dependency)
            db.session.commit()
            flash('Dependency added successfully!', 'success')
            return redirect(url_for('manage_dependencies', project_id=project_id))
    
    return render_template('dependencies.html', 
                         form=form, 
                         project=project, 
                         dependencies=dependencies,
                         activities=activities)

@app.route('/project/<int:project_id>/gantt')
def gantt_chart(project_id):
    """Display Gantt chart view"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    dependencies = Dependency.query.join(Activity, Dependency.predecessor_id == Activity.id).filter(Activity.project_id == project_id).all()
    
    return render_template('schedule_gantt.html', 
                         project=project, 
                         activities=activities, 
                         dependencies=dependencies)

@app.route('/project/<int:project_id>/linear')
def linear_schedule(project_id):
    """Display linear schedule view"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    
    return render_template('schedule_linear.html', 
                         project=project, 
                         activities=activities)

@app.route('/project/<int:project_id>/upload', methods=['GET', 'POST'])
def upload_document(project_id):
    """Upload project documents"""
    project = Project.query.get_or_404(project_id)
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            document = Document(
                project_id=project_id,
                filename=filename,
                original_filename=file.filename,
                file_type=file.filename.rsplit('.', 1)[1].lower(),
                file_size=os.path.getsize(filepath),
                document_type=form.document_type.data
            )
            db.session.add(document)
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
    
    return render_template('upload_document.html', form=form, project=project)

@app.route('/project/<int:project_id>/reports')
def project_reports(project_id):
    """Generate project reports and metrics"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    
    # Calculate current metrics
    metrics = calculate_schedule_metrics(project, activities)
    
    # Get historical metrics
    historical_metrics = ScheduleMetrics.query.filter_by(project_id=project_id).order_by(ScheduleMetrics.metric_date.desc()).limit(30).all()
    
    return render_template('reports.html', 
                         project=project, 
                         activities=activities, 
                         metrics=metrics, 
                         historical_metrics=historical_metrics)

@app.route('/api/project/<int:project_id>/activities')
def api_project_activities(project_id):
    """API endpoint for project activities data"""
    activities = Activity.query.filter_by(project_id=project_id).all()
    dependencies = Dependency.query.join(Activity, Dependency.predecessor_id == Activity.id).filter(Activity.project_id == project_id).all()
    
    activities_data = []
    for activity in activities:
        activities_data.append({
            'id': activity.id,
            'name': activity.name,
            'start_date': activity.start_date.isoformat() if activity.start_date else None,
            'end_date': activity.end_date.isoformat() if activity.end_date else None,
            'duration': activity.duration,
            'progress': activity.progress,
            'activity_type': activity.activity_type.value,
            'location_start': activity.location_start,
            'location_end': activity.location_end,
            'predecessors': activity.get_predecessor_ids(),
            'successors': activity.get_successor_ids()
        })
    
    dependencies_data = []
    for dep in dependencies:
        dependencies_data.append({
            'id': dep.id,
            'predecessor_id': dep.predecessor_id,
            'successor_id': dep.successor_id,
            'dependency_type': dep.dependency_type,
            'lag_days': dep.lag_days
        })
    
    return jsonify({
        'activities': activities_data,
        'dependencies': dependencies_data
    })

@app.route('/project/<int:project_id>/export/excel')
def export_excel(project_id):
    """Export project schedule to Excel"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    
    filepath = export_schedule_to_excel(project, activities)
    return send_file(filepath, as_attachment=True, download_name=f'{project.name}_schedule.xlsx')

@app.route('/project/<int:project_id>/export/pdf')
def export_pdf(project_id):
    """Export project schedule to PDF"""
    project = Project.query.get_or_404(project_id)
    activities = Activity.query.filter_by(project_id=project_id).all()
    
    filepath = generate_schedule_pdf(project, activities)
    return send_file(filepath, as_attachment=True, download_name=f'{project.name}_schedule.pdf')

# ========== API ENDPOINTS ==========



@app.route('/api/dashboard/metrics')
def api_dashboard_metrics():
    """API endpoint for real-time dashboard metrics"""
    try:
        projects = Project.query.all()
        activities = Activity.query.all()
        
        # Calculate comprehensive metrics
        metrics = {
            'projects': {
                'total': len(projects),
                'active': len([p for p in projects if p.status == ProjectStatus.ACTIVE]),
                'completed': len([p for p in projects if p.status == ProjectStatus.COMPLETED]),
                'planning': len([p for p in projects if p.status == ProjectStatus.PLANNING]),
                'cancelled': len([p for p in projects if p.status == ProjectStatus.CANCELLED])
            },
            'activities': {
                'total': len(activities),
                'completed': len([a for a in activities if a.progress >= 100]),
                'in_progress': len([a for a in activities if 0 < a.progress < 100]),
                'not_started': len([a for a in activities if a.progress == 0])
            },
            'budget': {
                'total': sum([p.budget or 0 for p in projects]),
                'active': sum([p.budget or 0 for p in projects if p.status == ProjectStatus.ACTIVE]),
                'spent': sum([a.actual_cost or 0 for a in activities])
            },
            'timeline': {
                'overdue_activities': len([a for a in activities if a.end_date and a.end_date < datetime.now().date() and a.progress < 100]),
                'upcoming_deadlines': len([a for a in activities if a.end_date and a.end_date <= datetime.now().date() + timedelta(days=7) and a.progress < 100])
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/project/<int:project_id>/update_activity_progress', methods=['POST'])
@login_required
def api_update_activity_progress(project_id):
    """API endpoint to update activity progress"""
    try:
        data = request.get_json()
        activity_id = data.get('activity_id')
        new_progress = data.get('progress')
        
        if not activity_id or new_progress is None:
            return jsonify({'success': False, 'error': 'Missing activity_id or progress'}), 400
        
        activity = Activity.query.filter_by(id=activity_id, project_id=project_id).first()
        if not activity:
            return jsonify({'success': False, 'error': 'Activity not found'}), 404
        
        # Validate progress value
        if not (0 <= new_progress <= 100):
            return jsonify({'success': False, 'error': 'Progress must be between 0 and 100'}), 400
        
        activity.progress = new_progress
        activity.updated_at = datetime.now()
        
        # Auto-update end date if activity is completed
        if new_progress >= 100 and not activity.end_date:
            activity.end_date = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'activity': {
                'id': activity.id,
                'name': activity.name,
                'progress': activity.progress,
                'end_date': activity.end_date.strftime('%Y-%m-%d') if activity.end_date else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dependency/<int:dependency_id>/delete', methods=['POST'])
def delete_dependency(dependency_id):
    """Delete a dependency"""
    dependency = Dependency.query.get_or_404(dependency_id)
    project_id = dependency.predecessor_activity.project_id
    
    db.session.delete(dependency)
    db.session.commit()
    flash('Dependency deleted successfully!', 'success')
    return redirect(url_for('manage_dependencies', project_id=project_id))

@app.route('/activity/<int:activity_id>/delete', methods=['POST'])
def delete_activity(activity_id):
    """Delete an activity"""
    activity = Activity.query.get_or_404(activity_id)
    project_id = activity.project_id
    
    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted successfully!', 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/import_schedule', methods=['GET', 'POST'])
def import_schedule():
    """Import external schedule files (XER, MPP, XML)"""
    form = ScheduleImportForm()
    
    # Populate existing projects dropdown
    projects = Project.query.all()
    form.existing_project.choices = [(0, 'Select Project')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        file = form.file.data
        if file:
            # Save uploaded file
            filename = secure_filename(file.filename)
            uploads_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, filename)
            file.save(file_path)
            
            try:
                # Import the schedule
                project_name = form.project_name.data if form.project_name.data else None
                imported_project, messages = import_schedule_file(file_path, project_name)
                
                if imported_project:
                    flash('Schedule imported successfully!', 'success')
                    if messages:
                        for msg in messages:
                            flash(f'Warning: {msg}', 'warning')
                    return redirect(url_for('project_detail', project_id=imported_project.id))
                else:
                    for error in messages:
                        flash(f'Import error: {error}', 'error')
                    
            except Exception as e:
                flash(f'Import failed: {str(e)}', 'error')
            finally:
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    return render_template('import_schedule.html', form=form)

@app.route('/project/<int:project_id>/5d_analysis', methods=['GET', 'POST'])
def five_d_analysis(project_id):
    """Generate 5D schedule analysis"""
    project = Project.query.get_or_404(project_id)
    form = FiveDAnalysisForm()
    
    if form.validate_on_submit():
        try:
            # Generate 5D analysis
            manager = FiveDScheduleManager(project)
            analysis_data = manager.calculate_5d_metrics()
            
            # Filter analysis based on selected type
            analysis_type = form.analysis_type.data
            if analysis_type != 'complete':
                analysis_data = {analysis_type: analysis_data.get(analysis_type, {})}
            
            # Save metrics to database
            metrics = ScheduleMetrics(
                project_id=project.id,
                schedule_performance_index=analysis_data.get('time_performance', {}).get('schedule_performance_index', 0),
                cost_performance_index=analysis_data.get('cost_performance', {}).get('cost_performance_index', 0),
                planned_value=analysis_data.get('cost_performance', {}).get('planned_value', 0),
                earned_value=analysis_data.get('cost_performance', {}).get('earned_value', 0),
                actual_cost=analysis_data.get('cost_performance', {}).get('actual_cost', 0),
                resource_utilization=analysis_data.get('resource_utilization', {}).get('utilization_percentage', 0),
                created_at=datetime.utcnow()
            )
            
            db.session.add(metrics)
            db.session.commit()
            
            flash('5D analysis generated successfully!', 'success')
            return render_template('5d_analysis.html', 
                                 project=project, 
                                 analysis_data=analysis_data,
                                 form=form)
            
        except Exception as e:
            flash(f'Analysis failed: {str(e)}', 'error')
    
    return render_template('5d_analysis.html', project=project, form=form)

@app.route('/project/<int:project_id>/5d_metrics')
def five_d_metrics_api(project_id):
    """API endpoint for 5D metrics data"""
    project = Project.query.get_or_404(project_id)
    
    try:
        manager = FiveDScheduleManager(project)
        metrics = manager.calculate_5d_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
