// Custom JavaScript for Device Management System

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-close alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Add current year to footer
    document.querySelector('.footer .text-muted').innerHTML = 
        document.querySelector('.footer .text-muted').innerHTML.replace('{{ current_year }}', new Date().getFullYear());
});

// Confirm delete
function confirmDelete(event, message) {
    if (!confirm(message || 'هل أنت متأكد من الحذف؟')) {
        event.preventDefault();
        return false;
    }
    return true;
}

// Print function
function printContent(elementId) {
    var content = document.getElementById(elementId);
    var printWindow = window.open('', '_blank');
    
    printWindow.document.write('<html><head><title>طباعة</title>');
    printWindow.document.write('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css">');
    printWindow.document.write('<style>body { font-family: "Tajawal", sans-serif; direction: rtl; }</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write(content.innerHTML);
    printWindow.document.write('</body></html>');
    
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(function() {
        printWindow.print();
        printWindow.close();
    }, 250);
}

// Date formatting helper
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA');
}

// Search functionality for tables
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const tr = table.getElementsByTagName('tr');
    
    for (let i = 1; i < tr.length; i++) {
        let txtValue = '';
        const td = tr[i].getElementsByTagName('td');
        
        for (let j = 0; j < td.length; j++) {
            txtValue += td[j].textContent || td[j].innerText;
        }
        
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            tr[i].style.display = '';
        } else {
            tr[i].style.display = 'none';
        }
    }
}