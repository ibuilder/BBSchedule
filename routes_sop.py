"""
SOP Compliance Routes for Carolinas Scheduling Requirements
Enhanced with NCMoH real-world example
"""

from flask import request, jsonify, render_template, redirect, url_for, flash
from app import app
from extensions import db
from services.sop_compliance_service import sop_service
from services.ncmoh_schedule_importer import ncmoh_importer
from models_sop_compliance import (
    SOPSchedule, SOPActivity, Fragnet, SchedulerAssignment, 
    PullPlanBoard, ScheduleReport, ScheduleTemplate,
    ScheduleType, ProjectSize, FloatStatus, UpdateType
)
from models import Project
import json
from datetime import datetime, timedelta

@app.route('/sop/dashboard')
def sop_dashboard():
    """SOP compliance dashboard"""
    projects = Project.query.all()
    
    # Get compliance summary for all projects
    compliance_summary = []
    for project in projects:
        try:
            dashboard = sop_service.get_sop_compliance_dashboard(project.id)
            compliance_summary.append({
                'project': project,
                'compliance': dashboard
            })
        except Exception as e:
            # Handle projects without SOP data gracefully
            compliance_summary.append({
                'project': project,
                'compliance': {
                    'project_info': {'contract_value': 0, 'project_size': 'unknown'},
                    'schedule_compliance': {'baseline_complete': False, 'requires_4d': False, 'four_d_complete': False},
                    'activity_compliance': {'total': 0, 'compliant': 0, 'compliance_rate': 0, 'id_violations': 0, 'duration_violations': 0, 'date_violations': 0},
                    'update_compliance': {'scheduler_required': False, 'update_deadline': 'Unknown'},
                    'reports_generated': 0,
                    'float_status': 'unknown'
                }
            })
    
    return render_template('sop/dashboard.html', 
                         compliance_summary=compliance_summary)

@app.route('/sop/project/<int:project_id>')
def sop_project_detail(project_id):
    """Detailed SOP compliance for specific project"""
    project = Project.query.get_or_404(project_id)
    
    try:
        dashboard = sop_service.get_sop_compliance_dashboard(project_id)
    except Exception as e:
        # Default dashboard for projects without SOP data
        dashboard = {
            'project_info': {'contract_value': 0, 'project_size': 'unknown'},
            'schedule_compliance': {'baseline_complete': False, 'requires_4d': False, 'four_d_complete': False},
            'activity_compliance': {'total': 0, 'compliant': 0, 'compliance_rate': 0, 'id_violations': 0, 'duration_violations': 0, 'date_violations': 0},
            'update_compliance': {'scheduler_required': False, 'update_deadline': 'Unknown'},
            'reports_generated': 0,
            'float_status': 'unknown'
        }
    
    # Get schedule timeline status
    schedules = SOPSchedule.query.filter_by(project_id=project_id).all()
    timeline_status = []
    for schedule in schedules:
        try:
            status = sop_service.check_schedule_development_timeline(schedule.id)
            timeline_status.append({
                'schedule': schedule,
                'timeline': status
            })
        except Exception as e:
            pass
    
    return render_template('sop/project_detail.html', 
                         project=project,
                         dashboard=dashboard,
                         timeline_status=timeline_status)

