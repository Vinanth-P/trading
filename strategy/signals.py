"""
Signal generation module.
SIMPLIFIED TREND-FOLLOWING STRATEGY for better performance.

Key principles:
1. Trade WITH the trend, not against it
2. Use fewer, higher-quality signals
3. Let winners run, cut losers quickly
"""
import pandas as pd
import numpy as np
from typing import Dict


class SignalGenerator:
    """Generate trading signals based on simplified trend-following strategy."""
    
    def __init__(
        self,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        rsi_neutral_low: float = 40,
        rsi_neutral_high: float = 60,
        gap_threshold: float = 0.03
    ):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_neutral_low = rsi_neutral_low
        self.rsi_neutral_high = rsi_neutral_high
        self.gap_threshold = gap_threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals for the dataframe."""
        df = df.copy()
        df['Signal'] = 0
        df['Signal_Strength'] = 0.0
        
        for symbol in df['Symbol'].unique():
            mask = df['Symbol'] == symbol
            symbol_df = df[mask].copy()
            
            buy_signals = self._generate_buy_signals(symbol_df)
            sell_signals = self._generate_sell_signals(symbol_df)
            
            df.loc[mask, 'Signal'] = 0
            df.loc[mask & buy_signals, 'Signal'] = 1
            df.loc[mask & sell_signals, 'Signal'] = -1
            
            df.loc[mask, 'Signal_Strength'] = self._calculate_signal_strength(
                symbol_df, buy_signals, sell_signals
            )
        
        return df
    
    def _generate_buy_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        SIMPLIFIED BUY STRATEGY:
        Buy when price momentum is positive and oversold conditions exist.
        
        Entry signals:
        1. Golden Cross + MACD confirmation
        2. Oversold bounce (RSI reversal from <30)
        3. Trend continuation (pullback in uptrend)
        """
        # === TREND DETECTION ===
        uptrend = df['MA_Short'] > df['MA_Long']
        strong_uptrend = (df['Close'] > df['MA_Short']) & (df['MA_Short'] > df['MA_Long'])
        
        # === MOMENTUM ===
        macd_positive = df['MACD'] > df['MACD_Signal']
        macd_turning_up = (df['MACD'] > df['MACD'].shift(1))
        rsi_rising = df['RSI'] > df['RSI'].shift(1)
        
        # === ENTRY SIGNALS ===
        
        # Signal 1: Golden Cross with momentum confirmation
        golden_cross = (
            (df['MA_Short'] > df['MA_Long']) &
            (df['MA_Short'].shift(1) <= df['MA_Long'].shift(1)) &
            macd_positive
        )
        
        # Signal 2: Oversold bounce - RSI turning up from oversold
        oversold_bounce = (
            (df['RSI'] < 35) &
            rsi_rising &
            (df['Close'] > df['Open'])  # Bullish candle
        )
        
        # Signal 3: Pullback entry in uptrend
        # Price pulled back to MA but trend still intact
        pullback_entry = (
            strong_uptrend &
            (df['Close'] <= df['MA_Short'] * 1.01) &  # Price near short MA
            (df['Close'] > df['MA_Long']) &  # Still above long MA
            (df['RSI'] < 50) &  # RSI not overbought
            macd_positive &
            (df['Close'] > df['Open'])  # Bullish candle
        )
        
        # Signal 4: MACD crossover in uptrend
        macd_cross_up = (
            uptrend &
            (df['MACD'] > df['MACD_Signal']) &
            (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) &
            (df['RSI'] < 60)  # Not overbought
        )
        
        # Combine signals
        buy_signal = golden_cross | oversold_bounce | pullback_entry | macd_cross_up
        
        return buy_signal
    
    def _generate_sell_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        SIMPLIFIED SELL STRATEGY:
        Sell only on clear trend reversal, not on minor pullbacks.
        
        Exit signals:
        1. Death Cross (clear trend reversal)
        2. Extreme overbought with reversal
        3. MACD bearish divergence in downtrend
        """
        # === TREND DETECTION ===
        downtrend = df['MA_Short'] < df['MA_Long']
        
        # === REVERSAL SIGNALS ===
        
        # Signal 1: Death Cross - clear trend reversal
        death_cross = (
            (df['MA_Short'] < df['MA_Long']) &
            (df['MA_Short'].shift(1) >= df['MA_Long'].shift(1))
        )
        
        # Signal 2: Extreme overbought reversal
        # RSI > 75 and starting to fall + bearish candle
        overbought_reversal = (
            (df['RSI'] > 75) &
            (df['RSI'] < df['RSI'].shift(1)) &  # RSI falling
            (df['Close'] < df['Open'])  # Bearish candle
        )
        
        # Signal 3: MACD bearish crossover in downtrend
        macd_cross_down = (
            downtrend &
            (df['MACD'] < df['MACD_Signal']) &
            (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        )
        
        # Signal 4: Price breakdown below long MA in downtrend
        breakdown = (
            downtrend &
            (df['Close'] < df['MA_Long']) &
            (df['Close'].shift(1) >= df['MA_Long'].shift(1)) &
            (df['RSI'] < 50)
        )
        
        # Combine signals - require stronger confirmation
        sell_signal = death_cross | overbought_reversal | (macd_cross_down & breakdown)
        
        return sell_signal
    
    def _calculate_signal_strength(
        self, 
        df: pd.DataFrame, 
        buy_signals: pd.Series, 
        sell_signals: pd.Series
    ) -> pd.Series:
        """Calculate signal strength (0-1)."""
        strength = pd.Series(0.5, index=df.index)
        
        for idx in buy_signals[buy_signals].index:
            try:
                score = 0
                if df.loc[idx, 'MA_Short'] > df.loc[idx, 'MA_Long']:
                    score += 1
                if df.loc[idx, 'MACD'] > df.loc[idx, 'MACD_Signal']:
                    score += 1
                if df.loc[idx, 'RSI'] < 60:
                    score += 1
                if df.loc[idx, 'Close'] > df.loc[idx, 'Open']:
                    score += 1
                strength.loc[idx] = score / 4
            except:
                pass
        
        for idx in sell_signals[sell_signals].index:
            try:
                score = 0
                if df.loc[idx, 'MA_Short'] < df.loc[idx, 'MA_Long']:
                    score += 1
                if df.loc[idx, 'MACD'] < df.loc[idx, 'MACD_Signal']:
                    score += 1
                if df.loc[idx, 'RSI'] > 50:
                    score += 1
                if df.loc[idx, 'Close'] < df.loc[idx, 'Open']:
                    score += 1
                strength.loc[idx] = score / 4
            except:
                pass
        
        return strength


def generate_signals(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convenience function to generate trading signals."""
    generator = SignalGenerator(**kwargs)
    return generator.generate_signals(df)


if __name__ == "__main__":
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
        ['Date', 'Symbol', 'Close', 'Signal', 'RSI', 'MACD']
    ])
    
    print(f"\nBuy signals: {(df_with_signals['Signal'] == 1).sum()}")
    print(f"Sell signals: {(df_with_signals['Signal'] == -1).sum()}")
