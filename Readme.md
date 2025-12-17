# Real-Time Quantitative Analytics Platform

A production-grade, end-to-end quantitative analytics system for cryptocurrency pairs trading. The platform ingests live market data from Binance WebSocket, performs statistical analysis including cointegration testing and spread calculations, and visualizes results through an interactive real-time dashboard.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)

## 📁 Project Structure

```
quant_analytics_app/
│
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── config/
│   └── settings.py                 # Configuration settings
│
├── storage/
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── database.py                 # Database connection
│   └── repository.py               # Data access layer
│
├── ingestion/
│   ├── binance_ws.py              # WebSocket client
│   └── tick_handler.py            # Tick batching and storage
│
├── analytics/
│   ├── resampler.py               # Tick-to-bar conversion
│   ├── statistics.py              # Statistical calculations
│   ├── regression.py              # OLS regression
│   ├── stationarity.py            # ADF test
│   ├── spread.py                  # Pairs analytics
│   └── rolling.py                 # In-memory buffer
│
├── alerts/
│   └── engine.py                   # Alert evaluation engine
│
├── api/
│   ├── routes.py                   # FastAPI endpoints
│   └── schemas.py                  # Pydantic models
│
├── frontend/
│   └── dashboard.py                # Streamlit UI
│
├── exports/
│   └── csv_exporter.py            # Data export utilities
│
└── data/
    └── market_data.db              # SQLite database (created at runtime)
```

### Data Pipeline
- **Real-time WebSocket Integration**: Live tick data from Binance with automatic reconnection
- **Efficient Storage**: SQLite database with optimized batch writes and indexing
- **Multi-Timeframe Resampling**: Automatic conversion to 1s, 1m, and 5m OHLCV bars
- **In-Memory Buffer**: Rolling buffer for sub-second analytics computation

### Analytics Engine
- **OLS Regression**: Hedge ratio calculation between asset pairs
- **Spread Analysis**: Mean-reversion spread construction and monitoring
- **Z-Score Normalization**: Rolling z-score for trading signal generation
- **Correlation Analysis**: Time-varying correlation tracking
- **Stationarity Testing**: Augmented Dickey-Fuller (ADF) test for mean-reversion validation
- **Statistical Measures**: Returns, volatility, and descriptive statistics

### Real-Time Dashboard
- **Interactive Charts**: Plotly-based candlestick charts with zoom and pan
- **Live Analytics Display**: Real-time spread, z-score, and correlation visualization
- **Configurable Parameters**: Adjustable rolling windows and timeframes
- **Alert System**: Rule-based alerts with customizable conditions
- **Data Export**: CSV export for all data types

### System Monitoring
- **Health Checks**: WebSocket connection status and message counters
- **Buffer Statistics**: Real-time buffer sizes and data flow metrics
- **Error Handling**: Comprehensive logging and graceful error recovery

## 🏗️ Architecture

### Data Flow

1. **Ingestion**: Binance WebSocket client receives live trade data (price, quantity, timestamp)
2. **Buffering**: Tick handler batches data for efficient database writes (100 ticks or 1 second)
3. **Storage**: SQLAlchemy ORM persists ticks to SQLite with proper indexing
4. **Caching**: Rolling buffer maintains recent 10,000 ticks in memory per symbol
5. **Resampling**: Periodic task (5s interval) converts ticks to OHLCV bars (1s, 1m, 5m)
6. **Analytics**: Continuous computation (1s interval) of hedge ratios, spreads, z-scores, correlations
7. **Alerting**: Rule engine evaluates conditions and triggers alerts on threshold breaches
8. **Visualization**: Dashboard polls API (2s cache) and renders interactive Plotly charts

### Technology Stack

**Backend**
- FastAPI: Async REST API framework
- SQLAlchemy: ORM for database operations
- SQLite: Lightweight persistent storage
- WebSockets: Real-time data streaming
- Asyncio: Concurrent task execution

**Analytics**
- Pandas: Time series data manipulation
- NumPy: Numerical computations
- Statsmodels: Statistical tests (OLS, ADF)
- SciPy: Scientific computing utilities

**Frontend**
- Streamlit: Interactive web application framework
- Plotly: Interactive charting library
- Requests: HTTP client for API calls

## 🚀 Quick Start

### Single Command Start

The application automatically launches just by:

