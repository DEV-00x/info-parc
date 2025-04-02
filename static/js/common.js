// Common JavaScript functions for device management system

// Initialize tooltips
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Counter animation for statistics
function animateCounters() {
    const counters = document.querySelectorAll('.counter');
    const speed = 200;
    
    counters.forEach(counter => {
        const target = +counter.innerText;
        const inc = target / speed;
        
        let count = 0;
        const updateCount = () => {
            if(count < target) {
                count += inc;
                counter.innerText = Math.ceil(count);
                setTimeout(updateCount, 1);
            } else {
                counter.innerText = target;
            }
        };
        
        updateCount();
    });
}

// Interactive elements
function initInteractiveElements() {
    // Interactive cards
    const cards = document.querySelectorAll('.interactive-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Interactive buttons
    const btns = document.querySelectorAll('.btn-interactive');
    btns.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.classList.add('pulse');
        });
        
        btn.addEventListener('mouseleave', function() {
            this.classList.remove('pulse');
        });
    });
    
    // Table row hover effects
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.addEventListener('mouseover', function() {
            this.classList.add('bg-light');
            this.style.transition = 'background-color 0.3s ease';
        });
        row.addEventListener('mouseout', function() {
            this.classList.remove('bg-light');
        });
    });
}

// Scroll animation
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Form validation
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// Date formatting
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Number formatting with Arabic numerals
function formatNumber(number) {
    if (number === null || number === undefined) return '-';
    return new Intl.NumberFormat('ar-SA').format(number);
}

// Copy to clipboard function
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    // Show toast notification
    showToast('تم النسخ إلى الحافظة');
}

// Toast notification
function showToast(message, type = 'success', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // Create toast content
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toastEl);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: duration
    });
    toast.show();
    
    // Remove toast after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// Print specific element
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const originalContents = document.body.innerHTML;
    const printContents = element.innerHTML;
    
    document.body.innerHTML = `
        <div class="print-section">
            ${printContents}
        </div>
    `;
    
    window.print();
    document.body.innerHTML = originalContents;
    
    // Reinitialize all scripts after restoring content
    initAllFunctions();
}

// Device type icon mapper
function getDeviceTypeIcon(type) {
    const iconMap = {
        'حاسوب مكتبي': 'fa-desktop',
        'حاسوب محمول': 'fa-laptop',
        'طابعة': 'fa-print',
        'ماسح ضوئي': 'fa-scanner',
        'راوتر': 'fa-wifi',
        'سويتش': 'fa-network-wired',
        'خادم': 'fa-server'
    };
    
    return iconMap[type] || 'fa-hdd';
}

// Status badge generator
function getStatusBadge(status) {
    let badgeClass = '';
    let icon = '';
    
    switch(status) {
        case 'فعال':
            badgeClass = 'bg-success';
            icon = 'fa-check-circle';
            break;
        case 'قيد الصيانة':
            badgeClass = 'bg-warning text-dark';
            icon = 'fa-tools';
            break;
        case 'غير فعال':
            badgeClass = 'bg-danger';
            icon = 'fa-times-circle';
            break;
        default:
            badgeClass = 'bg-secondary';
            icon = 'fa-question-circle';
    }
    
    return `<span class="badge ${badgeClass}"><i class="fas ${icon} me-1"></i> ${status}</span>`;
}

// Export table to Excel
function exportTableToExcel(tableId, fileName = 'exported_data') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const wb = XLSX.utils.table_to_book(table, {sheet: "Sheet1"});
    XLSX.writeFile(wb, `${fileName}.xlsx`);
}

// Search and highlight text in table
function searchAndHighlight(tableId, searchText) {
    if (!searchText) {
        removeHighlights(tableId);
        return;
    }
    
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    const searchRegex = new RegExp(searchText, 'gi');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let found = false;
        
        cells.forEach(cell => {
            const originalText = cell.innerText;
            if (originalText.match(searchRegex)) {
                found = true;
                cell.innerHTML = originalText.replace(searchRegex, match => `<mark>${match}</mark>`);
            }
        });
        
        if (found) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Remove highlights from table
function removeHighlights(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        row.style.display = '';
        const cells = row.querySelectorAll('td');
        
        cells.forEach(cell => {
            if (cell.querySelector('mark')) {
                cell.innerHTML = cell.innerText;
            }
        });
    });
}

// Initialize all functions
function initAllFunctions() {
    initTooltips();
    animateCounters();
    initInteractiveElements();
    initScrollAnimations();
    initFormValidation();
}

// Initialize all common functions when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initAllFunctions();
});

/**
 * Confirmation dialog for delete actions
 */
function confirmDelete(event, message) {
    if (!confirm(message)) {
        event.preventDefault();
        return false;
    }
    return true;
}

