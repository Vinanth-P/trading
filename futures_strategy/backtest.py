"""
Futures Backtesting Engine
Uses ICT-based strategy for NIFTY futures.
REALISTIC simulation with proper trade outcomes.
"""

import pandas as pd
import numpy as np
from .strategy import check_for_trade

INITIAL_EQUITY = 1_000_000
LOT_SIZE = 50  # NIFTY lot size
MAX_LOTS = 10  # Maximum lots per trade
SLIPPAGE_POINTS = 2  # Slippage in points


def compute_h1_levels(df, current_ts, lookback_hours=24):
    """Compute 1H swing highs and lows"""
    try:
        h1 = df.loc[:current_ts].resample('1H').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
        }).dropna().tail(lookback_hours)
        
        if len(h1) < 3:
            return [], []
        
        highs = []
        lows = []
        
        for i in range(1, len(h1) - 1):
            if h1.iloc[i].high > h1.iloc[i-1].high and h1.iloc[i].high > h1.iloc[i+1].high:
                highs.append(h1.iloc[i].high)
            if h1.iloc[i].low < h1.iloc[i-1].low and h1.iloc[i].low < h1.iloc[i+1].low:
                lows.append(h1.iloc[i].low)
        
        return highs[-5:], lows[-5:]
    except:
        return [], []


def compute_h4_levels(df, current_ts, lookback_hours=96):
    """Compute 4H swing highs and lows"""
    try:
        h4 = df.loc[:current_ts].resample('4H').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
        }).dropna().tail(lookback_hours // 4)
        
        if len(h4) < 3:
            return [], []
        
        highs = []
        lows = []
        
        for i in range(1, len(h4) - 1):
            if h4.iloc[i].high > h4.iloc[i-1].high and h4.iloc[i].high > h4.iloc[i+1].high:
                highs.append(h4.iloc[i].high)
            if h4.iloc[i].low < h4.iloc[i-1].low and h4.iloc[i].low < h4.iloc[i+1].low:
                lows.append(h4.iloc[i].low)
        
        return highs[-3:], lows[-3:]
    except:
        return [], []


def compute_h1_fvgs(df, current_ts, lookback_candles=60):
    """Detect 1H Fair Value Gaps"""
    try:
        h1 = df.loc[:current_ts].resample('1H').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
        }).dropna().tail(lookback_candles)
        
        fvgs = []
        
        for i in range(2, len(h1)):
            c1 = h1.iloc[i-2]
            c3 = h1.iloc[i]
            
            if c1.high < c3.low:
                fvgs.append((c1.high, c3.low))
            
            if c1.low > c3.high:
                fvgs.append((c3.high, c1.low))
        
        return fvgs[-5:]
    except:
        return []


def determine_daily_bias(day_df):
    """Determine daily bias based on morning session"""
    try:
        morning = day_df.between_time("09:15", "10:30")
        if morning.empty:
            return "NEUTRAL"
        
        morning_open = morning.iloc[0].open
        morning_close = morning.iloc[-1].close
        
        change_pct = (morning_close - morning_open) / morning_open * 100
        
        if change_pct > 0.15:
            return "BULLISH"
        elif change_pct < -0.15:
            return "BEARISH"
        else:
            return "NEUTRAL"
    except:
        return "NEUTRAL"


def simulate_trade_outcome(entry_ts, entry_price, stop_price, target_price, direction, day_df):
    """
    Simulate actual trade outcome by checking which price level is hit first.
    Returns: (exit_price, exit_reason, exit_time)
    """
    try:
        # Get candles after entry
        future_candles = day_df.loc[entry_ts:]
        
        if len(future_candles) < 2:
            # Exit at last available price
            return entry_price, "EOD", entry_ts
        
        for ts, candle in future_candles.iloc[1:].iterrows():  # Skip entry candle
            if direction == "LONG":
                # Check if stop hit first (more conservative)
                if candle.low <= stop_price:
                    return stop_price - SLIPPAGE_POINTS, "STOP_LOSS", ts
                # Check if target hit
                if candle.high >= target_price:
                    return target_price - SLIPPAGE_POINTS, "TARGET", ts
            else:  # SHORT
                # Check if stop hit first
                if candle.high >= stop_price:
                    return stop_price + SLIPPAGE_POINTS, "STOP_LOSS", ts
                # Check if target hit
                if candle.low <= target_price:
                    return target_price + SLIPPAGE_POINTS, "TARGET", ts
        
        # End of day - exit at last close
        last_candle = future_candles.iloc[-1]
        return last_candle.close, "EOD", future_candles.index[-1]
        
    except Exception as e:
        return entry_price, "ERROR", entry_ts


