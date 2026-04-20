"""
DSBDA - Data Science Big Data Analytics Backend
Multi-Regime Market Detection Engine
Real or synthetic data analysis with K-Means clustering
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, silhouette_samples, davies_bouldin_score
from datetime import datetime, timedelta
import yfinance as yf


class DataCollector:
    """Fetches real or synthetic market data"""
    
    @staticmethod
    def fetch_data(ticker, period='5y'):
        """Fetch market data with fallback to synthetic data"""
        print(f"Fetching {ticker} data for period {period}...")
        
        # Try real data first
        try:
            # Add User-Agent header to avoid blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            data = yf.download(ticker, period=period, progress=False)
            if data.empty:
                raise ValueError("Empty data")
            
            if isinstance(data.columns, pd.MultiIndex):
                data = data[ticker]
            
            print(f"✓ Downloaded {len(data)} real records")
            return data
        except Exception as e:
            print(f"⚠ Using synthetic data for {ticker} (Error: {str(e)[:50]}...)")
            return DataCollector._generate_synthetic(ticker, period)
    
    @staticmethod
    def _generate_synthetic(ticker, period):
        """Generate realistic synthetic OHLCV data"""
        period_days = {'5y': 1260, '3y': 756, '2y': 504, '1y': 252, '6mo': 126}
        days = period_days.get(period, 1260)
        
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.Timedelta(days=days)
        dates = pd.bdate_range(start=start_date, end=end_date)
        
        # Initial prices
        init_prices = {'NIFTY50.NS': 20000, '^BSESN': 65000, 'BANKNIFTY.NS': 45000, '^GSPC': 5000}
        price = init_prices.get(ticker, 100)
        
        np.random.seed(42)
        prices = [price]
        
        for _ in range(len(dates)-1):
            ret = np.random.normal(0.0003, 0.01)
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame({
            'Open': prices,
            'High': [p * 1.005 for p in prices],
            'Low': [p * 0.995 for p in prices],
            'Close': [p * (1 + np.random.normal(0, 0.003)) for p in prices],
            'Adj Close': [p * (1 + np.random.normal(0, 0.003)) for p in prices],
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        return df


class DataPreprocessor:
    """Cleans and prepares data for analysis"""
    
    @staticmethod
    def preprocess(df):
        """Preprocess OHLCV data"""
        df = df.copy()
        
        # Handle missing values
        df = df.ffill().bfill()
        
        # Ensure columns
        if len(df.columns) == 6:
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
        # Calculate returns
        df['Log_Return'] = np.log(df['Adj Close'] / df['Adj Close'].shift(1)).fillna(0)
        df['Return'] = df['Adj Close'].pct_change().fillna(0)
        
        # Volatility
        df['Volatility'] = df['Log_Return'].rolling(20).std().fillna(df['Log_Return'].std())
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = (df['Volume'] / df['Volume_MA']).fillna(1)
        
        # Moving averages
        df['MA_50'] = df['Close'].rolling(50).mean()
        df['Price_to_MA50'] = (df['Close'] / df['MA_50']).fillna(1)
        
        # Momentum and RSI
        df['Momentum'] = (df['Close'].diff(20) / df['Close'].shift(20)).fillna(0)
        df['Vol_of_Vol'] = df['Volatility'].rolling(20).std().fillna(df['Volatility'].std())
        df['RSI'] = DataPreprocessor._calc_rsi(df['Close'].values)
        
        return df.dropna()
    
    @staticmethod
    def _calc_rsi(prices, period=14):
        """Calculate RSI"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 1
        rsi = np.zeros(len(prices))
        rsi[:period] = 100 - 100 / (1 + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            upval = delta if delta > 0 else 0
            downval = -delta if delta < 0 else 0
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 1
            rsi[i] = 100 - 100 / (1 + rs)
        
        return rsi


class RegimeDetector:
    """K-Means based regime detection"""
    
    def __init__(self, n_regimes=4):
        self.kmeans = KMeans(n_clusters=n_regimes, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.cluster_map = {}
    
    def fit(self, df, features):
        """Fit K-Means model"""
        X = df[features].values
        X_scaled = self.scaler.fit_transform(X)
        self.kmeans.fit(X_scaled)
        
        # Map clusters to regimes
        predictions = self.kmeans.predict(X_scaled)
        self._map_clusters(df, features, predictions)
    
    def _map_clusters(self, df, features, predictions):
        """Map clusters to Bull/Bear/Sideways/Volatile"""
        returns = df['Log_Return'].values
        volatility = df['Volatility'].values
        
        cluster_stats = {}
        for cluster in range(4):
            mask = predictions == cluster
            cluster_stats[cluster] = {
                'return': returns[mask].mean(),
                'volatility': volatility[mask].mean()
            }
        
        # Sort by return to get Bull (highest) and Bear (lowest)
        sorted_clusters = sorted(cluster_stats.items(), key=lambda x: x[1]['return'])
        
        self.cluster_map = {
            sorted_clusters[-1][0]: 'Bull',      # Highest return
            sorted_clusters[0][0]: 'Bear',       # Lowest return
            sorted_clusters[1][0]: 'Sideways',   # Mid-low
            sorted_clusters[2][0]: 'Volatile'    # Mid-high
        }
    
    def predict(self, df, features):
        """Predict regimes"""
        X = df[features].values
        X_scaled = self.scaler.transform(X)
        clusters = self.kmeans.predict(X_scaled)
        return np.array([self.cluster_map.get(c, 'Sideways') for c in clusters])


class MarketAnalyzer:
    """Main market analysis orchestrator"""
    
    def __init__(self, ticker='NIFTY50.NS', period='5y'):
        self.ticker = ticker
        self.period = period
        self.df = None
        self.detector = None  # Store detector for distance-based confidence
        
        # Collect and process data
        raw_data = DataCollector.fetch_data(ticker, period)
        self.df = DataPreprocessor.preprocess(raw_data)
        
        # Define features
        self.features = ['Log_Return', 'Volatility', 'Volume_Ratio', 
                        'Momentum', 'Vol_of_Vol', 'RSI', 'Price_to_MA50']
        
        # Detect regimes
        self.detector = RegimeDetector(4)
        self.detector.fit(self.df, self.features)
        self.df['Regime'] = self.detector.predict(self.df, self.features)
        
        print(f"✓ {ticker} analyzer initialized with {len(self.df)} data points")
    
    def get_distance_based_confidence(self):
        """Calculate confidence using K-Means distance to nearest centroid"""
        if self.df is None or len(self.df) == 0 or self.detector is None:
            return 1.0
        
        try:
            current = self.df.iloc[-1]
            features_list = self.features
            
            # Get current feature vector
            X_current = current[features_list].values.reshape(1, -1)
            X_scaled = self.detector.scaler.transform(X_current)
            
            # Get distances to all centroids (in scaled feature space)
            distances = self.detector.kmeans.transform(X_scaled)[0]
            
            # Find nearest and second-nearest distances
            sorted_distances = np.sort(distances)
            nearest_dist = sorted_distances[0]
            second_nearest_dist = sorted_distances[1]
            
            # Confidence = 1 - (nearest / second_nearest)
            # If very close to multiple centroids, confidence is low
            # If far from all (high nearest_dist), but furthest from second, confidence is still good
            if second_nearest_dist == 0:
                # Point exactly at a centroid
                confidence = 1.0
            else:
                # Normalize by second nearest distance to get ratio
                ratio = nearest_dist / second_nearest_dist
                # Confidence is higher when ratio is lower (far from second centroid)
                confidence = max(0.01, 1 - ratio)  # Range: 0.01 to 1
            
            return round(confidence, 3)
        except Exception as e:
            return 1.0
            
    def get_ml_metrics(self):
        """Calculate real unsupervised cluster analytics for K-Means."""
        if self.df is None or len(self.df) == 0 or self.detector is None:
            return {}

        X = self.df[self.features].values
        X_scaled = self.detector.scaler.transform(X)
        predictions = self.detector.kmeans.predict(X_scaled)
        centroids = self.detector.kmeans.cluster_centers_

        # Global silhouette + per-sample silhouettes for per-cluster density.
        try:
            sil_score = float(silhouette_score(X_scaled, predictions))
            sil_samples = silhouette_samples(X_scaled, predictions)
        except Exception:
            sil_score = 0.0
            sil_samples = np.zeros(len(predictions))

        # Davies-Bouldin: lower is better; clamp for display.
        try:
            db_index = float(davies_bouldin_score(X_scaled, predictions))
        except Exception:
            db_index = 0.0

        # Inertia (within-cluster sum of squares) — real K-Means objective.
        inertia = float(self.detector.kmeans.inertia_)

        # Per-cluster stats: size, mean silhouette (density), centroid distance stats.
        per_cluster = []
        for c in range(self.detector.kmeans.n_clusters):
            mask = predictions == c
            size = int(mask.sum())
            if size == 0:
                continue
            cluster_points = X_scaled[mask]
            intra_dist = float(np.mean(np.linalg.norm(cluster_points - centroids[c], axis=1)))
            cluster_sil = float(np.mean(sil_samples[mask])) if size > 0 else 0.0
            per_cluster.append({
                'label': self.detector.cluster_map.get(c, f'Cluster {c}'),
                'size': size,
                'share_pct': round(size / len(predictions) * 100, 1),
                'mean_silhouette': round(cluster_sil, 3),
                'intra_dist': round(intra_dist, 3)
            })
        per_cluster.sort(key=lambda r: r['size'], reverse=True)

        # Inter-centroid separation (mean pairwise distance between centroids).
        inter_dists = []
        for i in range(len(centroids)):
            for j in range(i + 1, len(centroids)):
                inter_dists.append(float(np.linalg.norm(centroids[i] - centroids[j])))
        mean_separation = float(np.mean(inter_dists)) if inter_dists else 0.0

        # Feature importance via centroid variance across clusters.
        centroid_vars = np.var(centroids, axis=0)
        total_var = float(np.sum(centroid_vars)) + 1e-9
        importances = (centroid_vars / total_var) * 100
        top_features = [
            {'name': f, 'importance': round(float(imp), 1)}
            for f, imp in zip(self.features, importances)
        ]
        top_features.sort(key=lambda x: x['importance'], reverse=True)

        # Regime distribution counts.
        regimes = pd.Series([self.detector.cluster_map.get(p, 'Sideways') for p in predictions])
        counts = regimes.value_counts().to_dict()
        regime_distribution = {r: int(counts.get(r, 0)) for r in ['Bull', 'Bear', 'Sideways', 'Volatile']}
        imbalance = round(max(regime_distribution.values()) / (min([v for v in regime_distribution.values() if v > 0] or [1])), 2)

        # Cluster health: normalised silhouette 0-100 (sil in [-1,1]).
        cluster_health = round(((sil_score + 1) / 2) * 100, 1)

        # Data drift proxy: deviation of last-20-day feature means from full-history means.
        try:
            recent = X_scaled[-20:]
            overall_mean = X_scaled.mean(axis=0)
            drift = float(np.mean(np.abs(recent.mean(axis=0) - overall_mean)))
        except Exception:
            drift = 0.0

        # Model verdict based on silhouette & separation.
        if sil_score >= 0.35:
            verdict = 'Well-separated clusters'
        elif sil_score >= 0.15:
            verdict = 'Moderately separated clusters'
        else:
            verdict = 'Overlapping clusters — consider refitting'

        return {
            'silhouette_score': round(sil_score, 3),
            'davies_bouldin': round(db_index, 3),
            'inertia': round(inertia, 2),
            'cluster_health': cluster_health,
            'mean_separation': round(mean_separation, 3),
            'drift': round(drift, 4),
            'per_cluster': per_cluster,
            'top_features': top_features,
            'regime_distribution': regime_distribution,
            'imbalance': imbalance,
            'n_clusters': int(self.detector.kmeans.n_clusters),
            'n_features': len(self.features),
            'feature_names': list(self.features),
            'datapoints': len(self.df),
            'verdict': verdict,
            'timestamp': datetime.now().strftime('%b %d, %Y %I:%M %p')
        }

    def generate_reports(self):
        """Dynamically generate report summaries for 7 / 30 / 90 day windows."""
        if self.df is None or len(self.df) == 0:
            return []

        windows = [
            ('daily', 'Daily Summary Report', '📋', 7,
             'Regime breakdown, price action and volatility for the last trading week'),
            ('weekly', 'Weekly Performance Report', '📊', 30,
             'Month-over-month regime transitions, returns and volatility profile'),
            ('monthly', 'Monthly Analysis Report', '📈', 90,
             'Quarterly regime overview with drawdowns and Sharpe ratio by regime'),
            ('regime', 'Regime Transition Report', '🎯', 60,
             'Recent regime shifts and their realised impact on price and volatility')
        ]

        reports = []
        for rid, title, icon, days, desc in windows:
            window = self.df.iloc[-days:] if days < len(self.df) else self.df
            if len(window) == 0:
                continue

            start_price = float(window['Close'].iloc[0])
            end_price = float(window['Close'].iloc[-1])
            pct_change = (end_price - start_price) / start_price * 100 if start_price else 0.0
            max_dd = self._max_drawdown(window['Close'].values)
            regime_counts = window['Regime'].value_counts().to_dict()
            dominant_regime = max(regime_counts, key=regime_counts.get) if regime_counts else 'N/A'
            avg_vol = float(window['Volatility'].mean()) * 100

            # Count regime switches.
            switches = int((window['Regime'] != window['Regime'].shift()).sum() - 1)

            summary = (
                f"Over the last {len(window)} trading days, NIFTY 50 moved "
                f"{pct_change:+.2f}% ({start_price:.2f} → {end_price:.2f}). "
                f"The dominant regime was {dominant_regime} "
                f"({regime_counts.get(dominant_regime, 0)} days, "
                f"{regime_counts.get(dominant_regime, 0) / len(window) * 100:.0f}% of the window). "
                f"Average annualised volatility sat at {avg_vol:.2f}% with a maximum drawdown of {max_dd:.2f}%. "
                f"{switches} regime transition{'s' if switches != 1 else ''} were observed."
            )

            highlights = [
                f"{regime}: {count} days ({count / len(window) * 100:.0f}%)"
                for regime, count in sorted(regime_counts.items(), key=lambda x: -x[1])
            ]

            reports.append({
                'id': rid,
                'icon': icon,
                'title': title,
                'description': desc,
                'window_days': days,
                'actual_days': len(window),
                'generated': datetime.now().isoformat(),
                'metrics': {
                    'start_price': round(start_price, 2),
                    'end_price': round(end_price, 2),
                    'pct_change': round(pct_change, 2),
                    'max_drawdown_pct': round(max_dd, 2),
                    'avg_volatility_pct': round(avg_vol, 2),
                    'regime_switches': switches,
                    'dominant_regime': dominant_regime
                },
                'highlights': highlights,
                'summary': summary
            })
        return reports

    @staticmethod
    def _max_drawdown(prices):
        """Return max drawdown over a price series as a negative percentage."""
        if len(prices) == 0:
            return 0.0
        running_max = np.maximum.accumulate(prices)
        drawdowns = (prices - running_max) / running_max
        return float(drawdowns.min()) * 100

    def build_strategy(self):
        """Produce a live, metric-blended trading strategy suggestion."""
        if self.df is None or len(self.df) == 0:
            return None

        regime_info = self.get_current_regime()
        if regime_info is None:
            return None

        current = self.df.iloc[-1]
        vol_pct = float(current['Volatility']) * 100
        rsi = float(current['RSI'])
        momentum = float(current['Momentum']) * 100
        price_to_ma = float(current['Price_to_MA50'])
        vol_of_vol = float(current['Vol_of_Vol']) * 100
        volatility_series = self.df['Volatility'].tail(252)
        vol_median = float(volatility_series.median()) * 100 if len(volatility_series) else vol_pct
        vol_spike = vol_pct > vol_median * 1.5

        regime = regime_info['regime']
        confidence = regime_info['confidence']
        transitioning = regime_info.get('is_transitioning', False)

        # Baseline templates per regime.
        base = {
            'Bull': {
                'primary': 'Trend Following',
                'secondary': ['Momentum Trading', 'Long Positions'],
                'description': 'Uptrend confirmed. Ride momentum with disciplined stops.',
                'risk_level': 'Low to Medium',
                'actions': ['Buy on Support', 'Hold Long', 'Trailing Stops']
            },
            'Bear': {
                'primary': 'Short Selling',
                'secondary': ['Defensive', 'Hedging'],
                'description': 'Downtrend in force. Protect capital and fade rallies.',
                'risk_level': 'Medium to High',
                'actions': ['Sell on Resistance', 'Stop Losses', 'Reduce Exposure']
            },
            'Sideways': {
                'primary': 'Range Trading',
                'secondary': ['Mean Reversion'],
                'description': 'Price compressed inside a range — fade extremes.',
                'risk_level': 'Low',
                'actions': ['Buy Support', 'Sell Resistance', 'Tight Stops']
            },
            'Volatile': {
                'primary': 'Hedging',
                'secondary': ['Risk Management', 'Options'],
                'description': 'High volatility regime — size down and hedge tails.',
                'risk_level': 'High',
                'actions': ['Reduce Size', 'Protective Puts', 'Cash Reserve']
            }
        }.get(regime, None)

        if base is None:
            base = {
                'primary': 'Neutral', 'secondary': [], 'description': 'No clear regime.',
                'risk_level': 'Medium', 'actions': []
            }

        strategy = {**base, 'secondary': list(base['secondary']), 'actions': list(base['actions'])}
        modifiers = []

        if vol_spike:
            modifiers.append(f'Volatility spike: current {vol_pct:.2f}% vs median {vol_median:.2f}%')
            if regime == 'Bull':
                strategy['primary'] = 'Cautious Longs'
                strategy['description'] = 'Uptrend intact but volatility is elevated — scale in slowly.'
                strategy['risk_level'] = 'Medium'
                strategy['actions'].append('Half-size entries')
            elif regime == 'Bear':
                strategy['actions'].append('Widen stops to avoid noise')

        if rsi >= 70:
            modifiers.append(f'RSI overbought ({rsi:.1f})')
            strategy['actions'].append('Trim into strength')
        elif rsi <= 30:
            modifiers.append(f'RSI oversold ({rsi:.1f})')
            strategy['actions'].append('Look for reversal setups')

        if momentum > 5:
            modifiers.append(f'Strong positive momentum (+{momentum:.2f}% / 20d)')
        elif momentum < -5:
            modifiers.append(f'Strong negative momentum ({momentum:.2f}% / 20d)')

        if price_to_ma > 1.05 and regime == 'Bull':
            modifiers.append('Price stretched >5% above MA50 — expect mean reversion')
            strategy['actions'].append('Tighten trailing stop')
        elif price_to_ma < 0.95 and regime == 'Bear':
            modifiers.append('Price stretched >5% below MA50')

        if transitioning:
            modifiers.append(f'Regime transition detected (confidence {confidence*100:.0f}%)')
            strategy['description'] = strategy['description'] + ' Regime is transitioning — reduce conviction.'
            strategy['risk_level'] = 'Medium to High'
            strategy['actions'].insert(0, 'Hold reduced position until confirmation')

        strategy['modifiers'] = modifiers
        strategy['signals'] = {
            'rsi': round(rsi, 2),
            'momentum_20d_pct': round(momentum, 3),
            'volatility_pct': round(vol_pct, 3),
            'vol_median_pct': round(vol_median, 3),
            'vol_spike': bool(vol_spike),
            'price_to_ma50': round(price_to_ma, 4),
            'vol_of_vol_pct': round(vol_of_vol, 3)
        }
        return strategy
    
    def get_current_regime(self):
        """Get current regime"""
        if self.df is None or len(self.df) == 0:
            return None
        
        current = self.df.iloc[-1]
        
        # Get distance-based confidence
        confidence = self.get_distance_based_confidence()
        
        # Check if in transition (low confidence)
        is_transitioning = confidence < 0.7
        
        result = {
            'regime': current['Regime'],
            'confidence': confidence,
            'is_transitioning': is_transitioning,
            'price': round(float(current['Adj Close']), 2),
            'volatility': float(current['Volatility']),
            'return': float(current['Log_Return']),
            'date': str(self.df.index[-1].date())
        }
        return result
    
    def get_regime_statistics(self, lookback_days=252):
        """Get statistics per regime"""
        if self.df is None:
            return {}
        
        recent = self.df.iloc[-lookback_days:] if lookback_days < len(self.df) else self.df
        stats = {}
        
        for regime in ['Bull', 'Bear', 'Sideways', 'Volatile']:
            data = recent[recent['Regime'] == regime]
            
            if len(data) > 0:
                stats[regime] = {
                    'days': len(data),
                    'percentage': round(len(data) / len(recent) * 100, 1),
                    'avg_return': round(data['Return'].mean() * 100, 3),
                    'volatility': round(data['Volatility'].mean() * 100, 3),
                    'sharpe_ratio': round((data['Return'].mean() / (data['Return'].std() + 1e-6)) * np.sqrt(252), 3)
                }
        
        return stats
    
    def get_regime_transitions(self, lookback_days=252):
        """Get regime transitions"""
        if self.df is None:
            return {}
        
        recent = self.df.iloc[-lookback_days:] if lookback_days < len(self.df) else self.df
        transitions = {}
        
        for i in range(1, len(recent)):
            key = f"{recent['Regime'].iloc[i-1]}_to_{recent['Regime'].iloc[i]}"
            transitions[key] = transitions.get(key, 0) + 1
        
        return transitions
    
    def get_historical_data(self, days=100):
        """Get historical price and regime data"""
        if self.df is None:
            return []
        
        recent = self.df.iloc[-days:] if days < len(self.df) else self.df
        data = []
        
        for idx, row in recent.iterrows():
            data.append({
                'date': str(idx.date()),
                'price': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
                'regime': row['Regime'],
                'return': round(float(row['Return']) * 100, 3),
                'volatility': round(float(row['Volatility']) * 100, 3)
            })
        
        return data


def analyze_market(ticker='NIFTY50.NS', period='5y'):
    """Main function to analyze market"""
    print(f"\n{'='*60}")
    print(f"Analyzing {ticker}...")
    print(f"{'='*60}\n")
    
    analyzer = MarketAnalyzer(ticker=ticker, period=period)
    
    regime = analyzer.get_current_regime()
    if regime:
        print(f"✓ Current Regime: {regime['regime']} (confidence: {regime['confidence']*100:.0f}%)")
        print(f"  Volatility: {regime['volatility']*100:.2f}% | Return: {regime['return']*100:.3f}%")
    
    return analyzer


if __name__ == '__main__':
    analyzer = analyze_market('NIFTY50.NS', '5y')
    current = analyzer.get_current_regime()
    print(f"\n{current}")

