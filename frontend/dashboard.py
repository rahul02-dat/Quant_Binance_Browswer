import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="Quant Analytics Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:8000/api/v1"

st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Real-Time Quantitative Analytics Dashboard")

api_connected = False
api_status = {}

st.sidebar.title("System Status")

try:
    status_response = requests.get(f"{API_URL}/", timeout=2)
    if status_response.status_code == 200:
        status_data = status_response.json()
        api_connected = True
        api_status = status_data
        st.sidebar.success("✓ API Connected")
        
        if 'websocket_stats' in status_data:
            ws_stats = status_data['websocket_stats']
            msg_count = ws_stats.get('total_messages', 0)
            st.sidebar.metric("Messages Received", msg_count)
            
            if msg_count == 0:
                st.sidebar.warning("⚠ No data received yet. Wait 30s...")
            
            if ws_stats.get('buffer_sizes'):
                st.sidebar.write("**Buffer Sizes:**")
                for symbol, size in ws_stats['buffer_sizes'].items():
                    st.sidebar.text(f"{symbol}: {size}")
        
        if 'buffer_status' in status_data:
            st.sidebar.write("**Rolling Buffer:**")
            for symbol, count in status_data['buffer_status'].items():
                st.sidebar.text(f"{symbol}: {count} ticks")
    else:
        st.sidebar.error("⚠ API Connection Issue")
except requests.exceptions.ConnectionError:
    st.sidebar.error("✗ API Disconnected")
    st.error("🚨 Cannot connect to API server!")
    st.info("Make sure the API is running: `python app.py`")
    st.stop()
except Exception as e:
    st.sidebar.error(f"✗ Error: {str(e)[:50]}")

if not api_connected:
    st.error("🚨 API server is not responding")
    st.info("""
    **To fix this:**
    1. Open a terminal
    2. Run: `python app.py`
    3. Wait for "Application started" message
    4. Refresh this page
    """)
    
    if st.button("Try to reconnect"):
        st.rerun()
    
    st.stop()

col1, col2, col3 = st.columns(3)

with col1:
    symbol_x = st.selectbox("Symbol X", ["BTCUSDT", "ETHUSDT", "BNBUSDT"], key="symbol_x")

with col2:
    symbol_y = st.selectbox("Symbol Y", ["ETHUSDT", "BTCUSDT", "BNBUSDT"], key="symbol_y")

with col3:
    timeframe = st.selectbox("Timeframe", ["1s", "1m", "5m"], key="timeframe")

col4, col5 = st.columns(2)

with col4:
    rolling_window = st.slider("Rolling Window", 5, 100, 20, key="window")

with col5:
    auto_refresh = st.checkbox("Auto-refresh", value=True, key="auto_refresh")
    if auto_refresh:
        refresh_rate = st.slider("Refresh Rate (seconds)", 0.5, 5.0, 1.0, key="refresh")
    else:
        refresh_rate = None

tab1, tab2, tab3, tab4 = st.tabs(["Live Data", "Analytics", "Alerts", "Export"])

