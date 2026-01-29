"""
Signal generation module.
Generates buy/sell signals based on technical indicators and strategy rules.
"""
import pandas as pd
import numpy as np
from typing import Dict


class SignalGenerator:
    """Generate trading signals based on multi-indicator strategy."""
    
    def __init__(
        self,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        rsi_neutral_low: float = 35,
        rsi_neutral_high: float = 65,
        gap_threshold: float = 0.03
    ):
        """
        Initialize signal generator with strategy parameters.
        
        Args:
            rsi_oversold: RSI level considered oversold
            rsi_overbought: RSI level considered overbought
            rsi_neutral_low: Lower bound for neutral RSI (buy condition)
            rsi_neutral_high: Upper bound for neutral RSI (buy condition)
            gap_threshold: Maximum gap between open and previous close (3%)
        """
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_neutral_low = rsi_neutral_low
        self.rsi_neutral_high = rsi_neutral_high
        self.gap_threshold = gap_threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals for the dataframe.
        
        Args:
            df: DataFrame with OHLCV data and technical indicators
            
        Returns:
            DataFrame with added 'Signal' column (1=Buy, -1=Sell, 0=Hold)
        """
        df = df.copy()
        
        # Initialize signal column
        df['Signal'] = 0
        df['Signal_Strength'] = 0.0
        
        # Process each symbol separately
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            symbol_df = df[mask].copy()
            
            # Generate buy signals
            buy_signals = self._generate_buy_signals(symbol_df)
            
            # Generate sell signals
            sell_signals = self._generate_sell_signals(symbol_df)
            
            # Apply signals to main dataframe
            df.loc[mask, 'Signal'] = 0
            df.loc[mask & buy_signals, 'Signal'] = 1
            df.loc[mask & sell_signals, 'Signal'] = -1
            
            # Calculate signal strength (0-1)
            df.loc[mask, 'Signal_Strength'] = self._calculate_signal_strength(
                symbol_df, buy_signals, sell_signals
            )
        
        return df
    
    def _generate_buy_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate buy signals based on strategy rules.
        
        BUY when ALL conditions are met:
        1. Short MA crosses above Long MA (golden cross)
        2. RSI between 30-70 (not extreme)
        3. MACD line crosses above signal line
        4. Price near or below lower Bollinger Band
        5. No large gap from previous close
        """
        # Condition 1: Golden Cross (MA crossover)
        ma_cross = (
            (df['MA_Short'] > df['MA_Long']) &
            (df['MA_Short'].shift(1) <= df['MA_Long'].shift(1))
        )
        
        # Condition 2: RSI in neutral zone
        rsi_neutral = (
            (df['RSI'] >= self.rsi_neutral_low) &
            (df['RSI'] <= self.rsi_neutral_high)
        )
        
        # Condition 3: MACD bullish crossover
        macd_cross = (
            (df['MACD'] > df['MACD_Signal']) &
            (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        )
        
        # Condition 4: Price near lower Bollinger Band
        # Consider "near" as within 2% of lower band
        price_near_lower_bb = (
            df['Close'] <= df['BB_Lower'] * 1.02
        )
        
        # Condition 5: No large gap
        gap = abs(df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
        no_large_gap = (gap <= self.gap_threshold) | gap.isna()
        
        # Alternative buy condition: Strong oversold with upward momentum
        strong_oversold = (
            (df['RSI'] < self.rsi_oversold) &
            (df['MACD'] > df['MACD_Signal']) &
            (df['Close'] < df['BB_Lower'])
        )
        
        # More practical approach: Buy when at least 3 out of 5 conditions are met
        # OR in strong oversold situation
        condition_count = (
            ma_cross.astype(int) +
            rsi_neutral.astype(int) +
            macd_cross.astype(int) +
            price_near_lower_bb.astype(int) +
            no_large_gap.astype(int)
        )
        
        # Buy if 3+ conditions met OR strong oversold
        buy_signal = (condition_count >= 3) | strong_oversold

        
        return buy_signal
    
    def _generate_sell_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate sell signals based on strategy rules.
        
        SELL when ANY condition is met:
        1. Short MA crosses below Long MA (death cross)
        2. RSI > 70 (overbought)
        3. MACD line crosses below signal line
        4. Price touches upper Bollinger Band
        """
        # Condition 1: Death Cross
        ma_cross = (
            (df['MA_Short'] < df['MA_Long']) &
            (df['MA_Short'].shift(1) >= df['MA_Long'].shift(1))
        )
        
        # Condition 2: RSI overbought
        rsi_overbought = df['RSI'] > self.rsi_overbought
        
        # Condition 3: MACD bearish crossover
        macd_cross = (
            (df['MACD'] < df['MACD_Signal']) &
            (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        )
        
        # Condition 4: Price at upper Bollinger Band
        price_at_upper_bb = df['Close'] >= df['BB_Upper'] * 0.98
        
        # Combine conditions (any condition triggers sell)
        sell_signal = (
            ma_cross | rsi_overbought | macd_cross | price_at_upper_bb
        )
        
        return sell_signal
    
    def _calculate_signal_strength(
        self, 
        df: pd.DataFrame, 
        buy_signals: pd.Series, 
        sell_signals: pd.Series
    ) -> pd.Series:
        """
        Calculate signal strength (0-1) based on indicator alignment.
        Higher strength means more indicators agree.
        """
        strength = pd.Series(0.0, index=df.index)
        
        # For buy signals, count how many conditions are met
        buy_indices = buy_signals[buy_signals].index
        for idx in buy_indices:
            conditions_met = 0
            total_conditions = 5
            
            if idx > 0:
                # Check each condition
                if df.loc[idx, 'MA_Short'] > df.loc[idx, 'MA_Long']:
                    conditions_met += 1
                if 30 <= df.loc[idx, 'RSI'] <= 70:
                    conditions_met += 1
                if df.loc[idx, 'MACD'] > df.loc[idx, 'MACD_Signal']:
                    conditions_met += 1
                if df.loc[idx, 'Close'] <= df.loc[idx, 'BB_Lower'] * 1.02:
                    conditions_met += 1
                conditions_met += 1  # No gap condition assumed met
                
                strength.loc[idx] = conditions_met / total_conditions
        
        # For sell signals
        sell_indices = sell_signals[sell_signals].index
        for idx in sell_indices:
            conditions_met = 0
            total_conditions = 4
            
            if df.loc[idx, 'MA_Short'] < df.loc[idx, 'MA_Long']:
                conditions_met += 1
            if df.loc[idx, 'RSI'] > 70:
                conditions_met += 1
            if df.loc[idx, 'MACD'] < df.loc[idx, 'MACD_Signal']:
                conditions_met += 1
            if df.loc[idx, 'Close'] >= df.loc[idx, 'BB_Upper'] * 0.98:
                conditions_met += 1
            
            strength.loc[idx] = conditions_met / total_conditions
        
        return strength


def generate_signals(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Convenience function to generate trading signals.
    
    Args:
        df: DataFrame with OHLCV data and indicators
        **kwargs: Signal generation parameters
        
    Returns:
        DataFrame with signals
    """
    generator = SignalGenerator(**kwargs)
    return generator.generate_signals(df)


if __name__ == "__main__":
    # Test signal generation
    from data.fetcher import fetch_equity_data
    from data.preprocessor import preprocess_data
    from strategy.indicators import add_indicators
    
    symbols = ['RELIANCE']
    raw_data = fetch_equity_data(symbols, '2023-01-01', '2024-01-01')
    clean_data = preprocess_data(raw_data)
    df_with_indicators = add_indicators(clean_data)
    df_with_signals = generate_signals(df_with_indicators)
    
    print("Signals generated:")
    print(df_with_signals[df_with_signals['Signal'] != 0][
        ['Date', 'Symbol', 'Close', 'Signal', 'Signal_Strength', 'RSI', 'MACD']
    ])
    
    print(f"\nBuy signals: {(df_with_signals['Signal'] == 1).sum()}")
    print(f"Sell signals: {(df_with_signals['Signal'] == -1).sum()}")
