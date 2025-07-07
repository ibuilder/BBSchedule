from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, DateField, SelectField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import date
from models import ProjectStatus, ActivityType, ScheduleType

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date', validators=[Optional()])
    status = SelectField('Status', choices=[(status.value, status.value.title()) for status in ProjectStatus])
    total_sf = FloatField('Total Square Footage', validators=[Optional(), NumberRange(min=0)])
    floor_count = IntegerField('Floor Count', validators=[Optional(), NumberRange(min=0)])
    building_type = StringField('Building Type', validators=[Optional(), Length(max=100)])
    location = StringField('Location', validators=[Optional(), Length(max=200)])
    budget = FloatField('Budget', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Create Project')

class ActivityForm(FlaskForm):
    name = StringField('Activity Name', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    activity_type = SelectField('Activity Type', choices=[(type.value, type.value.title()) for type in ActivityType])
    duration = IntegerField('Duration (days)', validators=[DataRequired(), NumberRange(min=1)])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    progress = IntegerField('Progress (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    quantity = FloatField('Quantity', validators=[Optional(), NumberRange(min=0)])
    unit = StringField('Unit', validators=[Optional(), Length(max=50)])
    production_rate = FloatField('Production Rate (units/day)', validators=[Optional(), NumberRange(min=0)])
    resource_crew_size = IntegerField('Crew Size', validators=[Optional(), NumberRange(min=0)])
    cost_estimate = FloatField('Cost Estimate', validators=[Optional(), NumberRange(min=0)])
    actual_cost = FloatField('Actual Cost', validators=[Optional(), NumberRange(min=0)])
    location_start = FloatField('Start Location/Station', validators=[Optional(), NumberRange(min=0)])
    location_end = FloatField('End Location/Station', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Activity')

class ScheduleForm(FlaskForm):
    name = StringField('Schedule Name', validators=[DataRequired(), Length(min=1, max=200)])
    schedule_type = SelectField('Schedule Type', choices=[(type.value, type.value.title()) for type in ScheduleType])
    is_baseline = SelectField('Is Baseline', choices=[('false', 'No'), ('true', 'Yes')], default='false')
    submit = SubmitField('Create Schedule')

class DocumentUploadForm(FlaskForm):
    file = FileField('Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'dwg', 'jpg', 'jpeg', 'png'], 
                   'Only PDF, DOC, DOCX, XLS, XLSX, DWG, JPG, JPEG, PNG files are allowed.')
    ])
    document_type = SelectField('Document Type', choices=[
        ('plans', 'Plans'),
        ('logistics', 'Site Logistics'),
        ('bim', 'BIM Files'),
        ('other', 'Other')
    ])
    submit = SubmitField('Upload Document')

class DependencyForm(FlaskForm):
    predecessor_id = SelectField('Predecessor Activity', coerce=int, validators=[DataRequired()])
    successor_id = SelectField('Successor Activity', coerce=int, validators=[DataRequired()])
    dependency_type = SelectField('Dependency Type', choices=[
        ('FS', 'Finish to Start'),
        ('SS', 'Start to Start'),
        ('FF', 'Finish to Finish'),
        ('SF', 'Start to Finish')
    ], default='FS')
    lag_days = IntegerField('Lag Days', validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField('Add Dependency')

class ScheduleImportForm(FlaskForm):
    file = FileField('Schedule File', validators=[
        FileRequired(),
        FileAllowed(['xer', 'xml', 'mpp'], 
                   'Only Primavera XER, Microsoft Project XML, or MPP files are allowed.')
    ])
    project_name = StringField('Project Name (Optional)', validators=[Optional(), Length(max=200)])
    import_type = SelectField('Import Type', choices=[
        ('new', 'Create New Project'),
        ('merge', 'Merge with Existing Project')
    ], default='new')
    existing_project = SelectField('Existing Project (for merge)', coerce=int, validators=[Optional()])
    submit = SubmitField('Import Schedule')

class FiveDAnalysisForm(FlaskForm):
    analysis_type = SelectField('Analysis Type', choices=[
        ('complete', 'Complete 5D Analysis'),
        ('cost', 'Cost Performance Analysis'),
        ('resource', 'Resource Utilization Analysis'),
        ('spatial', 'Spatial Conflict Analysis'),
        ('productivity', 'Productivity Analysis'),
        ('risk', 'Risk Assessment')
    ], default='complete')
    include_3d_model = SelectField('Include 3D Visualization', choices=[
        ('yes', 'Yes - Generate 3D Timeline'),
        ('no', 'No - Standard Analysis')
    ], default='no')
    time_period = SelectField('Analysis Period', choices=[
        ('current', 'Current Status'),
        ('weekly', 'Weekly Analysis'),
        ('monthly', 'Monthly Analysis'),
        ('full', 'Full Project Timeline')
    ], default='current')
    submit = SubmitField('Generate 5D Analysis')
