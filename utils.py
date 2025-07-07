import os
import pandas as pd
from datetime import datetime, timedelta
import tempfile
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO

def calculate_schedule_metrics(project, activities):
    """Calculate comprehensive schedule performance metrics"""
    if not activities:
        return {
            'total_activities': 0,
            'completed_activities': 0,
            'in_progress_activities': 0,
            'not_started_activities': 0,
            'overdue_activities': 0,
            'completion_percentage': 0,
            'schedule_performance_index': 0,
            'cost_performance_index': 0,
            'critical_path_length': 0,
            'resource_utilization': 0,
            'budget_utilization': 0,
            'planned_value': 0,
            'earned_value': 0,
            'actual_cost': 0
        }
    
    # Basic activity counts
    total_activities = len(activities)
    completed_activities = sum(1 for a in activities if a.progress >= 100)
    in_progress_activities = sum(1 for a in activities if 0 < a.progress < 100)
    not_started_activities = sum(1 for a in activities if a.progress == 0)
    overdue_activities = sum(1 for a in activities if a.is_overdue())
    
    completion_percentage = (completed_activities / total_activities) * 100
    
    # Financial metrics
    planned_value = sum(a.cost_estimate or 0 for a in activities)
    earned_value = sum((a.cost_estimate or 0) * (a.progress / 100) for a in activities)
    actual_cost = sum(a.actual_cost or 0 for a in activities)
    
    # Performance indices
    spi = earned_value / planned_value if planned_value > 0 else 0  # Schedule Performance Index
    cpi = earned_value / actual_cost if actual_cost > 0 else 0      # Cost Performance Index
    
    # Critical path calculation (simplified - longest duration path)
    critical_path_length = max([a.duration for a in activities], default=0)
    
    # Resource utilization
    total_crew_capacity = sum(a.resource_crew_size or 0 for a in activities)
    utilized_crew = sum((a.resource_crew_size or 0) * (a.progress / 100) for a in activities)
    resource_utilization = (utilized_crew / total_crew_capacity * 100) if total_crew_capacity > 0 else 0
    
    # Budget utilization
    budget_utilization = (actual_cost / project.budget * 100) if project.budget and project.budget > 0 else 0
    
    return {
        'total_activities': total_activities,
        'completed_activities': completed_activities,
        'in_progress_activities': in_progress_activities,
        'not_started_activities': not_started_activities,
        'overdue_activities': overdue_activities,
        'completion_percentage': round(completion_percentage, 2),
        'schedule_performance_index': round(spi, 2),
        'cost_performance_index': round(cpi, 2),
        'critical_path_length': critical_path_length,
        'resource_utilization': round(resource_utilization, 2),
        'budget_utilization': round(budget_utilization, 2),
        'planned_value': round(planned_value, 2),
        'earned_value': round(earned_value, 2),
        'actual_cost': round(actual_cost, 2)
    }

