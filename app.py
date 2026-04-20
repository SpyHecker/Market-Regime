from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import os
import sys
import json
import math
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import uuid

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configuration
app.config['SECRET_KEY'] = 'market-regime-detection-secret-key'
app.config['DEBUG'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days

# ===========================
# UTILITY FUNCTIONS
# ===========================

def clean_nan_values(obj):
    """Remove NaN and Infinity values from dict/list recursively"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.floating, np.integer)):
        if isinstance(obj, np.floating) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return float(obj) if isinstance(obj, np.floating) else int(obj)
    elif isinstance(obj, (bool, np.bool_)):
        # Convert numpy booleans to Python bool
        return bool(obj)
    return obj

# Global analyzer instance for NIFTY50
analyzer = None
last_update_time = None

# ===========================
# SCHEDULER & REAL-TIME UPDATES
# ===========================

scheduler = BackgroundScheduler()

def refresh_market_data():
    """Refresh analyzer with latest market data"""
    global analyzer, last_update_time
    
    try:
        if analyzer is None:
            print("✗ Analyzer not initialized - skipping refresh")
            return
        
        # Fetch new data and reanalyze
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n📊 [LIVE UPDATE] Refreshing market data at {now}...")
        
        from dsbda import DataCollector, DataPreprocessor, RegimeDetector
        
        # Store old data length to verify fetch
        old_len = len(analyzer.df)
        
        # Fetch latest data
        print(f"  Fetching ^NSEI data (period=5y)...")
        raw_data = DataCollector.fetch_data('^NSEI', period='5y')
        
        if raw_data is None or len(raw_data) == 0:
            print(f"  ✗ Failed to fetch data - yfinance unavailable")
            return
        
        processed_data = DataPreprocessor.preprocess(raw_data)
        new_len = len(processed_data)
        
        # Verify data is fresh
        last_date_old = analyzer.df.index[-1]
        last_date_new = processed_data.index[-1]
        
        print(f"  Data: {old_len} → {new_len} points")
        print(f"  Last date: {last_date_old.date()} → {last_date_new.date()}")
        
        # Refit detector with new data
        detector = RegimeDetector(4)
        detector.fit(processed_data, analyzer.features)
        processed_data['Regime'] = detector.predict(processed_data, analyzer.features)
        
        # Update analyzer
        analyzer.df = processed_data
        analyzer.detector = detector
        
        # Update timestamp
        last_update_time = datetime.now()
        
        # Show current status
        regime = analyzer.get_current_regime()
        conf_str = f"{regime['confidence']*100:.0f}%"
        trans_marker = "⚠️ TRANSITION" if regime.get('is_transitioning') else "✓"
        
        print(f"✓ Market Update Complete {trans_marker}")
        print(f"  Regime: {regime['regime']} (Conf: {conf_str})")
        print(f"  Volatility: {regime['volatility']*100:.2f}% | Return: {regime['return']*100:.3f}%")
        print(f"  Last Update: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"✗ Error refreshing market data: {str(e)}")
        import traceback
        traceback.print_exc()

# ===========================
# INITIALIZATION
# ===========================

def initialize_analyzer():
    """Initialize analyzer on app startup"""
    global analyzer, last_update_time
    
    try:
        print("\n" + "="*60)
        print("Initializing Market Analyzer for NIFTY50...")
        print("="*60)
        
        from dsbda import analyze_market
        
        analyzer = analyze_market(ticker='^NSEI', period='5y')
        
        if analyzer:
            regime = analyzer.get_current_regime()
            last_update_time = datetime.now()
            
            print(f"✓ Analyzer initialized!")
            print(f"  Current Regime: {regime['regime']} (Confidence: {regime['confidence']*100:.0f}%)")
            print(f"  Volatility: {regime['volatility']*100:.2f}% | Daily Return: {regime['return']*100:.3f}%")
            print(f"  Data points: {len(analyzer.df)} | Last date: {regime['date']}")
            print(f"  Detector fitted: {'Yes' if analyzer.detector else 'No'}")
            print(f"  Last Update: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Start scheduler for real-time updates
            if not scheduler.running:
                scheduler.add_job(
                    refresh_market_data,
                    trigger=IntervalTrigger(minutes=5),
                    id='market_data_refresh',
                    name='Refresh Market Data Every 5 Minutes',
                    replace_existing=True
                )
                scheduler.start()
                print(f"\n✓ APScheduler started - next refresh in 5 minutes")
                print(f"✓ Live polling enabled - frontend checks every 10 seconds")
            else:
                print(f"\n⚠️ APScheduler already running")
            
            return True
        else:
            print("✗ Failed to initialize analyzer")
            return False
    
    except Exception as e:
        print(f"✗ Error initializing analyzer: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ===========================
# ROUTES
# ===========================

@app.route('/home')
def home():
    """Home/landing page"""
    return render_template('home.html')

@app.route('/')
def index():
    """Main entry point - redirects to dashboard if logged in, home if not"""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('home'))

@app.route('/auth', methods=['GET', 'POST'])
def auth(mode='login'):
    """Authentication page - login or register"""
    if request.method == 'POST':
        action = request.form.get('action', 'login')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        if action == 'login':
            # Simple demo login - in production use proper authentication
            if email and password:
                session['user_id'] = str(uuid.uuid4())
                session['user_name'] = email.split('@')[0].title()
                session['user_email'] = email
                session.permanent = True
                return redirect(url_for('dashboard'))
        elif action == 'register':
            # Simple demo signup - in production use proper registration
            if email and password:
                session['user_id'] = str(uuid.uuid4())
                session['user_name'] = email.split('@')[0].title()
                session['user_email'] = email
                session.permanent = True
                return redirect(url_for('dashboard'))
    
    mode = request.args.get('mode', 'login')
    return render_template('auth.html', mode=mode)

@app.route('/logout', methods=['POST'])
def logout():
    """Logout - clear session and redirect to home"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page - requires authentication"""
    if not session.get('user_id'):
        return redirect(url_for('auth', mode='login'))
    
    return render_template('dashboard.html')

@app.route('/app/<page>')
def app_page(page):
    """App sub-pages - requires authentication"""
    if not session.get('user_id'):
        return redirect(url_for('auth', mode='login'))
    
    # Page title mappings
    page_titles = {
        'regime': 'Regime Explorer',
        'ml': 'ML Insights',
        'reports': 'History & Reports',
        'profile': 'Profile',
        'settings': 'Settings',
        'docs': 'Documentation'
    }
    
    page_subtitles = {
        'regime': 'Explore different market regimes and their characteristics',
        'ml': 'Machine learning insights and predictions',
        'reports': 'Historical analysis and detailed reports',
        'profile': 'Manage your profile information',
        'settings': 'Configure your preferences',
        'docs': 'API documentation and guides'
    }
    
    page_title = page_titles.get(page, 'Feature')
    page_subtitle = page_subtitles.get(page, 'Coming soon...')
    
    # Check if a specific template exists for this page
    template_map = {
        'regime': 'regime.html',
        'ml': 'ml.html',
        'reports': 'reports.html',
        'profile': 'profile.html',
        'settings': 'settings.html',
        'docs': 'documentation.html'
    }
    
    template_name = template_map.get(page, 'app_page.html')
    
    return render_template(template_name, 
                         page_title=page_title,
                         page_subtitle=page_subtitle,
                         active_page=page)

@app.route('/analysis')
def analysis():
    """Analysis page"""
    return render_template('analysis.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/documentation')
def documentation():
    """Documentation page"""
    return render_template('documentation.html')

# ===========================
# API ENDPOINTS
# ===========================

@app.route('/api/current_regime', methods=['GET'])
def get_current_regime():
    """Get current market regime"""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500
        
        regime_info = analyzer.get_current_regime()
        
        if regime_info is None:
            return jsonify({'error': 'No data available'}), 500
        
        data = {
            'market': 'NIFTY 50 Index',
            'regime': regime_info['regime'],
            'confidence': regime_info['confidence'],
            'is_transitioning': regime_info.get('is_transitioning', False),
            'price': regime_info['price'],
            'volatility': round(regime_info['volatility'] * 100, 2),
            'daily_return': round(regime_info['return'] * 100, 3),
            'timestamp': regime_info['date'],
            'last_updated': last_update_time.isoformat() if last_update_time else None,
            'is_live': True
        }
        
        return jsonify(clean_nan_values(data)), 200
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical_analysis', methods=['GET'])
def get_historical_analysis():
    """Get historical regime analysis"""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500
        
        days = request.args.get('days', 252, type=int)
        
        stats = analyzer.get_regime_statistics(lookback_days=days)
        transitions = analyzer.get_regime_transitions(lookback_days=days)
        historical = analyzer.get_historical_data(days=days)
        
        data = {
            'market': 'NIFTY 50 Index',
            'period_days': days,
            'regimes': stats,
            'transitions': transitions,
            'historical': historical,
            'last_updated': last_update_time.isoformat() if last_update_time else None,
            'is_live': True
        }
        return jsonify(clean_nan_values(data)), 200
    
    except Exception as e:
        print(f"Error in get_historical_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy', methods=['GET'])
def get_strategy():
    """Get trading strategy dynamically blended with live signals"""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500

        regime_info = analyzer.get_current_regime()
        strategy = analyzer.build_strategy()

        data = {
            'market': 'NIFTY 50 Index',
            'regime': regime_info['regime'],
            'confidence': regime_info['confidence'],
            'is_transitioning': regime_info.get('is_transitioning', False),
            'strategy': strategy,
            'timestamp': regime_info['date'],
            'last_updated': last_update_time.isoformat() if last_update_time else None,
            'is_live': True
        }
        return jsonify(clean_nan_values(data)), 200

    except Exception as e:
        print(f"Error in get_strategy: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get detailed statistics"""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500
        
        days = request.args.get('days', 252, type=int)
        
        stats = analyzer.get_regime_statistics(lookback_days=days)
        transitions = analyzer.get_regime_transitions(lookback_days=days)
        regime_info = analyzer.get_current_regime()
        
        data = {
            'market': 'NIFTY 50 Index',
            'period_days': days,
            'current_regime': regime_info['regime'],
            'current_price': regime_info['price'],
            'current_volatility': round(regime_info['volatility'] * 100, 2),
            'regimes': stats,
            'transitions': transitions,
            'timestamp': datetime.now().isoformat(),
            'last_updated': last_update_time.isoformat() if last_update_time else None,
            'is_live': True
        }
        return jsonify(clean_nan_values(data)), 200
    
    except Exception as e:
        print(f"Error in get_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get supported markets"""
    return jsonify({
        'markets': ['NIFTY 50 Index (^NSEI)'],
        'default': '^NSEI'
    }), 200

@app.route('/api/ml_metrics', methods=['GET'])
def get_ml_metrics():
    """Expose real unsupervised K-Means cluster analytics."""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500

        m = analyzer.get_ml_metrics()
        if not m:
            return jsonify({'error': 'No metrics available'}), 500

        payload = {
            'model': 'K-Means (Unsupervised)',
            'algorithm': f"K-Means, k={m['n_clusters']}",
            'silhouette_score': m['silhouette_score'],
            'davies_bouldin': m['davies_bouldin'],
            'inertia': m['inertia'],
            'cluster_health': m['cluster_health'],
            'mean_separation': m['mean_separation'],
            'drift': m['drift'],
            'per_cluster': m['per_cluster'],
            'top_features': m['top_features'],
            'regime_distribution': m['regime_distribution'],
            'imbalance': m['imbalance'],
            'feature_names': m['feature_names'],
            'n_features': m['n_features'],
            'n_clusters': m['n_clusters'],
            'datapoints': m['datapoints'],
            'verdict': m['verdict'],
            'training_info': {
                'timestamp': m['timestamp'],
                'datapoints': m['datapoints'],
                'window_years': 5,
                'mode': 'Streaming Live (refit every 5 minutes)'
            },
            'last_updated': last_update_time.isoformat() if last_update_time else None,
            'is_live': True
        }
        return jsonify(clean_nan_values(payload)), 200
    except Exception as e:
        print(f"Error in get_ml_metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Return dynamically generated report summaries."""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500

        reports = analyzer.generate_reports()
        return jsonify(clean_nan_values({
            'market': 'NIFTY 50 Index',
            'reports': reports,
            'last_updated': last_update_time.isoformat() if last_update_time else None,
            'is_live': True
        })), 200
    except Exception as e:
        print(f"Error in get_reports: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<report_id>', methods=['GET'])
def download_report(report_id):
    """Return a single report in the requested format (json or html)."""
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized'}), 500

        fmt = request.args.get('format', 'json').lower()
        reports = analyzer.generate_reports()
        match = next((r for r in reports if r['id'] == report_id), None)
        if match is None:
            return jsonify({'error': f'Report {report_id} not found'}), 404

        if fmt == 'html':
            rows = ''.join(
                f"<tr><td>{k.replace('_', ' ').title()}</td><td>{v}</td></tr>"
                for k, v in match['metrics'].items()
            )
            highlights_html = ''.join(f"<li>{h}</li>" for h in match['highlights'])
            html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{match['title']}</title>
<style>body{{font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#111;}}
h1{{font-size:22px;margin:0 0 4px;}}h2{{font-size:15px;margin-top:24px;color:#333;}}
.meta{{color:#666;font-size:12px;margin-bottom:20px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}}
td{{padding:6px 8px;border-bottom:1px solid #eee;}} td:first-child{{color:#555;width:45%;}}
.summary{{background:#f6f9fc;padding:14px;border-left:3px solid #00a8ff;border-radius:4px;line-height:1.55;font-size:13px;}}
ul{{padding-left:20px;}}</style></head><body>
<h1>{match['icon']} {match['title']}</h1>
<div class="meta">NIFTY 50 Index · window: {match['actual_days']} trading days ·
generated {match['generated']}</div>
<h2>Summary</h2><div class="summary">{match['summary']}</div>
<h2>Key metrics</h2><table>{rows}</table>
<h2>Regime highlights</h2><ul>{highlights_html}</ul>
</body></html>"""
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

        return jsonify(clean_nan_values(match)), 200
    except Exception as e:
        print(f"Error in download_report: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/profile', methods=['GET', 'POST'])
def manage_profile():
    """Get/update user profile"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            session.update({
                'user_name': data.get('name', session.get('user_name')),
                'user_email': data.get('email', session.get('user_email'))
            })
            return jsonify({'success': True, 'message': 'Profile updated'}), 200
        
        profile = {
            'name': session.get('user_name', 'User'),
            'email': session.get('user_email', 'user@example.com'),
            'username': 'trader_' + str(session.get('user_id', ''))[-4:],
            'account_type': 'Premium',
            'joined': '2026-01-15',
            'last_login': datetime.now().isoformat()
        }
        return jsonify(profile), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    """Get/update user settings"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            session['settings'] = data
            return jsonify({'success': True, 'message': 'Settings updated'}), 200
        
        settings = session.get('settings', {
            'theme': 'dark',
            'notifications_enabled': True,
            'email_alerts': True,
            'push_alerts': False,
            'refresh_interval': 10,
            'default_timeframe': '252',
            'analysis_depth': 'detailed'
        })
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===========================
# ERROR HANDLERS
# ===========================

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ===========================
# CONTEXT PROCESSOR
# ===========================

@app.context_processor
def inject_config():
    return {
        'app_name': 'Market Regime Detector',
        'current_year': datetime.now().year,
        'version': '2.0.0',
        'status': 'Live with Real Data',
        'session': session,
        'user_name': session.get('user_name', 'User'),
        'user_email': session.get('user_email', ''),
        'user_id': session.get('user_id'),
        'active_page': 'dashboard'
    }

# ===========================
# APP STARTUP
# ===========================

if __name__ == '__main__':
    print("""
    ========================================================
    Multi-Regime Market Detection Engine - LIVE
    NIFTY50 Analysis
    ========================================================
    """)
    
    # Initialize analyzer before starting server
    initialize_analyzer()
    
    print("\n" + "="*60)
    print("Starting Flask server on http://localhost:5000")
    print("="*60)
    
    app.run(
        host='localhost',
        port=5000,
        debug=False,
        use_reloader=False
    )
