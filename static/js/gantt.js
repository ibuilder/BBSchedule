/**
 * Gantt Chart Implementation for Construction Project Scheduler
 * Handles interactive Gantt chart visualization with drag-and-drop functionality
 */

let ganttChart = null;
let ganttData = null;
let ganttDependencies = null;

/**
 * Initialize the Gantt chart with project data
 */
function initializeGanttChart(projectData, activities, dependencies) {
    try {
        ganttData = activities;
        ganttDependencies = dependencies;
        
        if (!ganttData || ganttData.length === 0) {
            showNoDataMessage();
            return;
        }
        
        // Sort activities by start date
        ganttData.sort((a, b) => {
            const dateA = new Date(a.start_date || projectData.start_date);
            const dateB = new Date(b.start_date || projectData.start_date);
            return dateA - dateB;
        });
        
        createGanttChart(projectData);
    } catch (error) {
        console.error('Error initializing Gantt chart:', error);
        showErrorMessage('Failed to initialize Gantt chart');
    }
}

/**
 * Show message when no data is available
 */
function showNoDataMessage() {
    const container = document.getElementById('gantt-chart-container');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i data-feather="bar-chart-2" class="feather-xl text-muted mb-3"></i>
                <h4 class="text-muted">No Activities Found</h4>
                <p class="text-muted">Add activities to your project to see the Gantt chart.</p>
            </div>
        `;
        feather.replace();
    }
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const container = document.getElementById('gantt-chart-container');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i data-feather="alert-circle" class="feather-xl text-danger mb-3"></i>
                <h4 class="text-danger">Chart Error</h4>
                <p class="text-muted">${message}</p>
            </div>
        `;
        feather.replace();
    }
}

/**
 * Create and render the Gantt chart
 */
function createGanttChart(projectData) {
    try {
        const canvas = document.getElementById('gantt-chart');
        if (!canvas) {
            console.error('Gantt chart canvas not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Prepare data for Chart.js
        const chartData = prepareGanttData(projectData);
        
        // Destroy existing chart if it exists
        if (ganttChart) {
            ganttChart.destroy();
        }
        
        ganttChart = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${projectData.name} - Gantt Chart`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return ganttData[context[0].dataIndex].name;
                        },
                        label: function(context) {
                            const activity = ganttData[context.dataIndex];
                            return [
                                `Duration: ${activity.duration} days`,
                                `Progress: ${activity.progress}%`,
                                `Type: ${activity.activity_type}`,
                                `Start: ${activity.start_date || 'TBD'}`,
                                `End: ${activity.end_date || 'TBD'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Timeline (Days)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Activities'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const elementIndex = elements[0].index;
                    const activity = ganttData[elementIndex];
                    showActivityDetails(activity);
                }
            }
        }
    });
        
    } catch (error) {
        console.error('Error creating Gantt chart:', error);
        showErrorMessage('Failed to create chart visualization');
    }
}

/**
 * Prepare data for the Gantt chart
 */
function prepareGanttData(projectData) {
    const labels = ganttData.map(activity => activity.name);
    const projectStart = new Date(projectData.start_date);
    
    // Create timeline data for horizontal bar chart
    const data = ganttData.map(activity => activity.duration);
    
    // Create datasets for Chart.js with different colors for different progress levels
    const backgroundColors = ganttData.map(activity => {
        if (activity.progress >= 100) return 'rgba(40, 167, 69, 0.8)'; // Green for completed
        if (activity.progress >= 50) return 'rgba(255, 193, 7, 0.8)'; // Yellow for in progress
        return 'rgba(108, 117, 125, 0.8)'; // Gray for not started
    });
    
    const datasets = [
        {
            label: 'Duration (days)',
            data: data,
            backgroundColor: backgroundColors,
            borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
            borderWidth: 1
        }
    ];
    
    return {
        labels: labels,
        datasets: datasets
    };
}

/**
 * Show activity details in a modal or sidebar
 */
function showActivityDetails(activity) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Activity Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <dl class="row">
                        <dt class="col-sm-4">Name:</dt>
                        <dd class="col-sm-8">${activity.name}</dd>
                        
                        <dt class="col-sm-4">Type:</dt>
                        <dd class="col-sm-8">${activity.activity_type}</dd>
                        
                        <dt class="col-sm-4">Duration:</dt>
                        <dd class="col-sm-8">${activity.duration} days</dd>
                        
                        <dt class="col-sm-4">Progress:</dt>
                        <dd class="col-sm-8">
                            <div class="progress">
                                <div class="progress-bar" style="width: ${activity.progress}%">
                                    ${activity.progress}%
                                </div>
                            </div>
                        </dd>
                        
                        <dt class="col-sm-4">Start Date:</dt>
                        <dd class="col-sm-8">${activity.start_date || 'TBD'}</dd>
                        
                        <dt class="col-sm-4">End Date:</dt>
                        <dd class="col-sm-8">${activity.end_date || 'TBD'}</dd>
                        
                        <dt class="col-sm-4">Predecessors:</dt>
                        <dd class="col-sm-8">${activity.predecessors.length > 0 ? activity.predecessors.join(', ') : 'None'}</dd>
                    </dl>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <a href="/activity/${activity.id}/edit" class="btn btn-primary">Edit Activity</a>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', function () {
        document.body.removeChild(modal);
    });
}