def export_schedule_to_excel(project, activities):
    """Export project schedule to Excel format"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()
    
    try:
        # Create Excel workbook
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            # Project Summary Sheet
            project_data = {
                'Project Name': [project.name],
                'Description': [project.description or ''],
                'Start Date': [project.start_date.strftime('%Y-%m-%d') if project.start_date else ''],
                'End Date': [project.end_date.strftime('%Y-%m-%d') if project.end_date else ''],
                'Status': [project.status.value if project.status else ''],
                'Budget': [project.budget or 0],
                'Location': [project.location or ''],
                'Building Type': [project.building_type or ''],
                'Total SF': [project.total_sf or 0],
                'Floor Count': [project.floor_count or 0]
            }
            project_df = pd.DataFrame(project_data)
            project_df.to_excel(writer, sheet_name='Project Summary', index=False)
            
            # Activities Sheet
            activities_data = []
            for activity in activities:
                activities_data.append({
                    'ID': activity.id,
                    'Name': activity.name,
                    'Description': activity.description or '',
                    'Type': activity.activity_type.value if activity.activity_type else '',
                    'Duration (Days)': activity.duration,
                    'Start Date': activity.start_date.strftime('%Y-%m-%d') if activity.start_date else '',
                    'End Date': activity.end_date.strftime('%Y-%m-%d') if activity.end_date else '',
                    'Progress (%)': activity.progress or 0,
                    'Quantity': activity.quantity or 0,
                    'Unit': activity.unit or '',
                    'Production Rate': activity.production_rate or 0,
                    'Crew Size': activity.resource_crew_size or 0,
                    'Cost Estimate': activity.cost_estimate or 0,
                    'Actual Cost': activity.actual_cost or 0,
                    'Location Start': activity.location_start or 0,
                    'Location End': activity.location_end or 0,
                    'Status': activity.get_progress_status(),
                    'Notes': activity.notes or ''
                })
            
            if activities_data:
                activities_df = pd.DataFrame(activities_data)
                activities_df.to_excel(writer, sheet_name='Activities', index=False)
            
            # Metrics Sheet
            metrics = calculate_schedule_metrics(project, activities)
            metrics_data = {
                'Metric': list(metrics.keys()),
                'Value': list(metrics.values())
            }
            metrics_df = pd.DataFrame(metrics_data)
            metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        
        return temp_file.name
        
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise e

def generate_schedule_pdf(project, activities):
    """Generate PDF report for project schedule"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.close()
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(temp_file.name, pagesize=landscape(letter))
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"Project Schedule Report: {project.name}", title_style))
        story.append(Spacer(1, 20))
        
        # Project Information
        story.append(Paragraph("Project Information", styles['Heading2']))
        project_info_data = [
            ['Project Name', project.name],
            ['Description', project.description or 'N/A'],
            ['Start Date', project.start_date.strftime('%Y-%m-%d') if project.start_date else 'N/A'],
            ['End Date', project.end_date.strftime('%Y-%m-%d') if project.end_date else 'N/A'],
            ['Status', project.status.value if project.status else 'N/A'],
            ['Budget', f"${project.budget:,.2f}" if project.budget else 'N/A'],
            ['Location', project.location or 'N/A']
        ]
        
        project_table = Table(project_info_data, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(project_table)
        story.append(Spacer(1, 20))
        
        # Activities Summary
        if activities:
            story.append(Paragraph("Activities Summary", styles['Heading2']))
            
            # Create activities table
            activities_data = [['ID', 'Activity Name', 'Type', 'Duration', 'Progress', 'Status', 'Cost Estimate']]
            
            for activity in activities[:20]:  # Limit to first 20 activities for PDF
                activities_data.append([
                    str(activity.id),
                    activity.name[:30] + '...' if len(activity.name) > 30 else activity.name,
                    activity.activity_type.value if activity.activity_type else 'N/A',
                    f"{activity.duration} days",
                    f"{activity.progress or 0}%",
                    activity.get_progress_status(),
                    f"${activity.cost_estimate:,.2f}" if activity.cost_estimate else 'N/A'
                ])
            
            activities_table = Table(activities_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch, 1*inch, 1.2*inch])
            activities_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            story.append(activities_table)
            story.append(Spacer(1, 20))
        
        # Metrics Summary
        metrics = calculate_schedule_metrics(project, activities)
        story.append(Paragraph("Project Metrics", styles['Heading2']))
        
        metrics_data = [
            ['Total Activities', str(metrics['total_activities'])],
            ['Completed Activities', str(metrics['completed_activities'])],
            ['In Progress Activities', str(metrics['in_progress_activities'])],
            ['Overdue Activities', str(metrics['overdue_activities'])],
            ['Completion Percentage', f"{metrics['completion_percentage']}%"],
            ['Schedule Performance Index', str(metrics['schedule_performance_index'])],
            ['Cost Performance Index', str(metrics['cost_performance_index'])],
            ['Budget Utilization', f"{metrics['budget_utilization']}%"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
        
        # Build PDF
        doc.build(story)
        return temp_file.name
        
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise e

def calculate_critical_path(activities, dependencies):
    """Calculate critical path using simple forward/backward pass"""
    if not activities:
        return []
    
    # Initialize activity timing
    activity_dict = {a.id: a for a in activities}
    early_start = {}
    early_finish = {}
    late_start = {}
    late_finish = {}
    
    # Forward pass - calculate early start and finish
    for activity in activities:
        predecessors = [dep for dep in dependencies if dep.successor_id == activity.id]
        if not predecessors:
            early_start[activity.id] = 0
        else:
            max_predecessor_finish = max([early_finish.get(dep.predecessor_id, 0) + (dep.lag_days or 0) 
                                        for dep in predecessors])
            early_start[activity.id] = max_predecessor_finish
        
        early_finish[activity.id] = early_start[activity.id] + activity.duration
    
    # Project completion time
    project_finish = max(early_finish.values()) if early_finish else 0
    
    # Backward pass - calculate late start and finish
    for activity in reversed(activities):
        successors = [dep for dep in dependencies if dep.predecessor_id == activity.id]
        if not successors:
            late_finish[activity.id] = project_finish
        else:
            min_successor_start = min([late_start.get(dep.successor_id, project_finish) - (dep.lag_days or 0) 
                                     for dep in successors])
            late_finish[activity.id] = min_successor_start
        
        late_start[activity.id] = late_finish[activity.id] - activity.duration
    
    # Identify critical activities (where early start = late start)
    critical_activities = []
    for activity in activities:
        if early_start.get(activity.id, 0) == late_start.get(activity.id, 0):
            critical_activities.append(activity)
    
    return critical_activities

def validate_schedule_logic(activities, dependencies):
    """Validate schedule logic and detect circular dependencies"""
    errors = []
    warnings = []
    
    # Check for circular dependencies using DFS
    def has_circular_dependency(activity_id, visited, rec_stack):
        visited[activity_id] = True
        rec_stack[activity_id] = True
        
        # Get all successors
        successors = [dep.successor_id for dep in dependencies if dep.predecessor_id == activity_id]
        
        for successor_id in successors:
            if not visited.get(successor_id, False):
                if has_circular_dependency(successor_id, visited, rec_stack):
                    return True
            elif rec_stack.get(successor_id, False):
                return True
        
        rec_stack[activity_id] = False
        return False
    
    # Check each activity for circular dependencies
    activity_ids = [a.id for a in activities]
    visited = {}
    rec_stack = {}
    
    for activity_id in activity_ids:
        if not visited.get(activity_id, False):
            if has_circular_dependency(activity_id, visited, rec_stack):
                errors.append(f"Circular dependency detected involving activity {activity_id}")
    
    # Check for missing start/end dates
    for activity in activities:
        if not activity.start_date and not activity.end_date:
            warnings.append(f"Activity '{activity.name}' has no start or end date")
        
        if activity.progress > 100:
            errors.append(f"Activity '{activity.name}' has progress > 100%")
        
        if activity.cost_estimate and activity.actual_cost and activity.actual_cost > activity.cost_estimate * 2:
            warnings.append(f"Activity '{activity.name}' actual cost significantly exceeds estimate")
    
    return {'errors': errors, 'warnings': warnings}

def export_schedule_to_excel(project, activities):
    """Export project schedule to Excel file"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Prepare data
    data = []
    for activity in activities:
        data.append({
            'Activity ID': activity.id,
            'Activity Name': activity.name,
            'Type': activity.activity_type.value,
            'Duration (days)': activity.duration,
            'Start Date': activity.start_date.strftime('%Y-%m-%d') if activity.start_date else '',
            'End Date': activity.end_date.strftime('%Y-%m-%d') if activity.end_date else '',
            'Progress (%)': activity.progress,
            'Quantity': activity.quantity or '',
            'Unit': activity.unit or '',
            'Production Rate': activity.production_rate or '',
            'Crew Size': activity.resource_crew_size or '',
            'Cost Estimate': activity.cost_estimate or '',
            'Actual Cost': activity.actual_cost or '',
            'Location Start': activity.location_start or '',
            'Location End': activity.location_end or '',
            'Notes': activity.notes or ''
        })
    
    # Create DataFrame and export
    df = pd.DataFrame(data)
    
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        # Project summary sheet
        project_data = {
            'Project Name': [project.name],
            'Description': [project.description or ''],
            'Start Date': [project.start_date.strftime('%Y-%m-%d')],
            'End Date': [project.end_date.strftime('%Y-%m-%d') if project.end_date else ''],
            'Status': [project.status.value],
            'Total SF': [project.total_sf or ''],
            'Floor Count': [project.floor_count or ''],
            'Building Type': [project.building_type or ''],
            'Location': [project.location or ''],
            'Budget': [project.budget or '']
        }
        project_df = pd.DataFrame(project_data)
        project_df.to_excel(writer, sheet_name='Project Summary', index=False)
        
        # Activities sheet
        df.to_excel(writer, sheet_name='Activities', index=False)
        
        # Metrics sheet
        metrics = calculate_schedule_metrics(project, activities)
        metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
        metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
    
    return temp_file.name

def generate_schedule_pdf(project, activities):
    """Generate project schedule PDF report"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    # Create PDF document
    doc = SimpleDocTemplate(temp_file.name, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph(f"Construction Schedule Report: {project.name}", title_style))
    story.append(Spacer(1, 20))
    
    # Project information
    project_info = [
        ['Project Name:', project.name],
        ['Start Date:', project.start_date.strftime('%Y-%m-%d')],
        ['End Date:', project.end_date.strftime('%Y-%m-%d') if project.end_date else 'TBD'],
        ['Status:', project.status.value.title()],
        ['Total SF:', f"{project.total_sf:,.0f}" if project.total_sf else 'N/A'],
        ['Building Type:', project.building_type or 'N/A'],
        ['Location:', project.location or 'N/A']
    ]
    
    project_table = Table(project_info, colWidths=[2*inch, 4*inch])
    project_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(project_table)
    story.append(Spacer(1, 20))
    
    # Activities table
    story.append(Paragraph("Project Activities", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    activity_data = [['Activity Name', 'Type', 'Duration', 'Start Date', 'Progress', 'Crew Size']]
    
    for activity in activities:
        activity_data.append([
            activity.name,
            activity.activity_type.value.title(),
            f"{activity.duration} days",
            activity.start_date.strftime('%Y-%m-%d') if activity.start_date else 'TBD',
            f"{activity.progress}%",
            str(activity.resource_crew_size) if activity.resource_crew_size else 'N/A'
        ])
    
    activity_table = Table(activity_data)
    activity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(activity_table)
    story.append(Spacer(1, 20))
    
    # Metrics
    metrics = calculate_schedule_metrics(project, activities)
    story.append(Paragraph("Schedule Metrics", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    metrics_data = [
        ['Total Activities', str(metrics['total_activities'])],
        ['Completed Activities', str(metrics['completed_activities'])],
        ['In Progress Activities', str(metrics['in_progress_activities'])],
        ['Completion Percentage', f"{metrics['completion_percentage']}%"],
        ['Schedule Performance Index', str(metrics['schedule_performance_index'])],
        ['Resource Utilization', f"{metrics['resource_utilization']}%"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metrics_table)
    
    # Build PDF
    doc.build(story)
    
    return temp_file.name

def calculate_critical_path(activities, dependencies):
    """Calculate critical path for project activities"""
    # This is a simplified critical path calculation
    # In a production system, you'd want a more sophisticated algorithm
    
    if not activities:
        return []
    
    # Create adjacency list
    graph = {}
    for activity in activities:
        graph[activity.id] = []
    
    for dep in dependencies:
        if dep.predecessor_id in graph:
            graph[dep.predecessor_id].append(dep.successor_id)
    
    # Find longest path (critical path)
    def dfs(node, path, visited):
        if node in visited:
            return path
        
        visited.add(node)
        max_path = path
        
        for neighbor in graph.get(node, []):
            new_path = dfs(neighbor, path + [neighbor], visited.copy())
            if len(new_path) > len(max_path):
                max_path = new_path
        
        return max_path
    
    critical_path = []
    for start_node in graph:
        path = dfs(start_node, [start_node], set())
        if len(path) > len(critical_path):
            critical_path = path
    
    return critical_path

def validate_schedule_logic(activities, dependencies):
    """Validate schedule logic and detect circular dependencies"""
    errors = []
    
    # Check for circular dependencies
    graph = {}
    for activity in activities:
        graph[activity.id] = []
    
    for dep in dependencies:
        if dep.predecessor_id in graph:
            graph[dep.predecessor_id].append(dep.successor_id)
    
    # DFS to detect cycles
    def has_cycle(node, visited, rec_stack):
        visited[node] = True
        rec_stack[node] = True
        
        for neighbor in graph.get(node, []):
            if not visited.get(neighbor, False):
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif rec_stack.get(neighbor, False):
                return True
        
        rec_stack[node] = False
        return False
    
    visited = {}
    rec_stack = {}
    
    for node in graph:
        if not visited.get(node, False):
            if has_cycle(node, visited, rec_stack):
                errors.append(f"Circular dependency detected involving activity {node}")
    
    # Check for missing predecessors/successors
    for dep in dependencies:
        if dep.predecessor_id not in graph:
            errors.append(f"Dependency references non-existent predecessor activity {dep.predecessor_id}")
        if dep.successor_id not in graph:
            errors.append(f"Dependency references non-existent successor activity {dep.successor_id}")
    
    return errors
