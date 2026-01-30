"""
Options Backtester
==================

Simulates options trading on historical data.

🎓 FOR BEGINNERS:
This module does the same thing as the equity backtester, but for options:
1. Get equity signals (BUY/SELL) from the existing strategy
2. Convert signals to option trades (CALL/PUT)
3. Track option positions and P&L
4. Calculate performance metrics

⚠️ HACKATHON SIMPLIFICATION:
- Uses simplified option pricing (2% of stock price)
- No Greeks, no theta decay, no volatility modeling
- Simple percentage-based entry/exit
- Reuses ALL existing equity signal logic

The key insight: We don't need a separate options strategy.
We just convert equity signals to options trades!
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from options.option_contract import OptionContract, OptionType
from options.option_selector import OptionSelector
from options.option_strategy import OptionExitStrategy, ExitConditions


@dataclass
class OptionsPortfolio:
    """
    Tracks options positions and cash.
    
    Similar to equity Portfolio but simplified for options:
    - Only tracks LONG options (buying calls/puts)
    - Max loss = premium paid
    - No margin requirements
    """
    initial_capital: float
    cash: float
    positions: Dict[str, OptionContract]  # symbol -> active option
    closed_trades: List[dict]
    portfolio_values: List[dict]
    
    @classmethod
    def create(cls, initial_capital: float) -> 'OptionsPortfolio':
        """Create a new options portfolio."""
        return cls(
            initial_capital=initial_capital,
            cash=initial_capital,
            positions={},
            closed_trades=[],
            portfolio_values=[]
        )


class OptionsBacktester:
    """
    Backtests options trading strategy.
    
    How it works:
    1. Takes DataFrame with equity signals (from existing strategy)
    2. Converts BUY → CALL, SELL → PUT
    3. Tracks option positions with simplified pricing
    4. Exits based on profit target, stop loss, or signal reversal
    5. Calculates performance metrics
    
    ⚠️ SIMPLIFIED for hackathon:
    - No real option prices (uses 2% of stock price estimate)
    - No Greeks updates or theta decay
    - One position per symbol at a time
    - Fixed position size (configurable)
    """
    
    def __init__(
        self,
        initial_capital: float = 1000000,
        position_size_pct: float = 0.10,  # 10% per trade
        max_positions: int = 5,
        profit_target_pct: float = 50.0,
        stop_loss_pct: float = -30.0,
        premium_percent: float = 0.02,
        expiry_days: int = 30
    ):
        """
        Initialize options backtester.
        
        Args:
            initial_capital: Starting capital (default: ₹10,00,000)
            position_size_pct: % of capital per trade (default: 10%)
            max_positions: Max concurrent positions (default: 5)
            profit_target_pct: Exit at this profit % (default: +50%)
            stop_loss_pct: Exit at this loss % (default: -30%)
            premium_percent: Option premium as % of stock (default: 2%)
            expiry_days: Days until expiry (default: 30)
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        
        # Initialize components
        self.selector = OptionSelector(
            premium_percent=premium_percent,
            expiry_days=expiry_days
        )
        
        self.exit_strategy = OptionExitStrategy(ExitConditions(
            profit_target_pct=profit_target_pct,
            stop_loss_pct=stop_loss_pct,
            days_before_expiry=5,
            exit_on_opposite_signal=True
        ))
        
        self.portfolio: Optional[OptionsPortfolio] = None
    
    def run(self, df: pd.DataFrame) -> Dict:
        """
        Run options backtest on data with equity signals.
        
        Args:
            df: DataFrame with columns: Date, Symbol, Close, Signal
                (This is the SAME DataFrame used for equity backtesting!)
                
        Returns:
            Dict with:
            - trade_history: DataFrame of all option trades
            - portfolio_history: DataFrame of daily portfolio values
            - initial_capital: Starting amount
            - final_capital: Ending amount
            - summary: Key statistics
            
        ⚠️ IMPORTANT:
        This reuses the EXISTING equity signals.
        No need for separate options strategy!
        """
        # Initialize portfolio
        self.portfolio = OptionsPortfolio.create(self.initial_capital)
        
        # Sort by date
        df = df.sort_values(['Date', 'Symbol']).reset_index(drop=True)
        dates = sorted(df['Date'].unique())
        
        print(f"🔵 Options Backtest: {dates[0]} to {dates[-1]}")
        print(f"   Initial Capital: ₹{self.initial_capital:,.2f}")
        
        # Process each day
        for date in dates:
            day_data = df[df['Date'] == date]
            current_prices = dict(zip(day_data['Symbol'], day_data['Close']))
            current_signals = dict(zip(day_data['Symbol'], day_data['Signal']))
            
            # 1. Check exits for existing positions
            self._check_exits(date, current_prices, current_signals)
            
            # 2. Check for new entry signals
            self._check_entries(date, day_data)
            
            # 3. Record daily portfolio value
            self._record_portfolio_value(date, current_prices)
        
        # Close any remaining positions at end
        self._close_all_positions(dates[-1], current_prices, "Backtest End")
        
        # Compile results
        return self._compile_results(df)
    
    def _check_exits(
        self,
        date: datetime,
        current_prices: Dict[str, float],
        current_signals: Dict[str, int]
    ):
        """Check if any positions should be closed."""
        positions_to_close = []
        
        for symbol, option in self.portfolio.positions.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            current_signal = current_signals.get(symbol, 0)
            
            should_exit, reason, exit_premium = self.exit_strategy.should_exit(
                option=option,
                current_date=date,
                current_underlying_price=current_price,
                current_equity_signal=current_signal
            )
            
            if should_exit:
                positions_to_close.append((symbol, date, exit_premium, reason))
        
        # Close positions
        for symbol, exit_date, exit_premium, reason in positions_to_close:
            self._close_position(symbol, exit_date, exit_premium, reason)
    
    def _check_entries(self, date: datetime, day_data: pd.DataFrame):
        """Check for new entry signals."""
        for _, row in day_data.iterrows():
            symbol = row['Symbol']
            signal = row.get('Signal', 0)
            
            # Skip if no signal or already have position
            if signal == 0 or symbol in self.portfolio.positions:
                continue
            
            # Skip if at max positions
            if len(self.portfolio.positions) >= self.max_positions:
                continue
            
            # Create option from signal
            option = self.selector.select_option_from_signal(
                symbol=symbol,
                signal=int(signal),
                underlying_price=row['Close'],
                date=date
            )
            
            if option:
                self._open_position(option)
    
    def _open_position(self, option: OptionContract):
        """Open a new option position."""
        # Calculate position cost
        position_value = self.portfolio.cash * self.position_size_pct
        num_contracts = max(1, int(position_value / option.entry_premium))
        
        # Update option quantity
        option.quantity = num_contracts
        total_cost = option.entry_premium * num_contracts
        
        # Check if we have enough cash
        if total_cost > self.portfolio.cash:
            return
        
        # Deduct cost and add position
        self.portfolio.cash -= total_cost
        self.portfolio.positions[option.symbol] = option
        
        option_type = "CALL 📈" if option.option_type == OptionType.CALL else "PUT 📉"
        print(f"   ➕ {option.entry_date.strftime('%Y-%m-%d')}: "
              f"BUY {num_contracts}x {option.symbol} {option_type} "
              f"@ ₹{option.entry_premium:.2f}")
    
    def _close_position(
        self,
        symbol: str,
        exit_date: datetime,
        exit_premium: float,
        reason: str
    ):
        """Close an option position."""
        if symbol not in self.portfolio.positions:
            return
        
        option = self.portfolio.positions[symbol]
        
        # Record exit details
        option.exit_date = exit_date
        option.exit_premium = exit_premium
        option.exit_reason = reason
        
        # Calculate P&L
        pnl = option.calculate_pnl(exit_premium)
        pnl_pct = option.calculate_pnl_percent(exit_premium)
        
        # Add proceeds to cash
        proceeds = exit_premium * option.quantity
        self.portfolio.cash += proceeds
        
        # Record closed trade
        self.portfolio.closed_trades.append(option.to_dict())
        
        # Remove from active positions
        del self.portfolio.positions[symbol]
        
        emoji = "✅" if pnl >= 0 else "❌"
        print(f"   {emoji} {exit_date.strftime('%Y-%m-%d')}: "
              f"SELL {option.symbol} {option.option_type.value} "
              f"→ P&L: ₹{pnl:.2f} ({pnl_pct:.1f}%) [{reason}]")
    
    def _close_all_positions(
        self,
        date: datetime,
        current_prices: Dict[str, float],
        reason: str
    ):
        """Close all remaining positions at backtest end."""
        for symbol in list(self.portfolio.positions.keys()):
            option = self.portfolio.positions[symbol]
            if symbol in current_prices:
                exit_premium = option.calculate_current_premium(current_prices[symbol])
                self._close_position(symbol, date, exit_premium, reason)
    
    def _record_portfolio_value(
        self,
        date: datetime,
        current_prices: Dict[str, float]
    ):
        """Record daily portfolio value."""
        # Calculate positions value
        positions_value = 0
        for symbol, option in self.portfolio.positions.items():
            if symbol in current_prices:
                current_premium = option.calculate_current_premium(current_prices[symbol])
                positions_value += current_premium * option.quantity
        
        total_value = self.portfolio.cash + positions_value
        
        self.portfolio.portfolio_values.append({
            'Date': date,
            'Cash': self.portfolio.cash,
            'Positions_Value': positions_value,
            'Portfolio_Value': total_value,
            'Num_Positions': len(self.portfolio.positions)
        })
    
    def _compile_results(self, df: pd.DataFrame) -> Dict:
        """Compile backtest results."""
        trade_df = pd.DataFrame(self.portfolio.closed_trades)
        portfolio_df = pd.DataFrame(self.portfolio.portfolio_values)
        
        # Calculate summary stats
        final_value = self.portfolio.cash
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        if not trade_df.empty:
            wins = len(trade_df[trade_df['PnL'] > 0])
            losses = len(trade_df[trade_df['PnL'] <= 0])
            win_rate = wins / len(trade_df) * 100 if len(trade_df) > 0 else 0
            avg_pnl_pct = trade_df['PnL_Pct'].mean()
        else:
            wins, losses, win_rate, avg_pnl_pct = 0, 0, 0, 0
        
        summary = {
            'Total Return (%)': total_return,
            'Total Trades': len(trade_df),
            'Winning Trades': wins,
            'Losing Trades': losses,
            'Win Rate (%)': win_rate,
            'Avg Trade Return (%)': avg_pnl_pct,
            'Initial Capital': self.initial_capital,
            'Final Capital': final_value
        }
        
        print(f"\n🔵 Options Backtest Complete!")
        print(f"   Total Return: {total_return:.2f}%")
        print(f"   Win Rate: {win_rate:.1f}% ({wins}W / {losses}L)")
        print(f"   Final Capital: ₹{final_value:,.2f}")
        
        return {
            'trade_history': trade_df,
            'portfolio_history': portfolio_df,
            'initial_capital': self.initial_capital,
            'final_capital': final_value,
            'summary': summary,
            'data': df,
            'asset_class': 'options'
        }