/**
 * Table Filter class for filtering and searching table data
 */
class TableFilter {
    constructor(options) {
        this.tableId = options.tableId;
        this.emptyStateId = options.emptyStateId;
        this.filterSelectors = options.filterSelectors || {};
        this.searchSelector = options.searchSelector;
        this.resetSelector = options.resetSelector;
        this.dataAttributes = options.dataAttributes || [];
        this.statsCounters = options.statsCounters || {};
        
        this.table = document.getElementById(this.tableId);
        this.emptyState = document.getElementById(this.emptyStateId);
        this.rows = this.table ? Array.from(this.table.querySelectorAll('tbody tr')) : [];
        
        this.initFilters();
        this.initSearch();
        this.initReset();
        this.updateStats();
    }
    
    initFilters() {
        for (const [key, selector] of Object.entries(this.filterSelectors)) {
            const element = document.querySelector(selector);
            if (element) {
                element.addEventListener('change', () => this.applyFilters());
            }
        }
    }
    
    initSearch() {
        const searchInput = document.querySelector(this.searchSelector);
        if (searchInput) {
            searchInput.addEventListener('input', () => this.applyFilters());
        }
    }
    
    initReset() {
        const resetButton = document.querySelector(this.resetSelector);
        if (resetButton) {
            resetButton.addEventListener('click', () => this.resetFilters());
        }
    }
    
    applyFilters() {
        if (!this.table) return;
        
        const filters = {};
        for (const [key, selector] of Object.entries(this.filterSelectors)) {
            const element = document.querySelector(selector);
            if (element) {
                filters[key] = element.value.toLowerCase();
            }
        }
        
        const searchInput = document.querySelector(this.searchSelector);
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        
        let visibleCount = 0;
        
        this.rows.forEach(row => {
            let visible = true;
            
            // Apply data attribute filters
            for (const [key, value] of Object.entries(filters)) {
                if (value && this.dataAttributes.includes(key)) {
                    const rowValue = row.getAttribute(`data-${key}`).toLowerCase();
                    if (rowValue !== value) {
                        visible = false;
                    }
                }
            }
            
            // Apply search filter
            if (visible && searchTerm) {
                const rowText = row.textContent.toLowerCase();
                if (!rowText.includes(searchTerm)) {
                    visible = false;
                }
            }
            
            // Apply date filter if present
            if (visible && filters.date && this.dataAttributes.includes('date')) {
                const rowDate = row.getAttribute('data-date');
                if (rowDate !== filters.date) {
                    visible = false;
                }
            }
            
            row.style.display = visible ? '' : 'none';
            if (visible) visibleCount++;
        });
        
        // Show/hide empty state
        if (this.emptyState) {
            this.emptyState.classList.toggle('d-none', visibleCount > 0);
        }
        
        this.updateStats();
    }
    
    resetFilters() {
        // Reset all filter inputs
        for (const selector of Object.values(this.filterSelectors)) {
            const element = document.querySelector(selector);
            if (element) {
                element.value = '';
            }
        }
        
        // Reset search input
        const searchInput = document.querySelector(this.searchSelector);
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Show all rows
        this.rows.forEach(row => {
            row.style.display = '';
        });
        
        // Hide empty state
        if (this.emptyState) {
            this.emptyState.classList.add('d-none');
        }
        
        this.updateStats();
    }
    
    updateStats() {
        if (!this.statsCounters) return;
        
        // Count total visible rows
        const totalVisible = this.rows.filter(row => row.style.display !== 'none').length;
        
        // Update total counter
        if (this.statsCounters.total) {
            const totalElement = document.getElementById(this.statsCounters.total);
            if (totalElement) {
                totalElement.textContent = totalVisible;
            }
        }
        
        // Count and update status-specific counters
        const statusCounts = {
            active: 0,
            inactive: 0,
            maintenance: 0,
            pending: 0,
            inProgress: 0,
            completed: 0
        };
        
        this.rows.forEach(row => {
            if (row.style.display !== 'none') {
                const status = row.getAttribute('data-status');
                
                if (status === 'actif') statusCounts.active++;
                else if (status === 'inactif') statusCounts.inactive++;
                else if (status === 'en maintenance') statusCounts.maintenance++;
                else if (status === 'en attente') statusCounts.pending++;
                else if (status === 'en cours') statusCounts.inProgress++;
                else if (status === 'terminé') statusCounts.completed++;
            }
        });
        
        // Update status counters
        for (const [key, value] of Object.entries(statusCounts)) {
            if (this.statsCounters[key]) {
                const element = document.getElementById(this.statsCounters[key]);
                if (element) {
                    element.textContent = value;
                }
            }
        }
    }
}