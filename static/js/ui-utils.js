
/**
 * UI Utilities for Hack Club Spaces
 * Centralized functions for common UI interactions
 */

// Toast notification system
function showToast(type, message, duration = 3000) {
    const toastContainer = document.getElementById('toast-container');
    
    // Create toast container if it doesn't exist
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Choose icon based on type
    let icon = 'info-circle';
    switch(type) {
        case 'success': icon = 'check-circle'; break;
        case 'error': icon = 'exclamation-circle'; break;
        case 'warning': icon = 'exclamation-triangle'; break;
        case 'info': icon = 'info-circle'; break;
    }

    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${icon}"></i>
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentNode.remove()">&times;</button>
    `;

    // Add toast to container
    const container = toastContainer || document.getElementById('toast-container');
    container.appendChild(toast);
    
    // Force reflow to trigger animation
    toast.offsetHeight;
    
    // Show toast
    toast.classList.add('show');

    // Auto remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Modal handling
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            document.body.style.overflow = '';
        }, 300);
    }
}

// Form validation helpers
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    
    // Clear previous errors
    form.querySelectorAll('.form-error').forEach(el => el.remove());
    
    for (const field in rules) {
        const input = form.querySelector(`[name="${field}"]`);
        if (!input) continue;
        
        const value = input.value.trim();
        const fieldRules = rules[field];
        
        // Required check
        if (fieldRules.required && value === '') {
            showFieldError(input, fieldRules.requiredMessage || 'This field is required');
            isValid = false;
            continue;
        }
        
        // Minimum length
        if (fieldRules.minLength && value.length < fieldRules.minLength) {
            showFieldError(input, `Must be at least ${fieldRules.minLength} characters`);
            isValid = false;
            continue;
        }
        
        // Maximum length
        if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
            showFieldError(input, `Must be no more than ${fieldRules.maxLength} characters`);
            isValid = false;
            continue;
        }
        
        // Email format
        if (fieldRules.email && !validateEmail(value)) {
            showFieldError(input, 'Please enter a valid email address');
            isValid = false;
            continue;
        }
        
        // Match fields (like password confirmation)
        if (fieldRules.matches) {
            const matchInput = form.querySelector(`[name="${fieldRules.matches}"]`);
            if (matchInput && value !== matchInput.value) {
                showFieldError(input, fieldRules.matchesMessage || 'Fields do not match');
                isValid = false;
                continue;
            }
        }
        
        // Custom validation
        if (fieldRules.custom && typeof fieldRules.custom === 'function') {
            const customResult = fieldRules.custom(value, form);
            if (customResult !== true) {
                showFieldError(input, customResult || 'Invalid value');
                isValid = false;
                continue;
            }
        }
    }
    
    return isValid;
}

function showFieldError(input, message) {
    // Remove any existing error for this field
    const existingError = input.parentNode.querySelector('.form-error');
    if (existingError) existingError.remove();
    
    // Add error message
    const errorElement = document.createElement('div');
    errorElement.className = 'form-error';
    errorElement.textContent = message;
    errorElement.style.color = '#ec3750';
    errorElement.style.fontSize = '0.85rem';
    errorElement.style.marginTop = '0.25rem';
    
    // Insert after the input
    input.parentNode.insertBefore(errorElement, input.nextSibling);
    
    // Highlight the input
    input.style.borderColor = '#ec3750';
    
    // Remove error when input changes
    const clearError = () => {
        const error = input.parentNode.querySelector('.form-error');
        if (error) error.remove();
        input.style.borderColor = '';
        input.removeEventListener('input', clearError);
    };
    
    input.addEventListener('input', clearError);
}

function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Copy to clipboard helper
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    navigator.clipboard.writeText(text)
        .then(() => showToast('success', successMessage))
        .catch(() => showToast('error', 'Failed to copy to clipboard'));
}

// Utilities for handling API requests
async function apiRequest(url, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.error || 'An error occurred');
        }
        
        return { success: true, data: responseData };
    } catch (error) {
        console.error('API Request Error:', error);
        return { success: false, error: error.message || 'An error occurred' };
    }
}

// Initialize UI when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Set up toast container if it doesn't exist
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Handle modal close buttons
    document.querySelectorAll('.close-btn').forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal');
            if (modal) {
                modal.classList.remove('show');
                setTimeout(() => {
                    document.body.style.overflow = '';
                }, 300);
            }
        });
    });
    
    // Close modals when clicking outside content
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
                setTimeout(() => {
                    document.body.style.overflow = '';
                }, 300);
            }
        });
    });
});
