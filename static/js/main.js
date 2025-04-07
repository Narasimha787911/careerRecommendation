// Main JavaScript functionality for the AI Career Recommendation System

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

    // Dynamic skill input in profile form
    const skillInput = document.getElementById('skill-input');
    const addSkillBtn = document.getElementById('add-skill-btn');
    const skillsList = document.getElementById('skills-list');
    const skillsInput = document.getElementById('skills-input');

    if (addSkillBtn && skillInput && skillsList) {
        addSkillBtn.addEventListener('click', function() {
            const skill = skillInput.value.trim();
            if (skill) {
                addSkill(skill);
                skillInput.value = '';
                skillInput.focus();
            }
        });

        skillInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSkillBtn.click();
            }
        });
    }

    function addSkill(skill) {
        // Create skill item
        const skillItem = document.createElement('div');
        skillItem.className = 'skill-tag d-inline-flex align-items-center me-2 mb-2';
        
        // Create skill text
        const skillText = document.createElement('span');
        skillText.textContent = skill;
        
        // Create remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn-close btn-close-white ms-2';
        removeBtn.setAttribute('aria-label', 'Remove');
        removeBtn.style.fontSize = '0.6rem';
        
        // Add event listener to remove button
        removeBtn.addEventListener('click', function() {
            skillItem.remove();
            updateSkillsInput();
        });
        
        // Append elements
        skillItem.appendChild(skillText);
        skillItem.appendChild(removeBtn);
        skillsList.appendChild(skillItem);
        
        // Update hidden input with all skills
        updateSkillsInput();
    }

    function updateSkillsInput() {
        const skills = [];
        const skillTags = skillsList.querySelectorAll('.skill-tag');
        
        skillTags.forEach(function(tag) {
            skills.push(tag.querySelector('span').textContent);
        });
        
        // Create hidden inputs for each skill
        skillsList.querySelectorAll('input[name="skills"]').forEach(input => input.remove());
        
        skills.forEach(skill => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'skills';
            input.value = skill;
            skillsList.appendChild(input);
        });
    }

    // Star rating functionality
    const ratingContainer = document.querySelector('.rating-stars');
    const ratingInput = document.getElementById('rating-input');
    
    if (ratingContainer && ratingInput) {
        const stars = ratingContainer.querySelectorAll('.fa-star');
        
        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const rating = index + 1;
                ratingInput.value = rating;
                
                // Update visual state
                stars.forEach((s, i) => {
                    if (i < rating) {
                        s.classList.add('selected');
                    } else {
                        s.classList.remove('selected');
                    }
                });
            });
            
            star.addEventListener('mouseover', () => {
                const rating = index + 1;
                
                // Update visual state on hover
                stars.forEach((s, i) => {
                    if (i < rating) {
                        s.classList.add('text-warning');
                    } else {
                        s.classList.remove('text-warning');
                    }
                });
            });
            
            star.addEventListener('mouseout', () => {
                // Restore selected state after hover
                const rating = parseInt(ratingInput.value) || 0;
                
                stars.forEach((s, i) => {
                    s.classList.remove('text-warning');
                    if (i < rating) {
                        s.classList.add('selected');
                    } else {
                        s.classList.remove('selected');
                    }
                });
            });
        });
    }

    // Initialize score bars
    const scoreBars = document.querySelectorAll('.score-bar');
    if (scoreBars) {
        scoreBars.forEach(bar => {
            const score = parseFloat(bar.getAttribute('data-score'));
            bar.style.width = `${score}%`;
            
            // Determine color based on score
            if (score >= 70) {
                bar.classList.add('bg-success');
            } else if (score >= 40) {
                bar.classList.add('bg-warning');
            } else {
                bar.classList.add('bg-danger');
            }
        });
    }

    // Form validation for assessment
    const assessmentForm = document.getElementById('assessment-form');
    if (assessmentForm) {
        assessmentForm.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            this.classList.add('was-validated');
        }, false);
    }
});
