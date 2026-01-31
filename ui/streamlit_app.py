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
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from data.fetcher import fetch_equity_data
from data.preprocessor import preprocess_data
from data.futures_fetcher import load_futures_data, get_available_date_range
from strategy.indicators import add_indicators
from strategy.signals import generate_signals
from backtesting.engine import run_backtest
from backtesting.futures_engine import run_futures_backtest
from backtesting.metrics import PerformanceMetrics

# Page configuration
st.set_page_config(
    page_title="Algorithmic Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Title and description
st.markdown("<h1>📈 Algorithmic Trading System</h1>", unsafe_allow_html=True)
st.markdown("**Multi-Indicator Momentum Strategy** | Equity Markets")

# Sidebar controls
st.sidebar.markdown("## ⚙️ Configuration")

# Market Type Selection
st.sidebar.markdown("### 📊 Market Type")
market_type = st.sidebar.radio(
    "Select Market",
    options=["Equity", "Futures"],
    horizontal=True,
    help="Choose between Equity trading (stocks) or Futures trading"
)

st.sidebar.markdown("---")

# Stock selection (only for Equity mode)
if market_type == "Equity":
    # Data Source Selection
    st.sidebar.markdown("### 📁 Data Source")
    data_source = st.sidebar.radio(
        "Choose data source",
        options=["API/Mock Data", "Upload Excel"],
        horizontal=True,
        help="Use API data or upload your own Excel file"
    )
    
    uploaded_file = None
    selected_stocks = []
    
    if data_source == "Upload Excel":
        st.sidebar.markdown("#### 📤 Upload Data File")
        uploaded_file = st.sidebar.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Upload Excel file with columns: Date, Symbol, Open, High, Low, Close, Volume"
        )
        
        if uploaded_file is not None:
            st.sidebar.success("✓ File uploaded successfully!")
            # We'll parse this later to get symbols
        else:
            st.sidebar.info(
                "📋 **Required columns:**\n"
                "- Date (YYYY-MM-DD)\n"
                "- Symbol (e.g., RELIANCE)\n"
                "- Open, High, Low, Close\n"
                "- Volume"
            )
            
            # Create and offer sample template download
            import io
            
            # Generate sample in memory
            sample_buffer = io.BytesIO()
            dates = pd.date_range('2023-01-01', '2023-01-10', freq='B')
            sample_data = []
            for symbol in ['RELIANCE', 'TCS']:
                base_price = 2000 if symbol == 'RELIANCE' else 3500
                for date in dates:
                    sample_data.append({
                        'Date': date,
                        'Symbol': symbol,
                        'Open': base_price + 10,
                        'High': base_price + 20,
                        'Low': base_price - 10,
                        'Close': base_price + 5,
                        'Volume': 1000000
                    })
            sample_df = pd.DataFrame(sample_data)
            sample_df.to_excel(sample_buffer, index=False, engine='openpyxl')
            sample_buffer.seek(0)
            
            st.sidebar.download_button(
                label="📥 Download Sample Template",
                data=sample_buffer,
                file_name="sample_trading_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download a sample Excel file to see the required format"
            )
    
    else:  # API/Mock Data
        st.sidebar.markdown("### 📊 Select Stocks")
        available_stocks = [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
            'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT'
        ]
        
        selected_stocks = st.sidebar.multiselect(
            "Choose stocks to analyze",
            options=available_stocks,
            default=['RELIANCE'],
            help="Select 1-5 stocks for backtesting"
        )
    
    # Date range
    st.sidebar.markdown("### 📅 Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime('2023-01-01')
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime('2024-01-01')
        )
    
    # Strategy parameters
    st.sidebar.markdown("### 🎯 Strategy Parameters")
    
    with st.sidebar.expander("Moving Averages", expanded=False):
        short_ma = st.slider("Short MA Period", 5, 30, 10)
        long_ma = st.slider("Long MA Period", 20, 60, 30)
    
    with st.sidebar.expander("RSI", expanded=False):
        rsi_period = st.slider("RSI Period", 7, 21, 14)
        rsi_oversold = st.slider("RSI Oversold", 20, 40, 30)
        rsi_overbought = st.slider("RSI Overbought", 60, 80, 70)
    
    with st.sidebar.expander("MACD", expanded=False):
        macd_fast = st.slider("MACD Fast", 8, 16, 12)
        macd_slow = st.slider("MACD Slow", 20, 30, 26)
        macd_signal = st.slider("MACD Signal", 7, 12, 9)
    
    # Risk management for Equity
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
        value=15,
        help="Percentage of portfolio per trade"
    ) / 100
    
    max_positions = st.sidebar.slider(
        "Max Concurrent Positions",
        min_value=1,
        max_value=5,
        value=4
    )
    
    stop_loss = st.sidebar.slider(
        "Stop Loss (%)",
        min_value=1,
        max_value=15,
        value=7,
        help="Percentage below entry price"
    ) / 100
    
    take_profit = st.sidebar.slider(
        "Take Profit (%)",
    min_value=5,
    max_value=30,
    value=15,
    help="Percentage above entry price"
) / 100

