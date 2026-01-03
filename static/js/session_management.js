// Prevent back button access after logout
(function() {
    // Check if user just logged out
    if (window.performance && performance.navigation.type === 2) {
        // User arrived via back button
        if (document.body.dataset.requiresAuth === 'true' && !document.body.dataset.isAuthenticated) {
            window.location.href = '/login/';
        }
    }
    
    // Prevent caching
    window.onpageshow = function(event) {
        if (event.persisted) {
            window.location.reload();
        }
    };
    
    // Clear history on logout
    if (window.location.pathname === '/logout/') {
        if (window.history && window.history.pushState) {
            window.history.pushState(null, null, window.location.href);
            window.onpopstate = function() {
                window.history.pushState(null, null, window.location.href);
            };
        }
    }
})();

// Session timeout warning
let sessionTimeout;
let warningTimeout;

function resetSessionTimer() {
    clearTimeout(sessionTimeout);
    clearTimeout(warningTimeout);
    
    // Warn 2 minutes before timeout
    warningTimeout = setTimeout(function() {
        if (confirm('Your session will expire in 2 minutes. Click OK to continue your session.')) {
            // Make a dummy request to extend session
            fetch('/dashboard/', { method: 'HEAD' });
        }
    }, 28 * 60 * 1000); // 28 minutes
    
    // Logout after 30 minutes
    sessionTimeout = setTimeout(function() {
        alert('Your session has expired. Please login again.');
        window.location.href = '/logout/';
    }, 30 * 60 * 1000); // 30 minutes
}

// Reset timer on user activity
if (document.body.dataset.isAuthenticated === 'true') {
    document.addEventListener('mousemove', resetSessionTimer);
    document.addEventListener('keypress', resetSessionTimer);
    document.addEventListener('click', resetSessionTimer);
    resetSessionTimer();
}