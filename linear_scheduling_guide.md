# Linear Scheduling Guide

## Overview
Linear scheduling is now fully integrated into your construction project scheduler. This method is perfect for projects that progress along a linear path, such as highways, pipelines, railways, or multi-story buildings.

## Setting Up Linear Scheduling

### 1. Enable Linear Scheduling for a Project
When creating or editing a project:

1. **Enable Linear Scheduling**: Set to "Yes"
2. **Station Units**: Choose from Meters, Feet, Kilometers, or Miles
3. **Project Start Station**: Enter the starting chainage/station (e.g., 0)
4. **Project End Station**: Enter the ending chainage/station (e.g., 1000)

### 2. Adding Location Data to Activities
For each activity, specify:

- **Start Location/Station**: Where the activity begins along the project alignment
- **End Location/Station**: Where the activity ends along the project alignment

## Example Linear Projects

### Highway Construction
- **Project Length**: 0 to 5000 meters
- **Activities**:
  - Earthwork: Station 0-1000m
  - Base Course: Station 100-1100m (starts after earthwork completion)
  - Asphalt Paving: Station 200-1200m (follows base course)

### High-Rise Building
- **Project Height**: Floor 1 to Floor 30
- **Activities**:
  - Concrete Pour: Floor 1-5
  - Steel Erection: Floor 2-6 (one floor behind concrete)
  - MEP Installation: Floor 3-7 (follows structure)

### Pipeline Installation
- **Project Length**: 0 to 10,000 feet
- **Activities**:
  - Trenching: Station 0-500ft
  - Pipe Laying: Station 100-600ft
  - Backfilling: Station 200-700ft

## Key Features

### Location-Based Filtering
- View activities within specific station ranges
- Filter by location to focus on specific project sections
- Identify spatial conflicts between activities

### Linear Schedule Visualization
- Time-Location diagrams showing activity progress along the project
- Visual representation of crew movement and productivity
- Identification of production rate consistency

### Spatial Conflict Detection
- Automatic detection of activities overlapping in time and location
- Warnings for crews working too close together
- Resource coordination recommendations

## Database Fields Added

### Project Table
- `linear_scheduling_enabled`: Boolean flag
- `project_start_station`: Starting location (Float)
- `project_end_station`: Ending location (Float)
- `station_units`: Units of measurement (String)

### Activity Table (Already Available)
- `location_start`: Activity start location (Float)
- `location_end`: Activity end location (Float)

## API Integration

### New Methods Available
```python
# Get project length
project.get_project_length()

# Get activities in location range
project.get_activities_by_location(start_station=100, end_station=500)

# Check if project uses linear scheduling
if project.linear_scheduling_enabled:
    # Handle linear scheduling logic
```

## Benefits of Linear Scheduling

1. **Better Resource Management**: Track crew movement and avoid conflicts
2. **Improved Productivity**: Identify optimal production rates and maintain rhythm
3. **Enhanced Coordination**: Visualize how activities flow along the project
4. **Risk Reduction**: Early detection of spatial and temporal conflicts
5. **Progress Monitoring**: Clear visualization of completion along the alignment

## Next Steps

1. Create a new project with linear scheduling enabled
2. Add activities with specific location ranges
3. View the linear schedule visualization
4. Use the 5D analysis to detect conflicts and optimize resources

The system now fully supports both traditional Gantt charts and linear scheduling methods, giving you flexibility to choose the best approach for each project type.