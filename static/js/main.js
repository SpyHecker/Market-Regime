/* ===========================
   MAIN JAVASCRIPT
   =========================== */

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initializeSmoothScroll();
    initializeTooltips();
    initializePopovers();
    handleNavigation();
    handleFormSubmissions();
});

// ===========================
// SMOOTH SCROLL
// ===========================

function initializeSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const hash = this.getAttribute('href');
            if (document.querySelector(hash)) {
                e.preventDefault();
                document.querySelector(hash).scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ===========================
// BOOTSTRAP TOOLTIPS & POPOVERS
// ===========================

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// ===========================
// NAVIGATION
// ===========================

function handleNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Close mobile menu if open
            const navbar = document.querySelector('.navbar-collapse');
            if (navbar.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbar, {
                    toggle: true
                });
            }
        });
    });

    // Highlight active nav item based on current page
    const currentPage = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });
}

// ===========================
// FORM SUBMISSIONS
// ===========================

function handleFormSubmissions() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            // Add loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

                // Simulate processing (replace with actual submission)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                    showNotification('Form submitted successfully!', 'success');
                }, 1500);
            }
        });
    });
}

// ===========================
// NOTIFICATIONS
// ===========================

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insert at top of main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(alertDiv, mainContent.firstChild);

        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// ===========================
// CHART HELPERS
// ===========================

function createSimpleLineChart(canvasId, labels, data, label, color = 'rgb(102, 126, 234)') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createBarChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

// ===========================
// DATA FETCHING
// ===========================

async function fetchData(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : undefined
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        showNotification('Error fetching data: ' + error.message, 'danger');
        return null;
    }
}

// ===========================
// UTILITY FUNCTIONS
// ===========================

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatPercentage(value, decimals = 2) {
    return (value * 100).toFixed(decimals) + '%';
}

function formatNumber(value, decimals = 0) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

function getRegimeColor(regime) {
    const colors = {
        'Bull': '#28a745',
        'Bear': '#dc3545',
        'Sideways': '#ffc107',
        'Volatile': '#6c757d'
    };
    return colors[regime] || '#667eea';
}

function getRegimeBadgeClass(regime) {
    const classes = {
        'Bull': 'bg-success',
        'Bear': 'bg-danger',
        'Sideways': 'bg-warning',
        'Volatile': 'bg-secondary'
    };
    return classes[regime] || 'bg-primary';
}

// ===========================
// FILTER & SEARCH
// ===========================

function filterTable(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const match = text.includes(searchTerm.toLowerCase());
        row.style.display = match ? '' : 'none';
    });
}

// ===========================
// LOCAL STORAGE HELPERS
// ===========================

function savePreference(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function getPreference(key, defaultValue = null) {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : defaultValue;
}

function removePreference(key) {
    localStorage.removeItem(key);
}

// ===========================
// SCROLL TO TOP
// ===========================

function initializeScrollToTop() {
    const scrollBtn = document.createElement('button');
    scrollBtn.id = 'scrollTop';
    scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollBtn.className = 'btn btn-primary btn-lg';
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        display: none;
        z-index: 99;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        padding: 0;
        align-items: center;
        justify-content: center;
    `;

    document.body.appendChild(scrollBtn);

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollBtn.style.display = 'flex';
        } else {
            scrollBtn.style.display = 'none';
        }
    });

    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize scroll to top on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeScrollToTop);
} else {
    initializeScrollToTop();
}

// ===========================
// SIDEBAR NAVIGATION (Documentation)
// ===========================

function initializeDocSidebar() {
    const sidebarLinks = document.querySelectorAll('.doc-sidebar a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');

            // Scroll to section
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Highlight active section on scroll
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('.doc-section');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });

        sidebarLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').slice(1) === current) {
                link.classList.add('active');
            }
        });
    });
}

// Initialize doc sidebar if it exists
if (document.querySelector('.doc-sidebar')) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDocSidebar);
    } else {
        initializeDocSidebar();
    }
}

// ===========================
// ANALYSIS PAGE FILTERS
// ===========================

function handleAnalysisFilters() {
    const analyzeBtn = document.querySelector('button');
    if (analyzeBtn && analyzeBtn.textContent.includes('Analyze')) {
        analyzeBtn.addEventListener('click', function() {
            const dateRange = document.getElementById('dateRange')?.value;
            const regimeType = document.getElementById('regimeType')?.value;

            // Save preferences
            savePreference('analysisFilters', {
                dateRange,
                regimeType
            });

            // Show loading state
            const originalText = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';

            // Simulate analysis (replace with actual API call)
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = originalText;
                showNotification('Analysis updated successfully!', 'success');
            }, 2000);
        });
    }

    // Restore previous filters
    const savedFilters = getPreference('analysisFilters');
    if (savedFilters) {
        if (document.getElementById('dateRange')) {
            document.getElementById('dateRange').value = savedFilters.dateRange;
        }
        if (document.getElementById('regimeType')) {
            document.getElementById('regimeType').value = savedFilters.regimeType;
        }
    }
}

// Initialize analysis filters if we're on the analysis page
if (document.getElementById('dateRange')) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', handleAnalysisFilters);
    } else {
        handleAnalysisFilters();
    }
}
