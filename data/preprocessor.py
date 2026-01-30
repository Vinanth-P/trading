"""
Data preprocessing module for cleaning and preparing equity data.
"""
import pandas as pd
import numpy as np
from typing import Optional


class DataPreprocessor:
    """Preprocess and clean equity data for backtesting."""
    
    def __init__(self):
        pass
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all preprocessing steps to the data.
        
        Args:
            df: Raw DataFrame with OHLCV data
            
        Returns:
            Preprocessed DataFrame
        """
        df = df.copy()
        
        # Ensure Date is datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sort by symbol and date
        df = df.sort_values(['Symbol', 'Date']).reset_index(drop=True)
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Remove outliers
        df = self._remove_outliers(df)
        
        # Calculate returns
        df = self._calculate_returns(df)
        
        # Validate data
        df = self._validate_data(df)
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset."""
        # Forward fill missing prices (use previous day's price)
        price_columns = ['Open', 'High', 'Low', 'Close']
        
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            df.loc[mask, price_columns] = df.loc[mask, price_columns].ffill()
        
        # Fill remaining NaN with backward fill
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            df.loc[mask, price_columns] = df.loc[mask, price_columns].bfill()
        
        # Fill volume with 0 if missing
        df['Volume'] = df['Volume'].fillna(0)
        
        # Drop rows that still have NaN
        df = df.dropna()
        
        return df
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove or cap extreme outliers that could be data errors.
        Using interquartile range (IQR) method for returns.
        """
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            symbol_data = df.loc[mask].copy()
            
            # Calculate daily returns
            symbol_data['temp_returns'] = symbol_data['Close'].pct_change()
            
            # Calculate IQR
            Q1 = symbol_data['temp_returns'].quantile(0.25)
            Q3 = symbol_data['temp_returns'].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier bounds (3 * IQR is more lenient than 1.5 * IQR)
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            # Remove extreme outliers
            outlier_mask = (
                (symbol_data['temp_returns'] < lower_bound) | 
                (symbol_data['temp_returns'] > upper_bound)
            )
            
            # Don't remove first row (NaN return)
            outlier_mask.iloc[0] = False
            
            # Update the main dataframe
            valid_indices = symbol_data[~outlier_mask].index
            df = df[df.index.isin(valid_indices) | (df['Symbol'] != symbol)]
        
        return df
    
    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns for each symbol."""
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            df.loc[mask, 'Returns'] = df.loc[mask, 'Close'].pct_change()
        
        # Fill first return with 0
        df['Returns'] = df['Returns'].fillna(0)
        
        return df
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data integrity.
        Ensure High >= Low, Close between High and Low, etc.
        """
        # Remove rows where High < Low (data error)
        df = df[df['High'] >= df['Low']]
        
        # Ensure Close is between High and Low
        df = df[
            (df['Close'] >= df['Low']) & 
            (df['Close'] <= df['High'])
        ]
        
        # Ensure Open is between High and Low
        df = df[
            (df['Open'] >= df['Low']) & 
            (df['Open'] <= df['High'])
        ]
        
        # Remove negative prices
        df = df[
            (df['Open'] > 0) & 
            (df['High'] > 0) & 
            (df['Low'] > 0) & 
            (df['Close'] > 0)
        ]
        
        # Remove negative volumes
        df = df[df['Volume'] >= 0]
        
        return df.reset_index(drop=True)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to preprocess data.
    
    Args:
        df: Raw DataFrame with OHLCV data
        
    Returns:
        Preprocessed DataFrame
    """
    preprocessor = DataPreprocessor()
    return preprocessor.preprocess(df)


if __name__ == "__main__":
    # Test the preprocessor
    from fetcher import fetch_equity_data
    
    symbols = ['RELIANCE', 'TCS']
    raw_data = fetch_equity_data(symbols, '2023-01-01', '2024-01-01')
    
    print("Raw data shape:", raw_data.shape)
    print("\nRaw data sample:")
    print(raw_data.head())
    
    clean_data = preprocess_data(raw_data)
    
    print("\n\nClean data shape:", clean_data.shape)
    print("\nClean data sample:")
    print(clean_data.head())
    print("\nClean data columns:", clean_data.columns.tolist())
