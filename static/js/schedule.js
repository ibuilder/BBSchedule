/**
 * General Schedule Utility Functions
 * Common functionality shared between Gantt and Linear scheduling
 */

/**
 * Date utility functions
 */
const DateUtils = {
    /**
     * Add business days to a date
     */
    addBusinessDays: function(date, days) {
        const result = new Date(date);
        let addedDays = 0;
        
        while (addedDays < days) {
            result.setDate(result.getDate() + 1);
            // Skip weekends (Saturday = 6, Sunday = 0)
            if (result.getDay() !== 0 && result.getDay() !== 6) {
                addedDays++;
            }
        }
        
        return result;
    },
    
    /**
     * Calculate business days between two dates
     */
    businessDaysBetween: function(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        let days = 0;
        const current = new Date(start);
        
        while (current <= end) {
            if (current.getDay() !== 0 && current.getDay() !== 6) {
                days++;
            }
            current.setDate(current.getDate() + 1);
        }
        
        return days;
    },
    
    /**
     * Format date for display
     */
    formatDate: function(date, format = 'short') {
        const d = new Date(date);
        const options = format === 'long' ? 
            { year: 'numeric', month: 'long', day: 'numeric' } :
            { year: 'numeric', month: 'short', day: 'numeric' };
        
        return d.toLocaleDateString('en-US', options);
    },
    
    /**
     * Check if date is weekend
     */
    isWeekend: function(date) {
        const day = new Date(date).getDay();
        return day === 0 || day === 6;
    }
};

/**
 * Schedule calculation utilities
 */
const ScheduleUtils = {
    /**
     * Calculate early start and finish dates
     */
    calculateEarlyDates: function(activities, dependencies) {
        const activityMap = new Map();
        activities.forEach(activity => {
            activityMap.set(activity.id, {
                ...activity,
                early_start: null,
                early_finish: null,
                late_start: null,
                late_finish: null,
                float: 0
            });
        });
        
        // Forward pass - calculate early dates
        const startActivities = activities.filter(activity => 
            !dependencies.some(dep => dep.successor_id === activity.id)
        );
        
        startActivities.forEach(activity => {
            const act = activityMap.get(activity.id);
            act.early_start = new Date(activity.start_date || new Date());
            act.early_finish = DateUtils.addBusinessDays(act.early_start, act.duration);
        });
        
        // Process remaining activities
        let processed = new Set(startActivities.map(a => a.id));
        let queue = [...startActivities];
        
        while (queue.length > 0) {
            const current = queue.shift();
            const successors = dependencies
                .filter(dep => dep.predecessor_id === current.id)
                .map(dep => activityMap.get(dep.successor_id));
            
            successors.forEach(successor => {
                if (!processed.has(successor.id)) {
                    const predecessors = dependencies
                        .filter(dep => dep.successor_id === successor.id)
                        .map(dep => activityMap.get(dep.predecessor_id));
                    
                    if (predecessors.every(pred => processed.has(pred.id))) {
                        // All predecessors processed, calculate early dates
                        const latestFinish = Math.max(...predecessors.map(pred => 
                            pred.early_finish.getTime()
                        ));
                        
                        successor.early_start = new Date(latestFinish);
                        successor.early_finish = DateUtils.addBusinessDays(
                            successor.early_start, 
                            successor.duration
                        );
                        
                        processed.add(successor.id);
                        queue.push(successor);
                    }
                }
            });
        }
        
        return Array.from(activityMap.values());
    },
    
    /**
     * Calculate late start and finish dates
     */
    calculateLateDates: function(activities, dependencies) {
        const activityMap = new Map();
        activities.forEach(activity => {
            activityMap.set(activity.id, { ...activity });
        });
        
        // Backward pass - calculate late dates
        const endActivities = activities.filter(activity => 
            !dependencies.some(dep => dep.predecessor_id === activity.id)
        );
        
        // Find project end date
        const projectEnd = Math.max(...activities.map(a => 
            a.early_finish ? a.early_finish.getTime() : 0
        ));
        
        endActivities.forEach(activity => {
            const act = activityMap.get(activity.id);
            act.late_finish = new Date(projectEnd);
            act.late_start = new Date(act.late_finish.getTime() - act.duration * 24 * 60 * 60 * 1000);
        });
        
        // Process remaining activities in reverse order
        let processed = new Set(endActivities.map(a => a.id));
        let queue = [...endActivities];
        
        while (queue.length > 0) {
            const current = queue.shift();
            const predecessors = dependencies
                .filter(dep => dep.successor_id === current.id)
                .map(dep => activityMap.get(dep.predecessor_id));
            
            predecessors.forEach(predecessor => {
                if (!processed.has(predecessor.id)) {
                    const successors = dependencies
                        .filter(dep => dep.predecessor_id === predecessor.id)
                        .map(dep => activityMap.get(dep.successor_id));
                    
                    if (successors.every(succ => processed.has(succ.id))) {
                        // All successors processed, calculate late dates
                        const earliestStart = Math.min(...successors.map(succ => 
                            succ.late_start.getTime()
                        ));
                        
                        predecessor.late_finish = new Date(earliestStart);
                        predecessor.late_start = new Date(
                            predecessor.late_finish.getTime() - 
                            predecessor.duration * 24 * 60 * 60 * 1000
                        );
                        
                        processed.add(predecessor.id);
                        queue.push(predecessor);
                    }
                }
            });
        }
        
        return Array.from(activityMap.values());
    },
    
    /**
     * Calculate total float for activities
     */
    calculateFloat: function(activities) {
        return activities.map(activity => ({
            ...activity,
            float: activity.late_start && activity.early_start ? 
                (activity.late_start.getTime() - activity.early_start.getTime()) / (24 * 60 * 60 * 1000) : 0
        }));
    },
    
    /**
     * Find critical path activities
     */
    findCriticalPath: function(activities) {
        return activities.filter(activity => 
            Math.abs(activity.float) < 0.5 // Activities with zero or near-zero float
        );
    }
};

