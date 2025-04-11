document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.backdropFilter = 'blur(12px) saturate(180%)';
        navbar.style.borderBottom = '1px solid rgba(236, 55, 80, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.8)';
        navbar.style.backdropFilter = 'blur(12px) saturate(180%)';
        navbar.style.borderBottom = '1px solid rgba(236, 55, 80, 0.1)';
    }
});

function openNewSiteModal() {
    const modal = document.querySelector('.modal');
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 0);
}

function closeNewSiteModal() {
    const modal = document.querySelector('.modal');
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.style.display = 'none';
    }, 200);
}

async function createNewSite(event) {
    event.preventDefault();
    const siteName = document.getElementById('siteName').value;
    
    if (!siteName) {
        alert('Please enter a site name');
        return;
    }

    try {
        const response = await fetch('/api/sites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: siteName })
        });

        const data = await response.json();
        if (response.ok) {
            window.location.href = `/edit/${data.site_id}`;
        } else {
            alert(data.message || 'Failed to create website');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to create website');
    }
}

function toggleFolder(header) {
    if (!header) return;
    const content = header.nextElementSibling;
    if (content && content.classList.contains('folder-content')) {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }
}

function openFile(element) {
    if (!element) return;
    document.querySelectorAll('.file').forEach(f => f.classList.remove('active'));
    element.classList.add('active');
}

// Handle "Learn More" click safely
function scrollToSection(event, id) {
    if (!id) return;
    const element = document.getElementById(id);
    if (element) {
        event.preventDefault();
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.add('loaded');

    // Safely bind folder headers
    document.querySelectorAll('.folder-header').forEach(header => {
        if (header) {
            header.addEventListener('click', () => toggleFolder(header));
        }
    });

    // Safely bind file clicks
    document.querySelectorAll('.file').forEach(file => {
        if (file) {
            file.addEventListener('click', () => openFile(file));
        }
    });

    // Bind Learn More links
    const learnMoreLinks = document.querySelectorAll('a[href="#features"]');
    learnMoreLinks.forEach(link => {
        if (link) {
            link.addEventListener('click', (e) => scrollToSection(e, 'features'));
        }
    });
    
    // Ensure toast container exists
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }
});

// Global function to show a notification
window.notify = function(type, message, duration) {
    if (typeof showToast === 'function') {
        return showToast(type, message, duration);
    } else {
        console.error('Toast function not found');
        alert(message);
    }
};

// Improved animation observer with faster transition
const observerOptions = {
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.feature-card').forEach(card => {
        if (card) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            card.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
            observer.observe(card);
        }
    });
});