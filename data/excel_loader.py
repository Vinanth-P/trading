"""
Excel data loader for manual data uploads.
Supports uploading custom OHLCV data from Excel files.
"""
import pandas as pd
import io
from typing import Optional, Union
from datetime import datetime


def load_excel_data(
    file_content: Union[bytes, str],
    validate: bool = True
) -> pd.DataFrame:
    """
    Load OHLCV data from an uploaded Excel file.
    
    Expected format:
    - Required columns: Date, Symbol, Open, High, Low, Close, Volume
    - Date can be in any common format
    - Symbol should be text (e.g., 'RELIANCE', 'TCS')
    - OHLC should be numeric
    - Volume should be integer
    
    Args:
        file_content: Excel file content (bytes from upload or file path)
        validate: Whether to validate the data structure
        
    Returns:
        DataFrame with standardized columns: Date, Symbol, Open, High, Low, Close, Volume
        
    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    try:
        # Read Excel file
        if isinstance(file_content, bytes):
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        else:
            df = pd.read_excel(file_content, engine='openpyxl')
        
        if df.empty:
            raise ValueError("Excel file is empty")
        
        # Standardize column names (case-insensitive matching)
        column_mapping = {
            'date': 'Date',
            'datetime': 'Date',
            'timestamp': 'Date',
            'symbol': 'Symbol',
            'stock': 'Symbol',
            'ticker': 'Symbol',
            'tradingsymbol': 'Symbol',  # Support futures format
            'trading_symbol': 'Symbol',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'vol': 'Volume'
        }
        
        # Create a mapping of actual columns to standardized names
        new_columns = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in column_mapping:
                new_columns[col] = column_mapping[col_lower]
        
        # Rename columns
        df = df.rename(columns=new_columns)
        
        # Check for required columns
        required_columns = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {', '.join(missing_columns)}\n\n"
                f"Required columns: Date, Symbol, Open, High, Low, Close, Volume\n"
                f"Found columns: {', '.join(df.columns)}\n\n"
                f"Note: Column names are case-insensitive. You can use:\n"
                f"  - Date, DateTime, or Timestamp for dates\n"
                f"  - Symbol, Stock, or Ticker for symbol names\n"
                f"  - Open, High, Low, Close, Volume (standard OHLCV)"
            )
        
        # Drop the 'time' column if present (not needed for daily data)
        if 'time' in df.columns or 'Time' in df.columns:
            time_cols = [col for col in df.columns if col.lower() == 'time']
            df = df.drop(columns=time_cols)
            print("ℹ️  Dropped 'time' column (not required for backtesting)")
        
        # Keep only required columns
        df = df[required_columns].copy()
        
        if validate:
            # Validate and clean data
            df = _validate_and_clean_data(df)
        
        return df
        
    except Exception as e:
        if "Missing required columns" in str(e):
            raise
        raise ValueError(f"Error reading Excel file: {str(e)}")


def _validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean the loaded data.
    
    Args:
        df: Raw DataFrame with required columns
        
    Returns:
        Cleaned and validated DataFrame
        
    Raises:
        ValueError: If data validation fails
    """
    # Convert Date column to datetime
    try:
        df['Date'] = pd.to_datetime(df['Date'])
    except Exception as e:
        raise ValueError(f"Invalid date format in Date column: {e}")
    
    # Ensure Symbol is string
    df['Symbol'] = df['Symbol'].astype(str).str.upper().str.strip()
    
    # Convert OHLCV to numeric
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in numeric_cols:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except Exception as e:
            raise ValueError(f"Invalid numeric data in {col} column: {e}")
    
    # Remove rows with missing values
    initial_rows = len(df)
    df = df.dropna()
    removed_rows = initial_rows - len(df)
    
    if removed_rows > 0:
        print(f"⚠️  Removed {removed_rows} rows with missing values")
    
    if df.empty:
        raise ValueError("No valid data remaining after removing rows with missing values")
    
    # Validate OHLC relationships
    invalid_rows = (
        (df['High'] < df['Low']) |
        (df['High'] < df['Open']) |
        (df['High'] < df['Close']) |
        (df['Low'] > df['Open']) |
        (df['Low'] > df['Close']) |
        (df['Open'] <= 0) |
        (df['Close'] <= 0) |
        (df['Volume'] < 0)
    )
    
    if invalid_rows.any():
        n_invalid = invalid_rows.sum()
        print(f"⚠️  Found {n_invalid} rows with invalid OHLC relationships or negative values")
        
        # Show first few invalid rows for debugging
        if n_invalid > 0:
            print("First few invalid rows:")
            print(df[invalid_rows].head())
        
        # Remove invalid rows
        df = df[~invalid_rows]
        
        if df.empty:
            raise ValueError("No valid data remaining after removing invalid OHLC relationships")
    
    # Sort by Symbol and Date
    df = df.sort_values(['Symbol', 'Date']).reset_index(drop=True)
    
    # Summary
    symbols = df['Symbol'].unique()
    date_range = f"{df['Date'].min().date()} to {df['Date'].max().date()}"
    
    print(f"✓ Loaded {len(df)} records for {len(symbols)} symbol(s)")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Date range: {date_range}")
    
    return df


def create_sample_excel(output_path: str = "sample_data.xlsx"):
    """
    Create a sample Excel file template for users to fill in.
    
    Args:
        output_path: Path where to save the sample file
    """
    # Create sample data
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
    
    df = pd.DataFrame(sample_data)
    
    # Save to Excel
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"✓ Sample Excel file created: {output_path}")
    print(f"\nFormat:")
    print("  - Date: YYYY-MM-DD format")
    print("  - Symbol: Stock ticker (e.g., RELIANCE, TCS)")
    print("  - Open, High, Low, Close: Price values")
    print("  - Volume: Trading volume")
    
    return output_path


if __name__ == "__main__":
    # Test the loader
    print("Creating sample Excel file...")
    sample_file = create_sample_excel("sample_trading_data.xlsx")
    
    print("\n" + "="*60)
    print("Testing Excel loader...")
    print("="*60 + "\n")
    
    # Load the sample file
    df = load_excel_data(sample_file)
    
    print("\nLoaded data preview:")
    print(df.head(10))
    
    print("\nData types:")
    print(df.dtypes)
