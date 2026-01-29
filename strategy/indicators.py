"""
Technical indicators module.
Calculates various technical indicators for trading strategy.
"""
import pandas as pd
import numpy as np
from typing import Tuple


class TechnicalIndicators:
    """Calculate technical indicators for trading strategies."""
    
    def __init__(self):
        pass
    
    def add_all_indicators(
        self, 
        df: pd.DataFrame,
        short_ma: int = 20,
        long_ma: int = 50,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0
    ) -> pd.DataFrame:
        """
        Add all technical indicators to the dataframe.
        
        Args:
            df: DataFrame with OHLCV data
            short_ma: Short moving average period
            long_ma: Long moving average period
            rsi_period: RSI calculation period
            macd_fast: MACD fast period
            macd_slow: MACD slow period
            macd_signal: MACD signal period
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation
            
        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()
        
        # Process each symbol separately
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            symbol_data = df.loc[mask, 'Close'].values
            high_data = df.loc[mask, 'High'].values
            low_data = df.loc[mask, 'Low'].values
            
            # Moving Averages
            df.loc[mask, 'MA_Short'] = self._calculate_sma(symbol_data, short_ma)
            df.loc[mask, 'MA_Long'] = self._calculate_sma(symbol_data, long_ma)
            
            # RSI
            df.loc[mask, 'RSI'] = self._calculate_rsi(symbol_data, rsi_period)
            
            # MACD
            macd, signal, histogram = self._calculate_macd(
                symbol_data, macd_fast, macd_slow, macd_signal
            )
            df.loc[mask, 'MACD'] = macd
            df.loc[mask, 'MACD_Signal'] = signal
            df.loc[mask, 'MACD_Hist'] = histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                symbol_data, bb_period, bb_std
            )
            df.loc[mask, 'BB_Upper'] = bb_upper
            df.loc[mask, 'BB_Middle'] = bb_middle
            df.loc[mask, 'BB_Lower'] = bb_lower
            
            # Additional useful metrics
            df.loc[mask, 'ATR'] = self._calculate_atr(high_data, low_data, symbol_data, 14)
        
        return df
    
    def _calculate_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        return pd.Series(data).rolling(window=period).mean().values
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        return pd.Series(data).ewm(span=period, adjust=False).mean().values
    
    def _calculate_rsi(self, data: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index.
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        """
        series = pd.Series(data)
        delta = series.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.values
    
    def _calculate_macd(
        self, 
        data: np.ndarray, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        series = pd.Series(data)
        
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    def _calculate_bollinger_bands(
        self, 
        data: np.ndarray, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Bollinger Bands.
        
        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        series = pd.Series(data)
        
        middle_band = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band.values, middle_band.values, lower_band.values
    
    def _calculate_atr(
        self, 
        high: np.ndarray, 
        low: np.ndarray, 
        close: np.ndarray, 
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate Average True Range (ATR) for volatility measurement.
        """
        high_series = pd.Series(high)
        low_series = pd.Series(low)
        close_series = pd.Series(close)
        
        # True Range calculation
        tr1 = high_series - low_series
        tr2 = abs(high_series - close_series.shift())
        tr3 = abs(low_series - close_series.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.values


def add_indicators(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Convenience function to add indicators to dataframe.
    
    Args:
        df: DataFrame with OHLCV data
        **kwargs: Indicator parameters
        
    Returns:
        DataFrame with indicators
    """
    calculator = TechnicalIndicators()
    return calculator.add_all_indicators(df, **kwargs)


if __name__ == "__main__":
    # Test the indicators
    from data.fetcher import fetch_equity_data
    from data.preprocessor import preprocess_data
    
    symbols = ['RELIANCE']
    raw_data = fetch_equity_data(symbols, '2023-01-01', '2024-01-01')
    clean_data = preprocess_data(raw_data)
    
    df_with_indicators = add_indicators(clean_data)
    
    print("Columns:", df_with_indicators.columns.tolist())
    print("\nData with indicators:")
    print(df_with_indicators[['Date', 'Close', 'MA_Short', 'MA_Long', 'RSI', 'MACD']].tail(10))
    
    # Check for NaN values
    print("\nNaN counts:")
    print(df_with_indicators.isna().sum())