with tab1:
    st.subheader("Live Price Data")
    
    price_placeholder = st.empty()
    stats_placeholder = st.empty()
    
    try:
        response_x = requests.get(f"{API_URL}/bars/{symbol_x}/{timeframe}?limit=100", timeout=5)
        response_y = requests.get(f"{API_URL}/bars/{symbol_y}/{timeframe}?limit=100", timeout=5)
        
        bars_x = response_x.json() if response_x.status_code == 200 else []
        bars_y = response_y.json() if response_y.status_code == 200 else []
        
        if bars_x and bars_y and len(bars_x) > 0 and len(bars_y) > 0:
            df_x = pd.DataFrame(bars_x)
            df_y = pd.DataFrame(bars_y)
            
            df_x['timestamp'] = pd.to_datetime(df_x['start_time'], unit='ms')
            df_y['timestamp'] = pd.to_datetime(df_y['start_time'], unit='ms')
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'{symbol_x} Price', f'{symbol_y} Price'),
                vertical_spacing=0.15
            )
            
            fig.add_trace(
                go.Candlestick(
                    x=df_x['timestamp'],
                    open=df_x['open'],
                    high=df_x['high'],
                    low=df_x['low'],
                    close=df_x['close'],
                    name=symbol_x
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Candlestick(
                    x=df_y['timestamp'],
                    open=df_y['open'],
                    high=df_y['high'],
                    low=df_y['low'],
                    close=df_y['close'],
                    name=symbol_y
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=600,
                showlegend=True,
                xaxis_rangeslider_visible=False,
                xaxis2_rangeslider_visible=False
            )
            
            price_placeholder.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(f"{symbol_x} Last", f"${df_x['close'].iloc[-1]:.2f}")
                st.metric(f"{symbol_x} Volume", f"{df_x['volume'].sum():.2f}")
            
            with col2:
                st.metric(f"{symbol_y} Last", f"${df_y['close'].iloc[-1]:.2f}")
                st.metric(f"{symbol_y} Volume", f"{df_y['volume'].sum():.2f}")
        else:
            st.info("Waiting for data... Please ensure the application is running and collecting data.")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server at http://localhost:8000. Make sure app.py is running.")
    except Exception as e:
        st.error(f"Error loading price data: {e}")

with tab2:
    st.subheader("Pair Analytics")
    
    analytics_placeholder = st.empty()
    
    if st.button("Run ADF Test"):
        st.info("ADF test will be computed with next analytics update")
    
    try:
        response = requests.get(
            f"{API_URL}/analytics/{symbol_x}/{symbol_y}/tick?limit=100",
            timeout=5
        )
        
        analytics = response.json() if response.status_code == 200 else []
        
        if analytics and len(analytics) > 0:
            df_analytics = pd.DataFrame(analytics)
            df_analytics['timestamp'] = pd.to_datetime(df_analytics['computed_at'], unit='ms')
            df_analytics = df_analytics.sort_values('timestamp')
            
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Spread', 'Z-Score', 'Rolling Correlation'),
                vertical_spacing=0.12
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_analytics['timestamp'],
                    y=df_analytics['spread'],
                    mode='lines',
                    name='Spread',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            if 'z_score' in df_analytics.columns and df_analytics['z_score'].notna().any():
                fig.add_trace(
                    go.Scatter(
                        x=df_analytics['timestamp'],
                        y=df_analytics['z_score'],
                        mode='lines',
                        name='Z-Score',
                        line=dict(color='green')
                    ),
                    row=2, col=1
                )
            
            fig.add_hline(y=2, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=-2, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
            
            if 'rolling_corr' in df_analytics.columns and df_analytics['rolling_corr'].notna().any():
                fig.add_trace(
                    go.Scatter(
                        x=df_analytics['timestamp'],
                        y=df_analytics['rolling_corr'],
                        mode='lines',
                        name='Correlation',
                        line=dict(color='purple')
                    ),
                    row=3, col=1
                )
            
            fig.update_layout(height=800, showlegend=True)
            
            analytics_placeholder.plotly_chart(fig, use_container_width=True)
            
            latest = df_analytics.iloc[-1]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                hr = latest.get('hedge_ratio')
                sp = latest.get('spread')
                st.metric("Hedge Ratio", f"{float(hr):.4f}" if pd.notna(hr) else "Computing...")
                st.metric("Spread", f"{float(sp):.4f}" if pd.notna(sp) else "Computing...")
            
            with col2:
                zs = latest.get('z_score')
                cr = latest.get('rolling_corr')
                st.metric("Z-Score", f"{float(zs):.4f}" if pd.notna(zs) else "Computing...")
                st.metric("Correlation", f"{float(cr):.4f}" if pd.notna(cr) else "Computing...")
            
            with col3:
                adf = latest.get('adf_stat')
                pv = latest.get('p_value')
                
                if pd.notna(adf) and pd.notna(pv):
                    st.metric("ADF Statistic", f"{float(adf):.4f}")
                    st.metric("P-Value", f"{float(pv):.4f}")
                else:
                    st.info("ADF Test computing...")
                    st.caption("Needs more data")
            
            st.subheader("Statistics Summary")
            
            st.write(f"**Data Points:** {len(df_analytics)}")
            st.write(f"**Time Range:** {df_analytics['timestamp'].min()} to {df_analytics['timestamp'].max()}")
            
            cols_to_summarize = [col for col in ['hedge_ratio', 'spread', 'z_score', 'rolling_corr'] if col in df_analytics.columns]
            if cols_to_summarize:
                summary_df = df_analytics[cols_to_summarize].describe()
                st.dataframe(summary_df)
            
            st.subheader("ADF Test Details")
            latest = df_analytics.iloc[-1]
            if pd.notna(latest.get('adf_stat')):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Test Result:**")
                    st.write(f"- ADF Statistic: {float(latest['adf_stat']):.4f}")
                    st.write(f"- P-Value: {float(latest['p_value']):.4f}")
                    
                with col_b:
                    st.write("**Interpretation:**")
                    p_val = float(latest['p_value'])
                    if p_val < 0.01:
                        st.success("Strong evidence of stationarity (p < 0.01)")
                    elif p_val < 0.05:
                        st.success("Evidence of stationarity (p < 0.05)")
                    elif p_val < 0.10:
                        st.warning("Weak evidence of stationarity (p < 0.10)")
                    else:
                        st.error("No evidence of stationarity (p ≥ 0.10)")
            else:
                st.info("ADF test requires at least 10 spread observations. Keep collecting data...")
        
        else:
            st.info(f"No analytics data available for {symbol_x}/{symbol_y}. Analytics require sufficient data accumulation (minimum {rolling_window} periods). Current data in system: check sidebar for buffer status.")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server. Make sure app.py is running.")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

with tab3:
    st.subheader("Alert Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alert_metric = st.selectbox("Metric", ["z_score", "spread", "rolling_corr", "hedge_ratio"])
    
    with col2:
        alert_condition = st.selectbox("Condition", [">", "<", ">=", "<="])
    
    with col3:
        alert_threshold = st.number_input("Threshold", value=2.0)
    
    if st.button("Create Alert"):
        try:
            response = requests.post(
                f"{API_URL}/alerts",
                json={
                    "metric": alert_metric,
                    "condition": alert_condition,
                    "threshold": alert_threshold
                }
            )
            if response.status_code == 200:
                st.success("Alert created successfully!")
            else:
                st.error(f"Failed to create alert: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API server. Make sure app.py is running.")
        except Exception as e:
            st.error(f"Error creating alert: {e}")
    
    st.subheader("Active Alerts")
    
    try:
        alerts_response = requests.get(f"{API_URL}/alerts", timeout=5)
        alerts = alerts_response.json() if alerts_response.status_code == 200 else []
        
        if alerts and len(alerts) > 0:
            for alert in alerts:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.text(f"{alert['metric']} {alert['condition']} {alert['threshold']}")
                
                with col2:
                    if st.button("Delete", key=f"delete_{alert['id']}"):
                        requests.delete(f"{API_URL}/alerts/{alert['id']}")
                        st.rerun()
        else:
            st.info("No active alerts")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server. Make sure app.py is running.")
    except Exception as e:
        st.error(f"Error loading alerts: {e}")

with tab4:
    st.subheader("Export Data")
    
    export_type = st.selectbox("Export Type", ["Resampled Bars", "Analytics"])
    
    if st.button("Export to CSV"):
        try:
            timestamp = int(time.time())
            
            if export_type == "Resampled Bars":
                response = requests.get(f"{API_URL}/bars/{symbol_x}/{timeframe}?limit=1000", timeout=5)
                if response.status_code == 200:
                    bars = response.json()
                    if bars and len(bars) > 0:
                        df = pd.DataFrame(bars)
                        filename = f"bars_{symbol_x}_{timeframe}_{timestamp}.csv"
                    else:
                        st.warning("No bar data available to export")
                        st.stop()
                else:
                    st.error("Failed to fetch bar data")
                    st.stop()
            else:
                response = requests.get(
                    f"{API_URL}/analytics/{symbol_x}/{symbol_y}/tick?limit=1000",
                    timeout=5
                )
                if response.status_code == 200:
                    analytics = response.json()
                    if analytics and len(analytics) > 0:
                        df = pd.DataFrame(analytics)
                        filename = f"analytics_{symbol_x}_{symbol_y}_{timeframe}_{timestamp}.csv"
                    else:
                        st.warning("No analytics data available to export")
                        st.stop()
                else:
                    st.error("Failed to fetch analytics data")
                    st.stop()
            
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
            
            st.success(f"Prepared {len(df)} rows for export")
        
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API server. Make sure the application is running.")
        except Exception as e:
            st.error(f"Error exporting data: {e}")

if auto_refresh and refresh_rate:
    time.sleep(refresh_rate)
    st.rerun()