else:  # Futures mode
    # Data Source Selection for Futures
    st.sidebar.markdown("### 📁 Data Source")
    futures_data_source = st.sidebar.radio(
        "Choose data source",
        options=["Use Stored Data", "Upload Excel"],
        horizontal=True,
        help="Use pre-loaded NIFTY futures data or upload your own"
    )
    
    futures_uploaded_file = None
    
    if futures_data_source == "Upload Excel":
        st.sidebar.markdown("#### 📤 Upload Futures Data")
        futures_uploaded_file = st.sidebar.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Upload Excel file with NIFTY futures OHLCV data",
            key="futures_upload"
        )
        
        if futures_uploaded_file is not None:
            st.sidebar.success("✓ File uploaded successfully!")
        else:
            st.sidebar.info(
                "� **Required columns:**\n"
                "- date/Date\n"
                "- tradingsymbol/Symbol\n"
                "- open, high, low, close\n"
                "- volume\n"
                "- time (optional)"
            )
            
            # Sample template for futures
            import io
            sample_buffer = io.BytesIO()
            dates = pd.date_range('2025-12-01', '2025-12-10', freq='B')
            sample_data = []
            base_price = 26000
            for date in dates:
                sample_data.append({
                    'date': date,
                    'time': '00:00:00',
                    'tradingsymbol': 'NIFTY',
                    'open': base_price + 10,
                    'high': base_price + 50,
                    'low': base_price - 30,
                    'close': base_price + 20,
                    'volume': 0
                })
            sample_df = pd.DataFrame(sample_data)
            sample_df.to_excel(sample_buffer, index=False, engine='openpyxl')
            sample_buffer.seek(0)
            
            st.sidebar.download_button(
                label="📥 Download Futures Template",
                data=sample_buffer,
                file_name="sample_nifty_futures.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download a sample Excel file for NIFTY futures data"
            )
    else:
        st.sidebar.info("📊 Using pre-loaded NIFTY futures data")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Futures Trading")
    
    # Strategy parameters for Futures
    st.sidebar.markdown("### 🎯 Strategy Parameters")
    
    with st.sidebar.expander("Risk-Reward Settings", expanded=True):
        min_rr = st.slider(
            "Minimum R:R Ratio",
            min_value=1.0,
            max_value=3.0,
            value=1.1,
            step=0.1,
            help="Minimum risk-reward ratio for trade entry"
        )
        
        min_stop_points = st.slider(
            "Min Stop Distance (pts)",
            min_value=5,
            max_value=30,
            value=10,
            help="Minimum stop loss distance in points"
        )
    
    with st.sidebar.expander("Trade Management", expanded=True):
        max_daily_losses = st.slider(
            "Max Daily Losses",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum losing trades per day before stopping"
        )
        
        risk_percent_bullish = st.slider(
            "Risk % (Biased)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.5,
            help="Risk per trade when market bias is clear"
        ) / 100
        
        risk_percent_neutral = st.slider(
            "Risk % (Neutral)",
            min_value=0.5,
            max_value=3.0,
            value=1.0,
            step=0.5,
            help="Risk per trade in neutral market"
        ) / 100
    
    # Capital for Futures
    st.sidebar.markdown("### 💰 Capital")
    initial_capital = st.sidebar.number_input(
        "Initial Capital (₹)",
        min_value=100000,
        max_value=10000000,
        value=1000000,
        step=100000,
        format="%d"
    )

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
    if market_type == "Equity":
        # Check if we have either selected stocks or uploaded file
        if data_source == "API/Mock Data" and not selected_stocks:
            st.error("⚠️ Please select at least one stock!")
        elif data_source == "Upload Excel" and uploaded_file is None:
            st.error("⚠️ Please upload an Excel file!")
        else:
            with st.spinner('🔄 Fetching data and running backtest...'):
                try:
                    # Fetch data based on source
                    progress_bar = st.progress(0)
                    
                    if data_source == "Upload Excel":
                        # Load from uploaded file
                        st.info("📂 Loading data from uploaded file...")
                        progress_bar.progress(20)
                        
                        from data.excel_loader import load_excel_data
                        raw_data = load_excel_data(uploaded_file.read())
                        
                        # Get symbols from uploaded data
                        selected_stocks = raw_data['Symbol'].unique().tolist()
                        st.info(f"📊 Found {len(selected_stocks)} symbol(s): {', '.join(selected_stocks)}")
                        
                    else:
                        # Fetch from API/Mock
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
                    
                    # Run backtest
                    st.info("⚙️ Running backtest simulation...")
                    progress_bar.progress(85)
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
                    
                    progress_bar.progress(100)
                    
                    #Check if mock data was used (will have predictable patterns)
                    if len(raw_data) > 0:
                        # Check if this looks like mock data (Symbol column values)
                        if hasattr(raw_data, 'attrs') and raw_data.attrs.get('is_mock_data'):
                            st.warning("⚠️ **Using Mock Data**: The Hackathon API did not return data. Results are based on synthetic data for testing purposes only.")
                    
                    # Store in session state
                    st.session_state.backtest_results = results
                    st.session_state.metrics = metrics
                    st.session_state.market_type = "Equity"
                    
                    st.success("✅ Backtest completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error during backtest: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    else:  # Futures mode
        with st.spinner('🔄 Loading futures data and running backtest...'):
            try:
                progress_bar = st.progress(0)
                
                # Handle data source
                futures_data = None
                if futures_data_source == "Upload Excel" and futures_uploaded_file is not None:
                    st.info("📂 Loading futures data from uploaded file...")
                    progress_bar.progress(20)
                    
                    from data.excel_loader import load_excel_data
                    futures_data = load_excel_data(futures_uploaded_file.read())
                    
                    symbols = futures_data['Symbol'].unique().tolist()
                    st.info(f"📊 Found {len(futures_data)} records for: {', '.join(symbols)}")
                else:
                    st.info("📥 Loading pre-stored futures data...")
                
                progress_bar.progress(30)
                
                # Run futures backtest
                st.info("⚙️ Running futures backtest with smart money concepts...")
                progress_bar.progress(50)
                
                results = run_futures_backtest(
                    initial_capital=initial_capital,
                    min_rr=min_rr,
                    max_daily_losses=max_daily_losses,
                    min_stop_points=min_stop_points,
                    risk_percent_bullish=risk_percent_bullish,
                    risk_percent_neutral=risk_percent_neutral,
                    custom_data=futures_data
                )
                
                # Calculate metrics for futures
                st.info("📊 Calculating performance metrics...")
                progress_bar.progress(85)
                
                if not results['trade_history'].empty:
                    metrics_calc = PerformanceMetrics(results)
                    metrics = metrics_calc.calculate_all_metrics()
                else:
                    # No trades executed
                    metrics = {}
                
                progress_bar.progress(100)
                
                # Store in session state
                st.session_state.backtest_results = results
                st.session_state.metrics = metrics
                st.session_state.market_type = "Futures"
                
                st.success("✅ Futures backtest completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error during futures backtest: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# Display results
if st.session_state.backtest_results is not None:
    results = st.session_state.backtest_results
    metrics = st.session_state.metrics
    
    # Key metrics at the top
    st.markdown("## 📊 Performance Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
    
    # Tabs for different visualizations
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Price Charts", "💰 Portfolio Performance", "📊 Trade Analysis", "⚠️ Risk Metrics", "📋 Trade Log"
    ])
    
    with tab1:
        st.markdown("### Price Charts with Trade Signals")
        
        # Check market type and show appropriate selector
        market_mode = st.session_state.get('market_type', 'Equity')
        
        if market_mode == "Equity":
            # Get selected stocks from results data
            available_symbols = results['data']['Symbol'].unique().tolist()
            display_stock = st.selectbox(
                "Select stock to view",
                options=available_symbols
            )
        else:
            # Futures mode - only one symbol
            display_stock = "NIFTY_FUT"
            st.info("📊 Viewing NIFTY Futures")
        
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
                    x=stock_data['datetime'] if 'datetime' in stock_data.columns else stock_data.get('Date', stock_data.index),
                    open=stock_data['open'] if 'open' in stock_data.columns else stock_data.get('Open'),
                    high=stock_data['high'] if 'high' in stock_data.columns else stock_data.get('High'),
                    low=stock_data['low'] if 'low' in stock_data.columns else stock_data.get('Low'),
                    close=stock_data['close'] if 'close' in stock_data.columns else stock_data.get('Close'),
                    name='Price'
                ),
                row=1, col=1
            )
            
            # Only add indicators for equity mode
            if market_mode == "Equity" and 'MA_Short' in stock_data.columns:
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
            
            # Volume (available for both modes)
            volume_col = 'volume' if 'volume' in stock_data.columns else 'Volume'
            if volume_col in stock_data.columns:
                x_col = 'datetime' if 'datetime' in stock_data.columns else 'Date'
                fig.add_trace(
                    go.Bar(
                        x=stock_data[x_col],
                        y=stock_data[volume_col] if volume_col in stock_data.columns else None,
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
            if market_mode == "Equity":
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
