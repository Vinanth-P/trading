"""
Futures Backtesting Engine
Wrapper for futures strategy backtesting compatible with Streamlit UI.
"""
import sys
import pandas as pd
from pathlib import Path
from datetime import timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from futures.strategy import check_for_trade
from data.futures_fetcher import load_futures_data, get_daily_levels


def run_futures_backtest(
    initial_capital=1000000,
    min_rr=1.1,
    max_daily_losses=3,
    min_stop_points=10,
    risk_percent_bullish=0.02,
    risk_percent_neutral=0.01,
    custom_data=None
):
    """
    Run futures backtest with smart money concepts strategy.
    
    Args:
        initial_capital: Starting capital in INR
        min_rr: Minimum risk-reward ratio
        max_daily_losses: Maximum losses allowed per day
        min_stop_points: Minimum stop distance in points
        risk_percent_bullish: Risk per trade when biased (%)
        risk_percent_neutral: Risk per trade when neutral (%)
        custom_data: Optional DataFrame with custom data (for Excel uploads)
        
    Returns:
        dict: Backtest results with trade history, portfolio history, and data
    """
    # Load data
    if custom_data is not None:
        # Use uploaded data
        df = custom_data.copy()
        # Ensure datetime index
        if 'Date' in df.columns:
            df['datetime'] = pd.to_datetime(df['Date'])
            df = df.set_index('datetime')
        # Ensure lowercase column names for consistency
        df.columns = [col.lower() if col not in ['datetime', 'Date'] else col for col in df.columns]
    else:
        # Load default futures data
        df = load_futures_data()
    
    daily = get_daily_levels(df)
    
    # Initialize tracking
    equity = initial_capital
    trades_log = []
    portfolio_history = []
    open_trade = None
    state = None
    current_date = None
    
    # Run backtest
    for ts, row in df.iterrows():
        day = ts.date()
        
        # Reset daily state at start of new day
        if day != current_date:
            current_date = day
            if day in daily.index:
                state = {
                    "equity": equity,
                    "losses": 0,
                    "bias": "NEUTRAL",
                    "pdh": daily.loc[day, "PDH"],
                    "pdl": daily.loc[day, "PDL"],
                    "h1_highs": [],
                    "h1_lows": [],
                    "h4_highs": [],
                    "h4_lows": [],
                    "h1_fvgs": [],
                }
        
        # Track portfolio value
        portfolio_value = equity
        if open_trade:
            # Calculate unrealized P&L
            if open_trade["direction"] == "LONG":
                unrealized_pnl = open_trade["qty"] * (row.close - open_trade["entry"])
            else:
                unrealized_pnl = open_trade["qty"] * (open_trade["entry"] - row.close)
            portfolio_value = equity + unrealized_pnl
        
        portfolio_history.append({
            "Date": ts,
            "Portfolio_Value": portfolio_value,
            "Cash": equity,
            "Positions_Value": portfolio_value - equity
        })
        
        # Check for exit if in a trade
        if open_trade:
            elapsed = ts - open_trade["entry_time"]
            exit_price = None
            exit_reason = None
            
            if open_trade["direction"] == "LONG":
                if row.low <= open_trade["stop"]:
                    exit_price = open_trade["stop"]
                    exit_reason = "Stop Loss"
                elif row.high >= open_trade["target"]:
                    exit_price = open_trade["target"]
                    exit_reason = "Target Hit"
            else:  # SHORT
                if row.high >= open_trade["stop"]:
                    exit_price = open_trade["stop"]
                    exit_reason = "Stop Loss"
                elif row.low <= open_trade["target"]:
                    exit_price = open_trade["target"]
                    exit_reason = "Target Hit"
            
            # Time-based exit (24 hours)
            if exit_price is None and elapsed >= timedelta(hours=24):
                exit_price = row.close
                exit_reason = "Time Exit"
            
            # Exit trade
            if exit_price is not None:
                pnl = open_trade["qty"] * (
                    exit_price - open_trade["entry"]
                    if open_trade["direction"] == "LONG"
                    else open_trade["entry"] - exit_price
                )
                
                equity += pnl
                if pnl < 0:
                    state["losses"] += 1
                
                duration = (ts - open_trade["entry_time"]).total_seconds() / 3600  # hours
                
                trades_log.append({
                    "Symbol": "NIFTY_FUT",
                    "Entry_Date": open_trade["entry_time"],
                    "Exit_Date": ts,
                    "Direction": open_trade["direction"],
                    "Entry_Price": open_trade["entry"],
                    "Exit_Price": exit_price,
                    "Quantity": open_trade["qty"],
                    "PnL": pnl,
                    "PnL_Pct": (pnl / (open_trade["qty"] * open_trade["entry"])),
                    "Duration_Hours": duration,
                    "Duration_Days": duration / 24,
                    "Exit_Reason": exit_reason,
                    "RR": open_trade["rr"],
                    "Bias": open_trade["bias"],
                    "Execution_POI": open_trade["execution_poi"],
                    "Entry_Model": open_trade["entry_model"]
                })
                
                open_trade = None
            continue
        
        # Check for new trade entry
        if state is not None:
            trade = check_for_trade(row, df, ts, state, equity)
            if trade:
                open_trade = trade
    
    # Create results dictionary
    df_result = df.reset_index()
    df_result['Symbol'] = 'NIFTY_FUT'  # Add Symbol column for consistency with equity data
    
    results = {
        "trade_history": pd.DataFrame(trades_log),
        "portfolio_history": pd.DataFrame(portfolio_history),
        "data": df_result,
        "initial_capital": initial_capital,
        "final_capital": equity
    }
    
    return results