def run_futures_backtest(df, initial_equity=INITIAL_EQUITY):
    """
    Run backtest on futures data using ICT strategy.
    REALISTIC: Simulates actual trade outcomes based on price action.
    """
    
    # Prepare data
    df = df.copy()
    
    # Handle datetime column/index
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Ensure column names are lowercase
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Sort and clean
    df.sort_index(inplace=True)
    df = df[['open', 'high', 'low', 'close']].dropna()
    
    df['date'] = df.index.date

    # Get daily high/low for PDH/PDL
    daily = df.groupby('date').agg(
        PDH=('high', 'max'),
        PDL=('low', 'min')
    )

    equity = initial_equity
    trades_log = []
    equity_history = []
    dates = list(df['date'].unique())

    # Add signal columns
    df['signal'] = 0
    df['trade_type'] = ''

    for i, day in enumerate(dates):
        day_df = df[df['date'] == day]
        
        if day_df.empty:
            continue

        # Get PDH/PDL from previous day
        if i > 0:
            prev_day = dates[i-1]
            pdh = daily.loc[prev_day, 'PDH']
            pdl = daily.loc[prev_day, 'PDL']
        else:
            pdh = daily.loc[day, 'PDH']
            pdl = daily.loc[day, 'PDL']

        # Determine daily bias
        bias = determine_daily_bias(day_df)

        # Initialize daily state
        state = {
            'equity': equity,
            'trades': 0,
            'losses': 0,
            'bias': bias,
            'pdh': pdh,
            'pdl': pdl,
            'h1_highs': [],
            'h1_lows': [],
            'h4_highs': [],
            'h4_lows': [],
            'h1_fvgs': [],
        }
        
        # Track if we're in a trade (no overlapping trades)
        in_trade = False
        trade_exit_time = None

        for ts, row in day_df.iterrows():
            # Skip if still in previous trade
            if in_trade and trade_exit_time and ts <= trade_exit_time:
                continue
            else:
                in_trade = False
            
            # Update context levels every hour
            if ts.minute == 0:
                state['h1_highs'], state['h1_lows'] = compute_h1_levels(df, ts)
                state['h4_highs'], state['h4_lows'] = compute_h4_levels(df, ts)
                state['h1_fvgs'] = compute_h1_fvgs(df, ts)
            
            # Check for trade signal
            trade = check_for_trade(row, day_df, ts, state, equity)
            
            if trade is None:
                continue

            direction = trade['direction']
            entry_price = trade['entry']
            stop_price = trade['stop']
            target_price = trade['target']
            
            # Calculate proper position size (in lots)
            risk_per_point = abs(entry_price - stop_price)
            if risk_per_point == 0:
                continue
            
            # Risk 1-2% of equity
            risk_amount = equity * trade['risk_pct']
            
            # Calculate lots (capped)
            lots = min(int(risk_amount / (risk_per_point * LOT_SIZE)), MAX_LOTS)
            if lots < 1:
                lots = 1
            
            qty = lots * LOT_SIZE
            
            # SIMULATE actual trade outcome
            exit_price, exit_reason, exit_time = simulate_trade_outcome(
                ts, entry_price, stop_price, target_price, direction, day_df
            )
            
            # Calculate P&L
            if direction == 'LONG':
                pnl = qty * (exit_price - entry_price)
            else:
                pnl = qty * (entry_price - exit_price)
            
            # Apply slippage on entry
            pnl -= qty * SLIPPAGE_POINTS / LOT_SIZE

            # Update equity and state
            equity += pnl
            state['equity'] = equity
            state['trades'] += 1
            if pnl < 0:
                state['losses'] += 1
            
            # Mark trade
            in_trade = True
            trade_exit_time = exit_time

            # Mark signal on data
            df.loc[ts, 'signal'] = 1 if direction == 'LONG' else -1
            df.loc[ts, 'trade_type'] = direction

            trades_log.append({
                'date': day,
                'time': ts,
                'direction': direction,
                'bias': trade['bias'],
                'entry': entry_price,
                'stop': stop_price,
                'target': target_price,
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'exit_time': exit_time,
                'rr': trade['rr'],
                'lots': lots,
                'qty': qty,
                'pnl': pnl,
                'equity': equity,
                'execution_poi': trade.get('execution_poi', ''),
                'entry_model': trade.get('entry_model', '')
            })

        # Record end-of-day equity
        equity_history.append({
            'date': day,
            'equity': equity
        })

    # Create results
    trades_df = pd.DataFrame(trades_log)
    equity_df = pd.DataFrame(equity_history)
    
    # Calculate metrics
    metrics = calculate_futures_metrics(trades_df, initial_equity, equity)
    
    return {
        'trades_df': trades_df,
        'equity_curve': equity_df,
        'metrics': metrics,
        'data': df,
        'initial_capital': initial_equity,
        'final_capital': equity,
        'asset_class': 'futures'
    }


def calculate_futures_metrics(trades_df, initial_equity, final_equity):
    """Calculate performance metrics"""
    
    if trades_df.empty:
        return {
            'Total Trades': 0,
            'Winning Trades': 0,
            'Losing Trades': 0,
            'Win Rate': 0,
            'Total Return': 0,
            'Total PnL': 0,
            'Average Trade PnL': 0,
            'Best Trade': 0,
            'Worst Trade': 0,
            'Profit Factor': 0,
            'Average RR': 0
        }
    
    winning = trades_df[trades_df['pnl'] > 0]
    losing = trades_df[trades_df['pnl'] <= 0]
    
    total_profit = winning['pnl'].sum() if not winning.empty else 0
    total_loss = abs(losing['pnl'].sum()) if not losing.empty else 1  # Avoid division by zero
    
    return {
        'Total Trades': len(trades_df),
        'Winning Trades': len(winning),
        'Losing Trades': len(losing),
        'Win Rate': len(winning) / len(trades_df) * 100 if len(trades_df) > 0 else 0,
        'Total Return': (final_equity - initial_equity) / initial_equity * 100,
        'Total PnL': trades_df['pnl'].sum(),
        'Average Trade PnL': trades_df['pnl'].mean(),
        'Best Trade': trades_df['pnl'].max(),
        'Worst Trade': trades_df['pnl'].min(),
        'Profit Factor': total_profit / total_loss if total_loss > 0 else 0,
        'Average RR': trades_df['rr'].mean() if 'rr' in trades_df.columns else 0
    }
