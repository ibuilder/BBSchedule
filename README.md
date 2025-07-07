# Construction Project Scheduler

A comprehensive Flask-based web application for managing construction project schedules with advanced visualization, 5D scheduling capabilities, and seamless integration with industry-standard tools.

## Features

### 🏗️ Core Functionality
- **Project Management**: Create, edit, and track construction projects with detailed metadata
- **Activity Scheduling**: Comprehensive activity management with Gantt and linear scheduling views
- **Dependency Management**: Define and visualize task dependencies with multiple relationship types
- **Progress Tracking**: Real-time progress updates with visual indicators
- **Resource Management**: Track crew sizes, production rates, and resource utilization

### 📊 Advanced Analytics
- **5D Scheduling**: Integrate time, cost, resources, and spatial dimensions
- **Performance Metrics**: Schedule Performance Index (SPI), Cost Performance Index (CPI)
- **Critical Path Analysis**: Automated critical path calculation and visualization
- **Budget Tracking**: Cost estimates vs actual costs with variance analysis
- **Risk Assessment**: Automated risk detection and reporting

### 📁 File Import/Export
- **Primavera P6 (.xer)**: Import existing P6 schedules
- **Microsoft Project (.xml, .mpp)**: Import MS Project files
- **Excel Export**: Export schedules to Excel format
- **PDF Reports**: Generate comprehensive PDF reports

### 🎨 User Interface
- **Responsive Design**: Mobile-friendly interface with Bootstrap
- **Interactive Charts**: Chart.js visualizations for Gantt and linear schedules
- **Real-time Updates**: Live dashboard metrics and progress tracking
- **User Authentication**: Session-based authentication system

## Technology Stack

### Backend
- **Framework**: Flask 3.0+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **File Processing**: pandas, openpyxl, reportlab
- **Authentication**: Flask sessions with login management

### Frontend
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js with date adapters
- **Icons**: Feather Icons
- **Responsive**: Mobile-first design

### Data Processing
- **Schedule Import**: Custom parsers for XER and XML formats
- **Export Tools**: Excel/PDF generation with professional formatting
- **Analytics**: Advanced metrics calculation and visualization

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Modern web browser

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd construction-scheduler
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Set the following environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/scheduler_db"
   export SESSION_SECRET="your-secret-key-here"
   ```

4. **Database Setup**
   ```bash
   # The application will automatically create tables on first run
   python main.py
   ```

5. **Run the Application**
   ```bash
   # Development
   python main.py
   
   # Production with Gunicorn
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## Usage Guide

### Getting Started

1. **Login**: Use any username/password combination (demo mode)
2. **Create Project**: Click "New Project" and fill in project details
3. **Add Activities**: Navigate to project details and add construction activities
4. **Set Dependencies**: Define task relationships in the Dependencies section
5. **Track Progress**: Update activity progress and monitor dashboard metrics

### Project Management

**Creating Projects**
- Enter project name, description, and timeline
- Specify construction details (square footage, floors, building type)
- Set budget and location information

**Managing Activities**
- Add activities with duration, type, and resource requirements
- Set start/end dates and progress percentages
- Include cost estimates and production rates

**Schedule Visualization**
- **Gantt Chart**: Traditional timeline view with dependencies
- **Linear Schedule**: Location-based scheduling for repetitive activities

### Import/Export

**Importing Schedules**
- Navigate to "Import Schedule"
- Upload .xer (Primavera) or .xml (MS Project) files
- Review imported data and merge with existing projects

**Exporting Data**
- **Excel**: Comprehensive project data with multiple sheets
- **PDF**: Professional reports with charts and metrics

### 5D Analysis

Access advanced 5D scheduling analysis from project reports:
- Time performance analysis
- Cost variance tracking
- Resource utilization metrics
- Spatial conflict detection
- Risk assessment and recommendations

## API Endpoints

### Project Data
```
GET /api/project/{id}/activities     # Get project activities and dependencies
GET /api/dashboard/metrics           # Real-time dashboard metrics
GET /api/projects/search            # Search projects with filters
```

### Progress Updates
```
POST /api/project/{id}/update_activity_progress  # Update activity progress
GET /api/project/{id}/activities/overdue        # Get overdue activities
```

### Analytics
```
GET /api/project/{id}/5d_metrics    # 5D scheduling analysis
```

## File Structure

```
construction-scheduler/
├── app.py              # Flask application setup
├── main.py             # Application entry point
├── models.py           # Database models and schemas
├── routes.py           # URL routes and view functions
├── forms.py            # WTForms for form handling
├── utils.py            # Utility functions and calculations
├── import_utils.py     # Schedule import functionality
├── static/
│   ├── css/
│   │   └── custom.css  # Custom styling
│   └── js/
│       ├── gantt.js    # Gantt chart functionality
│       ├── linear.js   # Linear schedule functionality
│       └── dashboard.js # Dashboard interactions
├── templates/
│   ├── auth/           # Authentication templates
│   ├── base.html       # Base template
│   ├── index.html      # Dashboard
│   └── ...             # Various page templates
└── uploads/            # File upload directory
```

## Database Schema

### Core Tables
- **projects**: Project metadata and settings
- **activities**: Individual tasks with scheduling data
- **dependencies**: Task relationships and constraints
- **schedules**: Different schedule views and baselines

### Analytics Tables
- **schedule_metrics**: Performance tracking over time
- **historical_projects**: Project snapshots and baselines
- **documents**: File attachments and references

## Configuration

### Environment Variables
```bash
DATABASE_URL          # PostgreSQL connection string
SESSION_SECRET        # Flask session encryption key
UPLOAD_FOLDER        # File upload directory (optional)
MAX_CONTENT_LENGTH   # Maximum upload size (optional)
```

### Application Settings
- File upload limits and allowed types
- Session timeout and security settings
- Database connection pooling
- Logging configuration

## Development

### Code Structure
- **Models**: SQLAlchemy ORM classes in `models.py`
- **Views**: Flask routes and business logic in `routes.py`
- **Forms**: WTForms validation in `forms.py`
- **Utils**: Helper functions and calculations in `utils.py`
- **Import**: Schedule file processing in `import_utils.py`

### Adding Features
1. Define database models in `models.py`
2. Create forms in `forms.py` for user input
3. Add routes in `routes.py` for new functionality
4. Create templates for new pages
5. Add utility functions as needed

### Testing Import Functionality
```python
from import_utils import import_schedule_file

# Test XER import
project = import_schedule_file('sample_project.xer', 'Test Project')

# Test XML import
project = import_schedule_file('project.xml', 'MS Project Import')
```

## Troubleshooting

### Common Issues

**Database Connection Errors**
- Verify DATABASE_URL environment variable
- Ensure PostgreSQL is running
- Check database permissions

**File Import Failures**
- Verify file format (.xer, .xml supported)
- Check file encoding (UTF-8 recommended)
- Review error logs for specific issues

**Chart Display Issues**
- Ensure JavaScript is enabled
- Check browser console for errors
- Verify Chart.js library loading

### Performance Optimization
- Use database indexing for large projects
- Implement pagination for activity lists
- Optimize chart rendering for many activities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or feature requests:
- Create an issue on GitHub
- Review the troubleshooting section
- Check existing documentation

## Changelog

### Version 1.0.0 (Current)
- Initial release with core scheduling functionality
- Primavera P6 and MS Project import support
- 5D scheduling analysis capabilities
- Real-time dashboard and metrics
- Excel/PDF export functionality
- Mobile-responsive interface

---

**Built with ❤️ for the construction industry**