def run_options_backtest(
    df: pd.DataFrame,
    initial_capital: float = 1000000,
    **kwargs
) -> Dict:
    """
    Convenience function to run options backtest.
    
    Args:
        df: DataFrame with equity signals (Date, Symbol, Close, Signal)
        initial_capital: Starting capital
        **kwargs: Additional backtester parameters
        
    Returns:
        Backtest results dictionary
        
    Usage:
        results = run_options_backtest(df_with_signals, initial_capital=1000000)
    """
    backtester = OptionsBacktester(initial_capital=initial_capital, **kwargs)
    return backtester.run(df)


# ============================================================
# METRICS CALCULATION (Similar to equity metrics.py)
# ============================================================

class OptionsPerformanceMetrics:
    """
    Calculate performance metrics for options backtest.
    
    Same structure as equity PerformanceMetrics for consistency.
    """
    
    def __init__(self, results: Dict):
        self.trade_history = results['trade_history']
        self.portfolio_history = results['portfolio_history']
        self.initial_capital = results['initial_capital']
        self.final_capital = results['final_capital']
    
    def calculate_all_metrics(self) -> Dict:
        """Calculate all performance metrics."""
        metrics = {}
        
        # Return metrics
        total_return = (self.final_capital - self.initial_capital) / self.initial_capital
        metrics['Total Return'] = total_return
        metrics['Total Return (%)'] = total_return * 100
        
        # Trade statistics
        if not self.trade_history.empty:
            metrics['Total Trades'] = len(self.trade_history)
            
            winning = self.trade_history[self.trade_history['PnL'] > 0]
            losing = self.trade_history[self.trade_history['PnL'] <= 0]
            
            metrics['Winning Trades'] = len(winning)
            metrics['Losing Trades'] = len(losing)
            metrics['Win Rate (%)'] = len(winning) / len(self.trade_history) * 100
            
            metrics['Average Trade (%)'] = self.trade_history['PnL_Pct'].mean()
            metrics['Best Trade (%)'] = self.trade_history['PnL_Pct'].max()
            metrics['Worst Trade (%)'] = self.trade_history['PnL_Pct'].min()
            
            # Option-specific: Count CALLs vs PUTs
            calls = self.trade_history[self.trade_history['Option_Type'] == 'CALL']
            puts = self.trade_history[self.trade_history['Option_Type'] == 'PUT']
            metrics['CALL Trades'] = len(calls)
            metrics['PUT Trades'] = len(puts)
            
            # Profit factor
            total_wins = winning['PnL'].sum() if len(winning) > 0 else 0
            total_losses = abs(losing['PnL'].sum()) if len(losing) > 0 else 0
            metrics['Profit Factor'] = total_wins / total_losses if total_losses > 0 else float('inf')
        else:
            metrics['Total Trades'] = 0
            metrics['Winning Trades'] = 0
            metrics['Losing Trades'] = 0
            metrics['Win Rate (%)'] = 0
            metrics['Average Trade (%)'] = 0
            metrics['Best Trade (%)'] = 0
            metrics['Worst Trade (%)'] = 0
            metrics['CALL Trades'] = 0
            metrics['PUT Trades'] = 0
            metrics['Profit Factor'] = 0
        
        # Risk metrics from portfolio history
        if not self.portfolio_history.empty:
            pf = self.portfolio_history.copy()
            pf['Returns'] = pf['Portfolio_Value'].pct_change()
            
            # Volatility
            daily_vol = pf['Returns'].std()
            metrics['Volatility (%)'] = daily_vol * np.sqrt(252) * 100
            
            # Sharpe (assume 0% risk-free)
            avg_return = pf['Returns'].mean()
            metrics['Sharpe Ratio'] = (avg_return / daily_vol * np.sqrt(252)) if daily_vol > 0 else 0
            
            # Max Drawdown
            running_max = pf['Portfolio_Value'].cummax()
            drawdown = (pf['Portfolio_Value'] - running_max) / running_max
            metrics['Max Drawdown (%)'] = drawdown.min() * 100
        else:
            metrics['Volatility (%)'] = 0
            metrics['Sharpe Ratio'] = 0
            metrics['Max Drawdown (%)'] = 0
        
        return metrics
