/**
 * AI Optimization JavaScript
 * Handles AI-powered scheduling features and recommendations
 */

class AIOptimizationManager {
    constructor() {
        this.recommendations = [];
        this.scenarios = [];
        this.isLoading = false;
    }

    /**
     * Initialize AI optimization features
     */
    init() {
        this.setupEventHandlers();
        this.loadAIRecommendations();
    }

    /**
     * Setup event handlers for AI features
     */
    setupEventHandlers() {
        // Auto-refresh recommendations every 5 minutes
        setInterval(() => {
            this.loadAIRecommendations();
        }, 300000);

        // Handle AI optimization buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-ai-action]')) {
                const action = e.target.getAttribute('data-ai-action');
                this.handleAIAction(action, e.target);
            }
        });
    }

    /**
     * Load AI recommendations for current project
     */
    async loadAIRecommendations(projectId = null) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            // Get project ID from URL if not provided
            if (!projectId) {
                const urlParts = window.location.pathname.split('/');
                projectId = urlParts[urlParts.indexOf('project') + 1];
            }

            const response = await fetch(`/api/project/${projectId}/ai_recommendations`);
            const data = await response.json();

            if (data.error) {
                console.error('AI recommendations error:', data.error);
                return;
            }

            this.recommendations = data;
            this.updateAIRecommendationsUI();
            
        } catch (error) {
            console.error('Error loading AI recommendations:', error);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Update UI with AI recommendations
     */
    updateAIRecommendationsUI() {
        // Update AI insights widget
        const aiWidget = document.getElementById('ai-insights-widget');
        if (aiWidget && this.recommendations) {
            this.renderAIInsightsWidget(aiWidget);
        }

        // Update project detail AI section
        const aiSection = document.getElementById('ai-recommendations-section');
        if (aiSection && this.recommendations) {
            this.renderAIRecommendationsSection(aiSection);
        }
    }

    /**
     * Render AI insights widget for dashboard
     */
    renderAIInsightsWidget(container) {
        const riskCount = this.recommendations.risk_recommendations?.length || 0;
        const resourceCount = this.recommendations.resource_recommendations?.length || 0;
        
        container.innerHTML = `
            <div class="card border-primary">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0"><i data-feather="cpu"></i> AI Insights</h6>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="h4 text-warning">${riskCount}</div>
                            <small class="text-muted">Risk Alerts</small>
                        </div>
                        <div class="col-6">
                            <div class="h4 text-success">${resourceCount}</div>
                            <small class="text-muted">Optimizations</small>
                        </div>
                    </div>
                    <div class="mt-3">
                        <button class="btn btn-sm btn-outline-primary w-100" onclick="showAIDetails()">
                            View AI Analysis
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Render AI recommendations section
     */
    renderAIRecommendationsSection(container) {
        let html = `
            <div class="card">
                <div class="card-header">
                    <h5><i data-feather="brain"></i> AI Recommendations</h5>
                </div>
                <div class="card-body">
        `;

        // Risk recommendations
        if (this.recommendations.risk_recommendations?.length > 0) {
            html += `
                <h6 class="text-warning">Risk Mitigation:</h6>
                <ul class="list-unstyled mb-3">
            `;
            this.recommendations.risk_recommendations.forEach(rec => {
                html += `<li class="mb-2"><i data-feather="alert-triangle" class="text-warning me-2"></i>${rec}</li>`;
            });
            html += `</ul>`;
        }

        // Resource recommendations
        if (this.recommendations.resource_recommendations?.length > 0) {
            html += `
                <h6 class="text-success">Resource Optimization:</h6>
                <ul class="list-unstyled mb-3">
            `;
            this.recommendations.resource_recommendations.forEach(rec => {
                if (rec) {
                    html += `<li class="mb-2"><i data-feather="users" class="text-success me-2"></i>${rec}</li>`;
                }
            });
            html += `</ul>`;
        }

        // Priority actions
        if (this.recommendations.priority_actions?.length > 0) {
            html += `
                <h6 class="text-primary">Priority Actions:</h6>
                <ul class="list-unstyled">
            `;
            this.recommendations.priority_actions.forEach(action => {
                html += `<li class="mb-2"><i data-feather="check-circle" class="text-primary me-2"></i>${action}</li>`;
            });
            html += `</ul>`;
        }

        html += `
                </div>
            </div>
        `;

        container.innerHTML = html;
        
        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Handle AI action buttons
     */
    async handleAIAction(action, button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i data-feather="loader" class="spinner"></i> Processing...';
        button.disabled = true;

        try {
            switch (action) {
                case 'generate-scenarios':
                    await this.generateOptimizationScenarios();
                    break;
                case 'analyze-completion':
                    await this.analyzeCompletionProbability();
                    break;
                case 'optimize-resources':
                    await this.optimizeResourceAllocation();
                    break;
                case 'predict-durations':
                    await this.predictActivityDurations();
                    break;
                default:
                    console.warn('Unknown AI action:', action);
            }
        } catch (error) {
            console.error('AI action error:', error);
            this.showNotification('AI analysis failed. Please try again.', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
            
            // Re-initialize feather icons
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }
    }

    /**
     * Generate optimization scenarios
     */
    async generateOptimizationScenarios() {
        const projectId = this.getCurrentProjectId();
        if (!projectId) return;

        // Redirect to AI optimization page
        window.location.href = `/project/${projectId}/ai_optimization`;
    }

    /**
     * Analyze completion probability
     */
    async analyzeCompletionProbability() {
        const projectId = this.getCurrentProjectId();
        if (!projectId) return;

        const response = await fetch(`/project/${projectId}/completion_probability`);
        const data = await response.json();

        if (data.error) {
            this.showNotification(data.error, 'error');
            return;
        }

        this.showCompletionProbabilityModal(data);
    }

    /**
     * Show completion probability modal
     */
    showCompletionProbabilityModal(data) {
        const modalHtml = `
            <div class="modal fade" id="completionProbabilityModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">AI Completion Analysis</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row text-center mb-3">
                                <div class="col-6">
                                    <div class="h3 text-primary">${data.completion_probability.toFixed(1)}%</div>
                                    <p class="text-muted">On-time Completion</p>
                                </div>
                                <div class="col-6">
                                    <div class="h6">${new Date(data.expected_completion_date).toLocaleDateString()}</div>
                                    <p class="text-muted">Expected Date</p>
                                </div>
                            </div>
                            
                            <h6>Critical Factors:</h6>
                            <ul>
                                ${data.critical_factors.map(factor => `<li>${factor}</li>`).join('')}
                            </ul>
                            
                            <h6>AI Recommendations:</h6>
                            <ul>
                                ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="aiManager.exportAnalysisReport()">
                                Export Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if present
        const existingModal = document.getElementById('completionProbabilityModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('completionProbabilityModal'));
        modal.show();
    }

    /**
     * Get current project ID from URL
     */
    getCurrentProjectId() {
        const urlParts = window.location.pathname.split('/');
        const projectIndex = urlParts.indexOf('project');
        
        if (projectIndex !== -1 && urlParts[projectIndex + 1]) {
            return urlParts[projectIndex + 1];
        }
        
        return null;
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Create toast notification
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'primary'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Show toast
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove toast element after it hides
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    /**
     * Export AI analysis report
     */
    exportAnalysisReport() {
        const projectId = this.getCurrentProjectId();
        if (!projectId) return;

        // For now, show notification that feature is coming
        this.showNotification('AI report export feature coming soon!', 'info');
    }
}

// Global AI functions for navigation menu
function showAIForAllProjects() {
    alert('Portfolio AI analysis feature coming soon!');
}

function showAIDetails() {
    const projectId = window.aiManager?.getCurrentProjectId();
    if (projectId) {
        window.location.href = `/project/${projectId}/ai_optimization`;
    } else {
        alert('Please select a project first');
    }
}

// Initialize AI manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiManager = new AIOptimizationManager();
    window.aiManager.init();
});

// Add CSS for spinner animation
const style = document.createElement('style');
style.textContent = `
    .spinner {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .ai-recommendation-item {
        border-left: 3px solid #007bff;
        padding-left: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .ai-risk-item {
        border-left: 3px solid #ffc107;
        padding-left: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .ai-success-item {
        border-left: 3px solid #28a745;
        padding-left: 1rem;
        margin-bottom: 0.5rem;
    }
`;
document.head.appendChild(style);