@app.route('/sop/schedule/create', methods=['GET', 'POST'])
def create_sop_schedule():
    """Create SOP-compliant schedule"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            schedule_type = ScheduleType(data.get('schedule_type'))
            project_id = int(data.get('project_id'))
            start_date = datetime.fromisoformat(data.get('start_date')) if data.get('start_date') else None
            
            schedule = sop_service.create_sop_schedule(
                project_id=project_id,
                schedule_type=schedule_type,
                start_date=start_date
            )
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'schedule_id': schedule.id,
                    'message': f'SOP schedule created: {schedule_type.value}'
                })
            else:
                flash(f'SOP schedule created: {schedule_type.value}', 'success')
                return redirect(url_for('sop_project_detail', project_id=project_id))
                
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            else:
                flash(f'Error creating schedule: {str(e)}', 'error')
                return redirect(url_for('sop_dashboard'))
    
    # GET request - show form
    projects = Project.query.all()
    schedule_types = [{'value': st.value, 'name': st.value.replace('_', ' ').title()} 
                     for st in ScheduleType]
    
    return render_template('sop/create_schedule.html', 
                         projects=projects,
                         schedule_types=schedule_types)

@app.route('/sop/import/ncmoh', methods=['POST'])
def import_ncmoh_project():
    """Import the NCMoH museum project as SOP example"""
    try:
        project = ncmoh_importer.import_project()
        
        flash(f'Successfully imported NCMoH project: {project.name}', 'success')
        return jsonify({
            'success': True,
            'project_id': project.id,
            'message': 'NCMoH Museum project imported successfully with full SOP compliance'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/sop/activity/validate', methods=['POST'])
def validate_sop_activity():
    """Validate activity SOP compliance"""
    data = request.get_json()
    
    # Create temporary activity for validation
    activity = SOPActivity(
        activity_id=data.get('activity_id', ''),
        duration=int(data.get('duration', 0)),
        actual_start=datetime.fromisoformat(data['actual_start']) if data.get('actual_start') else None,
        actual_finish=datetime.fromisoformat(data['actual_finish']) if data.get('actual_finish') else None,
        planned_start=datetime.fromisoformat(data['planned_start']) if data.get('planned_start') else None,
        planned_finish=datetime.fromisoformat(data['planned_finish']) if data.get('planned_finish') else None
    )
    
    validation_results = sop_service.validate_activity_sop_compliance(activity)
    
    return jsonify({
        'success': True,
        'validation': validation_results,
        'recommendations': _get_activity_recommendations(validation_results)
    })

def _get_activity_recommendations(validation_results):
    """Get recommendations for activity compliance"""
    recommendations = []
    
    if not validation_results['activity_id_valid']:
        recommendations.append('Activity ID must be 5 characters or less')
    
    if not validation_results['duration_valid']:
        recommendations.append('Activity duration must be 15 days or less')
    
    if not validation_results['dates_populated']:
        recommendations.append('All activities must have AS/AF or PS/PF dates populated')
    
    return recommendations

@app.route('/sop/scheduler/assign', methods=['POST'])
def assign_scheduler():
    """Assign scheduler based on SOP rules"""
    data = request.get_json()
    
    project_id = int(data.get('project_id'))
    contract_value = float(data.get('contract_value', 0))
    
    assignment = sop_service.assign_scheduler(project_id, contract_value)
    
    return jsonify({
        'success': True,
        'assignment': {
            'scheduler_level': assignment.scheduler_level,
            'scheduler_name': assignment.scheduler_name,
            'requires_scheduler': assignment.is_over_10m,
            'project_size': assignment.project_size.value
        }
    })

@app.route('/sop/fragnet/create', methods=['POST'])
def create_fragnet():
    """Create fragnet per SOP requirements"""
    data = request.get_json()
    
    fragnet = sop_service.create_fragnet(
        schedule_id=int(data.get('schedule_id')),
        trigger_type=data.get('trigger_type'),
        delay_days=int(data.get('delay_days', 0)),
        description=data.get('description', '')
    )
    
    return jsonify({
        'success': True,
        'fragnet_id': fragnet.id,
        'requires_recovery': fragnet.requires_recovery,
        'message': 'Fragnet created successfully'
    })

@app.route('/sop/pull-plan/<int:project_id>')
def pull_plan_board(project_id):
    """Display pull planning board"""
    project = Project.query.get_or_404(project_id)
    pull_plan = PullPlanBoard.query.filter_by(project_id=project_id).first()
    
    if not pull_plan:
        pull_plan = sop_service.create_pull_plan_board(project_id)
    
    # Parse JSON data for display
    weeks_data = {
        'week_1': json.loads(pull_plan.week_1_activities) if pull_plan.week_1_activities else [],
        'week_2': json.loads(pull_plan.week_2_activities) if pull_plan.week_2_activities else [],
        'week_3': json.loads(pull_plan.week_3_activities) if pull_plan.week_3_activities else [],
        'week_4': json.loads(pull_plan.week_4_activities) if pull_plan.week_4_activities else []
    }
    
    special_activities = {
        'deliveries': json.loads(pull_plan.deliveries) if pull_plan.deliveries else [],
        'inspections': json.loads(pull_plan.inspections) if pull_plan.inspections else [],
        'safety': json.loads(pull_plan.safety_activities) if pull_plan.safety_activities else [],
        'meetings': json.loads(pull_plan.preinstall_meetings) if pull_plan.preinstall_meetings else []
    }
    
    return render_template('sop/pull_plan_board.html',
                         project=project,
                         weeks_data=weeks_data,
                         special_activities=special_activities)

@app.route('/sop/reports/<int:project_id>')
def sop_reports(project_id):
    """Generate and display SOP-required reports"""
    project = Project.query.get_or_404(project_id)
    
    # Generate reports if they don't exist
    existing_reports = ScheduleReport.query.filter_by(project_id=project_id).all()
    if not existing_reports:
        reports = sop_service.generate_sop_reports(project_id)
    else:
        reports = existing_reports
    
    # Organize reports by type
    report_types = {
        'full_schedule': next((r for r in reports if r.full_schedule), None),
        'baseline_comparison': next((r for r in reports if r.baseline_comparison), None),
        'lookahead_schedule': next((r for r in reports if r.lookahead_schedule), None),
        'longest_path': next((r for r in reports if r.longest_path), None),
        'total_float_report': next((r for r in reports if r.total_float_report), None),
        'update_form': next((r for r in reports if r.update_form), None)
    }
    
    return render_template('sop/reports.html',
                         project=project,
                         report_types=report_types)

@app.route('/sop/templates')
def schedule_templates():
    """Display schedule templates"""
    templates = ScheduleTemplate.query.all()
    
    if not templates:
        # Create templates if they don't exist
        templates = sop_service.create_schedule_templates()
    
    # Group templates by type
    template_groups = {}
    for template in templates:
        if template.template_type not in template_groups:
            template_groups[template.template_type] = []
        template_groups[template.template_type].append(template)
    
    return render_template('sop/templates.html',
                         template_groups=template_groups)

@app.route('/api/sop/project/<int:project_id>/compliance')
def api_sop_compliance(project_id):
    """API endpoint for SOP compliance data"""
    try:
        dashboard = sop_service.get_sop_compliance_dashboard(project_id)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'compliance_data': dashboard
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sop/float-status/<int:schedule_id>')
def api_float_status(schedule_id):
    """API endpoint for float status"""
    try:
        float_status = sop_service.update_schedule_float_status(schedule_id)
        
        return jsonify({
            'success': True,
            'schedule_id': schedule_id,
            'float_status': float_status.value if float_status else 'unknown'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sop/monthly-validation/<int:project_id>')
def api_monthly_validation(project_id):
    """API endpoint for monthly update validation"""
    try:
        validation = sop_service.validate_monthly_update_requirements(project_id)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'validation': validation
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# SOP Workflow endpoints
@app.route('/sop/workflow/<int:project_id>/<schedule_type>')
def sop_workflow(project_id, schedule_type):
    """SOP workflow management"""
    project = Project.query.get_or_404(project_id)
    
    workflow_steps = {
        'dd': ['Draft (2 weeks)', 'Review (1 week)', 'Finalize (1 week)'],
        'cd': ['Update (2 weeks)', 'Review (1 week)', 'Finalize (1 week)'],
        'baseline': ['Baseline (2 weeks)', 'Change Order Integration']
    }
    
    current_schedule = SOPSchedule.query.filter_by(
        project_id=project_id, 
        schedule_type=ScheduleType(schedule_type)
    ).first()
    
    timeline_status = None
    if current_schedule:
        timeline_status = sop_service.check_schedule_development_timeline(current_schedule.id)
    
    return render_template('sop/workflow.html',
                         project=project,
                         schedule_type=schedule_type,
                         workflow_steps=workflow_steps.get(schedule_type, []),
                         current_schedule=current_schedule,
                         timeline_status=timeline_status)

@app.route('/sop/demo/ncmoh')
def ncmoh_demo():
    """NCMoH Museum project demo page"""
    # Check if NCMoH project exists
    ncmoh_project = Project.query.filter(
        Project.name.contains('NC Museum of History')
    ).first()
    
    if not ncmoh_project:
        return render_template('sop/ncmoh_demo.html', project=None)
    
    # Get comprehensive compliance data
    compliance_data = ncmoh_importer.get_sop_compliance_summary(ncmoh_project.id)
    
    # Get SOP schedules
    sop_schedules = SOPSchedule.query.filter_by(project_id=ncmoh_project.id).all()
    
    # Get SOP activities
    sop_activities = []
    for schedule in sop_schedules:
        activities = SOPActivity.query.filter_by(schedule_id=schedule.id).all()
        sop_activities.extend(activities)
    
    return render_template('sop/ncmoh_demo.html',
                         project=ncmoh_project,
                         compliance_data=compliance_data,
                         sop_schedules=sop_schedules,
                         sop_activities=sop_activities[:20])  # Show first 20 activities