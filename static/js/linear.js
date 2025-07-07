/**
 * Linear Schedule Implementation for Construction Project Scheduler
 * Handles linear scheduling visualization showing time vs location
 */

let linearChart = null;
let resourceChart = null;
let linearData = null;

/**
 * Initialize the linear schedule with project data
 */
function initializeLinearSchedule(projectData, activities) {
    try {
        linearData = activities.filter(activity => 
            activity.location_start !== null && 
            activity.location_end !== null
        );
        
        if (linearData.length === 0) {
            showNoLocationDataMessage();
            return;
        }
        
        createLinearChart(projectData);
    } catch (error) {
        console.error('Error initializing linear schedule:', error);
        showLinearErrorMessage('Failed to initialize linear schedule');
    }
}

/**
 * Create and render the linear schedule chart
 */
function createLinearChart(projectData) {
    try {
        const canvas = document.getElementById('linear-chart');
        if (!canvas) {
            console.error('Linear chart canvas not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Prepare data for Chart.js
        const chartData = prepareLinearData(projectData);
        
        // Destroy existing chart if it exists
        if (linearChart) {
            linearChart.destroy();
        }
        
        linearChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${projectData.name} - Linear Schedule`,
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
                            return context[0].dataset.label;
                        },
                        label: function(context) {
                            const activity = linearData.find(a => a.name === context.dataset.label);
                            return [
                                `Location: ${context.parsed.y}`,
                                `Date: ${new Date(context.parsed.x).toLocaleDateString()}`,
                                `Duration: ${activity?.duration || 'N/A'} days`,
                                `Progress: ${activity?.progress || 0}%`,
                                `Production Rate: ${activity?.production_rate || 'N/A'} units/day`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM dd'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Location/Station'
                    },
                    beginAtZero: true
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            elements: {
                line: {
                    tension: 0.1
                },
                point: {
                    radius: 4,
                    hoverRadius: 6
                }
            }
        }
    });
    
    } catch (error) {
        console.error('Error creating linear chart:', error);
        showLinearErrorMessage('Failed to create chart visualization');
    }
}

/**
 * Prepare data for the linear schedule chart
 */
function prepareLinearData(projectData) {
    const datasets = [];
    const colors = [
        '#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d',
        '#17a2b8', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c'
    ];
    
    linearData.forEach((activity, index) => {
        const startDate = new Date(activity.start_date || projectData.start_date);
        const endDate = activity.end_date ? 
            new Date(activity.end_date) : 
            new Date(startDate.getTime() + activity.duration * 24 * 60 * 60 * 1000);
        
        // Create data points for the activity line
        const dataPoints = [
            {
                x: startDate,
                y: activity.location_start
            },
            {
                x: endDate,
                y: activity.location_end
            }
        ];
        
        // Add progress indicator if activity is in progress
        if (activity.progress > 0 && activity.progress < 100) {
            const progressDate = new Date(startDate.getTime() + 
                (endDate.getTime() - startDate.getTime()) * (activity.progress / 100));
            const progressLocation = activity.location_start + 
                (activity.location_end - activity.location_start) * (activity.progress / 100);
            
            dataPoints.splice(1, 0, {
                x: progressDate,
                y: progressLocation
            });
        }
        
        datasets.push({
            label: activity.name,
            data: dataPoints,
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length] + '20',
            fill: false,
            tension: 0.1,
            pointBackgroundColor: colors[index % colors.length],
            pointBorderColor: colors[index % colors.length],
            pointRadius: 5,
            pointHoverRadius: 7
        });
    });
    
    return { datasets: datasets };
}

/**
 * Initialize resource utilization chart
 */
function initializeResourceChart(projectData, activities) {
    const ctx = document.getElementById('resource-chart').getContext('2d');
    
    // Prepare resource data over time
    const resourceData = prepareResourceData(projectData, activities);
    
    // Destroy existing chart if it exists
    if (resourceChart) {
        resourceChart.destroy();
    }
    
    resourceChart = new Chart(ctx, {
        type: 'line',
        data: resourceData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Resource Utilization Over Time',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM dd'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of Resources'
                    },
                    beginAtZero: true
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

/**
 * Prepare resource utilization data
 */
function prepareResourceData(projectData, activities) {
    const startDate = new Date(projectData.start_date);
    const endDate = projectData.end_date ? 
        new Date(projectData.end_date) : 
        new Date(startDate.getTime() + 365 * 24 * 60 * 60 * 1000); // Default to 1 year
    
    // Generate daily resource counts
    const dailyData = [];
    const currentDate = new Date(startDate);
    
    while (currentDate <= endDate) {
        let totalResources = 0;
        
        activities.forEach(activity => {
            const activityStart = new Date(activity.start_date || projectData.start_date);
            const activityEnd = activity.end_date ? 
                new Date(activity.end_date) : 
                new Date(activityStart.getTime() + activity.duration * 24 * 60 * 60 * 1000);
            
            if (currentDate >= activityStart && currentDate <= activityEnd) {
                totalResources += activity.resource_crew_size || 0;
            }
        });
        
        dailyData.push({
            x: new Date(currentDate),
            y: totalResources
        });
        
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return {
        datasets: [{
            label: 'Total Resources',
            data: dailyData,
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            fill: true,
            tension: 0.1
        }]
    };
}

/**
 * Calculate production rates and efficiency
 */
function calculateProductionMetrics() {
    const metrics = {
        averageProductionRate: 0,
        totalQuantity: 0,
        estimatedDuration: 0,
        efficiency: 0
    };
    
    if (linearData.length === 0) return metrics;
    
    let totalRate = 0;
    let rateCount = 0;
    
    linearData.forEach(activity => {
        if (activity.production_rate) {
            totalRate += activity.production_rate;
            rateCount++;
        }
        
        if (activity.quantity) {
            metrics.totalQuantity += activity.quantity;
        }
        
        metrics.estimatedDuration += activity.duration;
    });
    
    metrics.averageProductionRate = rateCount > 0 ? totalRate / rateCount : 0;
    metrics.efficiency = metrics.totalQuantity > 0 ? 
        (metrics.averageProductionRate * metrics.estimatedDuration) / metrics.totalQuantity : 0;
    
    return metrics;
}

/**
 * Show location conflicts and overlaps
 */
function analyzeLocationConflicts() {
    const conflicts = [];
    
    for (let i = 0; i < linearData.length; i++) {
        for (let j = i + 1; j < linearData.length; j++) {
            const activity1 = linearData[i];
            const activity2 = linearData[j];
            
            // Check for location overlap
            const loc1Start = Math.min(activity1.location_start, activity1.location_end);
            const loc1End = Math.max(activity1.location_start, activity1.location_end);
            const loc2Start = Math.min(activity2.location_start, activity2.location_end);
            const loc2End = Math.max(activity2.location_start, activity2.location_end);
            
            if (loc1Start < loc2End && loc2Start < loc1End) {
                // Check for time overlap
                const date1Start = new Date(activity1.start_date);
                const date1End = new Date(activity1.end_date || 
                    date1Start.getTime() + activity1.duration * 24 * 60 * 60 * 1000);
                const date2Start = new Date(activity2.start_date);
                const date2End = new Date(activity2.end_date || 
                    date2Start.getTime() + activity2.duration * 24 * 60 * 60 * 1000);
                
                if (date1Start < date2End && date2Start < date1End) {
                    conflicts.push({
                        activity1: activity1.name,
                        activity2: activity2.name,
                        type: 'location_time_overlap'
                    });
                }
            }
        }
    }
    
    return conflicts;
}

/**
 * Show error message for linear chart
 */
function showLinearErrorMessage(message) {
    const container = document.getElementById('linear-chart-container');
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
 * Show message when no location data is available
 */
function showNoLocationDataMessage() {
    const container = document.getElementById('linear-chart-container');
    container.innerHTML = `
        <div class="text-center py-5">
            <i data-feather="map-pin" class="feather-xl text-muted mb-3"></i>
            <h4 class="text-muted">No Location Data Available</h4>
            <p class="text-muted">
                Linear scheduling requires activities to have location/station data.<br>
                Please add location start and end points to your activities.
            </p>
            <a href="#" class="btn btn-primary" onclick="showLocationHelp()">
                <i data-feather="help-circle"></i>
                Learn About Linear Scheduling
            </a>
        </div>
    `;
    
    // Re-initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Show help information about linear scheduling
 */
function showLocationHelp() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Linear Scheduling Guide</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <h6>What is Linear Scheduling?</h6>
                    <p>Linear scheduling is a method used in construction projects where work progresses linearly through space over time. It's particularly useful for:</p>
                    <ul>
                        <li>Highway construction</li>
                        <li>Pipeline installation</li>
                        <li>High-rise building construction (floor by floor)</li>
                        <li>Repetitive construction activities</li>
                    </ul>
                    
                    <h6>Setting Up Location Data</h6>
                    <p>To use linear scheduling, each activity needs:</p>
                    <ul>
                        <li><strong>Start Location:</strong> Where the activity begins (e.g., Station 0+00, Floor 1)</li>
                        <li><strong>End Location:</strong> Where the activity ends (e.g., Station 5+00, Floor 10)</li>
                        <li><strong>Production Rate:</strong> How much work is completed per day</li>
                    </ul>
                    
                    <h6>Benefits</h6>
                    <ul>
                        <li>Visualize work progression through space and time</li>
                        <li>Identify resource conflicts and bottlenecks</li>
                        <li>Optimize crew utilization</li>
                        <li>Maintain continuous workflow</li>
                    </ul>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
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
 * Export linear schedule as image
 */
function exportLinearChart() {
    const canvas = document.getElementById('linear-chart');
    const link = document.createElement('a');
    link.download = 'linear-schedule.png';
    link.href = canvas.toDataURL();
    link.click();
}

/**
 * Toggle between different linear schedule views
 */
function toggleLinearView(viewType) {
    switch (viewType) {
        case 'location':
            // Standard location vs time view
            createLinearChart({
                name: linearChart.options.plugins.title.text.replace(' - Linear Schedule', ''),
                start_date: linearData[0]?.start_date
            });
            break;
            
        case 'production':
            // Production rate view
            createProductionRateChart();
            break;
            
        case 'resources':
            // Resource utilization view
            initializeResourceChart({
                name: linearChart.options.plugins.title.text.replace(' - Linear Schedule', ''),
                start_date: linearData[0]?.start_date
            }, linearData);
            break;
    }
}

/**
 * Create production rate visualization
 */
function createProductionRateChart() {
    const ctx = document.getElementById('linear-chart').getContext('2d');
    
    const productionData = linearData.map(activity => ({
        x: activity.production_rate || 0,
        y: activity.location_end - activity.location_start,
        label: activity.name
    }));
    
    if (linearChart) {
        linearChart.destroy();
    }
    
    linearChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Production Rate vs Distance',
                data: productionData,
                backgroundColor: 'rgba(0, 123, 255, 0.6)',
                borderColor: 'rgba(0, 123, 255, 1)',
                pointRadius: 8,
                pointHoverRadius: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Production Rate Analysis',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.label}: ${context.parsed.x} units/day, ${context.parsed.y} units distance`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Production Rate (units/day)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Distance (units)'
                    }
                }
            }
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for linear schedule controls
    const exportBtn = document.getElementById('export-linear');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportLinearChart);
    }
    
    const viewToggle = document.getElementById('linear-view-toggle');
    if (viewToggle) {
        viewToggle.addEventListener('change', function() {
            toggleLinearView(this.value);
        });
    }
});
