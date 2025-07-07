# Construction Project Scheduler

A comprehensive Flask-based web application for managing construction project schedules with advanced 5D scheduling capabilities. The system supports both Gantt chart and linear scheduling methodologies, providing enterprise-level project management for construction teams.

## 🚀 Features

### ✅ Core Project Management
- **Complete Project CRUD** - Create, view, edit, and manage construction projects
- **Activity Scheduling** - Detailed task management with Gantt and linear scheduling
- **Dependency Management** - Complex task relationships with lag calculations
- **Progress Tracking** - Real-time activity progress updates with visual indicators
- **Resource Management** - Crew size and production rate tracking
- **Cost Management** - Budget estimates vs actual cost tracking and analysis

### ✅ Advanced Scheduling (5D)
- **Time Dimension** - Traditional scheduling with start/end dates and durations
- **Cost Dimension** - Budget tracking, cost performance index (CPI) calculations
- **Resource Dimension** - Crew allocation, equipment, and material tracking
- **Location Dimension** - Linear scheduling with station/chainage support
- **Quality Dimension** - Progress quality metrics and performance indicators

### ✅ File Import/Export
- **Primavera P6 (.xer)** - Full import of existing P6 schedules with activities and dependencies
- **Microsoft Project (.xml)** - Import MS Project files with task relationships
- **Excel Export** - Professional multi-sheet reports with charts and metrics
- **PDF Reports** - Comprehensive schedule reports with visualizations

### ✅ Analytics & Reporting
- **Real-time Dashboard** - Live project metrics and KPIs
- **Schedule Performance Index (SPI)** - Earned value management calculations
- **Critical Path Analysis** - Automated critical path identification
- **Risk Assessment** - Spatial conflict detection and risk analysis
- **Resource Utilization** - Crew and equipment utilization tracking

### ✅ User Experience
- **Responsive Design** - Bootstrap 5 interface optimized for mobile and desktop
- **Interactive Charts** - Chart.js visualizations for Gantt and linear schedules
- **User Authentication** - Secure session-based login system
- **File Management** - Document upload and organization by project

## 🛠 Technology Stack

### Backend
- **Flask 3.0+** - Modern Python web framework
- **SQLAlchemy** - Advanced ORM with PostgreSQL support
- **PostgreSQL** - Production-ready database with complex relationships
- **Gunicorn** - WSGI HTTP server for production deployment

### Frontend
- **Bootstrap 5** - Responsive UI framework with dark theme
- **Chart.js** - Interactive charts and visualizations
- **Feather Icons** - Consistent iconography
- **JavaScript** - Dynamic interactions and real-time updates

### File Processing
- **openpyxl** - Excel file generation and processing
- **ReportLab** - PDF report generation with charts
- **chardet** - File encoding detection
- **xmltodict** - XML parsing for MS Project files

## 📋 Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Environment variables: `DATABASE_URL`, `SESSION_SECRET`

### Quick Start
```bash
# Clone and navigate to project
cd construction-scheduler

# Install dependencies (handled automatically by Replit)
# Dependencies: flask, sqlalchemy, postgresql, bootstrap

# Set environment variables
export DATABASE_URL="postgresql://..."
export SESSION_SECRET="your-secret-key"

# Run the application
python main.py
# or
gunicorn --bind 0.0.0.0:5000 main:app
```

### Environment Configuration
```bash
DATABASE_URL=postgresql://user:password@localhost/construction_scheduler
SESSION_SECRET=your-secure-session-secret
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB file upload limit
```

## 🗃 Database Schema

### Core Models
- **Projects** - Main project entities with budget, location, and timeline tracking
- **Activities** - Detailed tasks with progress, resources, and cost tracking
- **Dependencies** - Task relationships (FS, SS, FF, SF) with lag support
- **Schedules** - Multiple schedule types (Gantt, Linear) with baseline support
- **Documents** - File attachments organized by project and type
- **ScheduleMetrics** - Historical performance data for analytics
- **HistoricalProject** - Project snapshots for baseline comparisons

