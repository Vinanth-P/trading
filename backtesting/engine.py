"""
Backtesting engine module.
Simulates trading strategy execution on historical data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from backtesting.portfolio import Portfolio


class BacktestEngine:
    """Core backtesting engine for simulating trades."""
    
    def __init__(
        self,
        initial_capital: float = 1000000,
        position_size: float = 0.20,
        max_positions: int = 3,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10,
        transaction_cost: float = 0.001
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital
            position_size: Position size as fraction of portfolio
            max_positions: Maximum concurrent positions
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            transaction_cost: Transaction cost per trade
        """
        self.portfolio = Portfolio(
            initial_capital=initial_capital,
            position_size=position_size,
            max_positions=max_positions,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            transaction_cost=transaction_cost
        )
        
        self.initial_capital = initial_capital
    
    def run(self, df: pd.DataFrame) -> Dict:
        """
        Run backtest on data with signals.
        
        Args:
            df: DataFrame with OHLCV, indicators, and signals
            
        Returns:
            Dictionary containing backtest results
        """
        # Ensure data is sorted by date
        df = df.sort_values(['Date', 'Symbol']).reset_index(drop=True)
        
        # Get unique dates
        dates = sorted(df['Date'].unique())
        
        print(f"Running backtest from {dates[0]} to {dates[-1]}")
        print(f"Initial capital: ₹{self.initial_capital:,.2f}")
        
        # Iterate through each date
        for date in dates:
            # Get data for this date
            day_data = df[df['Date'] == date]
            
            # Create price dictionary for this date
            current_prices = dict(zip(day_data['Symbol'], day_data['Close']))
            
            # First, check exit conditions (stop-loss, take-profit)
            self.portfolio.check_exit_conditions(date, current_prices)
            
            # Then, check for sell signals
            sell_signals = day_data[day_data['Signal'] == -1]
            for _, row in sell_signals.iterrows():
                symbol = row['Symbol']
                if symbol in self.portfolio.positions:
                    self.portfolio.close_position(
                        symbol, date, row['Close'], "Sell Signal"
                    )
            
            # Finally, check for buy signals
            buy_signals = day_data[day_data['Signal'] == 1]
            for _, row in buy_signals.iterrows():
                symbol = row['Symbol']
                if self.portfolio.can_open_position(symbol):
                    self.portfolio.open_position(
                        symbol, date, row['Close']
                    )
            
            # Record portfolio value
            self.portfolio.record_portfolio_value(date, current_prices)
        
        # Close any remaining positions at the end
        final_date = dates[-1]
        final_prices = dict(zip(
            df[df['Date'] == final_date]['Symbol'],
            df[df['Date'] == final_date]['Close']
        ))
        
        for symbol in list(self.portfolio.positions.keys()):
            if symbol in final_prices:
                self.portfolio.close_position(
                    symbol, final_date, final_prices[symbol], "Backtest End"
                )
        
        # Compile results
        results = self._compile_results(df)
        
        return results
    
    def _compile_results(self, df: pd.DataFrame) -> Dict:
        """Compile backtest results."""
        trade_history = self.portfolio.get_trade_history_df()
        portfolio_history = self.portfolio.get_portfolio_history_df()
        
        # Calculate final portfolio value
        final_value = self.portfolio.cash
        
        results = {
            'trade_history': trade_history,
            'portfolio_history': portfolio_history,
            'initial_capital': self.initial_capital,
            'final_capital': final_value,
            'data': df
        }
        
        print(f"\nBacktest completed!")
        print(f"Final capital: ₹{final_value:,.2f}")
        print(f"Total return: {((final_value - self.initial_capital) / self.initial_capital * 100):.2f}%")
        print(f"Total trades: {len(trade_history)}")
        
        return results


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 1000000,
    **kwargs
) -> Dict:
    """
    Convenience function to run backtest.
    
    Args:
        df: DataFrame with OHLCV, indicators, and signals
        initial_capital: Starting capital
        **kwargs: Additional backtesting parameters
        
    Returns:
        Backtest results dictionary
    """
    engine = BacktestEngine(initial_capital=initial_capital, **kwargs)
    return engine.run(df)


if __name__ == "__main__":
    # Test backtest engine
    from data.fetcher import fetch_equity_data
    from data.preprocessor import preprocess_data
    from strategy.indicators import add_indicators
    from strategy.signals import generate_signals
    
    print("Fetching data...")
    symbols = ['RELIANCE', 'TCS']
    raw_data = fetch_equity_data(symbols, '2023-01-01', '2024-01-01')
    
    print("Preprocessing...")
    clean_data = preprocess_data(raw_data)
    
    print("Calculating indicators...")
    df_with_indicators = add_indicators(clean_data)
    
    print("Generating signals...")
    df_with_signals = generate_signals(df_with_indicators)
    
    print("\nRunning backtest...")
    results = run_backtest(df_with_signals, initial_capital=1000000)
    
    print("\nTrade History:")
    print(results['trade_history'][['Symbol', 'Entry_Date', 'Exit_Date', 'PnL', 'PnL_Pct']])