/**
 * Validation utilities
 */
const ValidationUtils = {
    /**
     * Validate schedule logic
     */
    validateSchedule: function(activities, dependencies) {
        const errors = [];
        
        // Check for circular dependencies
        const visited = new Set();
        const recursionStack = new Set();
        
        function hasCycle(activityId) {
            if (recursionStack.has(activityId)) {
                return true;
            }
            if (visited.has(activityId)) {
                return false;
            }
            
            visited.add(activityId);
            recursionStack.add(activityId);
            
            const successors = dependencies
                .filter(dep => dep.predecessor_id === activityId)
                .map(dep => dep.successor_id);
            
            for (const successor of successors) {
                if (hasCycle(successor)) {
                    return true;
                }
            }
            
            recursionStack.delete(activityId);
            return false;
        }
        
        activities.forEach(activity => {
            if (hasCycle(activity.id)) {
                errors.push(`Circular dependency detected involving activity ${activity.id}`);
            }
        });
        
        // Check for missing dates
        activities.forEach(activity => {
            if (!activity.start_date) {
                errors.push(`Activity "${activity.name}" is missing start date`);
            }
            if (activity.duration <= 0) {
                errors.push(`Activity "${activity.name}" has invalid duration`);
            }
        });
        
        // Check for invalid dependencies
        dependencies.forEach(dep => {
            const predecessor = activities.find(a => a.id === dep.predecessor_id);
            const successor = activities.find(a => a.id === dep.successor_id);
            
            if (!predecessor) {
                errors.push(`Dependency references non-existent predecessor ${dep.predecessor_id}`);
            }
            if (!successor) {
                errors.push(`Dependency references non-existent successor ${dep.successor_id}`);
            }
            
            if (predecessor && successor && predecessor.id === successor.id) {
                errors.push(`Activity "${predecessor.name}" cannot depend on itself`);
            }
        });
        
        return errors;
    },
    
    /**
     * Validate activity data
     */
    validateActivity: function(activity) {
        const errors = [];
        
        if (!activity.name || activity.name.trim() === '') {
            errors.push('Activity name is required');
        }
        
        if (!activity.duration || activity.duration <= 0) {
            errors.push('Activity duration must be greater than 0');
        }
        
        if (activity.progress < 0 || activity.progress > 100) {
            errors.push('Activity progress must be between 0 and 100');
        }
        
        if (activity.start_date && activity.end_date) {
            const start = new Date(activity.start_date);
            const end = new Date(activity.end_date);
            
            if (start >= end) {
                errors.push('Start date must be before end date');
            }
        }
        
        return errors;
    }
};

