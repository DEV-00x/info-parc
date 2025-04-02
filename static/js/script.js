/**
 * Main script file for the Device Management System
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Add animation to counters
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        const value = parseInt(counter.textContent);
        let startValue = 0;
        const duration = 1000;
        const increment = value / (duration / 20);
        
        const updateCounter = () => {
            startValue += increment;
            if (startValue < value) {
                counter.textContent = Math.floor(startValue);
                setTimeout(updateCounter, 20);
            } else {
                counter.textContent = value;
            }
        };
        
        updateCounter();
    });
});