
/**
 * Event Helper Utilities
 * Provides safe event handling for DOM elements that might not exist
 */

// Safely add event listener to an element that might not exist
function safeAddEventListener(selector, eventType, handler) {
    try {
        const element = typeof selector === 'string' 
            ? document.querySelector(selector) 
            : selector;
            
        if (element) {
            element.addEventListener(eventType, handler);
            return true;
        }
        return false;
    } catch (error) {
        console.warn(`Error adding event listener to ${selector}:`, error);
        return false;
    }
}

// Safely add event listeners to multiple elements
function safeAddEventListeners(selectors, eventType, handler) {
    try {
        const elements = typeof selectors === 'string' 
            ? document.querySelectorAll(selectors) 
            : selectors;
            
        if (elements && elements.length > 0) {
            elements.forEach(element => {
                element.addEventListener(eventType, handler);
            });
            return elements.length;
        }
        return 0;
    } catch (error) {
        console.warn(`Error adding event listeners to ${selectors}:`, error);
        return 0;
    }
}

// Execute a function only when an element exists
function whenElementExists(selector, callback, maxAttempts = 10, interval = 200) {
    let attempts = 0;
    
    const checkElement = () => {
        const element = typeof selector === 'string' 
            ? document.querySelector(selector) 
            : selector;
            
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

// Execute a callback when DOM is ready, with fallbacks
function onDOMReady(callback) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', callback);
        // Backup in case DOMContentLoaded fails
        window.addEventListener('load', function() {
            if (!window._domReadyExecuted) {
                callback();
            }
        });
    } else {
        // Already loaded
        callback();
    }
    
    // Mark as executed
    window._domReadyExecuted = true;
}
