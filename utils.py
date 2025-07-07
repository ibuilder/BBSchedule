import os
import pandas as pd
from datetime import datetime, timedelta
import tempfile
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

def calculate_schedule_metrics(project, activities):
    """Calculate schedule performance metrics"""
    if not activities:
        return {
            'total_activities': 0,
            'completed_activities': 0,
            'in_progress_activities': 0,
            'not_started_activities': 0,
            'completion_percentage': 0,
            'schedule_performance_index': 0,
            'critical_path_length': 0,
            'resource_utilization': 0
        }
    
    total_activities = len(activities)
    completed_activities = sum(1 for a in activities if a.progress == 100)
    in_progress_activities = sum(1 for a in activities if 0 < a.progress < 100)
    not_started_activities = sum(1 for a in activities if a.progress == 0)
    
    completion_percentage = (completed_activities / total_activities) * 100
    
    # Calculate planned vs actual progress
    planned_value = sum(a.cost_estimate or 0 for a in activities)
    earned_value = sum((a.cost_estimate or 0) * (a.progress / 100) for a in activities)
    actual_cost = sum(a.actual_cost or 0 for a in activities)
    
    # Schedule Performance Index
    spi = earned_value / planned_value if planned_value > 0 else 0
    
    # Critical path calculation (simplified)
    critical_path_length = max([a.duration for a in activities], default=0)
    
    # Resource utilization (simplified)
    total_crew_capacity = sum(a.resource_crew_size or 0 for a in activities)
    utilized_crew = sum((a.resource_crew_size or 0) * (a.progress / 100) for a in activities)
    resource_utilization = (utilized_crew / total_crew_capacity * 100) if total_crew_capacity > 0 else 0
    
    return {
        'total_activities': total_activities,
        'completed_activities': completed_activities,
        'in_progress_activities': in_progress_activities,
        'not_started_activities': not_started_activities,
        'completion_percentage': round(completion_percentage, 2),
        'schedule_performance_index': round(spi, 2),
        'critical_path_length': critical_path_length,
        'resource_utilization': round(resource_utilization, 2),
        'planned_value': planned_value,
        'earned_value': earned_value,
        'actual_cost': actual_cost
    }

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
