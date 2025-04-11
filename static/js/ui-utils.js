
/**
 * Shows a toast notification
 * @param {string} type - 'success', 'error', 'warning', or 'info'
 * @param {string} message - The message to display
 * @param {number} duration - Duration in ms the toast should be visible (default: 5000)
 */
function showToast(type, message, duration = 5000) {
  // Validate type
  const validTypes = ['success', 'error', 'warning', 'info'];
  if (!validTypes.includes(type)) {
    type = 'info';
  }
  
  // Get or create toast container
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    document.body.appendChild(toastContainer);
  }
  
  // Get appropriate icon
  const iconMap = {
    'success': 'check-circle',
    'error': 'exclamation-circle',
    'warning': 'exclamation-triangle',
    'info': 'info-circle'
  };
  const icon = iconMap[type];
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <i class="fas fa-${icon}"></i>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close">&times;</button>
  `;
  
  // Add event listener to close button
  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  });
  
  // Add to container
  toastContainer.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);
  
  // Auto remove after duration
  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }
  }, duration);
  
  // Return the toast element for potential further manipulation
  return toast;
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  
  modal.style.display = 'flex';
  modal.offsetHeight; 
  modal.classList.add('show');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  
  modal.classList.remove('show');
  setTimeout(() => {
    modal.style.display = 'none';
  }, 300);
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}

function deploySite() {
  openModal('deployModal');
}

function closeDeployModal() {
  closeModal('deployModal');
}

function openDeployedSite() {
  const slug = document.getElementById('site-slug').value;
  window.open(`https://hackclub.space/s/${slug}`, '_blank');
}

function initModals() {
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.classList.remove('show');
        setTimeout(() => {
          this.style.display = 'none';
        }, 300);
      }
    });
  });
  
  document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const modal = this.closest('.modal');
      modal.classList.remove('show');
      setTimeout(() => {
        modal.style.display = 'none';
      }, 300);
    });
  });
}

function initTooltips() {
  const tooltips = document.querySelectorAll('[data-tooltip]');
  tooltips.forEach(element => {
    const tooltipText = element.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.classList.add('tooltip');
    tooltip.textContent = tooltipText;
    
    element.addEventListener('mouseenter', () => {
      document.body.appendChild(tooltip);
      const rect = element.getBoundingClientRect();
      tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
      tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
      setTimeout(() => tooltip.classList.add('visible'), 10);
    });
    
    element.addEventListener('mouseleave', () => {
      tooltip.classList.remove('visible');
      setTimeout(() => {
        if (tooltip.parentElement) {
          tooltip.parentElement.removeChild(tooltip);
        }
      }, 300);
    });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  initModals();
  initTooltips();
  
  const splitViewToggle = document.getElementById('splitViewToggle');
  if (splitViewToggle) {
    splitViewToggle.style.position = 'fixed';
    splitViewToggle.style.right = '20px';
    splitViewToggle.style.bottom = '20px';
    splitViewToggle.style.zIndex = '100';
    splitViewToggle.style.backgroundColor = 'var(--primary)';
    splitViewToggle.style.color = 'white';
    splitViewToggle.style.width = '40px';
    splitViewToggle.style.height = '40px';
    splitViewToggle.style.borderRadius = '50%';
    splitViewToggle.style.display = 'flex';
    splitViewToggle.style.alignItems = 'center';
    splitViewToggle.style.justifyContent = 'center';
    splitViewToggle.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
    splitViewToggle.style.cursor = 'pointer';
  }
});
/**
 * Unified toast notification system
 * @param {string} type - Type of toast: 'success', 'error', 'info', 'warning'
 * @param {string} message - Message to display in the toast
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(type, message, duration = 3000) {
    // Ensure toast container exists
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Determine icon based on type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    else if (type === 'error') icon = 'exclamation-circle';
    else if (type === 'warning') icon = 'exclamation-triangle';
    
    // Set inner HTML
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${icon}"></i>
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close">&times;</button>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Animation timing
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Add close functionality
    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
    }
    
    // Auto dismiss
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }
    }, duration);
    
    return toast;
}

// Global availability
window.showToast = showToast;