```bash
python app.py
```

### Access Points

Once started, open your browser to:

- **Dashboard**: http://localhost:8501 (main interface)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Status**: http://localhost:8000/api/v1/ (health check)

#### Live Data Tab

**Purpose**: Monitor real-time price movements

**Features**:
- Dual candlestick charts for selected symbol pairs
- Current price and volume metrics
- Auto-updating every 2 seconds
- Zoom, pan, and time range selection

**Controls**:
- **Symbol X/Y**: Select asset pairs (e.g., BTCUSDT, ETHUSDT)
- **Timeframe**: Choose bar period (1s for fastest updates)

#### Analytics Tab

**Purpose**: Perform pairs trading analysis

**Features**:
- Spread chart (Y - β·X)
- Z-score with ±2 threshold lines
- Rolling correlation visualization
- Statistical summary table
- ADF test results and interpretation

**Key Metrics**:
- **Hedge Ratio**: OLS regression coefficient (β)
- **Spread**: Mean-reverting price differential
- **Z-Score**: Standardized spread (-2 to +2 trading range)
- **Correlation**: Time-varying relationship (0 to 1)
- **ADF Statistic**: Stationarity test statistic
- **P-Value**: Significance level (< 0.05 = stationary)

**Trading Signals**:
- Z-Score > 2: Spread overextended (short signal)
- Z-Score < -2: Spread underextended (long signal)
- |Z-Score| < 0.5: Near equilibrium (exit signal)

#### Alerts Tab

**Purpose**: Configure automated monitoring

**Setup**:
1. Select metric (z_score, spread, correlation, hedge_ratio)
2. Choose condition (>, <, >=, <=)
3. Set threshold value
4. Click "Create Alert"

**Example Alerts**:
- "z_score > 2.0" → Alert when spread is overextended
- "correlation < 0.7" → Alert when pair relationship weakens
- "spread > 100" → Alert on unusual spread values

#### Export Tab

**Purpose**: Download data for external analysis

**Options**:
- **Resampled Bars**: OHLCV data for selected symbol and timeframe
- **Analytics**: Complete analytics history with all metrics

**Output Format**: CSV files with timestamps for archival

### System Status Sidebar

**Indicators**:
- **Messages Received**: Total WebSocket messages processed
- **Buffer Sizes**: Current ticks in memory per symbol
- **Rolling Buffer**: Total ticks available for analytics

**Health Check**:
- Green "✓ API Connected": System operational
- Red "✗ API Disconnected": Server not running
- ⚠ Warnings: Data collection issues

### Pairs Trading Framework

The application implements a statistical arbitrage strategy based on cointegration and mean reversion principles.

#### 1. Hedge Ratio Calculation

We use Ordinary Least Squares (OLS) regression to model the relationship:

```
Y(t) = β₀ + β₁·X(t) + ε(t)
```

Where:
- **Y(t)**: Price of asset Y at time t
- **X(t)**: Price of asset X at time t  
- **β₁**: Hedge ratio (number of X units per Y unit)
- **β₀**: Intercept term
- **ε(t)**: Residual error

**Implementation**: `analytics/regression.py`

#### 2. Spread Construction

The spread represents deviation from equilibrium:

```
Spread(t) = Y(t) - β₁·X(t)
```

A stationary spread indicates mean-reversion opportunity.

**Key Property**: If spread is mean-reverting, it will return to its historical average, enabling profitable trades.

**Implementation**: `analytics/spread.py`

#### 3. Z-Score Normalization

Standardize the spread for consistent trading thresholds:

```
Z(t) = [Spread(t) - μ(Spread)] / σ(Spread)
```

Where:
- **μ(Spread)**: Rolling mean of spread (window = 20 periods)
- **σ(Spread)**: Rolling standard deviation of spread

**Trading Interpretation**:
- **Z > 2**: Spread 2 standard deviations above mean (short opportunity)
- **Z < -2**: Spread 2 standard deviations below mean (long opportunity)
- **|Z| < 0.5**: Spread near equilibrium (no trade or exit)

**Implementation**: `analytics/spread.py`

#### 4. Rolling Correlation

Measures time-varying linear relationship:

```
ρ(t) = Corr[X(t-w:t), Y(t-w:t)]
```

Where **w** is the rolling window size (default: 20 periods).

