
// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Safe element selector that won't throw errors if element doesn't exist
  function safeQuerySelector(selector) {
    const element = document.querySelector(selector);
    return element;
  }

  // Safe event binding that checks if element exists first
  function safeAddEventListener(selector, event, callback) {
    const element = safeQuerySelector(selector);
    if (element) {
      element.addEventListener(event, callback);
    }
  }

  // Initialize tabs if they exist
  const tabButtons = document.querySelectorAll('.tab-btn');
  if (tabButtons.length > 0) {
    tabButtons.forEach(button => {
      button.addEventListener('click', function() {
        const tabName = this.getAttribute('onclick').match(/openTab\('(.+?)'\)/)[1];
        
        // Load data when switching to tab
        if (tabName === 'stream') {
          loadPosts();
        } else if (tabName === 'assignments') {
          loadAssignments();
        } else if (tabName === 'resources') {
          loadResources();
        } else if (tabName === 'chat') {
          loadChatChannels();
        }
      });
    });

    // Set active tab
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab) {
      const tabName = activeTab.getAttribute('onclick').match(/openTab\('(.+?)'\)/)[1];
      openTab(tabName);
      
      // Load data for active tab
      if (tabName === 'stream') {
        loadPosts();
      } else if (tabName === 'assignments') {
        loadAssignments();
      } else if (tabName === 'resources') {
        loadResources();
      } else if (tabName === 'chat') {
        loadChatChannels();
      }
    }
  }

  // Setup chat input event handler
  safeAddEventListener('#chat-message-input', 'keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // Setup confirm club permissions checkbox
  safeAddEventListener('#confirmClubPermissions', 'change', function() {
    const confirmBtn = document.getElementById('confirmJoinBtn');
    if (confirmBtn) {
      confirmBtn.disabled = !this.checked;
    }
  });
});
