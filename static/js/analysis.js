/* ===========================
   ANALYSIS PAGE INITIALIZATION
   =========================== */

let analysisData = {
    stats: null,
    historical: null,
    transitions: null,
    currentPeriod: 252  // 1 year by default
};

let analysisCharts = {
    historyChart: null,
    transitionChart: null,
    correlationChart: null,
    returnsChart: null
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🎯 Analysis page initializing...');
    initializeEventListeners();
    await loadAnalysisData(252);
});

// ===========================
// EVENT LISTENERS
// ===========================

function initializeEventListeners() {
    // Date range selector
    const dateRangeEl = document.getElementById('dateRange');
    if (dateRangeEl) {
        dateRangeEl.addEventListener('change', async function(e) {
            const days = getDaysFromRange(e.target.value);
            await loadAnalysisData(days);
        });
    }
    
    // Analyze button
    const analyzeBtn = document.querySelector('button:has(i.fa-search)');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async function() {
            const days = getDaysFromRange(document.getElementById('dateRange').value);
            await loadAnalysisData(days);
        });
    }
}

function getDaysFromRange(range) {
    const ranges = {
        '1m': 21,
        '3m': 63,
        '6m': 126,
        '1y': 252,
        '5y': 1260,
        '10y': 2520
    };
    return ranges[range] || 252;
}

// ===========================
// LOAD DATA
// ===========================

async function loadAnalysisData(days) {
    try {
        console.log(`📡 Loading analysis data for ${days} days...`);
        
        analysisData.currentPeriod = days;
        
        // Fetch data from APIs
        const statsPromise = fetch(`/api/stats?days=${days}`).then(r => r.json());
        const historicalPromise = fetch(`/api/historical_analysis?days=${days}`).then(r => r.json());
        
        const [statsData, historicalData] = await Promise.all([statsPromise, historicalPromise]);
        
        analysisData.stats = statsData;
        analysisData.historical = historicalData.historical || [];  // Get the array from the response
        analysisData.transitions = historicalData.transitions || {};
        
        console.log('✓ Data loaded successfully');
        
        // Update UI
        updateStatistics();
        updateCharts();
        
        console.log('✓ Analysis page updated');
    } catch (error) {
        console.error('❌ Error loading analysis data:', error);
        showAnalysisError('Failed to load analysis data. Please try again.');
    }
}

// ===========================
// UPDATE STATISTICS
// ===========================

function updateStatistics() {
    if (!analysisData.stats) return;
    
    const regimes = analysisData.stats.regimes || {};
    
    // Update stat boxes
    const statBoxes = document.querySelectorAll('.stat-box');
    const regimeNames = Object.keys(regimes);
    
    statBoxes.forEach((box, index) => {
        if (index < regimeNames.length) {
            const regimeName = regimeNames[index];
            const regimeStats = regimes[regimeName];
            
            const days = regimeStats.days || 0;
            const percentage = (days / analysisData.currentPeriod * 100).toFixed(1);
            const avgReturn = ((regimeStats.avg_return || 0) * 100).toFixed(2);
            
            const valueDivs = box.querySelectorAll('[class*="stat-"]');
            if (valueDivs.length >= 2) {
                valueDivs[0].textContent = `${days} days`;
                valueDivs[1].textContent = `${regimeName} Duration`;
                
                const smallEl = box.querySelector('small');
                if (smallEl) {
                    smallEl.textContent = `${percentage}% of period (${avgReturn}% avg return)`;
                }
            }
        }
    });
}

// ===========================
// UPDATE CHARTS
// ===========================

async function updateCharts() {
    console.log('📊 Updating charts...');
    
    await updateHistoryChart();
    await updateTransitionChart();
    await updateCorrelationChart();
    await updateReturnsChart();
    
    console.log('✓ Charts updated');
}