**Interpretation**:
- **ρ > 0.7**: Strong positive correlation (good for pairs trading)
- **0.3 < ρ < 0.7**: Moderate correlation (watch carefully)
- **ρ < 0.3**: Weak correlation (avoid this pair)

**Implementation**: `analytics/statistics.py`

#### 5. Augmented Dickey-Fuller (ADF) Test

Tests the null hypothesis: "Spread has a unit root (non-stationary)"

**Test Equation**:
```
ΔSpread(t) = α + β·Spread(t-1) + Σγᵢ·ΔSpread(t-i) + ε(t)
```

**Interpretation**:
- **p-value < 0.01**: Strong evidence of stationarity (high confidence)
- **p-value < 0.05**: Evidence of stationarity (standard threshold)
- **p-value > 0.05**: Cannot reject non-stationarity (risky for pairs trading)

**Critical Requirement**: Stationarity is essential for pairs trading, as it ensures the spread will revert to its mean.

**Implementation**: `analytics/stationarity.py`

### Resampling Algorithm

Tick-to-bar conversion using Pandas resample:

**Process**:
1. Group ticks by time period (1s, 1m, 5m)
2. Calculate OHLCV:
   - **Open**: First price in period
   - **High**: Maximum price in period
   - **Low**: Minimum price in period
   - **Close**: Last price in period
   - **Volume**: Sum of quantities in period

**Implementation**: `analytics/resampler.py`

### Performance Characteristics

**Computation Frequency**:
- **Tick Ingestion**: Real-time (microseconds)
- **Analytics Update**: Every 1 second
- **Resampling**: Every 5 seconds
- **Dashboard Refresh**: Every 2 seconds (cached)

**Data Requirements**:
- **Minimum for analytics**: 10 ticks per symbol
- **Recommended for z-score**: 20+ periods
- **Required for ADF test**: 10+ spread observations

## 🔌 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. System Status
```http
GET /api/v1/
```

**Response**:
```json
{
  "status": "running",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "websocket_stats": {
    "total_messages": 15000,
    "buffer_sizes": {"BTCUSDT": 5753, "ETHUSDT": 6170},
    "is_running": true
  },
  "buffer_status": {"BTCUSDT": 5753, "ETHUSDT": 6170}
}
```

#### 2. Get Recent Ticks
```http
GET /api/v1/ticks/{symbol}?limit=1000
```

**Parameters**:
- `symbol`: Trading pair (e.g., BTCUSDT)
- `limit`: Number of ticks (default: 1000)

**Response**: Array of tick objects

#### 3. Get Resampled Bars
```http
GET /api/v1/bars/{symbol}/{timeframe}?limit=500
```

**Parameters**:
- `symbol`: Trading pair
- `timeframe`: 1s, 1m, or 5m
- `limit`: Number of bars (default: 500)

**Response**: Array of OHLCV objects

#### 4. Get Analytics
```http
GET /api/v1/analytics/{symbol_x}/{symbol_y}/{timeframe}?limit=100
```

**Parameters**:
- `symbol_x`: First symbol in pair
- `symbol_y`: Second symbol in pair
- `timeframe`: tick, 1s, 1m, or 5m
- `limit`: Number of records (default: 100)

**Response**: Array of analytics objects with hedge_ratio, spread, z_score, etc.

#### 5. Create Alert
```http
POST /api/v1/alerts
Content-Type: application/json

{
  "metric": "z_score",
  "condition": ">",
  "threshold": 2.0
}
```

**Response**: Created alert object with ID

#### 6. Get Active Alerts
```http
GET /api/v1/alerts
```

**Response**: Array of alert objects

### Module Responsibilities

**app.py**: Application orchestrator, manages lifecycle of all components

**storage/**: Database abstraction layer using repository pattern

**ingestion/**: WebSocket connection and tick data handling

**analytics/**: Pure functions for statistical computations

**alerts/**: Rule-based monitoring and alerting system

**api/**: REST API for dashboard communication

**frontend/**: Interactive web interface

**exports/**: Data export functionality

### Statistical Concepts

- **Cointegration**: Long-run equilibrium relationship between non-stationary series
- **Stationarity**: Time series with constant mean and variance
- **Mean Reversion**: Tendency for prices to return to average
- **Z-Score**: Standard score measuring distance from mean in standard deviations