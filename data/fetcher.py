"""
Data fetcher module for retrieving equity data from the Hackathon API.
Data is fetched STRICTLY from http://13.201.224.23:8001
"""
import requests
import pandas as pd
from datetime import datetime
from typing import List, Optional
import io


class EquityDataFetcher:
    """Fetch equity data from the Hackathon API endpoint."""
    
    # Hackathon API - STRICT data source
    BASE_URL = "http://13.201.224.23:8001"
    
    def __init__(self):
        self.base_url = self.BASE_URL
        
    def fetch_equity_data(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str,
        interval: str = "day"
    ) -> pd.DataFrame:
        """
        Fetch equity data for given symbols and date range from Hackathon API.
        
        Args:
            symbols: List of stock symbols (e.g., ['RELIANCE', 'TCS'])
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval ('day' for daily, 'minute' for minute)
            
        Returns:
            DataFrame with columns: Date, Symbol, Open, High, Low, Close, Volume
        """
        all_data = []
        
        # Calculate days_ago from start_date
        start_dt = pd.to_datetime(start_date)
        days_ago = (datetime.now() - start_dt).days + 1  # +1 to include start date
        
        for symbol in symbols:
            try:
                print(f"Fetching data for {symbol} from Hackathon API...")
                df = self._fetch_from_api(symbol, days_ago, interval)
                
                if df is not None and not df.empty:
                    # Add symbol column
                    df['Symbol'] = symbol
                    
                    # Filter by date range
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
                    
                    if not df.empty:
                        all_data.append(df)
                        print(f"  Successfully fetched {len(df)} records for {symbol}")
                    else:
                        print(f"  Warning: No data for {symbol} in date range {start_date} to {end_date}")
                else:
                    print(f"  Warning: No data received for {symbol}")
                    
            except Exception as e:
                print(f"  Error fetching data for {symbol}: {e}")
                continue
        
        if not all_data:
            raise ValueError(
                f"No data could be fetched from Hackathon API ({self.BASE_URL}). "
                "Please check API availability and symbol names."
            )
        
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values(['Symbol', 'Date']).reset_index(drop=True)
        
        # Ensure required columns are present
        required_cols = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in combined_df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        return combined_df[required_cols]
    
    def _fetch_from_api(
        self, 
        symbol: str, 
        days_ago: int,
        interval: str = "day"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data for a single symbol from the Hackathon API.
        
        API Endpoint: POST /fetch-data
        Returns: Excel file (.xlsx) with OHLCV data
        """
        url = f"{self.base_url}/fetch-data"
        
        # Request payload
        payload = {
            "asset_class": "equity",
            "stocks": [symbol],
            "indexes": [],
            "interval": interval,
            "days_ago": days_ago,
            "equity_source": "zerodha"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            
            if response.status_code == 200 and len(response.content) > 100:
                return self._parse_excel_response(response.content, symbol)
            elif response.status_code == 404:
                print(f"    No data available for {symbol}")
                return None
            else:
                error_msg = response.text[:200] if response.text else "Unknown error"
                print(f"    API error {response.status_code}: {error_msg}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"    Request timed out for {symbol}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"    Connection error to API")
            return None
        except Exception as e:
            print(f"    Error: {e}")
            return None
    
    def _parse_excel_response(self, content: bytes, symbol: str) -> Optional[pd.DataFrame]:
        """Parse Excel file response into DataFrame."""
        try:
            # Read Excel file from bytes
            df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            
            if df.empty:
                return None
            
            # Standardize column names
            column_map = {
                'date': 'Date',
                'time': 'Time',
                'tradingsymbol': 'TradingSymbol',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                'historical_volatility': 'HistoricalVolatility'
            }
            
            # Rename columns (case-insensitive)
            df.columns = [column_map.get(col.lower(), col) for col in df.columns]
            
            # For minute data, we may need to aggregate to daily
            if 'Time' in df.columns:
                # This is minute data - aggregate to daily
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Group by date and aggregate OHLCV
                daily_df = df.groupby('Date').agg({
                    'Open': 'first',      # First open of the day
                    'High': 'max',        # Highest high
                    'Low': 'min',         # Lowest low
                    'Close': 'last',      # Last close of the day
                    'Volume': 'sum'       # Total volume
                }).reset_index()
                
                return daily_df
            else:
                # Already daily data
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Keep only required columns
                required = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                available = [col for col in required if col in df.columns]
                
                # Ensure Volume exists
                if 'Volume' not in df.columns:
                    df['Volume'] = 0
                    
                return df[available]
                
        except Exception as e:
            print(f"    Error parsing Excel response: {e}")
            return None


def fetch_equity_data(
    symbols: List[str], 
    start_date: str, 
    end_date: str
) -> pd.DataFrame:
    """
    Convenience function to fetch equity data from Hackathon API.
    
    Data Source: http://13.201.224.23:8001 (STRICT)
    
    Args:
        symbols: List of stock symbols (e.g., ['RELIANCE', 'TCS'])
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        
    Returns:
        DataFrame with OHLCV data for all symbols
    """
    fetcher = EquityDataFetcher()
    return fetcher.fetch_equity_data(symbols, start_date, end_date)


if __name__ == "__main__":
    # Test the fetcher
    print("=" * 60)
    print("Testing Hackathon API Data Fetcher")
    print(f"API Endpoint: {EquityDataFetcher.BASE_URL}")
    print("=" * 60)
    
    symbols = ['RELIANCE']
    start = '2026-01-20'
    end = '2026-01-30'
    
    try:
        data = fetch_equity_data(symbols, start, end)
        print(f"\nData fetched successfully!")
        print(f"Total records: {len(data)}")
        print(f"Columns: {list(data.columns)}")
        print(f"\nSample data:")
        print(data.head(10).to_string())
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
