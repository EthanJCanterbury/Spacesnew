
// Club Dashboard JavaScript
// Centralizes all event handling with proper error prevention

document.addEventListener('DOMContentLoaded', function() {
  // Initialize the dashboard safely
  initializeDashboard();
});

// Main initialization function
function initializeDashboard() {
  console.log("Initializing club dashboard...");
  
  // Set up tab functionality
  setupTabs();
  
  // Load data for active tab
  loadActiveTabData();
  
  // Set up event listeners safely
  setupEventListeners();
  
  console.log("Club dashboard initialization complete");
}

// Safely set up all event listeners with proper null checks
function setupEventListeners() {
  // Form submissions
  safeAddEventListener('#createChannelForm', 'submit', function(e) {
    e.preventDefault();
    createChannel();
  });
  
  safeAddEventListener('#addResourceForm', 'submit', function(e) {
    e.preventDefault();
    addResource();
  });
  
  safeAddEventListener('#createAssignmentForm', 'submit', function(e) {
    e.preventDefault();
    createAssignment();
  });
  
  // Chat message input
  safeAddEventListener('#chat-message-input', 'keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });
  
  // Modal close buttons
  document.querySelectorAll('.close-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const modalId = this.closest('.modal').id;
      closeModal(modalId);
    });
  });
}

// Safely add an event listener with null checks
function safeAddEventListener(selector, eventType, handler) {
  const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
  
  if (element) {
    element.addEventListener(eventType, handler);
    return true;
  } else {
    console.warn(`Element not found: ${selector}, event listener not attached for ${eventType}`);
    return false;
  }
}

// Set up tab functionality
function setupTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  
  if (tabButtons && tabButtons.length > 0) {
    tabButtons.forEach(btn => {
      btn.addEventListener('click', function() {
        const tabName = this.getAttribute('onclick').match(/openTab\('(.+?)'\)/)[1];
        openTab(tabName);
      });
    });
  }
}

// Load data for the active tab
function loadActiveTabData() {
  const activeTab = document.querySelector('.tab-pane.active');
  
  if (activeTab) {
    const tabId = activeTab.id;
    
    if (tabId === 'stream') loadPosts();
    else if (tabId === 'assignments') loadAssignments();
    else if (tabId === 'resources') loadResources();
    else if (tabId === 'chat') loadChatChannels();
  }
}

// Utility function to wait for an element to exist before executing callback
function whenElementExists(selector, callback, maxAttempts = 10, interval = 200) {
  let attempts = 0;
  
  const checkElement = () => {
    const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
    
    if (element) {
      callback(element);
      return true;
    } else if (attempts < maxAttempts) {
      attempts++;
      setTimeout(checkElement, interval);
      return false;
    }
    
    console.warn(`Element ${selector} not found after ${maxAttempts} attempts`);
    return false;
  };
  
  return checkElement();
}

// The rest of your existing functions from club_dashboard.html would go here
// but using the safe pattern established above
