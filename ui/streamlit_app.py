"""
Streamlit Trading Dashboard
Professional UI for algorithmic trading strategy visualization and backtesting.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.fetcher import fetch_equity_data
from data.preprocessor import preprocess_data
from strategy.indicators import add_indicators
from strategy.signals import generate_signals
from backtesting.engine import run_backtest
from backtesting.metrics import PerformanceMetrics

# Options module imports (Hackathon addition)
from options.option_backtester import run_options_backtest, OptionsPerformanceMetrics

# Futures module imports (Separate ICT strategy)
from futures_strategy.backtest import run_futures_backtest

# Page configuration
st.set_page_config(
    page_title="Algorithmic Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium dark theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #00d4ff;
        --secondary-color: #00ff88;
        --danger-color: #ff3366;
        --bg-dark: #0e1117;
        --bg-card: #1a1d29;
    }
    
    /* Headers */
    h1 {
        color: var(--primary-color);
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    h2, h3 {
        color: var(--secondary-color);
        font-weight: 600;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 212, 255, 0.3);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d29 0%, #0e1117 100%);
    }
    
    /* Data tables */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Success/Error messages */
    .success-box {
        background: rgba(0, 255, 136, 0.1);
        border-left: 4px solid var(--secondary-color);
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: rgba(255, 51, 102, 0.1);
        border-left: 4px solid var(--danger-color);
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Title and description
st.markdown("<h1>📈 Algorithmic Trading System</h1>", unsafe_allow_html=True)
st.markdown("**Multi-Indicator Momentum Strategy** | Equity & Options Markets")

# Sidebar controls
st.sidebar.markdown("## ⚙️ Configuration")

# ASSET CLASS SELECTOR (NEW - Hackathon Feature)
st.sidebar.markdown("### 🎯 Asset Class")
asset_class = st.sidebar.radio(
    "Select trading mode:",
    options=["Equity", "Options", "Futures"],
    index=0,
    help="Equity: Direct stock trading | Options: CALL/PUT based on equity signals | Futures: NIFTY Futures with ICT strategy"
)

# Show options info if selected
if asset_class == "Options":
    st.sidebar.info(
        "📌 **Options Mode:**\n"
        "• BUY signal → Buy CALL\n"
        "• SELL signal → Buy PUT\n"
        "• Premium ≈ 2% of stock price\n"
        "• Exit: +50% profit / -30% loss"
    )

# Show Futures info if selected
if asset_class == "Futures":
    st.sidebar.info(
        "📌 **Futures Mode (ICT Strategy):**\n"
        "• Session-based trading (9:15-12:00, 13:30-15:30)\n"
        "• FVG Tally for bias detection\n"
        "• PDH/PDL sweep confirmation\n"
        "• Displacement + BOS entry\n"
        "• Risk: 1-2% per trade"
    )

# Initialize selected_stocks with default even if not used (for Futures mode)
selected_stocks = []
initial_capital = 1000000  # Default capital

# ============ FUTURES MODE SIDEBAR ============
if asset_class == "Futures":
    st.sidebar.markdown("### 📁 Data Source")
    
    # Preset CSV paths (check multiple locations)
    import os
    PRESET_PATHS = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample", "nifty_futures_1m_last_60_days.csv"),
        "d:/ALGO TRADING FINAL/br/nifty_futures_1m_last_60_days.csv",
    ]
    PRESET_CSV_PATH = None
    for p in PRESET_PATHS:
        if os.path.exists(p):
            PRESET_CSV_PATH = p
            break
    
    data_source = st.sidebar.radio(
        "Choose data source:",
        options=["Use Preset Data", "Upload CSV"],
        index=0
    )
    
    futures_df = None
    
    if data_source == "Use Preset Data":
        if PRESET_CSV_PATH:
            st.sidebar.success("📊 Will use: `nifty_futures_1m_last_60_days.csv`")
            st.sidebar.caption(f"File found at: {PRESET_CSV_PATH}")
        else:
            st.sidebar.warning("Preset file not found. Please upload a CSV.")
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload OHLC CSV",
            type=['csv'],
            help="CSV must have columns: datetime, open, high, low, close"
        )
        if uploaded_file is not None:
            st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")
    
    initial_capital = st.sidebar.number_input(
        "Initial Capital (₹)",
        min_value=100000,
        max_value=10000000,
        value=1000000,
        step=100000,
        format="%d"
    )
    
    # Run backtest button for Futures
    st.sidebar.markdown("---")
    run_backtest_button = st.sidebar.button(
        "🚀 Run Futures Backtest",
        use_container_width=True,
        type="primary"
    )

# ============ EQUITY / OPTIONS MODE SIDEBAR ============
else:
    # Stock selection
    st.sidebar.markdown("### 📊 Select Stocks")
    available_stocks = [
        'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
        'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT'
    ]
    
    selected_stocks = st.sidebar.multiselect(
        "Choose stocks to analyze",
        options=available_stocks,
        default=['RELIANCE', 'TCS', 'INFY'],
        help="Select 1-5 stocks for backtesting"
    )
    
    # Date range
    st.sidebar.markdown("### 📅 Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime('2022-01-01')
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime('2024-01-01')
        )
    
    # Strategy parameters
    st.sidebar.markdown("### 🎯 Strategy Parameters")
    
    with st.sidebar.expander("Moving Averages", expanded=False):
        short_ma = st.slider("Short MA Period", 10, 50, 20)
        long_ma = st.slider("Long MA Period", 30, 100, 50)
    
    with st.sidebar.expander("RSI", expanded=False):
        rsi_period = st.slider("RSI Period", 7, 21, 14)
        rsi_oversold = st.slider("RSI Oversold", 20, 40, 30)
        rsi_overbought = st.slider("RSI Overbought", 60, 80, 70)
    
    with st.sidebar.expander("MACD", expanded=False):
        macd_fast = st.slider("MACD Fast", 8, 16, 12)
        macd_slow = st.slider("MACD Slow", 20, 30, 26)
        macd_signal = st.slider("MACD Signal", 7, 12, 9)
    
    # Risk management
    st.sidebar.markdown("### ⚠️ Risk Management")
    initial_capital = st.sidebar.number_input(
        "Initial Capital (₹)",
        min_value=100000,
        max_value=10000000,
        value=1000000,
        step=100000,
        format="%d"
    )
    
    position_size = st.sidebar.slider(
        "Position Size (%)",
        min_value=5,
        max_value=50,
        value=20,
        help="Percentage of portfolio per trade"
    ) / 100
    
    max_positions = st.sidebar.slider(
        "Max Concurrent Positions",
        min_value=1,
        max_value=5,
        value=3
    )
    
    stop_loss = st.sidebar.slider(
        "Stop Loss (%)",
        min_value=1,
        max_value=15,
        value=5,
        help="Percentage below entry price"
    ) / 100
    
    take_profit = st.sidebar.slider(
        "Take Profit (%)",
        min_value=5,
        max_value=30,
        value=10,
        help="Percentage above entry price"
    ) / 100
    
    # Run backtest button
    st.sidebar.markdown("---")
    run_backtest_button = st.sidebar.button(
        "🚀 Run Backtest",
        use_container_width=True,
        type="primary"
    )

# Initialize session state
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None


# Run backtest
if run_backtest_button:
    # ============ FUTURES MODE BACKTEST ============
    if asset_class == "Futures":
        with st.spinner('🔄 Running Futures backtest with ICT strategy...'):
            try:
                progress_bar = st.progress(0)
                st.info("📥 Loading futures data...")
                progress_bar.progress(20)
                
                # Load data based on source selection
                import os
                PRESET_CSV_PATH = "d:/ALGO TRADING FINAL/futures/nifty_futures_1m_last_60_days.csv"
                
                if data_source == "Use Preset Data":
                    if os.path.exists(PRESET_CSV_PATH):
                        futures_df = pd.read_csv(PRESET_CSV_PATH)
                        st.success(f"✅ Loaded {len(futures_df):,} candles from preset file")
                    else:
                        st.error(f"❌ Preset file not found: {PRESET_CSV_PATH}")
                        st.stop()
                else:
                    if uploaded_file is not None:
                        futures_df = pd.read_csv(uploaded_file)
                        st.success(f"✅ Loaded {len(futures_df):,} candles from uploaded file")
                    else:
                        st.error("❌ Please upload a CSV file!")
                        st.stop()
                
                progress_bar.progress(50)
                st.info("⚙️ Running ICT strategy backtest...")
                
                # Run futures backtest
                results = run_futures_backtest(futures_df, initial_equity=initial_capital)
                
                progress_bar.progress(100)
                
                # Store in session state
                st.session_state.backtest_results = results
                st.session_state.metrics = results['metrics']
                
                st.success("✅ Futures backtest completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error during backtest: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # ============ EQUITY / OPTIONS MODE BACKTEST ============
    elif not selected_stocks:
        st.error("⚠️ Please select at least one stock!")
    else:
        with st.spinner('🔄 Fetching data and running backtest...'):
            try:
                # Fetch data
                progress_bar = st.progress(0)
                st.info("📥 Fetching equity data...")
                progress_bar.progress(20)
                
                raw_data = fetch_equity_data(
                    selected_stocks,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                # Preprocess
                st.info("🧹 Preprocessing data...")
                progress_bar.progress(40)
                clean_data = preprocess_data(raw_data)
                
                # Add indicators
                st.info("📊 Calculating technical indicators...")
                progress_bar.progress(60)
                df_with_indicators = add_indicators(
                    clean_data,
                    short_ma=short_ma,
                    long_ma=long_ma,
                    rsi_period=rsi_period,
                    macd_fast=macd_fast,
                    macd_slow=macd_slow,
                    macd_signal=macd_signal
                )
                
                # Generate signals
                st.info("🎯 Generating trading signals...")
                progress_bar.progress(70)
                df_with_signals = generate_signals(
                    df_with_indicators,
                    rsi_oversold=rsi_oversold,
                    rsi_overbought=rsi_overbought
                )
                
                # Run backtest (EQUITY or OPTIONS based on selection)
                progress_bar.progress(85)
                
                if asset_class == "Equity":
                    st.info("⚙️ Running EQUITY backtest...")
                    results = run_backtest(
                        df_with_signals,
                        initial_capital=initial_capital,
                        position_size=position_size,
                        max_positions=max_positions,
                        stop_loss_pct=stop_loss,
                        take_profit_pct=take_profit
                    )
                    # Calculate metrics
                    metrics_calc = PerformanceMetrics(results)
                    metrics = metrics_calc.calculate_all_metrics()
                else:
                    st.info("⚙️ Running OPTIONS backtest (CALL/PUT from equity signals)...")
                    results = run_options_backtest(
                        df_with_signals,
                        initial_capital=initial_capital,
                        position_size_pct=position_size,
                        max_positions=max_positions,
                        profit_target_pct=take_profit * 100 * 5,  # Scale to 50%
                        stop_loss_pct=-stop_loss * 100 * 6  # Scale to -30%
                    )
                    # Calculate metrics
                    metrics_calc = OptionsPerformanceMetrics(results)
                    metrics = metrics_calc.calculate_all_metrics()
                
                progress_bar.progress(100)
                
                # Store in session state
                st.session_state.backtest_results = results
                st.session_state.metrics = metrics
                
                st.success("✅ Backtest completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error during backtest: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# Display results
if st.session_state.backtest_results is not None:
    results = st.session_state.backtest_results
    metrics = st.session_state.metrics
    
    # Detect asset class from results
    is_options = results.get('asset_class') == 'options'
    is_futures = results.get('asset_class') == 'futures'
    
    if is_futures:
        asset_label = "📊 FUTURES (ICT Strategy)"
    elif is_options:
        asset_label = "📊 OPTIONS"
    else:
        asset_label = "📈 EQUITY"
    
    # Key metrics at the top
    st.markdown(f"## {asset_label} Performance Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Futures mode uses different metric keys
    if is_futures:
        with col1:
            total_return = metrics.get('Total Return', 0)
            st.metric(
                "Total Return",
                f"{total_return:.2f}%",
                delta=f"{total_return:.2f}%"
            )
        
        with col2:
            profit_factor = metrics.get('Profit Factor', 0)
            st.metric(
                "Profit Factor",
                f"{profit_factor:.2f}",
                delta="Higher is better"
            )
        
        with col3:
            win_rate = metrics.get('Win Rate', 0)
            st.metric(
                "Win Rate",
                f"{win_rate:.1f}%"
            )
        
        with col4:
            total_pnl = metrics.get('Total PnL', 0)
            st.metric(
                "Total P&L",
                f"₹{total_pnl:,.0f}",
                delta=f"₹{total_pnl:,.0f}"
            )
        
        with col5:
            total_trades = metrics.get('Total Trades', 0)
            st.metric(
                "Total Trades",
                f"{int(total_trades)}"
            )
    else:
        with col1:
            total_return = metrics['Total Return (%)']
            st.metric(
                "Total Return",
                f"{total_return:.2f}%",
                delta=f"{total_return:.2f}%"
            )
        
        with col2:
            sharpe = metrics['Sharpe Ratio']
            st.metric(
                "Sharpe Ratio",
                f"{sharpe:.2f}",
                delta="Higher is better"
            )
        
        with col3:
            win_rate = metrics['Win Rate (%)']
            st.metric(
                "Win Rate",

            f"{win_rate:.1f}%"
        )
        
        with col4:
            max_dd = metrics['Max Drawdown (%)']
            st.metric(
                "Max Drawdown",
                f"{abs(max_dd):.2f}%",
                delta=f"-{abs(max_dd):.2f}%",
                delta_color="inverse"
            )
        
        with col5:
            total_trades = metrics['Total Trades']
            st.metric(
                "Total Trades",
                f"{int(total_trades)}"
            )
    
    st.markdown("---")
    
    # ============ FUTURES MODE VISUALIZATION ============
    if is_futures:
        tab1, tab2, tab3 = st.tabs([
            "📈 Candlestick Chart", "💰 Equity Curve", "📋 Trade Log"
        ])
        
        with tab1:
            st.markdown("### NIFTY Futures - Price Chart with Trade Signals")
            
            data_df = results['data']
            if not data_df.empty:
                # Create candlestick chart
                fig = go.Figure()
                
                # Candlestick
                fig.add_trace(
                    go.Candlestick(
                        x=data_df.index,
                        open=data_df['open'],
                        high=data_df['high'],
                        low=data_df['low'],
                        close=data_df['close'],
                        name='Price',
                        increasing_line_color='#00ff88',
                        decreasing_line_color='#ff3366'
                    )
                )
                
                # Buy signals (BULLISH trades)
                buy_signals = data_df[data_df['signal'] == 1]
                if not buy_signals.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=buy_signals.index,
                            y=buy_signals['low'] * 0.999,  # Slightly below low
                            mode='markers',
                            name='LONG Entry',
                            marker=dict(
                                symbol='triangle-up',
                                size=12,
                                color='#00ff88',
                                line=dict(color='white', width=1)
                            )
                        )
                    )
                
                # Sell signals (BEARISH trades)
                sell_signals = data_df[data_df['signal'] == -1]
                if not sell_signals.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=sell_signals.index,
                            y=sell_signals['high'] * 1.001,  # Slightly above high
                            mode='markers',
                            name='SHORT Entry',
                            marker=dict(
                                symbol='triangle-down',
                                size=12,
                                color='#ff3366',
                                line=dict(color='white', width=1)
                            )
                        )
                    )
                
                fig.update_layout(
                    title="NIFTY Futures with ICT Strategy Signals",
                    xaxis_title="DateTime",
                    yaxis_title="Price (₹)",
                    template='plotly_dark',
                    height=700,
                    xaxis_rangeslider_visible=False,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show trade statistics
                st.markdown("#### Trade Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("LONG Trades", f"{len(buy_signals)}")
                with col2:
                    st.metric("SHORT Trades", f"{len(sell_signals)}")
                with col3:
                    st.metric("Avg R:R", f"{metrics.get('Average RR', 0):.2f}")
                with col4:
                    st.metric("Avg Trade P&L", f"₹{metrics.get('Average Trade PnL', 0):,.0f}")
            else:
                st.warning("No data to display.")
        
        with tab2:
            st.markdown("### Equity Curve")
            
            equity_df = results.get('equity_curve', pd.DataFrame())
            if not equity_df.empty:
                fig = go.Figure()
                
                fig.add_trace(
                    go.Scatter(
                        x=equity_df['date'].astype(str),
                        y=equity_df['equity'],
                        name='Equity',
                        line=dict(color='#00ff88', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(0, 255, 136, 0.1)'
                    )
                )
                
                fig.add_hline(
                    y=results['initial_capital'],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Initial Capital",
                    annotation_position="right"
                )
                
                fig.update_layout(
                    title="Portfolio Equity Over Time",
                    xaxis_title="Date",
                    yaxis_title="Equity (₹)",
                    template='plotly_dark',
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Additional metrics
                st.markdown("#### Performance Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Initial Capital", f"₹{results['initial_capital']:,}")
                with col2:
                    st.metric("Final Capital", f"₹{results['final_capital']:,.0f}")
                with col3:
                    pnl = results['final_capital'] - results['initial_capital']
                    st.metric("Net P&L", f"₹{pnl:,.0f}", delta=f"₹{pnl:,.0f}")
            else:
                st.warning("No equity data to display.")
        
        with tab3:
            st.markdown("### Complete Trade Log")
            
            trades_df = results.get('trades_df', pd.DataFrame())
            if not trades_df.empty:
                # Format for display
                display_df = trades_df.copy()
                display_df['time'] = pd.to_datetime(display_df['time']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['entry'] = display_df['entry'].apply(lambda x: f"₹{x:,.2f}")
                display_df['stop'] = display_df['stop'].apply(lambda x: f"₹{x:,.2f}")
                display_df['target'] = display_df['target'].apply(lambda x: f"₹{x:,.2f}")
                display_df['pnl'] = display_df['pnl'].apply(lambda x: f"₹{x:,.0f}")
                display_df['rr'] = display_df['rr'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(
                    display_df[['date', 'time', 'bias', 'entry', 'stop', 'target', 'rr', 'pnl']],
                    use_container_width=True,
                    height=500
                )
                
                # Download button
                csv = trades_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Trade Log (CSV)",
                    data=csv,
                    file_name="futures_trade_log.csv",
                    mime="text/csv"
                )
            else:
                st.info("No trades were executed in this backtest. The strategy may not have found valid setups in the data.")
    
    # ============ EQUITY / OPTIONS VISUALIZATION ============
    else:
        # Tabs for different visualizations
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Price Charts", "💰 Portfolio Performance", "📊 Trade Analysis", "⚠️ Risk Metrics", "📋 Trade Log"
        ])

    
        with tab1:
            st.markdown("### Price Charts with Trade Signals")
            
            # Select stock to display
            display_stock = st.selectbox(
                "Select stock to view",
                options=selected_stocks
            )
            
            if display_stock:
                stock_data = results['data'][results['data']['Symbol'] == display_stock].copy()

            
            # Create candlestick chart with indicators
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.5, 0.15, 0.15, 0.2],
                subplot_titles=(
                    f'{display_stock} - Price & Indicators',
                    'RSI',
                    'MACD',
                    'Volume'
                )
            )
            
            # Candlestick
            fig.add_trace(
                go.Candlestick(
                    x=stock_data['Date'],
                    open=stock_data['Open'],
                    high=stock_data['High'],
                    low=stock_data['Low'],
                    close=stock_data['Close'],
                    name='Price'
                ),
                row=1, col=1
            )
            
            # Moving averages
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['MA_Short'],
                    name=f'MA{short_ma}',
                    line=dict(color='cyan', width=1)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['MA_Long'],
                    name=f'MA{long_ma}',
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )
            
            # Bollinger Bands
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['BB_Upper'],
                    name='BB Upper',
                    line=dict(color='gray', width=1, dash='dash'),
                    opacity=0.5
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['BB_Lower'],
                    name='BB Lower',
                    line=dict(color='gray', width=1, dash='dash'),
                    opacity=0.5,
                    fill='tonexty'
                ),
                row=1, col=1
            )
            
            # Buy signals
            buy_signals = stock_data[stock_data['Signal'] == 1]
            fig.add_trace(
                go.Scatter(
                    x=buy_signals['Date'],
                    y=buy_signals['Close'],
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color='#00ff88',
                        line=dict(color='white', width=1)
                    )
                ),
                row=1, col=1
            )
            
            # Sell signals
            sell_signals = stock_data[stock_data['Signal'] == -1]
            fig.add_trace(
                go.Scatter(
                    x=sell_signals['Date'],
                    y=sell_signals['Close'],
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(
                        symbol='triangle-down',
                        size=15,
                        color='#ff3366',
                        line=dict(color='white', width=1)
                    )
                ),
                row=1, col=1
            )
            
            # RSI
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['RSI'],
                    name='RSI',
                    line=dict(color='purple', width=2)
                ),
                row=2, col=1
            )
            
            # RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
            
            # MACD
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['MACD'],
                    name='MACD',
                    line=dict(color='blue', width=2)
                ),
                row=3, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=stock_data['MACD_Signal'],
                    name='Signal',
                    line=dict(color='red', width=2)
                ),
                row=3, col=1
            )
            
            # MACD Histogram
            colors = ['green' if val >= 0 else 'red' for val in stock_data['MACD_Hist']]
            fig.add_trace(
                go.Bar(
                    x=stock_data['Date'],
                    y=stock_data['MACD_Hist'],
                    name='Histogram',
                    marker_color=colors,
                    opacity=0.5
                ),
                row=3, col=1
            )
            
            # Volume
            fig.add_trace(
                go.Bar(
                    x=stock_data['Date'],
                    y=stock_data['Volume'],
                    name='Volume',
                    marker_color='rgba(0, 212, 255, 0.5)'
                ),
                row=4, col=1
            )
            
            # Update layout
            fig.update_layout(
                height=1000,
                template='plotly_dark',
                showlegend=True,
                xaxis_rangeslider_visible=False,
                hovermode='x unified'
            )
            
            fig.update_xaxes(title_text="Date", row=4, col=1)
            fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
            fig.update_yaxes(title_text="MACD", row=3, col=1)
            fig.update_yaxes(title_text="Volume", row=4, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### Portfolio Value Over Time")
        
        portfolio_df = results['portfolio_history']
        
        # Create portfolio value chart
        fig = go.Figure()
        
        # Portfolio value
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Portfolio_Value'],
                name='Portfolio Value',
                line=dict(color='#00ff88', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 136, 0.1)'
            )
        )
        
        # Benchmark (buy and hold initial value)
        fig.add_hline(
            y=initial_capital,
            line_dash="dash",
            line_color="orange",
            annotation_text="Initial Capital",
            annotation_position="right"
        )
        
        fig.update_layout(
            title="Portfolio Growth",
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            template='plotly_dark',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Drawdown chart
        st.markdown("### Drawdown Analysis")
        
        metrics_calc = PerformanceMetrics(results)
        drawdown_df = metrics_calc.get_drawdown_series()
        
        fig_dd = go.Figure()
        
        fig_dd.add_trace(
            go.Scatter(
                x=drawdown_df['Date'],
                y=drawdown_df['Drawdown'] * 100,
                name='Drawdown',
                line=dict(color='#ff3366', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 51, 102, 0.2)'
            )
        )
        
        fig_dd.update_layout(
            title="Underwater Plot (Drawdown %)",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template='plotly_dark',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # Cash vs Invested
        st.markdown("### Cash vs Invested Capital")
        
        fig_alloc = go.Figure()
        
        fig_alloc.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Cash'],
                name='Cash',
                line=dict(color='cyan', width=2),
                stackgroup='one'
            )
        )
        
        fig_alloc.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Positions_Value'],
                name='Invested',
                line=dict(color='#00ff88', width=2),
                stackgroup='one'
            )
        )
        
        fig_alloc.update_layout(
            title="Portfolio Allocation",
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            template='plotly_dark',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_alloc, use_container_width=True)
    
    with tab3:
        st.markdown("### Trade Analysis")
        
        trade_df = results['trade_history']
        
        if not trade_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # P&L distribution
                fig_pnl = go.Figure()
                
                winning_trades = trade_df[trade_df['PnL'] > 0]
                losing_trades = trade_df[trade_df['PnL'] < 0]
                
                fig_pnl.add_trace(
                    go.Bar(
                        x=winning_trades.index,
                        y=winning_trades['PnL'],
                        name='Wins',
                        marker_color='#00ff88'
                    )
                )
                
                fig_pnl.add_trace(
                    go.Bar(
                        x=losing_trades.index,
                        y=losing_trades['PnL'],
                        name='Losses',
                        marker_color='#ff3366'
                    )
                )
                
                fig_pnl.update_layout(
                    title="Trade P&L Distribution",
                    xaxis_title="Trade Number",
                    yaxis_title="P&L (₹)",
                    template='plotly_dark',
                    height=400
                )
                
                st.plotly_chart(fig_pnl, use_container_width=True)
            
            with col2:
                # Trade duration
                fig_duration = go.Figure()
                
                fig_duration.add_trace(
                    go.Histogram(
                        x=trade_df['Duration_Days'],
                        nbinsx=20,
                        name='Duration',
                        marker_color='#00d4ff'
                    )
                )
                
                fig_duration.update_layout(
                    title="Trade Duration Distribution",
                    xaxis_title="Days Held",
                    yaxis_title="Number of Trades",
                    template='plotly_dark',
                    height=400
                )
                
                st.plotly_chart(fig_duration, use_container_width=True)
            
            # Exit reason pie chart
            st.markdown("### Exit Reasons")
            
            exit_reasons = trade_df['Exit_Reason'].value_counts()
            
            fig_exit = go.Figure(
                data=[
                    go.Pie(
                        labels=exit_reasons.index,
                        values=exit_reasons.values,
                        hole=0.4,
                        marker_colors=['#00ff88', '#ff3366', '#00d4ff', '#ffa500']
                    )
                ]
            )
            
            fig_exit.update_layout(
                title="Trade Exit Reasons",
                template='plotly_dark',
                height=400
            )
            
            st.plotly_chart(fig_exit, use_container_width=True)
            
        else:
            st.warning("No trades were executed in this backtest.")
    
    with tab4:
        st.markdown("### Risk Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Return Metrics")
            st.metric("Total Return", f"{metrics['Total Return (%)']:.2f}%")
            st.metric("Annualized Return", f"{metrics['Annualized Return (%)']:.2f}%")
            st.metric("Average Trade Return", f"{metrics['Average Trade (%)']:.2f}%")
            st.metric("Best Trade", f"{metrics['Best Trade (%)']:.2f}%")
            st.metric("Worst Trade", f"{metrics['Worst Trade (%)']:.2f}%")
        
        with col2:
            st.markdown("#### Risk Metrics")
            st.metric("Volatility (Annualized)", f"{metrics['Volatility (%)']:.2f}%")
            st.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
            st.metric("Max Drawdown", f"{abs(metrics['Max Drawdown (%)']):.2f}%")
            st.metric("Calmar Ratio", f"{metrics['Calmar Ratio']:.2f}")
            st.metric("Profit Factor", f"{metrics['Profit Factor']:.2f}")
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Trade Statistics")
            st.metric("Total Trades", f"{int(metrics['Total Trades'])}")
            st.metric("Winning Trades", f"{int(metrics['Winning Trades'])}")
            st.metric("Losing Trades", f"{int(metrics['Losing Trades'])}")
            st.metric("Win Rate", f"{metrics['Win Rate (%)']:.1f}%")
        
        with col4:
            st.markdown("#### Advanced Metrics")
            st.metric("Avg Winning Trade", f"{metrics['Average Winning Trade (%)']:.2f}%")
            st.metric("Avg Losing Trade", f"{metrics['Average Losing Trade (%)']:.2f}%")
            st.metric("Avg Hold Time", f"{metrics['Average Hold Time (days)']:.1f} days")
            st.metric("Max DD Duration", f"{int(metrics['Max Drawdown Duration (days)'])} days")
    
    with tab5:
        st.markdown("### Complete Trade Log")
        
        trade_df = results['trade_history']
        
        if not trade_df.empty:
            # Format dataframe for display
            display_df = trade_df.copy()
            display_df['Entry_Date'] = pd.to_datetime(display_df['Entry_Date']).dt.strftime('%Y-%m-%d')
            display_df['Exit_Date'] = pd.to_datetime(display_df['Exit_Date']).dt.strftime('%Y-%m-%d')
            display_df['Entry_Price'] = display_df['Entry_Price'].apply(lambda x: f"₹{x:.2f}")
            display_df['Exit_Price'] = display_df['Exit_Price'].apply(lambda x: f"₹{x:.2f}")
            display_df['PnL'] = display_df['PnL'].apply(lambda x: f"₹{x:.2f}")
            display_df['PnL_Pct'] = display_df['PnL_Pct'].apply(lambda x: f"{x*100:.2f}%")
            
            st.dataframe(
                display_df[[
                    'Symbol', 'Entry_Date', 'Exit_Date', 
                    'Entry_Price', 'Exit_Price', 'Quantity',
                    'PnL', 'PnL_Pct', 'Duration_Days', 'Exit_Reason'
                ]],
                use_container_width=True,
                height=600
            )
            
            # Download button
            csv = trade_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Trade Log (CSV)",
                data=csv,
                file_name="trade_log.csv",
                mime="text/csv"
            )
        else:
            st.warning("No trades were executed in this backtest.")

else:
    # Welcome message when no backtest has been run
    st.markdown("""
    ## Welcome to the Algorithmic Trading System! 👋
    
    This platform allows you to backtest a **multi-indicator momentum strategy** on Indian equity markets.
    
    ### 🎯 Strategy Overview
    
    The strategy combines multiple technical indicators to identify high-probability trading opportunities:
    
    - **Moving Averages**: Trend identification using golden/death crosses
    - **RSI (Relative Strength Index)**: Momentum and overbought/oversold conditions
    - **MACD**: Trend strength and direction changes
    - **Bollinger Bands**: Volatility-based entry/exit points
    
    ### 🚀 Getting Started
    
    1. **Select stocks** from the sidebar (1-5 stocks recommended)
    2. **Choose date range** for backtesting
    3. **Adjust strategy parameters** (optional - defaults are optimized)
    4. **Configure risk management** settings
    5. **Click "Run Backtest"** to see results
    
    ### 📊 What You'll See
    
    After running the backtest, you'll get:
    
    - **Price charts** with buy/sell signals overlaid
    - **Portfolio performance** tracking over time
    - **Comprehensive metrics**: Returns, Sharpe ratio, drawdown, win rate
    - **Trade analysis**: P&L distribution, duration, exit reasons
    - **Detailed trade log**: Every trade with entry/exit details
    
    ---
    
    **Ready to start?** Configure your parameters in the sidebar and click "Run Backtest"! 🚀
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 2rem;'>"
    "Built with ❤️ using Streamlit | Algorithmic Trading System v1.0"
    "</div>",
    unsafe_allow_html=True
)
