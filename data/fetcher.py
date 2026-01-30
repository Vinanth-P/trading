"""
Data fetcher module for retrieving equity data from HACKATHON DATASET.

⚠️ IMPORTANT - HACKATHON RULES:
- Must use ONLY the customized dataset provided by organizers
- External datasets (Yahoo Finance, etc.) are NOT permitted
- Paste your dataset link in HACKATHON_DATASET_URL below

HOW TO USE:
1. When you receive the dataset link, paste it in HACKATHON_DATASET_URL
2. The fetcher will automatically load from that URL
3. If URL not set, sample data is used for TESTING ONLY
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
from io import StringIO


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PASTE YOUR HACKATHON DATASET LINK BELOW                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

HACKATHON_DATASET_URL = "http://13.201.224.23:8001/"

# Alternative: Local file path (if dataset is downloaded)
HACKATHON_DATASET_FILE = None  # ← OR paste local path (e.g., "C:/hackathon/equity_data.csv")

# ╔══════════════════════════════════════════════════════════════════════════════╗


class HackathonDataFetcher:
    """
    Fetch equity data from the HACKATHON-PROVIDED dataset.
    
    ⚠️ NO external data sources allowed per hackathon rules.
    """
    
    def __init__(
        self, 
        dataset_url: Optional[str] = None,
        dataset_file: Optional[str] = None
    ):
        """
        Initialize fetcher with hackathon dataset source.
        
        Args:
            dataset_url: URL to hackathon dataset (CSV/JSON)
            dataset_file: Local file path to downloaded dataset
        """
        self.dataset_url = dataset_url or HACKATHON_DATASET_URL
        self.dataset_file = dataset_file or HACKATHON_DATASET_FILE
        self._cached_data: Optional[pd.DataFrame] = None
    
    def fetch_equity_data(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch equity data for given symbols from hackathon dataset.
        
        Args:
            symbols: List of stock symbols (e.g., ['RELIANCE', 'TCS'])
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval (ignored - using provided data granularity)
            
        Returns:
            DataFrame with columns: Date, Symbol, Open, High, Low, Close, Volume
        """
        # Load full dataset (cached after first load)
        full_data = self._load_hackathon_data()
        
        # If no hackathon data, generate sample data for testing
        if full_data.empty:
            return self._generate_sample_data_for_symbols(symbols, start_date, end_date)
        
        # Filter by symbols
        if 'Symbol' in full_data.columns:
            filtered = full_data[full_data['Symbol'].isin(symbols)].copy()
        else:
            # If no Symbol column, assume single-stock dataset
            filtered = full_data.copy()
            if symbols:
                filtered['Symbol'] = symbols[0]
        
        # Ensure Date column is datetime
        if 'Date' in filtered.columns:
            filtered['Date'] = pd.to_datetime(filtered['Date'])
        elif 'date' in filtered.columns:
            filtered['Date'] = pd.to_datetime(filtered['date'])
            filtered = filtered.drop(columns=['date'])
        
        # Filter by date range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        filtered = filtered[(filtered['Date'] >= start) & (filtered['Date'] <= end)]
        
        # Standardize column names
        filtered = self._standardize_columns(filtered)
        
        # Sort and return
        filtered = filtered.sort_values(['Symbol', 'Date']).reset_index(drop=True)
        
        if filtered.empty:
            print(f"⚠️ No data found for symbols {symbols} in date range {start_date} to {end_date}")
            print("   Falling back to sample data for TESTING purposes...")
            return self._generate_sample_data_for_symbols(symbols, start_date, end_date)
        
        print(f"✅ Loaded {len(filtered)} records for {filtered['Symbol'].nunique()} symbols")
        return filtered
    
    def _load_hackathon_data(self) -> pd.DataFrame:
        """
        Load data from hackathon source (URL or file).
        
        Priority:
        1. Cached data (if already loaded)
        2. URL (HACKATHON_DATASET_URL)
        3. Local file (HACKATHON_DATASET_FILE)
        4. Sample data (for testing only - NOT for submission!)
        """
        # Return cached data if available
        if self._cached_data is not None:
            return self._cached_data
        
        # Try loading from URL
        if self.dataset_url:
            try:
                print(f"📥 Loading hackathon dataset from URL...")
                self._cached_data = self._load_from_url(self.dataset_url)
                print(f"✅ Loaded {len(self._cached_data)} records from hackathon URL")
                return self._cached_data
            except Exception as e:
                print(f"❌ Error loading from URL: {e}")
        
        # Try loading from local file
        if self.dataset_file:
            try:
                print(f"📥 Loading hackathon dataset from file...")
                self._cached_data = self._load_from_file(self.dataset_file)
                print(f"✅ Loaded {len(self._cached_data)} records from local file")
                return self._cached_data
            except Exception as e:
                print(f"❌ Error loading from file: {e}")
        
        # No hackathon data available - use sample data for TESTING only
        print("=" * 60)
        print("⚠️  WARNING: HACKATHON DATASET NOT CONFIGURED!")
        print("=" * 60)
        print("   Paste your dataset link in data/fetcher.py:")
        print("   HACKATHON_DATASET_URL = 'your_link_here'")
        print("")
        print("   Using SAMPLE DATA for testing purposes only.")
        print("   This is NOT valid for hackathon submission!")
        print("=" * 60)
        
        return pd.DataFrame()  # Empty - will trigger sample data generation
    
    def _load_from_url(self, url: str) -> pd.DataFrame:
        """Load dataset from URL (supports CSV and JSON)."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        
        if 'json' in content_type or url.endswith('.json'):
            return pd.DataFrame(response.json())
        else:
            # Assume CSV
            return pd.read_csv(StringIO(response.text))
    
    def _load_from_file(self, filepath: str) -> pd.DataFrame:
        """Load dataset from local file."""
        if filepath.endswith('.json'):
            return pd.read_json(filepath)
        elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            return pd.read_excel(filepath)
        else:
            # Assume CSV
            return pd.read_csv(filepath)
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names to: Date, Symbol, Open, High, Low, Close, Volume
        
        Handles common variations in column naming.
        """
        # Common column name mappings (lowercase -> standard)
        column_mappings = {
            'date': 'Date',
            'datetime': 'Date',
            'timestamp': 'Date',
            'symbol': 'Symbol',
            'ticker': 'Symbol',
            'stock': 'Symbol',
            'open': 'Open',
            'open_price': 'Open',
            'high': 'High',
            'high_price': 'High',
            'low': 'Low',
            'low_price': 'Low',
            'close': 'Close',
            'close_price': 'Close',
            'adj_close': 'Close',
            'adjusted_close': 'Close',
            'volume': 'Volume',
            'vol': 'Volume',
            'traded_volume': 'Volume'
        }
        
        # Rename columns
        df.columns = [column_mappings.get(col.lower(), col) for col in df.columns]
        
        # Ensure required columns exist
        required = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            if col not in df.columns:
                if col == 'Volume':
                    df[col] = 0  # Default volume if missing
                else:
                    raise ValueError(f"Required column '{col}' not found in dataset")
        
        return df
    
    def _generate_sample_data_for_symbols(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        Generate sample data for testing when hackathon data unavailable.
        
        ⚠️ FOR TESTING ONLY - NOT FOR HACKATHON SUBMISSION!
        """
        all_data = []
        
        for symbol in symbols:
            df = self._generate_sample_data(symbol, start_date, end_date)
            df['Symbol'] = symbol
            all_data.append(df)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
    
    def _generate_sample_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        Generate realistic sample data for demonstration purposes.
        
        ⚠️ FOR TESTING ONLY - NOT FOR HACKATHON SUBMISSION!
        """
        # Convert dates
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Generate date range (business days only)
        dates = pd.bdate_range(start=start, end=end)
        
        # Set base price based on symbol
        base_prices = {
            'RELIANCE': 2500,
            'TCS': 3500,
            'INFY': 1500,
            'HDFCBANK': 1600,
            'ICICIBANK': 900,
            'SBIN': 600,
            'BHARTIARTL': 800,
            'ITC': 400,
            'KOTAKBANK': 1800,
            'LT': 2200
        }
        
        base_price = base_prices.get(symbol, 1000)
        
        # Generate random walk with trend
        np.random.seed(hash(symbol) % 2**32)
        n_days = len(dates)
        
        if n_days == 0:
            return pd.DataFrame()
        
        # Returns with slight upward bias
        returns = np.random.normal(0.0005, 0.02, n_days)
        
        # Calculate prices
        close_prices = base_price * (1 + returns).cumprod()
        
        # Generate OHLC
        daily_range = np.random.uniform(0.01, 0.03, n_days)
        
        high_prices = close_prices * (1 + daily_range / 2)
        low_prices = close_prices * (1 - daily_range / 2)
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = base_price
        
        # Add some randomness to open prices
        open_prices = open_prices * (1 + np.random.normal(0, 0.005, n_days))
        
        # Generate volume
        base_volume = np.random.randint(1000000, 5000000)
        volumes = np.random.randint(
            int(base_volume * 0.5), 
            int(base_volume * 1.5), 
            n_days
        )
        
        # Create DataFrame
        df = pd.DataFrame({
            'Date': dates,
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volumes
        })
        
        return df


# Backward-compatible class alias
EquityDataFetcher = HackathonDataFetcher


def fetch_equity_data(
    symbols: List[str], 
    start_date: str, 
    end_date: str
) -> pd.DataFrame:
    """
    Convenience function to fetch equity data from hackathon dataset.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        
    Returns:
        DataFrame with OHLCV data for all symbols
    """
    fetcher = HackathonDataFetcher()
    return fetcher.fetch_equity_data(symbols, start_date, end_date)


if __name__ == "__main__":
    # Test the fetcher
    print("Testing hackathon data fetcher...")
    print("")
    
    symbols = ['RELIANCE', 'TCS', 'INFY']
    data = fetch_equity_data(symbols, '2023-01-01', '2024-01-01')
    
    if not data.empty:
        print("\nSample data:")
        print(data.head(10))
        print(f"\nTotal records: {len(data)}")
        print(f"Symbols: {data['Symbol'].unique()}")
        print(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
