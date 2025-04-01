/**
 * Common table filtering and stats functionality
 */
class TableFilter {
    constructor(options) {
        this.tableId = options.tableId;
        this.emptyStateId = options.emptyStateId || 'empty-state';
        this.filterSelectors = options.filterSelectors || {};
        this.searchSelector = options.searchSelector || '#search-input';
        this.resetSelector = options.resetSelector || '#reset-filters';
        this.clearSelector = options.clearSelector || '#clear-filters';
        this.dataAttributes = options.dataAttributes || [];
        this.statsCounters = options.statsCounters || {};
        
        this.init();
    }
    
    init() {
        // Get DOM elements
        this.table = document.getElementById(this.tableId);
        this.rows = this.table.querySelectorAll('tbody tr');
        this.emptyState = document.getElementById(this.emptyStateId);
        this.searchInput = document.querySelector(this.searchSelector);
        this.resetFiltersBtn = document.querySelector(this.resetSelector);
        this.clearFiltersBtn = document.querySelector(this.clearSelector);
        
        // Get filter elements
        this.filters = {};
        for (const [key, selector] of Object.entries(this.filterSelectors)) {
            this.filters[key] = document.querySelector(selector);
        }
        
        // Initialize tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });
        
        // Bind events
        this.bindEvents();
        
        // Calculate initial stats
        this.updateStats();
    }
    
    bindEvents() {
        // Add event listeners to filter elements
        for (const filter of Object.values(this.filters)) {
            filter.addEventListener('change', () => this.filterTable());
        }
        
        // Add event listener to search input
        this.searchInput.addEventListener('input', () => this.filterTable());
        
        // Add event listeners to reset buttons
        this.resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        if (this.clearFiltersBtn) {
            this.clearFiltersBtn.addEventListener('click', () => this.resetFilters());
        }
    }
    
    filterTable() {
        // Get filter values
        const filterValues = {};
        for (const [key, filter] of Object.entries(this.filters)) {
            filterValues[key] = filter.value;
        }
        
        const searchValue = this.searchInput.value.toLowerCase();
        
        let visibleCount = 0;
        
        // Filter rows
        this.rows.forEach(row => {
            // Check if row matches all filters
            let match = true;
            
            // Check data attribute filters
            for (const attr of this.dataAttributes) {
                const value = row.getAttribute(`data-${attr}`);
                if (filterValues[attr] && value !== filterValues[attr]) {
                    match = false;
                    break;
                }
            }
            
            // Check search text
            if (match && searchValue) {
                const text = row.textContent.toLowerCase();
                if (!text.includes(searchValue)) {
                    match = false;
                }
            }
            
            // Show/hide row
            if (match) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Show/hide empty state
        if (visibleCount === 0) {
            this.emptyState.classList.remove('d-none');
        } else {
            this.emptyState.classList.add('d-none');
        }
    }
    
    resetFilters() {
        // Reset filter values
        for (const filter of Object.values(this.filters)) {
            filter.value = '';
        }
        
        // Reset search input
        this.searchInput.value = '';
        
        // Show all rows
        this.rows.forEach(row => {
            row.style.display = '';
        });
        
        // Hide empty state
        this.emptyState.classList.add('d-none');
    }
    
    updateStats() {
        if (!this.statsCounters || Object.keys(this.statsCounters).length === 0) return;
        
        // Initialize counters
        const counts = {};
        for (const key of Object.keys(this.statsCounters)) {
            counts[key] = 0;
        }
        
        // Count rows by status
        this.rows.forEach(row => {
            for (const [key, attr] of Object.entries(this.statsCounters)) {
                const value = row.getAttribute(`data-${attr.dataAttr}`);
                if (value === attr.value) {
                    counts[key]++;
                }
            }
        });
        
        // Update counter elements
        for (const [key, count] of Object.entries(counts)) {
            const element = document.getElementById(this.statsCounters[key].elementId);
            if (element) element.textContent = count;
        }
    }
}