// Main JavaScript for AI Career Recommendation System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize animated elements
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    if (animatedElements.length > 0) {
        // Check if element is in viewport
        function isInViewport(element) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.bottom >= 0
            );
        }
        
        // Add visible class to elements in viewport
        function handleScroll() {
            animatedElements.forEach(element => {
                if (isInViewport(element)) {
                    element.classList.add('visible');
                }
            });
        }
        
        // Initial check
        handleScroll();
        
        // Listen for scroll events
        window.addEventListener('scroll', handleScroll);
    }
    
    // Form validation for assessment
    const assessmentForm = document.getElementById('assessment-form');
    if (assessmentForm) {
        assessmentForm.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Get all required text areas
            const requiredTextareas = assessmentForm.querySelectorAll('textarea[required]');
            requiredTextareas.forEach(textarea => {
                if (!textarea.value.trim()) {
                    isValid = false;
                    textarea.classList.add('is-invalid');
                } else {
                    textarea.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                // Show alert
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger alert-dismissible fade show';
                alertDiv.role = 'alert';
                alertDiv.innerHTML = `
                    Please fill out all required fields.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Get the form heading
                const formHeading = assessmentForm.querySelector('.card-header');
                formHeading.after(alertDiv);
                
                // Scroll to top of form
                window.scrollTo({
                    top: assessmentForm.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    }
    
    // Star rating system
    const ratingInputs = document.querySelectorAll('.rating-container input');
    if (ratingInputs.length > 0) {
        ratingInputs.forEach(input => {
            input.addEventListener('change', function() {
                // Update hidden input with the selected value
                const ratingValue = document.getElementById('rating-value');
                if (ratingValue) {
                    ratingValue.value = this.value;
                }
            });
        });
    }
    
    // Skills multi-select enhancement
    const skillsSelect = document.getElementById('skills');
    if (skillsSelect) {
        // If the browser supports the 'multiple' attribute, add it
        skillsSelect.setAttribute('multiple', 'multiple');
        
        // Create a helper text
        const helperText = document.createElement('div');
        helperText.className = 'form-text';
        helperText.textContent = 'Hold Ctrl (or Cmd on Mac) to select multiple skills';
        skillsSelect.after(helperText);
    }
    
    // Match indicators
    const matchIndicators = document.querySelectorAll('.match-indicator');
    if (matchIndicators.length > 0) {
        matchIndicators.forEach(indicator => {
            const score = parseFloat(indicator.dataset.score);
            const fill = indicator.querySelector('.match-fill');
            if (fill) {
                fill.style.width = `${score * 100}%`;
                
                // Change color based on score
                if (score >= 0.8) {
                    fill.style.backgroundColor = 'var(--bs-success)';
                } else if (score >= 0.6) {
                    fill.style.backgroundColor = 'var(--bs-primary)';
                } else if (score >= 0.4) {
                    fill.style.backgroundColor = 'var(--bs-warning)';
                } else {
                    fill.style.backgroundColor = 'var(--bs-danger)';
                }
            }
        });
    }
    
    // Market trend chart configuration
    const trendCharts = document.querySelectorAll('.trend-chart canvas');
    if (trendCharts.length > 0) {
        // Set global chart options
        Chart.defaults.color = '#adb5bd';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        
        // Initialize each chart with its specific data (data should be populated by server-side)
        // This is just a placeholder in case we need to add custom configuration
    }
});