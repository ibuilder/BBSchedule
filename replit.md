# Construction Project Scheduler

## Overview

This is a Flask-based web application for managing construction project schedules. The system supports both Gantt chart and linear scheduling methodologies, providing comprehensive project management capabilities for construction teams. The application handles project planning, activity scheduling, resource management, and progress tracking with visual scheduling tools. Key features include importing existing schedules from Primavera P6 (.xer) and Microsoft Project (.xml, .mpp) files, and advanced 5D scheduling analysis combining time, cost, resources, and spatial dimensions.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite for development (configurable to PostgreSQL via DATABASE_URL)
- **Forms**: Flask-WTF for form handling and validation
- **File Handling**: Werkzeug for secure file uploads
- **Authentication**: Basic session management (no user auth implemented yet)

### Frontend Architecture
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Feather Icons for consistent iconography
- **Charts**: Chart.js for Gantt and linear schedule visualizations
- **Styling**: Custom CSS with Bootstrap overrides

### Database Schema
- **Projects**: Main project entities with metadata (budget, location, dates)
- **Activities**: Individual project tasks with scheduling details
- **Dependencies**: Task relationships and sequencing
- **Schedules**: Different schedule views (Gantt, Linear)
- **Documents**: File attachments for projects
- **Enums**: Status tracking (Planning, Active, Completed, Cancelled)

## Key Components

### Models (models.py)
- **Project**: Central project entity with relationships to activities and schedules
- **Activity**: Individual tasks with timing, resources, and location data
- **Schedule**: Different schedule types (Gantt vs Linear)
- **Document**: File management for project documents
- **Dependencies**: Task sequencing and relationships

### Forms (forms.py)
- **ProjectForm**: Project creation and editing
- **ActivityForm**: Activity management with duration and resource fields
- **ScheduleForm**: Schedule type selection and baseline management
- **DocumentUploadForm**: File upload with type validation

### Routes (routes.py)
- Dashboard with project overview and metrics
- Project CRUD operations
- Activity management within projects
- Schedule visualization (Gantt and Linear)
- Document management and file uploads
- Export capabilities (Excel, PDF)

### Utilities (utils.py)
- Schedule performance calculations
- Export functionality for Excel and PDF
- Metrics calculation for project dashboards
- Resource utilization tracking

### Import Utilities (import_utils.py)
- Primavera P6 (.xer) file import and parsing
- Microsoft Project (.xml, .mpp) file import support
- 5D scheduling analysis and metrics calculation
- Spatial conflict detection and risk assessment
- Cost and resource performance analysis

## Data Flow

1. **Project Creation**: Users create projects with basic metadata
2. **Activity Planning**: Activities are added to projects with scheduling details
3. **Schedule Generation**: System generates Gantt or Linear schedule views
4. **Progress Tracking**: Activities are updated with progress percentages
5. **Reporting**: Metrics calculated and reports generated

## External Dependencies

### Python Packages
- Flask: Web framework
- SQLAlchemy: Database ORM
- Flask-WTF: Form handling
- Werkzeug: WSGI utilities
- ReportLab: PDF generation
- Pandas: Data manipulation for exports

### Frontend Libraries
- Bootstrap 5: UI framework
- Chart.js: Chart visualization
- Feather Icons: Icon library

### File Storage
- Local file system for document uploads
- Configurable upload directory with size limits

## Deployment Strategy

### Development
- Built-in Flask development server
- SQLite database for local development
- Debug mode enabled with detailed logging

### Production Ready Features
- ProxyFix middleware for reverse proxy deployment
- Environment variable configuration
- Database connection pooling
- Secure file upload handling
- Session management

### Configuration
- Database URL configurable via environment variables
- Upload folder and size limits configurable
- Session secret key from environment
- Logging configuration for debugging

## Changelog

- July 07, 2025. Initial setup
- July 07, 2025. Added schedule import functionality (.xer, .mpp, .xml files)
- July 07, 2025. Implemented 5D scheduling analysis capabilities

## User Preferences

Preferred communication style: Simple, everyday language.