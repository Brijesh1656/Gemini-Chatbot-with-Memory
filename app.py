import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import time

# Page config
st.set_page_config(
    page_title="Stock Analysis Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Improved CSS with better contrast and readability
st.markdown("""
<style>
    /* Main background and text */
    .main {
        background-color: #0e1117;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Metric cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(99, 102, 241, 0.1);
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d29;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Cached data fetching
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker, start_date, end_date):
    """Fetch stock data with error handling"""
    try:
        df = yf.download(
            ticker, 
            start=start_date, 
            end=end_date, 
            progress=False,
            auto_adjust=True
        )
        
        if df.empty:
            return None, "No data found for this ticker"
        
        return df, None
    except Exception as e:
        return None, f"Error: {str(e)}"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ticker_info(ticker):
    """Fetch ticker info"""
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except:
        return {}

def calculate_technical_indicators(df):
    """Calculate technical indicators"""
    df_copy = df.copy()
    
    # RSI
    delta = df_copy['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan) 
    df_copy['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df_copy['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df_copy['Close'].ewm(span=26, adjust=False).mean()
    df_copy['MACD'] = exp1 - exp2
    df_copy['MACD_Signal'] = df_copy['MACD'].ewm(span=9, adjust=False).mean()
    df_copy['MACD_Hist'] = df_copy['MACD'] - df_copy['MACD_Signal']
    
    # Bollinger Bands
    df_copy['BB_Middle'] = df_copy['Close'].rolling(window=20).mean()
    std = df_copy['Close'].rolling(window=20).std()
    df_copy['BB_Upper'] = df_copy['BB_Middle'] + (2 * std)
    df_copy['BB_Lower'] = df_copy['BB_Middle'] - (2 * std)
    
    # Moving Averages
    df_copy['SMA_20'] = df_copy['Close'].rolling(window=20).mean()
    df_copy['SMA_50'] = df_copy['Close'].rolling(window=50).mean()
    df_copy['SMA_200'] = df_copy['Close'].rolling(window=200).mean()
    
    return df_copy

# Header
st.markdown("""
<div class="main-header">
    <h1>📈 Stock Analysis Pro</h1>
    <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; margin-top: 0.5rem;">
        Technical Analysis & Market Intelligence
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'stock_data' not in st.session_state:
    st.session_state['stock_data'] = None

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    ticker = st.text_input(
        "Stock Ticker",
        value="AAPL",
        placeholder="e.g., AAPL, MSFT, GOOGL"
    ).upper()
    
    st.divider()
    
    # Date range presets
    date_preset = st.selectbox(
        "📅 Quick Date Range",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years", "Custom"]
    )
    
    today = datetime.today().date()
    
    if date_preset == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start",
                value=today - timedelta(days=365),
                max_value=today
            )
        with col2:
            end_date = st.date_input(
                "End",
                value=today,
                max_value=today
            )
    else:
        days_map = {
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180,
            "1 Year": 365,
            "2 Years": 730,
            "5 Years": 1825
        }
        start_date = today - timedelta(days=days_map[date_preset])
        end_date = today
        st.info(f"📆 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    st.divider()
    
    if st.button("🚀 Fetch Data", use_container_width=True):
        with st.spinner(f"Fetching {ticker} data..."):
            df, error = fetch_stock_data(ticker, start_date, end_date)
            
            if error:
                st.error(error)
            else:
                ticker_info = fetch_ticker_info(ticker)
                st.session_state['stock_data'] = df
                st.session_state['ticker_info'] = ticker_info
                st.success(f"✅ Loaded {len(df)} days!")
    
    # Data info
    if st.session_state['stock_data'] is not None:
        st.divider()
        st.markdown("### 📊 Data Info")
        data = st.session_state['stock_data']
        st.metric("Total Days", len(data))
        st.caption(f"From: {data.index[0].strftime('%Y-%m-%d')}")
        st.caption(f"To: {data.index[-1].strftime('%Y-%m-%d')}")

# Main content
if st.session_state['stock_data'] is not None:
    data = st.session_state['stock_data'].copy()
    ticker_info = st.session_state.get('ticker_info', {})
    
    # Calculate indicators if enough data
    if len(data) >= 50:
        data = calculate_technical_indicators(data)
    
    # Key Metrics
    st.markdown("### 📊 Key Metrics")
    
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
    
    high_52w = data['High'].tail(252).max() if len(data) >= 252 else data['High'].max()
    low_52w = data['Low'].tail(252).min() if len(data) >= 252 else data['Low'].min()
    avg_volume = data['Volume'].tail(20).mean()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Current Price",
            f"${current_price:.2f}",
            f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
    
    with col2:
        st.metric(
            "52W High",
            f"${high_52w:.2f}",
            f"{((current_price / high_52w - 1) * 100):.1f}% from high"
        )
    
    with col3:
        st.metric(
            "52W Low",
            f"${low_52w:.2f}",
            f"{((current_price / low_52w - 1) * 100):.1f}% from low"
        )
    
    with col4:
        st.metric(
            "Avg Volume (20D)",
            f"{avg_volume/1e6:.2f}M",
            f"Last: {data['Volume'].iloc[-1]/1e6:.2f}M"
        )
    
    with col5:
        market_cap = ticker_info.get('marketCap', 0)
        if market_cap > 0:
            market_cap_str = f"${market_cap/1e9:.2f}B" if market_cap > 1e9 else f"${market_cap/1e6:.2f}M"
        else:
            market_cap_str = "N/A"
        
        pe_ratio = ticker_info.get('trailingPE', 'N/A')
        pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
        
        st.metric("Market Cap", market_cap_str, f"P/E: {pe_str}")
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Price Chart", "📊 Technical Indicators", "⚡ Backtest"])
    
    # TAB 1: Price Chart
    with tab1:
        chart_col1, chart_col2 = st.columns([3, 1])
        
        with chart_col1:
            chart_type = st.radio(
                "Chart Type",
                ["Candlestick", "Line", "Area"],
                horizontal=True
            )
        
        with chart_col2:
            show_volume = st.checkbox("Show Volume", value=True)
        
        # Indicators
        indicators = st.multiselect(
            "Overlay Indicators",
            ["SMA (20)", "SMA (50)", "SMA (200)", "Bollinger Bands"],
            default=["SMA (20)", "SMA (50)"]
        )
        
        # Create figure
        if show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3],
                subplot_titles=(f'{ticker} Price', 'Volume')
            )
        else:
            fig = go.Figure()
        
        # Add price chart
        if chart_type == "Candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name="Price",
                    increasing_line_color='#10b981',
                    decreasing_line_color='#ef4444'
                ),
                row=1, col=1
            )
        elif chart_type == "Line":
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    name='Close',
                    line=dict(color='#667eea', width=2)
                ),
                row=1, col=1
            )
        elif chart_type == "Area":
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    name='Close',
                    fill='tozeroy',
                    line=dict(color='#667eea', width=2),
                    fillcolor='rgba(102, 126, 234, 0.3)'
                ),
                row=1, col=1
            )
        
        # Add indicators
        colors = ['#8b5cf6', '#ec4899', '#f59e0b']
        color_idx = 0
        
        for indicator in indicators:
            if "SMA" in indicator and indicator in ['SMA (20)', 'SMA (50)', 'SMA (200)']:
                col_name = indicator.replace(' ', '_').replace('(', '').replace(')', '')
                if col_name in data.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data[col_name],
                            mode='lines',
                            name=indicator,
                            line=dict(color=colors[color_idx % len(colors)], width=2)
                        ),
                        row=1, col=1
                    )
                    color_idx += 1
            
            elif indicator == "Bollinger Bands" and 'BB_Upper' in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['BB_Upper'],
                        mode='lines',
                        name='BB Upper',
                        line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dash'),
                        showlegend=False
                    ),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['BB_Lower'],
                        mode='lines',
                        name='Bollinger Bands',
                        line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(255, 255, 255, 0.05)'
                    ),
                    row=1, col=1
                )
        
        # Add volume
        if show_volume:
            colors_volume = ['#ef4444' if data['Close'].iloc[i] < data['Open'].iloc[i] else '#10b981' 
                           for i in range(len(data))]
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color=colors_volume,
                    opacity=0.5,
                    showlegend=False
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            height=700,
            template='plotly_dark',
            hovermode='x unified',
            showlegend=True,
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: Technical Indicators
    with tab2:
        if 'RSI' in data.columns and 'MACD' in data.columns:
            # Indicator metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                current_rsi = data['RSI'].iloc[-1]
                rsi_signal = "🟢 Oversold" if current_rsi < 30 else "🔴 Overbought" if current_rsi > 70 else "🟡 Neutral"
                st.metric("RSI (14)", f"{current_rsi:.2f}", rsi_signal)
            
            with col2:
                current_macd = data['MACD'].iloc[-1]
                current_signal = data['MACD_Signal'].iloc[-1]
                macd_trend = "🟢 Bullish" if current_macd > current_signal else "🔴 Bearish"
                st.metric("MACD", f"{current_macd:.4f}", macd_trend)
            
            with col3:
                if 'BB_Upper' in data.columns:
                    bb_position = ((data['Close'].iloc[-1] - data['BB_Lower'].iloc[-1]) / 
                                 (data['BB_Upper'].iloc[-1] - data['BB_Lower'].iloc[-1])) * 100
                    bb_signal = "🔴 Near Upper" if bb_position > 80 else "🟢 Near Lower" if bb_position < 20 else "🟡 Mid Range"
                    st.metric("BB Position", f"{bb_position:.1f}%", bb_signal)
            
            st.divider()
            
            # RSI Chart
            st.markdown("#### RSI (Relative Strength Index)")
            rsi_fig = go.Figure()
            rsi_fig.add_trace(go.Scatter(
                x=data.index,
                y=data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#667eea', width=2)
            ))
            rsi_fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought")
            rsi_fig.add_hline(y=30, line_dash="dash", line_color="#10b981", annotation_text="Oversold")
            rsi_fig.update_layout(
                height=300,
                template='plotly_dark',
                hovermode='x unified',
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(rsi_fig, use_container_width=True)
            
            # MACD Chart
            st.markdown("#### MACD")
            macd_fig = go.Figure()
            macd_fig.add_trace(go.Scatter(
                x=data.index,
                y=data['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='#667eea', width=2)
            ))
            macd_fig.add_trace(go.Scatter(
                x=data.index,
                y=data['MACD_Signal'],
                mode='lines',
                name='Signal',
                line=dict(color='#f59e0b', width=2)
            ))
            colors_hist = ['#10b981' if val >= 0 else '#ef4444' for val in data['MACD_Hist']]
            macd_fig.add_trace(go.Bar(
                x=data.index,
                y=data['MACD_Hist'],
                name='Histogram',
                marker_color=colors_hist,
                opacity=0.5
            ))
            macd_fig.update_layout(
                height=300,
                template='plotly_dark',
                hovermode='x unified'
            )
            st.plotly_chart(macd_fig, use_container_width=True)
        else:
            st.warning("⚠️ Not enough data to calculate indicators. Try a longer date range (at least 50 days).")
    
    # TAB 3: Backtest
    with tab3:
        st.info("🚀 **Coming Soon**: Strategy backtesting with SMA crossovers, RSI, and MACD strategies!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Strategy", ["SMA Crossover (20/50)", "SMA Crossover (50/200)", "RSI Mean Reversion", "MACD"])
        with col2:
            st.number_input("Initial Capital ($)", value=10000, step=1000)
        
        st.button("🚀 Run Backtest", use_container_width=True, disabled=True)
    
    # Export section
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        csv = data.to_csv()
        st.download_button(
            "📥 Download Data (CSV)",
            csv,
            file_name=f"{ticker}_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        st.info("💡 Export your analysis data for further processing")

else:
    # Welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem;">
        <h2 style="color: #667eea;">👋 Welcome to Stock Analysis Pro</h2>
        <p style="font-size: 1.2rem; opacity: 0.8; margin: 2rem 0;">
            Enter a stock ticker in the sidebar and click "Fetch Data" to get started
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📈 **Interactive Charts**\n\nCandlestick, line, and area charts with multiple technical indicators")
    
    with col2:
        st.info("📊 **Technical Analysis**\n\nRSI, MACD, Bollinger Bands, and moving averages")
    
    with col3:
        st.info("💾 **Export Data**\n\nDownload historical data in CSV format")

# Footer
st.divider()
st.caption("⚠️ For educational purposes only. Not financial advice. Data provided by Yahoo Finance.")
