# BBSchedule - Construction Project Scheduler

🏗️ **An advanced AI-driven construction project scheduling platform** built for the **Balfour Beatty AI Hackathon**. This comprehensive Flask-based web application transforms infrastructure planning through intelligent, data-driven insights and interactive management tools with enterprise-grade 5D scheduling capabilities.

## 🚀 Features

### ✅ Core Project Management
- **Complete Project CRUD** - Create, view, edit, and manage construction projects with full lifecycle support
- **Activity Scheduling** - Detailed task management with both Gantt chart and linear scheduling methodologies
- **Dependency Management** - Complex task relationships (FS, SS, FF, SF) with lag calculations and critical path analysis
- **Progress Tracking** - Real-time activity progress updates with visual indicators and completion percentages
- **Resource Management** - Crew size allocation, production rate tracking, and equipment utilization
- **Cost Management** - Budget estimates vs actual cost tracking with variance analysis

### ✅ Advanced Scheduling (5D) - Enterprise Grade
- **Time Dimension** - Traditional scheduling with start/end dates, durations, and critical path calculations
- **Cost Dimension** - Budget tracking with Cost Performance Index (CPI) and Earned Value Management
- **Resource Dimension** - Crew allocation, equipment tracking, and resource conflict detection
- **Location Dimension** - Linear scheduling with station/chainage support for infrastructure projects
- **Quality Dimension** - Progress quality metrics, performance indicators, and risk assessment

### ✅ File Import/Export
- **Primavera P6 (.xer)** - Full import of existing P6 schedules with activities and dependencies
- **Microsoft Project (.xml)** - Import MS Project files with task relationships
- **Excel Export** - Professional multi-sheet reports with charts and metrics
- **PDF Reports** - Comprehensive schedule reports with visualizations

### ✅ AI-Powered Analytics & Reporting
- **Real-time Dashboard** - Live project metrics, KPIs, and executive-level insights
- **AI Optimization Engine** - Smart scheduling recommendations and scenario analysis
- **Schedule Performance Index (SPI)** - Advanced earned value management calculations
- **Critical Path Analysis** - Automated critical path identification with optimization suggestions
- **Risk Assessment** - Spatial conflict detection, weather impact analysis, and predictive risk modeling
- **Resource Utilization** - Intelligent crew and equipment utilization with optimization recommendations

### ✅ User Experience & Integration
- **Responsive Design** - Bootstrap 5 dark theme interface optimized for mobile, tablet, and desktop
- **Interactive Visualizations** - Chart.js-powered Gantt charts and linear schedules with real-time updates
- **Secure Authentication** - Session-based login system with comprehensive security middleware
- **File Management** - Document upload, organization, and version control by project
- **External Integrations** - Support for Procore, Autodesk Construction Cloud, and PlanGrid connectivity
- **Mobile/PWA Support** - Progressive Web App capabilities with offline functionality

## 🛠 Technology Stack

### Backend
- **Flask 3.0+** - Modern Python web framework with application factory pattern
- **SQLAlchemy** - Advanced ORM with PostgreSQL support and connection pooling
- **PostgreSQL** - Production-ready database with complex relationships and optimized indexes
- **Gunicorn** - WSGI HTTP server for production deployment with auto-reload
- **Service Architecture** - Modular business logic layer with dedicated service classes

### Frontend & Visualization
- **Bootstrap 5** - Responsive UI framework with custom dark theme optimized for construction management
- **Chart.js** - Interactive Gantt charts and linear scheduling visualizations with real-time data
- **Feather Icons** - Consistent iconography throughout the application
- **JavaScript ES6+** - Modern JavaScript with dynamic interactions and API integration

### File Processing
- **openpyxl** - Excel file generation and processing
- **ReportLab** - PDF report generation with charts
- **chardet** - File encoding detection
- **xmltodict** - XML parsing for MS Project files

## 📋 Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database (automatically configured on Replit)
- Environment variables: `DATABASE_URL`, `SESSION_SECRET`

### Quick Start on Replit
1. **Fork or Import** this repository to Replit
2. **Dependencies** are automatically installed via `pyproject.toml`
3. **Database** PostgreSQL is automatically provisioned and configured
4. **Environment Variables** are automatically set for development
5. **Run** the application using the "Run" button or `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

### Local Development Setup
```bash
# Clone and navigate to project
git clone <repository-url>
cd bbschedule

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export SESSION_SECRET="your-secure-session-secret"

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Load test data (optional)
python load_test_data.py

# Run the application
gunicorn --bind 0.0.0.0:5000 --reload main:app
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

### Chart & Visualization APIs
- `GET /api/project/{id}/activities` - Activity data optimized for Chart.js
- `GET /api/project/{id}/chart_data` - Chart-ready data with critical path
- `GET /api/projects/{id}/linear_schedule` - Linear schedule data with location mapping
- `GET /api/project/{id}/schedule_summary` - Real-time project statistics

### Dashboard & Analytics APIs
- `GET /api/dashboard/metrics` - Real-time dashboard metrics and KPIs
- `GET /api/project/{id}/ai_recommendations` - AI-powered project insights
- `POST /api/project/{id}/apply_ai_scenario` - Apply AI optimization scenarios
- `GET /api/projects/search` - Advanced project search with filters

### Project Management APIs
- `POST /api/project/{id}/update_activity_progress` - Update activity progress
- `GET /api/project/{id}/activities/overdue` - Overdue activities tracking
- `POST /projects/{id}/upload_document` - Document upload and management
- `GET /projects/{id}/export/excel` - Professional Excel export with charts
- `GET /projects/{id}/export/pdf` - Comprehensive PDF report generation
- `POST /import/schedule` - Import Primavera P6 (.xer) and MS Project (.xml) files

### Health & Monitoring APIs
- `GET /health/ping` - Simple health check for load balancers
- `GET /health/ready` - Readiness check for application deployment
- `GET /health/status` - Comprehensive system status with metrics

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

## 🚀 Recent Improvements (Latest - July 8, 2025)

### ✅ Enhanced JavaScript & Python Backend Integration
- **Fixed Critical JavaScript Errors** - Resolved linear schedule loading issues with robust date fallback handling
- **Python Backend Enhancement** - Enhanced linear schedule API with comprehensive success/error handling structure
- **API Parity Achievement** - Both Gantt chart and linear schedule APIs now have equivalent robust Python backend support
- **AI Scenario Application** - Fixed AI optimization feature with proper module imports and error handling

### ✅ Robust Chart Data Loading
- **Chart.js Integration** - Complete Chart.js integration with proper error states and loading indicators
- **Real-time Data Updates** - Linear schedules now load activity data successfully with location-based visualization
- **Enhanced Error Handling** - Comprehensive JavaScript error management with user-friendly feedback
- **API Response Consistency** - All visualization endpoints use consistent success/data/metadata structure

### ✅ Production-Ready Features
- **Database Optimization** - Strategic indexing and connection pooling for enterprise performance
- **Security Middleware** - Comprehensive security headers, rate limiting, and HTTPS enforcement
- **Health Monitoring** - Production health checks with real-time status and metrics
- **Mobile PWA Support** - Progressive Web App capabilities with offline functionality

### ✅ Codebase Quality Improvements
- **Removed Unused Files** - Cleaned up backup files (app_old.py, models_backup.py, routes_backup.py, routes_old.py)
- **Code Organization** - Maintained clean, modular architecture with service layer separation
- **Documentation Updates** - Comprehensive README updates with current feature status and API documentation
- **Performance Optimization** - Removed unused Python bytecode files and cache directories

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