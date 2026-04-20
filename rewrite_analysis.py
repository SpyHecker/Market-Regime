import sys
import re

with open('templates/analysis.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update extensions and blocks
html = html.replace('{% extends "base.html" %}', '{% extends "app_page.html" %}')
html = html.replace('{% block title %}Historical Analysis - Market Regime Detector{% endblock %}', '')
html = html.replace('{% block content %}', '{% block page_content %}')

# 2. Add custom styles block at the top of page_content
styles = """
<style>
    .analysis-container { max-width: 100%; display: flex; flex-direction: column; gap: 24px; }
    .card-header { padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 16px; font-family: var(--fh); font-weight: 700; color: var(--cyan); display: flex; align-items: center; gap: 8px; }
    .filter-grid { display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 20px; align-items: flex-end; }
    .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
    .analysis-chart-canvas { width: 100%; height: 350px; background: rgba(0,212,255,0.03); border: 1px dashed rgba(0,212,255,0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
    
    .data-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
    .data-table th { padding: 12px 16px; background: rgba(255,255,255,0.04); color: var(--text-1); border-bottom: 1px solid rgba(255,255,255,0.1); }
    .data-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); color: var(--text-2); }
    .data-table tr:hover td { background: rgba(0,212,255,0.02); }
    
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
    .badge-bull { background: rgba(0,230,118,0.15); color: var(--green); border: 1px solid rgba(0,230,118,0.3); }
    .badge-bear { background: rgba(255,61,87,0.15); color: var(--red); border: 1px solid rgba(255,61,87,0.3); }
    .badge-side { background: rgba(255,179,0,0.15); color: var(--amber); border: 1px solid rgba(255,179,0,0.3); }
    .badge-vol { background: rgba(139,92,246,0.15); color: var(--violet); border: 1px solid rgba(139,92,246,0.3); }
</style>
<div class="analysis-container">
    <div>
        <h1 class="h1">Historical Analysis</h1>
        <p class="p">Deep dive into market regime patterns and historical trends</p>
    </div>
"""

# Replace the header section
html = re.sub(r'<div class="analysis-container">.*?<!-- Header -->.*?</section>\s*<!-- Analysis Tools -->\s*<section class="py-5">\s*<div class="container">', styles, html, flags=re.DOTALL)

# Replace the old end tags
html = html.replace('        </div>\n    </section>\n</div>', '</div>')

# Fix filter section
filter_old = """            <!-- Filter Controls -->
            <div class="row mb-5">
                <div class="col-12">
                    <div class="card shadow-sm border-0">
                        <div class="card-header bg-light border-bottom">
                            <h5 class="mb-0"><i class="fas fa-filter"></i> Analysis Filters</h5>
                        </div>
                        <div class="card-body">
                            <div class="row g-3">
                                <div class="col-md-3">
                                    <label class="form-label">Date Range</label>
                                    <select class="form-select" id="dateRange">
                                        <option value="1m">Last Month</option>
                                        <option value="3m">Last 3 Months</option>
                                        <option value="6m">Last 6 Months</option>
                                        <option value="1y">Last Year</option>
                                        <option value="5y" selected>Last 5 Years</option>
                                        <option value="10y">Last 10 Years</option>
                                    </select>
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Regime Type</label>
                                    <select class="form-select" id="regimeType">
                                        <option value="">All Regimes</option>
                                        <option value="bull">Bull Markets</option>
                                        <option value="bear">Bear Markets</option>
                                        <option value="sideways">Sideways Markets</option>
                                        <option value="volatile">High Volatility</option>
                                    </select>
                                </div>
                                <div class="col-md-6 d-flex align-items-end">
                                    <button class="btn btn-primary w-100">
                                        <i class="fas fa-search"></i> Analyze
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>"""

filter_new = """    <!-- Filter Controls -->
    <div class="card">
        <div class="card-header"><i class="fas fa-filter"></i> Analysis Filters</div>
        <div class="filter-grid">
            <div class="form-group mb-0">
                <label class="form-label">Date Range</label>
                <select class="form-select" id="dateRange">
                    <option value="1m">Last Month</option>
                    <option value="3m">Last 3 Months</option>
                    <option value="6m">Last 6 Months</option>
                    <option value="1y">Last Year</option>
                    <option value="5y" selected>Last 5 Years</option>
                    <option value="10y">Last 10 Years</option>
                </select>
            </div>
            <div class="form-group mb-0">
                <label class="form-label">Regime Type</label>
                <select class="form-select" id="regimeType">
                    <option value="">All Regimes</option>
                    <option value="bull">Bull Markets</option>
                    <option value="bear">Bear Markets</option>
                    <option value="sideways">Sideways Markets</option>
                    <option value="volatile">High Volatility</option>
                </select>
            </div>
            <div>
                <button class="btn btn-primary" style="width:100%;">
                    <i class="fas fa-search"></i> Analyze
                </button>
            </div>
        </div>
    </div>"""

html = html.replace(filter_old, filter_new)

# Fix row wrappers
html = html.replace('<div class="row mb-5">', '<div class="grid-1 gap-20">')
html = html.replace('<div class="col-12">', '')
html = html.replace('</div>\n                </div>\n            </div>', '</div>\n    </div>')

# Fix cards
html = html.replace('<div class="card shadow-sm border-0">', '<div class="card">')
html = html.replace('<div class="card-header bg-light border-bottom d-flex justify-content-between align-items-center">', '<div class="card-header" style="justify-content: space-between;">')
html = html.replace('<h5 class="mb-0">', '<div>')
html = html.replace('</h5>', '</div>')

# Chart area
html = html.replace('<div class="chart-container" style="position: relative; height:400px; width:100%">', '<div class="analysis-chart-canvas">')
html = html.replace('<canvas id="historicalChart"></canvas>', 'Interactive charts and visualization will load here')

# Stats rows
html = html.replace('<div class="row g-4 mb-5">', '<div class="stat-row">')
html = html.replace('<div class="col-md-3">', '')
html = html.replace('<div class="card shadow-sm border-0 bg-primary text-white h-100">', '<div class="stat-box">')
html = html.replace('<div class="card shadow-sm border-0 bg-success text-white h-100">', '<div class="stat-box">')
html = html.replace('<div class="card shadow-sm border-0 bg-danger text-white h-100">', '<div class="stat-box">')
html = html.replace('<div class="card shadow-sm border-0 bg-warning text-dark h-100">', '<div class="stat-box">')
html = html.replace('<h6 class="card-title text-white-50">', '<div class="stat-label">')
html = html.replace('<h6 class="card-title text-dark-50">', '<div class="stat-label">')
html = html.replace('</h6>', '</div>')
html = html.replace('<h3 class="mb-0">', '<div class="stat-value text-cyan">')
html = html.replace('</h3>', '</div>')

# Tables
html = html.replace('<div class="table-responsive">', '')
html = html.replace('<table class="table table-hover mb-0">', '<table class="data-table">')
html = html.replace('<thead class="table-light">', '<thead>')

# Badges
html = html.replace('<span class="badge bg-success">', '<span class="badge badge-bull">')
html = html.replace('<span class="badge bg-danger">', '<span class="badge badge-bear">')
html = html.replace('<span class="badge bg-warning text-dark">', '<span class="badge badge-side">')
html = html.replace('<span class="badge bg-info">', '<span class="badge badge-vol">')

html = html.replace('class="text-success"', 'style="color: var(--green)"')
html = html.replace('class="text-danger"', 'style="color: var(--red)"')
html = html.replace('class="btn btn-sm btn-outline-secondary"', 'class="btn" style="background: rgba(255,255,255,0.1);"')
html = html.replace('class="btn btn-sm btn-outline-primary"', 'class="btn" style="border: 1px solid var(--cyan); background: transparent; color: var(--cyan);"')

html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL) # remove end inline styles

with open('templates/analysis.html', 'w', encoding='utf-8') as f:
    f.write(html)