async function updateHistoryChart() {
    const canvas = document.getElementById('historyChart');
    if (!canvas) return;
    
    if (analysisCharts.historyChart) {
        analysisCharts.historyChart.destroy();
    }
    
    try {
        const historicalData = analysisData.historical || [];
        
        // Group data points (show every nth point to avoid crowding)
        const step = Math.ceil(historicalData.length / 50);
        const sampledData = historicalData.filter((_, i) => i % step === 0).slice(-50);
        
        const dates = sampledData.map(d => d.date || 'N/A');
        const prices = sampledData.map(d => parseFloat(d.price) || 0);
        const regimes = sampledData.map(d => {
            const regimeMap = { 'Bull': 1, 'Bear': 2, 'Sideways': 3, 'Volatile': 4 };
            return regimeMap[d.regime] || 0;
        });
        
        const ctx = canvas.getContext('2d');
        analysisCharts.historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Price Index',
                        data: prices,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.05)',
                        tension: 0.4,
                        yAxisID: 'y',
                        borderWidth: 2
                    },
                    {
                        label: 'Regime Signal',
                        data: regimes,
                        borderColor: '#764ba2',
                        backgroundColor: 'rgba(118, 75, 162, 0.1)',
                        type: 'bar',
                        yAxisID: 'y1',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: false
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        max: 5,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating history chart:', error);
    }
}

async function updateTransitionChart() {
    const canvas = document.getElementById('transitionChart');
    if (!canvas) return;
    
    if (analysisCharts.transitionChart) {
        analysisCharts.transitionChart.destroy();
    }
    
    try {
        const transitions = analysisData.transitions || {};
        const labels = Object.keys(transitions);
        const data = Object.values(transitions);
        
        // Color based on regime types
        const colors = labels.map(label => {
            if (label.includes('Bull→Bull') || label.includes('Bull')) return '#28a745';
            if (label.includes('Bear→Bear') || label.includes('Bear')) return '#dc3545';
            if (label.includes('Sideways')) return '#ffc107';
            return '#6c757d';
        });
        
        const ctx = canvas.getContext('2d');
        analysisCharts.transitionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Transition Count',
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating transition chart:', error);
    }
}

async function updateCorrelationChart() {
    const canvas = document.getElementById('correlationChart');
    if (!canvas) return;
    
    if (analysisCharts.correlationChart) {
        analysisCharts.correlationChart.destroy();
    }
    
    try {
        const historicalData = analysisData.historical || [];
        const volatilities = historicalData.map(d => (d.volatility || 0) * 100);
        const returns = historicalData.map(d => (d.return || 0) * 100);
        const regimes = historicalData.map(d => d.regime || 'Unknown');
        
        // Group data by regime
        const bullData = [];
        const bearData = [];
        const sidewaysData = [];
        const volatileData = [];
        
        returns.forEach((ret, i) => {
            const point = { x: volatilities[i], y: ret };
            if (regimes[i] === 'Bull') bullData.push(point);
            else if (regimes[i] === 'Bear') bearData.push(point);
            else if (regimes[i] === 'Sideways') sidewaysData.push(point);
            else volatileData.push(point);
        });
        
        const ctx = canvas.getContext('2d');
        analysisCharts.correlationChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Bull Market',
                        data: bullData,
                        backgroundColor: 'rgba(40, 167, 69, 0.6)',
                        borderColor: '#28a745'
                    },
                    {
                        label: 'Bear Market',
                        data: bearData,
                        backgroundColor: 'rgba(220, 53, 69, 0.6)',
                        borderColor: '#dc3545'
                    },
                    {
                        label: 'Sideways',
                        data: sidewaysData,
                        backgroundColor: 'rgba(255, 193, 7, 0.6)',
                        borderColor: '#ffc107'
                    },
                    {
                        label: 'Volatile',
                        data: volatileData,
                        backgroundColor: 'rgba(108, 117, 125, 0.6)',
                        borderColor: '#6c757d'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Volatility (%)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Daily Return (%)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating correlation chart:', error);
    }
}

async function updateReturnsChart() {
    const canvas = document.getElementById('returnsChart');
    if (!canvas) return;
    
    try {
        const stats = analysisData.stats.regimes || {};
        
        // Extract regime data
        const regimes = Object.keys(stats);
        const returns = regimes.map(r => (stats[r].avg_return || 0) * 100);
        const volatilities = regimes.map(r => (stats[r].volatility || 0) * 100);
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (analysisCharts.returnsChart) {
            analysisCharts.returnsChart.destroy();
        }
        
        analysisCharts.returnsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: regimes,
                datasets: [
                    {
                        label: 'Avg Daily Return (%)',
                        data: returns,
                        backgroundColor: [
                            '#28a745',  // Bull - Green
                            '#dc3545',  // Bear - Red
                            '#ffc107',  // Sideways - Yellow
                            '#6c757d'   // Volatile - Gray
                        ],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Average Daily Return (%)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating returns chart:', error);
    }
}

// ===========================
// ERROR HANDLING
// ===========================

function showAnalysisError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>Error:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.analysis-container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
}
