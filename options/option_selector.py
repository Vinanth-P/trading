"""
Option Selector
===============

Converts equity trading signals into option trade selections.

🎓 FOR BEGINNERS:
This module answers the question:
"The equity strategy says BUY/SELL. Which option should we trade?"

Logic:
- Equity BUY signal  → Select a CALL option (profit if price rises)
- Equity SELL signal → Select a PUT option (profit if price falls)

⚠️ HACKATHON SIMPLIFICATION:
- We always select ATM (At-The-Money) options
- Strike = current stock price
- No complex strike selection logic
- No delta/gamma optimization
"""

import pandas as pd
from datetime import datetime
from typing import List, Optional, Tuple

from options.option_contract import OptionContract, OptionType


class OptionSelector:
    """
    Selects which option to trade based on equity signals.
    
    This is the "bridge" between equity signals and options trades.
    
    ⚠️ SIMPLIFIED for hackathon:
    - Always selects ATM options (strike = current price)
    - Premium estimated as 2% of stock price
    - No strike optimization or volatility analysis
    """
    
    def __init__(
        self,
        premium_percent: float = 0.02,
        expiry_days: int = 30
    ):
        """
        Initialize option selector.
        
        Args:
            premium_percent: Option premium as % of stock price (default: 2%)
            expiry_days: Days until option expiry (default: 30)
            
        ⚠️ These are SIMPLIFIED assumptions, not real market data.
        """
        self.premium_percent = premium_percent
        self.expiry_days = expiry_days
    
    def select_option_from_signal(
        self,
        symbol: str,
        signal: int,
        underlying_price: float,
        date: datetime
    ) -> Optional[OptionContract]:
        """
        Convert an equity signal to an option trade.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            signal: Equity signal (+1=BUY, -1=SELL, 0=HOLD)
            underlying_price: Current stock price
            date: Signal date
            
        Returns:
            OptionContract if signal is +1 or -1, None if 0
            
        Examples:
            signal=+1 (BUY equity)  → CALL option on RELIANCE
            signal=-1 (SELL equity) → PUT option on RELIANCE
            signal=0 (HOLD)         → No option trade
        """
        return OptionContract.create_from_signal(
            symbol=symbol,
            signal=signal,
            underlying_price=underlying_price,
            date=date,
            expiry_days=self.expiry_days
        )
    
    def process_signals_dataframe(
        self,
        df: pd.DataFrame
    ) -> List[Tuple[datetime, str, OptionContract]]:
        """
        Process a DataFrame with equity signals and extract option trades.
        
        Args:
            df: DataFrame with columns: Date, Symbol, Close, Signal
            
        Returns:
            List of tuples: (date, symbol, OptionContract)
            Only includes rows where Signal != 0
            
        This is used by the backtester to know WHEN and WHAT options to trade.
        """
        option_signals = []
        
        for _, row in df.iterrows():
            signal = row.get('Signal', 0)
            
            if signal != 0:
                option = self.select_option_from_signal(
                    symbol=row['Symbol'],
                    signal=int(signal),
                    underlying_price=row['Close'],
                    date=row['Date']
                )
                
                if option:
                    option_signals.append((row['Date'], row['Symbol'], option))
        
        return option_signals
    
    def explain_selection(self, signal: int, symbol: str, price: float) -> str:
        """
        Generate human-readable explanation of option selection.
        
        Used for UI display and judge explanation.
        """
        if signal == 1:
            option_type = "CALL"
            reason = "Equity indicators are BULLISH (BUY signal)"
            expectation = "Stock price expected to RISE"
        elif signal == -1:
            option_type = "PUT"
            reason = "Equity indicators are BEARISH (SELL signal)"
            expectation = "Stock price expected to FALL"
        else:
            return f"No option trade for {symbol} (HOLD signal)"
        
        premium = price * self.premium_percent
        
        return (
            f"📊 {symbol} Option Selection:\n"
            f"   • Type: {option_type}\n"
            f"   • Strike: ₹{price:.2f} (ATM)\n"
            f"   • Premium: ₹{premium:.2f} (estimated)\n"
            f"   • Reason: {reason}\n"
            f"   • Expectation: {expectation}"
        )


def select_options_from_equity_signals(
    df: pd.DataFrame,
    premium_percent: float = 0.02,
    expiry_days: int = 30
) -> List[Tuple[datetime, str, OptionContract]]:
    """
    Convenience function to convert equity signals to option selections.
    
    Args:
        df: DataFrame with equity signals (must have: Date, Symbol, Close, Signal)
        premium_percent: Option premium as % of stock price
        expiry_days: Days until option expiry
        
    Returns:
        List of (date, symbol, OptionContract) tuples
        
    Usage:
        options = select_options_from_equity_signals(df_with_signals)
    """
    selector = OptionSelector(
        premium_percent=premium_percent,
        expiry_days=expiry_days
    )
    return selector.process_signals_dataframe(df)