/**
 * Export utilities
 */
const ExportUtils = {
    /**
     * Export schedule data to CSV
     */
    exportToCSV: function(activities, filename = 'schedule.csv') {
        const headers = [
            'ID', 'Name', 'Type', 'Duration', 'Start Date', 'End Date', 
            'Progress', 'Quantity', 'Unit', 'Production Rate', 'Crew Size', 
            'Cost Estimate', 'Actual Cost', 'Location Start', 'Location End', 'Notes'
        ];
        
        const rows = activities.map(activity => [
            activity.id,
            activity.name,
            activity.activity_type,
            activity.duration,
            activity.start_date || '',
            activity.end_date || '',
            activity.progress,
            activity.quantity || '',
            activity.unit || '',
            activity.production_rate || '',
            activity.resource_crew_size || '',
            activity.cost_estimate || '',
            activity.actual_cost || '',
            activity.location_start || '',
            activity.location_end || '',
            activity.notes || ''
        ]);
        
        const csvContent = [headers, ...rows]
            .map(row => row.map(field => `"${field}"`).join(','))
            .join('\n');
        
        this.downloadFile(csvContent, filename, 'text/csv');
    },
    
    /**
     * Export schedule data to JSON
     */
    exportToJSON: function(data, filename = 'schedule.json') {
        const jsonContent = JSON.stringify(data, null, 2);
        this.downloadFile(jsonContent, filename, 'application/json');
    },
    
    /**
     * Download file helper
     */
    downloadFile: function(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
};

/**
 * UI utilities
 */
const UIUtils = {
    /**
     * Show loading indicator
     */
    showLoading: function(element) {
        element.classList.add('loading');
        element.style.pointerEvents = 'none';
    },
    
    /**
     * Hide loading indicator
     */
    hideLoading: function(element) {
        element.classList.remove('loading');
        element.style.pointerEvents = '';
    },
    
    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to toast container or create one
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toastContainer.removeChild(toast);
        });
    },
    
    /**
     * Confirm dialog
     */
    confirm: function(message, callback) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Action</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirm-btn">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        
        modal.querySelector('#confirm-btn').addEventListener('click', function() {
            callback();
            bootstrapModal.hide();
        });
        
        bootstrapModal.show();
        
        // Clean up modal when hidden
        modal.addEventListener('hidden.bs.modal', function () {
            document.body.removeChild(modal);
        });
    }
};

/**
 * Performance monitoring
 */
const PerformanceUtils = {
    /**
     * Measure function execution time
     */
    measure: function(name, func) {
        const start = performance.now();
        const result = func();
        const end = performance.now();
        console.log(`${name} took ${end - start} milliseconds`);
        return result;
    },
    
    /**
     * Throttle function execution
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * Debounce function execution
     */
    debounce: function(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            const later = function() {
                timeout = null;
                func.apply(context, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Global initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        UIUtils.showToast('An error occurred. Please try again.', 'danger');
    });
    
    // Add global unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        UIUtils.showToast('An error occurred. Please try again.', 'danger');
    });
});

// Export utilities for use in other modules
window.ScheduleUtils = ScheduleUtils;
window.DateUtils = DateUtils;
window.ValidationUtils = ValidationUtils;
window.ExportUtils = ExportUtils;
window.UIUtils = UIUtils;
window.PerformanceUtils = PerformanceUtils;
