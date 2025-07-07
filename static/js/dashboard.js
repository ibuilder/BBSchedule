// Dashboard functionality and real-time updates
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Chart.js if on dashboard
    if (document.getElementById('activityStatusChart')) {
        initializeActivityStatusChart();
    }
    
    // Set up real-time updates
    setInterval(updateDashboardMetrics, 30000); // Update every 30 seconds
});

function initializeActivityStatusChart() {
    const ctx = document.getElementById('activityStatusChart').getContext('2d');
    
    // Get data from the template or fetch via API
    const completedActivities = parseInt(document.querySelector('[data-completed-activities]')?.dataset.completedActivities || '0');
    const inProgressActivities = parseInt(document.querySelector('[data-inprogress-activities]')?.dataset.inprogressActivities || '0');
    const notStartedActivities = parseInt(document.querySelector('[data-notstarted-activities]')?.dataset.notstartedActivities || '0');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Progress', 'Not Started'],
            datasets: [{
                data: [completedActivities, inProgressActivities, notStartedActivities],
                backgroundColor: [
                    '#28a745',  // Green for completed
                    '#ffc107',  // Yellow for in progress  
                    '#6c757d'   // Gray for not started
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function updateDashboardMetrics() {
    fetch('/api/dashboard/metrics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateMetricCards(data.metrics);
            }
        })
        .catch(error => {
            console.log('Dashboard update failed:', error);
        });
}

function updateMetricCards(metrics) {
    // Update project counts
    const projectCards = document.querySelectorAll('[data-metric]');
    projectCards.forEach(card => {
        const metricType = card.dataset.metric;
        const valueElement = card.querySelector('.metric-value');
        
        if (valueElement && metrics.projects[metricType] !== undefined) {
            valueElement.textContent = metrics.projects[metricType];
        }
    });
    
    // Update activity counts
    const activityElements = document.querySelectorAll('[data-activity-metric]');
    activityElements.forEach(element => {
        const metricType = element.dataset.activityMetric;
        if (metrics.activities[metricType] !== undefined) {
            element.textContent = metrics.activities[metricType];
        }
    });
}

// Mobile responsiveness helpers
function adjustDashboardForMobile() {
    if (window.innerWidth < 768) {
        // Stack metric cards on mobile
        document.querySelectorAll('.dashboard-card').forEach(card => {
            card.classList.add('mb-3');
        });
    }
}

window.addEventListener('resize', adjustDashboardForMobile);
adjustDashboardForMobile(); // Run on load