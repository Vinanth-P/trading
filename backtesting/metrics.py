"""
Performance metrics module.
Calculates various performance metrics for backtesting results.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple


class PerformanceMetrics:
    """Calculate trading strategy performance metrics."""
    
    def __init__(self, results: Dict):
        """
        Initialize with backtest results.
        
        Args:
            results: Dictionary from backtesting engine
        """
        self.trade_history = results['trade_history']
        self.portfolio_history = results['portfolio_history']
        self.initial_capital = results['initial_capital']
        self.final_capital = results['final_capital']
    
    def calculate_all_metrics(self) -> Dict:
        """
        Calculate all performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Return metrics
        total_return = (self.final_capital - self.initial_capital) / self.initial_capital
        metrics['Total Return'] = total_return
        metrics['Total Return (%)'] = total_return * 100
        
        # Annualized return
        if not self.portfolio_history.empty:
            days = (self.portfolio_history['Date'].max() - 
                   self.portfolio_history['Date'].min()).days
            years = days / 365.25
            if years > 0:
                annualized_return = (1 + total_return) ** (1 / years) - 1
                metrics['Annualized Return (%)'] = annualized_return * 100
            else:
                metrics['Annualized Return (%)'] = 0
        else:
            metrics['Annualized Return (%)'] = 0
        
        # Trade statistics
        if not self.trade_history.empty:
            metrics['Total Trades'] = len(self.trade_history)
            
            winning_trades = self.trade_history[self.trade_history['PnL'] > 0]
            losing_trades = self.trade_history[self.trade_history['PnL'] < 0]
            
            metrics['Winning Trades'] = len(winning_trades)
            metrics['Losing Trades'] = len(losing_trades)
            
            # Win rate
            if len(self.trade_history) > 0:
                metrics['Win Rate (%)'] = (len(winning_trades) / len(self.trade_history)) * 100
            else:
                metrics['Win Rate (%)'] = 0
            
            # Average trade
            metrics['Average Trade (%)'] = self.trade_history['PnL_Pct'].mean() * 100
            metrics['Average Winning Trade (%)'] = (
                winning_trades['PnL_Pct'].mean() * 100 if len(winning_trades) > 0 else 0
            )
            metrics['Average Losing Trade (%)'] = (
                losing_trades['PnL_Pct'].mean() * 100 if len(losing_trades) > 0 else 0
            )
            
            # Best and worst trade
            metrics['Best Trade (%)'] = self.trade_history['PnL_Pct'].max() * 100
            metrics['Worst Trade (%)'] = self.trade_history['PnL_Pct'].min() * 100
            
            # Average hold time
            metrics['Average Hold Time (days)'] = self.trade_history['Duration_Days'].mean()
            
            # Profit factor
            total_wins = winning_trades['PnL'].sum() if len(winning_trades) > 0 else 0
            total_losses = abs(losing_trades['PnL'].sum()) if len(losing_trades) > 0 else 0
            
            if total_losses > 0:
                metrics['Profit Factor'] = total_wins / total_losses
            else:
                metrics['Profit Factor'] = np.inf if total_wins > 0 else 0
        else:
            metrics['Total Trades'] = 0
            metrics['Winning Trades'] = 0
            metrics['Losing Trades'] = 0
            metrics['Win Rate (%)'] = 0
            metrics['Average Trade (%)'] = 0
            metrics['Average Winning Trade (%)'] = 0
            metrics['Average Losing Trade (%)'] = 0
            metrics['Best Trade (%)'] = 0
            metrics['Worst Trade (%)'] = 0
            metrics['Average Hold Time (days)'] = 0
            metrics['Profit Factor'] = 0
        
        # Risk metrics
        if not self.portfolio_history.empty:
            # Calculate returns
            self.portfolio_history['Returns'] = self.portfolio_history['Portfolio_Value'].pct_change()
            
            # Volatility (annualized)
            daily_volatility = self.portfolio_history['Returns'].std()
            metrics['Volatility (%)'] = daily_volatility * np.sqrt(252) * 100
            
            # Sharpe Ratio (assuming 0% risk-free rate)
            if daily_volatility > 0:
                avg_daily_return = self.portfolio_history['Returns'].mean()
                sharpe = (avg_daily_return / daily_volatility) * np.sqrt(252)
                metrics['Sharpe Ratio'] = sharpe
            else:
                metrics['Sharpe Ratio'] = 0
            
            # Maximum Drawdown
            max_dd, max_dd_pct, max_dd_duration = self._calculate_max_drawdown()
            metrics['Max Drawdown (%)'] = max_dd_pct * 100
            metrics['Max Drawdown Duration (days)'] = max_dd_duration
            
            # Calmar Ratio (annualized return / max drawdown)
            if max_dd_pct != 0:
                metrics['Calmar Ratio'] = metrics['Annualized Return (%)'] / (max_dd_pct * 100)
            else:
                metrics['Calmar Ratio'] = 0
        else:
            metrics['Volatility (%)'] = 0
            metrics['Sharpe Ratio'] = 0
            metrics['Max Drawdown (%)'] = 0
            metrics['Max Drawdown Duration (days)'] = 0
            metrics['Calmar Ratio'] = 0
        
        return metrics
    
    def _calculate_max_drawdown(self) -> Tuple[float, float, int]:
        """
        Calculate maximum drawdown.
        
        Returns:
            Tuple of (max_dd_value, max_dd_pct, max_dd_duration_days)
        """
        if self.portfolio_history.empty:
            return 0, 0, 0
        
        portfolio_values = self.portfolio_history['Portfolio_Value'].values
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(portfolio_values)
        
        # Calculate drawdown
        drawdown = portfolio_values - running_max
        drawdown_pct = drawdown / running_max
        
        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdown_pct)
        max_dd_pct = drawdown_pct[max_dd_idx]
        max_dd_value = drawdown[max_dd_idx]
        
        # Find duration of max drawdown
        # Find the peak before max drawdown
        peak_idx = np.argmax(portfolio_values[:max_dd_idx+1])
        max_dd_duration = max_dd_idx - peak_idx
        
        return max_dd_value, max_dd_pct, max_dd_duration
    
    def get_drawdown_series(self) -> pd.DataFrame:
        """
        Get drawdown series for plotting.
        
        Returns:
            DataFrame with Date and Drawdown columns
        """
        if self.portfolio_history.empty:
            return pd.DataFrame()
        
        df = self.portfolio_history.copy()
        
        # Calculate running maximum
        df['Running_Max'] = df['Portfolio_Value'].cummax()
        
        # Calculate drawdown
        df['Drawdown'] = (df['Portfolio_Value'] - df['Running_Max']) / df['Running_Max']
        
        return df[['Date', 'Drawdown']]
    
    def print_summary(self):
        """Print a summary of performance metrics."""
        metrics = self.calculate_all_metrics()
        
        print("\n" + "="*60)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("="*60)
        
        print(f"\n📊 RETURNS")
        print(f"  Total Return:           {metrics['Total Return (%)']:>10.2f}%")
        print(f"  Annualized Return:      {metrics['Annualized Return (%)']:>10.2f}%")
        
        print(f"\n📈 TRADE STATISTICS")
        print(f"  Total Trades:           {metrics['Total Trades']:>10.0f}")
        print(f"  Winning Trades:         {metrics['Winning Trades']:>10.0f}")
        print(f"  Losing Trades:          {metrics['Losing Trades']:>10.0f}")
        print(f"  Win Rate:               {metrics['Win Rate (%)']:>10.2f}%")
        print(f"  Average Trade:          {metrics['Average Trade (%)']:>10.2f}%")
        print(f"  Best Trade:             {metrics['Best Trade (%)']:>10.2f}%")
        print(f"  Worst Trade:            {metrics['Worst Trade (%)']:>10.2f}%")
        print(f"  Profit Factor:          {metrics['Profit Factor']:>10.2f}")
        print(f"  Avg Hold Time:          {metrics['Average Hold Time (days)']:>10.1f} days")
        
        print(f"\n⚠️  RISK METRICS")
        print(f"  Volatility:             {metrics['Volatility (%)']:>10.2f}%")
        print(f"  Sharpe Ratio:           {metrics['Sharpe Ratio']:>10.2f}")
        print(f"  Max Drawdown:           {metrics['Max Drawdown (%)']:>10.2f}%")
        print(f"  Max DD Duration:        {metrics['Max Drawdown Duration (days)']:>10.0f} days")
        print(f"  Calmar Ratio:           {metrics['Calmar Ratio']:>10.2f}")
        
        print("\n" + "="*60)


def calculate_metrics(results: Dict) -> Dict:
    """
    Convenience function to calculate metrics.
    
    Args:
        results: Backtest results dictionary
        
    Returns:
        Dictionary of performance metrics
    """
    calculator = PerformanceMetrics(results)
    return calculator.calculate_all_metrics()


def print_metrics(results: Dict):
    """Print metrics summary."""
    calculator = PerformanceMetrics(results)
    calculator.print_summary()


if __name__ == "__main__":
    # Test metrics calculation
    from data.fetcher import fetch_equity_data
    from data.preprocessor import preprocess_data
    from strategy.indicators import add_indicators
    from strategy.signals import generate_signals
    from backtesting.engine import run_backtest
    
    symbols = ['RELIANCE']
    raw_data = fetch_equity_data(symbols, '2023-01-01', '2024-01-01')
    clean_data = preprocess_data(raw_data)
    df_with_indicators = add_indicators(clean_data)
    df_with_signals = generate_signals(df_with_indicators)
    
    results = run_backtest(df_with_signals, initial_capital=1000000)
    
    # Print metrics
    print_metrics(results)
    
    # Get metrics dict
    metrics = calculate_metrics(results)
    print("\nMetrics dictionary:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