/**
 * Calculate critical path for the project
 */
function calculateCriticalPath() {
    if (!ganttData || !ganttDependencies) return [];
    
    // Simple critical path calculation
    // In a production system, this would be more sophisticated
    const activities = [...ganttData];
    const dependencies = [...ganttDependencies];
    
    // Find activities with no predecessors (start activities)
    const startActivities = activities.filter(activity => 
        !dependencies.some(dep => dep.successor_id === activity.id)
    );
    
    // Find the longest path from start to end
    let criticalPath = [];
    let maxDuration = 0;
    
    function findPath(activityId, currentPath, totalDuration) {
        const activity = activities.find(a => a.id === activityId);
        if (!activity) return;
        
        const newPath = [...currentPath, activityId];
        const newDuration = totalDuration + activity.duration;
        
        // Find successors
        const successors = dependencies
            .filter(dep => dep.predecessor_id === activityId)
            .map(dep => dep.successor_id);
        
        if (successors.length === 0) {
            // End activity found
            if (newDuration > maxDuration) {
                maxDuration = newDuration;
                criticalPath = newPath;
            }
        } else {
            // Continue with successors
            successors.forEach(successorId => {
                findPath(successorId, newPath, newDuration);
            });
        }
    }
    
    // Start from each start activity
    startActivities.forEach(startActivity => {
        findPath(startActivity.id, [], 0);
    });
    
    return criticalPath;
}

/**
 * Highlight critical path on the chart
 */
function highlightCriticalPath() {
    const criticalPath = calculateCriticalPath();
    
    if (criticalPath.length === 0) {
        alert('No critical path found. Please ensure activities have proper dependencies.');
        return;
    }
    
    // Update chart to highlight critical path activities
    const criticalActivities = ganttData.filter(activity => 
        criticalPath.includes(activity.id)
    );
    
    // Add critical path dataset
    const criticalData = criticalActivities.map(activity => {
        if (!activity.start_date) return null;
        
        const startDate = new Date(activity.start_date);
        const endDate = new Date(activity.end_date || startDate.getTime() + activity.duration * 24 * 60 * 60 * 1000);
        
        return {
            x: [startDate, endDate],
            y: ganttData.indexOf(activity)
        };
    });
    
    ganttChart.data.datasets.push({
        label: 'Critical Path',
        data: criticalData,
        backgroundColor: 'rgba(220, 53, 69, 0.8)',
        borderColor: 'rgba(220, 53, 69, 1)',
        borderWidth: 2
    });
    
    ganttChart.update();
}

/**
 * Export Gantt chart as image
 */
function exportGanttChart() {
    const canvas = document.getElementById('gantt-chart');
    const link = document.createElement('a');
    link.download = 'gantt-chart.png';
    link.href = canvas.toDataURL();
    link.click();
}

/**
 * Update activity progress
 */
function updateActivityProgress(activityId, newProgress) {
    const activity = ganttData.find(a => a.id === activityId);
    if (activity) {
        activity.progress = newProgress;
        // Re-render chart with updated data
        createGanttChart({
            name: ganttChart.options.plugins.title.text.replace(' - Gantt Chart', ''),
            start_date: ganttData[0].start_date
        });
    }
}

/**
 * Filter activities by type
 */
function filterActivitiesByType(activityType) {
    const filteredData = activityType === 'all' ? 
        ganttData : 
        ganttData.filter(activity => activity.activity_type === activityType);
    
    // Update chart with filtered data
    const originalData = ganttData;
    ganttData = filteredData;
    
    createGanttChart({
        name: ganttChart.options.plugins.title.text.replace(' - Gantt Chart', ''),
        start_date: filteredData[0]?.start_date || originalData[0]?.start_date
    });
}

/**
 * Initialize event listeners for Gantt chart controls
 */
function initializeGanttControls() {
    // Add control buttons if they exist
    const criticalPathBtn = document.getElementById('show-critical-path');
    if (criticalPathBtn) {
        criticalPathBtn.addEventListener('click', highlightCriticalPath);
    }
    
    const exportBtn = document.getElementById('export-gantt');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportGanttChart);
    }
    
    const filterSelect = document.getElementById('activity-type-filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            filterActivitiesByType(this.value);
        });
    }
}

// Initialize controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeGanttControls();
});
