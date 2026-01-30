"""
Futures Data Fetcher
Loads and provides futures market data for backtesting.
"""
import os
import pandas as pd
from pathlib import Path


def load_futures_data(data_file=None):
    """
    Load futures data from CSV file.
    
    Args:
        data_file: Path to the futures data CSV. If None, uses default location.
        
    Returns:
        pd.DataFrame: DataFrame with datetime index and OHLC columns
    """
    if data_file is None:
        # Default to futures/data/futures_minute_clean.csv
        base_dir = Path(__file__).parent.parent
        data_file = base_dir / "futures" / "data" / "futures_minute_clean.csv"
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(
            f"Futures data file not found: {data_file}\n"
            "Please ensure futures data is available in the futures/data/ directory."
        )
    
    # Load data
    df = pd.read_csv(data_file, parse_dates=["datetime"])
    df.set_index("datetime", inplace=True)
    df["date"] = df.index.date
    
    return df


def get_daily_levels(df):
    """
    Calculate daily high and low levels (PDH/PDL).
    
    Args:
        df: DataFrame with datetime index and OHLC data
        
    Returns:
        pd.DataFrame: Daily levels with PDH and PDL
    """
    daily = df.groupby("date").agg(
        PDH=("high", "max"),
        PDL=("low", "min")
    )
    return daily


def get_available_date_range(data_file=None):
    """
    Get the date range available in the futures data.
    
    Args:
        data_file: Path to the futures data CSV. If None, uses default location.
        
    Returns:
        tuple: (start_date, end_date)
    """
    df = load_futures_data(data_file)
    return df.index.min(), df.index.max()
