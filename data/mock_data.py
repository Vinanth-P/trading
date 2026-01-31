"""
Fallback data generator for when the Hackathon API is unavailable or has no data.
This generates realistic synthetic stock data for testing purposes.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List


def generate_mock_equity_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    base_price_range: tuple = (100, 5000)
) -> pd.DataFrame:
    """
    Generate realistic mock OHLCV data for testing when API is unavailable.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        base_price_range: Tuple of (min, max) for base prices
        
    Returns:
        DataFrame with columns: Date, Symbol, Open, High, Low, Close, Volume
    """
    np.random.seed(42)  # For reproducibility
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Generate business days
    date_range = pd.bdate_range(start=start, end=end)
    
    all_data = []
    
    for symbol in symbols:
        # Random base price for this symbol
        base_price = np.random.uniform(*base_price_range)
        
        # Generate price series with trend and volatility
        n_days = len(date_range)
        
        # Random walk with trend
        trend = np.random.uniform(-0.0005, 0.001)  # Slight upward bias
        volatility = np.random.uniform(0.015, 0.025)  # Daily volatility
        
        returns = np.random.normal(trend, volatility, n_days)
        price_multipliers = np.exp(np.cumsum(returns))
        
        close_prices = base_price * price_multipliers
        
        # Generate OHLC from close prices
        for i, date in enumerate(date_range):
            close = close_prices[i]
            
            # Intraday range (typical 0.5% to 3%)
            daily_range_pct = np.random.uniform(0.005, 0.03)
            
            # Open near previous close with some gap
            if i == 0:
                open_price = close * np.random.uniform(0.995, 1.005)
            else:
                open_price = close_prices[i-1] * np.random.uniform(0.99, 1.01)
            
            # High and low based on close and range
            high = max(open_price, close) * (1 + daily_range_pct * np.random.uniform(0.3, 1.0))
            low = min(open_price, close) * (1 - daily_range_pct * np.random.uniform(0.3, 1.0))
            
            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            # Volume (higher on volatile days)
            base_volume = np.random.uniform(1_000_000, 10_000_000)
            volume_multiplier = 1 + abs(returns[i]) * 10  # Higher volume on big moves
            volume = int(base_volume * volume_multiplier)
            
            all_data.append({
                'Date': date,
                'Symbol': symbol,
                'Open': round(open_price, 2),
                'High': round(high, 2),
                'Low': round(low, 2),
                'Close': round(close, 2),
                'Volume': volume
            })
    
    df = pd.DataFrame(all_data)
    df = df.sort_values(['Symbol', 'Date']).reset_index(drop=True)
    
    return df


if __name__ == "__main__":
    # Test the mock data generator
    print("Generating mock equity data for testing...")
    
    symbols = ['RELIANCE', 'TCS', 'INFY']
    start = '2023-01-01'
    end = '2024-01-01'
    
    df = generate_mock_equity_data(symbols, start, end)
    
    print(f"\nGenerated {len(df)} records for {len(symbols)} symbols")
    print(f"\nSample data:")
    print(df.head(10).to_string())
    
    print(f"\nData statistics by symbol:")
    for symbol in symbols:
        symbol_df = df[df['Symbol'] == symbol]
        print(f"\n{symbol}:")
        print(f"  Records: {len(symbol_df)}")
        print(f"  Date range: {symbol_df['Date'].min()} to {symbol_df['Date'].max()}")
        print(f"  Price range: ₹{symbol_df['Close'].min():.2f} to ₹{symbol_df['Close'].max():.2f}")
        print(f"  Avg volume: {symbol_df['Volume'].mean():,.0f}")
