import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Quant Analytics Dashboard", layout="wide")

API_URL = "http://localhost:8000"

st.title("Real-Time Quantitative Analytics Dashboard")

st.sidebar.title("System Status")

try:
    status_response = requests.get(f"{API_URL}/", timeout=2)
    if status_response.status_code == 200:
        status_data = status_response.json()
        st.sidebar.success("✓ API Connected")
        
        if 'websocket_stats' in status_data:
            ws_stats = status_data['websocket_stats']
            st.sidebar.metric("Messages Received", ws_stats.get('total_messages', 0))
            
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
except:
    st.sidebar.error("✗ API Disconnected")

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
    refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2, key="refresh")

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
            f"{API_URL}/analytics/{symbol_x}/{symbol_y}/{timeframe}?limit=100",
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
                st.metric("Hedge Ratio", f"{latest['hedge_ratio']:.4f}" if pd.notna(latest['hedge_ratio']) else "N/A")
                st.metric("Spread", f"{latest['spread']:.4f}" if pd.notna(latest['spread']) else "N/A")
            
            with col2:
                z_score_value = latest['z_score']
                st.metric("Z-Score", f"{z_score_value:.4f}" if pd.notna(z_score_value) else "N/A")
                st.metric("Correlation", f"{latest['rolling_corr']:.4f}" if pd.notna(latest['rolling_corr']) else "N/A")
            
            with col3:
                st.metric("ADF Statistic", f"{latest['adf_stat']:.4f}" if pd.notna(latest['adf_stat']) else "N/A")
                st.metric("P-Value", f"{latest['p_value']:.4f}" if pd.notna(latest['p_value']) else "N/A")
            
            st.subheader("Statistics Summary")
            summary_df = df_analytics[['hedge_ratio', 'spread', 'z_score', 'rolling_corr']].describe()
            st.dataframe(summary_df)
        
        else:
            st.info(f"No analytics data available for {symbol_x}/{symbol_y} on {timeframe} timeframe. Analytics require sufficient data accumulation (minimum {rolling_window} periods).")
    
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
                    f"{API_URL}/analytics/{symbol_x}/{symbol_y}/{timeframe}?limit=1000",
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

if st.sidebar.checkbox("Auto-refresh", value=True):
    time.sleep(refresh_rate)
    st.rerun()