import sys
import re

with open('templates/documentation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update extensions and blocks
html = html.replace('{% extends "base.html" %}', '{% extends "app_page.html" %}')
html = html.replace('{% block title %}Documentation - Market Regime Detector{% endblock %}', '')
html = html.replace('{% block content %}', '{% block page_content %}')

# 2. Remove old inline styles FIRST
html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)

# 3. Add custom styles block at the top of page_content
styles = """
<style>
    .doc-layout { display: grid; grid-template-columns: 250px 1fr; gap: 40px; margin-top: 30px; }
    .doc-nav { position: sticky; top: 20px; display: flex; flex-direction: column; gap: 8px; }
    .doc-nav-item { padding: 10px 14px; color: var(--text-2); border-radius: 8px; font-size: 13px; font-weight: 500; transition: all 0.2s; border: 1px solid transparent; text-decoration: none; }
    .doc-nav-item:hover { background: rgba(0,212,255,0.05); color: var(--text-1); }
    .doc-nav-item.active { background: rgba(0,212,255,0.1); color: var(--cyan); border-color: rgba(0,212,255,0.2); }
    
    .doc-section { margin-bottom: 40px; padding-bottom: 30px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .doc-section h2 { font-family: var(--fh); font-size: 24px; color: var(--cyan); margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid rgba(0,212,255,0.2); }
    .doc-section h4 { font-family: var(--fh); font-size: 18px; margin: 24px 0 16px 0; color: var(--text-1); }
    .doc-section p, .doc-section li { color: var(--text-2); line-height: 1.7; font-size: 14px; }
    
    .doc-component { background: rgba(0,212,255,0.03); border-left: 3px solid var(--cyan); padding: 16px 20px; margin: 16px 0; border-radius: 0 8px 8px 0; }
    
    .regime-doc { background: var(--panel); padding: 20px; margin: 16px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid var(--cyan); }
    .regime-doc h4 { margin-top: 0; }
    
    .strategy-box { background: var(--panel); padding: 20px; margin: 16px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid #fff; }
    
    .doc-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }
    .doc-table th { text-align: left; padding: 12px 16px; background: rgba(255,255,255,0.04); color: var(--text-1); border-bottom: 1px solid rgba(255,255,255,0.1); }
    .doc-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); color: var(--text-2); }
    
    .alert-info { background: rgba(0,212,255,0.1); border: 1px solid rgba(0,212,255,0.2); padding: 16px; border-radius: 8px; margin: 20px 0; color: var(--text-1); }
    code { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; font-family: var(--fm); font-size: 12px; color: var(--cyan); }
    pre { background: #020810; padding: 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); overflow-x: auto; margin: 16px 0; }
    pre code { background: none; padding: 0; color: #a5d6ff; }
    
    .faq-item { margin: 20px 0; padding: 20px; background: var(--panel); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
    .faq-item .question { font-family: var(--fh); font-size: 16px; color: var(--cyan); margin-bottom: 10px; font-weight: 700; }
</style>
<div class="card" style="max-width: 100%;">
    <h1 class="h1">Documentation</h1>
    <p class="p">Complete guide to using the Market Regime Detection Engine</p>
    
    <div class="doc-layout">
"""

# Replace the specific header and sidebar container part manually
html = re.sub(r'<div class="documentation-container[^>]*>.*?<!-- Main Content -->\s*<div class="col-lg-9">', styles + """
        <!-- Sidebar Navigation -->
        <div>
            <div class="doc-nav">
                <a href="#getting-started" class="doc-nav-item active">Getting Started</a>
                <a href="#dashboard" class="doc-nav-item">Dashboard Guide</a>
                <a href="#analysis" class="doc-nav-item">Analysis Tools</a>
                <a href="#regimes" class="doc-nav-item">Market Regimes</a>
                <a href="#strategies" class="doc-nav-item">Trading Strategies</a>
                <a href="#algorithms" class="doc-nav-item">Algorithms</a>
                <a href="#api" class="doc-nav-item">API Reference</a>
                <a href="#faq" class="doc-nav-item">FAQ</a>
            </div>
        </div>
        
        <!-- Main Content -->
        <div>
""", html, flags=re.DOTALL)

# Close the new divs at the bottom
html = html.replace('                </div>\n            </div>\n        </div>\n    </section>\n</div>', '        </div>\n    </div>\n</div>')

# Replace table classes
html = html.replace('<table class="table table-sm table-bordered">', '<table class="doc-table">')
html = html.replace('<div class="table-responsive">', '')
html = html.replace('</div>\n                        </div>', '</div>\n                        ')

# Remove generic Bootstrap classes sprinkled around
html = html.replace('class="mb-4"', '')
html = html.replace('class="mb-3"', '')
html = html.replace('class="card mb-4"', 'class="doc-section"')
html = html.replace('class="card-body"', '')
html = html.replace('<h3 class="card-title h4 mb-3">', '<h2>')
html = html.replace('</h3>', '</h2>')
html = html.replace('<h3 class="card-title h4">', '<h2>')

with open('templates/documentation.html', 'w', encoding='utf-8') as f:
    f.write(html)