### Data Relationships
```
Project (1) ──→ (N) Activity
Activity (N) ──→ (N) Dependency
Project (1) ──→ (N) Schedule
Project (1) ──→ (N) Document
Project (1) ──→ (N) ScheduleMetrics
```

## 📊 API Endpoints

### REST API
- `GET /api/project/{id}/activities` - Activity data for charts
- `GET /api/dashboard/metrics` - Real-time dashboard metrics
- `POST /api/project/{id}/update_activity_progress` - Update progress
- `GET /api/projects/search` - Project search with filters
- `GET /api/project/{id}/activities/overdue` - Overdue activities

### File Operations
- `POST /projects/{id}/upload_document` - Document upload
- `GET /projects/{id}/export/excel` - Excel export
- `GET /projects/{id}/export/pdf` - PDF report generation
- `POST /import/schedule` - Import .xer/.xml files

## 🎯 Usage Examples

### Creating a New Project
1. Navigate to "Projects" → "Create New Project"
2. Fill in project details (name, dates, budget, location)
3. Add activities with durations and resource requirements
4. Define dependencies between activities
5. Generate Gantt chart or linear schedule

### Importing Existing Schedules
1. Go to "Import Schedule" 
2. Upload .xer (Primavera) or .xml (MS Project) file
3. Map activity types and validate data
4. Review imported project and activities
5. Adjust and optimize as needed

### 5D Analysis Workflow
1. Select project for analysis
2. Choose analysis type (complete, cost, resource, spatial)
3. Set time period (current, weekly, monthly, full timeline)
4. Review generated metrics and recommendations
5. Export results to Excel or PDF

## 🔧 Development

### Code Structure
```
├── app.py              # Flask application setup
├── models.py           # Database models and relationships
├── routes.py           # Web routes and API endpoints
├── forms.py            # WTForms for data validation
├── utils.py            # Utility functions and calculations
├── import_utils.py     # File import processors
├── static/             # CSS, JavaScript, and assets
├── templates/          # Jinja2 HTML templates
└── uploads/            # File upload directory
```

### Key Utility Functions
- `calculate_schedule_metrics()` - SPI, CPI, and performance calculations
- `export_schedule_to_excel()` - Multi-sheet Excel report generation
- `generate_schedule_pdf()` - Comprehensive PDF reports
- `calculate_critical_path()` - Critical path analysis algorithm
- `validate_schedule_logic()` - Schedule validation and error detection

### Import Processors
- `XERImporter` - Primavera P6 file parser
- `MPPImporter` - Microsoft Project XML parser
- `FiveDScheduleManager` - 5D analysis and optimization

## 📈 Performance Metrics

### Supported Calculations
- **Schedule Performance Index (SPI)** = Earned Value / Planned Value
- **Cost Performance Index (CPI)** = Earned Value / Actual Cost
- **Resource Utilization** = Actual Hours / Available Hours
- **Critical Path Variance** = Standard deviation of critical path durations
- **Quality Score** = Weighted average of completion quality metrics

### Real-time Analytics
- Project completion percentages
- Budget utilization tracking
- Overdue activity identification
- Resource conflict detection
- Spatial overlap analysis

## 🚀 Deployment

### Production Deployment
The application is ready for deployment with:
- PostgreSQL database support
- Gunicorn WSGI server configuration
- ProxyFix middleware for reverse proxies
- Session management with secure cookies
- File upload validation and security

### Scaling Considerations
- Database connection pooling configured
- Static file serving optimized
- Chart rendering client-side for performance
- Efficient query patterns with SQLAlchemy
- Background processing capability for large imports

## 📝 License & Support

This is a comprehensive construction scheduling application built with modern web technologies. The codebase includes full implementations of all classes, models, and utilities with professional error handling and documentation.

For technical support or feature requests, refer to the application documentation or contact the development team.

---

**Built with Flask • PostgreSQL • Bootstrap • Chart.js**

*Professional construction project management made simple*