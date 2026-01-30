"""
Option Contract Definition
==========================

This file defines what an option trade looks like.

🎓 FOR BEGINNERS:
An option contract has:
- Symbol: Which stock (e.g., RELIANCE)
- Type: CALL (bet price goes up) or PUT (bet price goes down)
- Strike: The price at which you can buy/sell
- Premium: How much you pay for the option (your max loss)
- Expiry: When the option expires

⚠️ HACKATHON SIMPLIFICATION:
We use a dataclass to keep things simple and readable.
No complex Greeks or margin calculations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class OptionType(Enum):
    """Type of option: CALL or PUT."""
    CALL = "CALL"  # Buy when you think price will GO UP
    PUT = "PUT"    # Buy when you think price will GO DOWN


@dataclass
class OptionContract:
    """
    Represents a single option trade.
    
    Attributes:
        symbol: Stock symbol (e.g., 'RELIANCE')
        option_type: CALL or PUT
        strike_price: The strike price (we use ATM = current stock price)
        entry_premium: Premium paid to buy the option
        entry_date: When we bought the option
        underlying_price_at_entry: Stock price when we entered
        expiry_date: When the option expires
        quantity: Number of contracts (default: 1)
        
    ⚠️ SIMPLIFIED:
    - Premium = 2% of stock price (not real Black-Scholes)
    - Strike = current stock price (ATM option)
    - Expiry = 30 days from entry (fixed)
    """
    symbol: str
    option_type: OptionType
    strike_price: float
    entry_premium: float
    entry_date: datetime
    underlying_price_at_entry: float
    expiry_date: datetime
    quantity: int = 1
    
    # Exit fields (filled when position is closed)
    exit_date: Optional[datetime] = None
    exit_premium: Optional[float] = None
    exit_reason: Optional[str] = None
    
    @classmethod
    def create_from_signal(
        cls,
        symbol: str,
        signal: int,  # +1 = BUY equity signal, -1 = SELL equity signal
        underlying_price: float,
        date: datetime,
        expiry_days: int = 30
    ) -> Optional['OptionContract']:
        """
        Create an option contract from an equity signal.
        
        Logic:
        - Equity BUY signal (+1)  → Create CALL option
        - Equity SELL signal (-1) → Create PUT option
        - No signal (0)           → Return None
        
        Args:
            symbol: Stock symbol
            signal: Equity signal (+1, -1, or 0)
            underlying_price: Current stock price
            date: Signal date
            expiry_days: Days until expiry (default: 30)
            
        Returns:
            OptionContract or None if no signal
            
        ⚠️ SIMPLIFIED PRICING:
        Premium = 2% of stock price (fixed assumption)
        This is NOT realistic but demonstrates the concept.
        """
        if signal == 0:
            return None
        
        # Determine option type from equity signal
        option_type = OptionType.CALL if signal == 1 else OptionType.PUT
        
        # SIMPLIFIED: Premium is 2% of stock price
        # Real options use Black-Scholes, but this is good enough for demo
        premium = underlying_price * 0.02
        
        # SIMPLIFIED: Strike = current price (ATM option)
        strike = underlying_price
        
        # SIMPLIFIED: Fixed 30-day expiry
        expiry = date + timedelta(days=expiry_days)
        
        return cls(
            symbol=symbol,
            option_type=option_type,
            strike_price=strike,
            entry_premium=premium,
            entry_date=date,
            underlying_price_at_entry=underlying_price,
            expiry_date=expiry,
            quantity=1
        )
    
    def calculate_current_premium(self, current_underlying_price: float) -> float:
        """
        Estimate current option premium based on underlying price movement.
        
        ⚠️ SIMPLIFIED MODEL (no Greeks):
        - CALL: If stock goes UP, option value goes UP
        - PUT: If stock goes DOWN, option value goes UP
        
        Formula:
        - CALL premium change ≈ (current_price - entry_price) / entry_price * 3
        - PUT premium change ≈ (entry_price - current_price) / entry_price * 3
        
        The "3" is a simplified "delta-like" multiplier.
        Real options have complex Greeks, but this captures the direction.
        """
        price_change_pct = (current_underlying_price - self.underlying_price_at_entry) / self.underlying_price_at_entry
        
        # Simplified multiplier (like a rough delta approximation)
        # ATM options have delta ~0.5, but moves are amplified
        leverage_factor = 3.0
        
        if self.option_type == OptionType.CALL:
            # CALL profits when price goes UP
            premium_change_pct = price_change_pct * leverage_factor
        else:
            # PUT profits when price goes DOWN
            premium_change_pct = -price_change_pct * leverage_factor
        
        # New premium (can't go below 0)
        new_premium = self.entry_premium * (1 + premium_change_pct)
        return max(new_premium, 0.01)  # Minimum premium of ₹0.01
    
    def calculate_pnl(self, exit_premium: float) -> float:
        """
        Calculate profit/loss on this option trade.
        
        P&L = (Exit Premium - Entry Premium) × Quantity
        
        Note: For options, max loss = premium paid (if buying options)
        """
        return (exit_premium - self.entry_premium) * self.quantity
    
    def calculate_pnl_percent(self, exit_premium: float) -> float:
        """Calculate P&L as percentage of premium paid."""
        return (exit_premium - self.entry_premium) / self.entry_premium * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            'Symbol': self.symbol,
            'Option_Type': self.option_type.value,
            'Strike': self.strike_price,
            'Entry_Date': self.entry_date,
            'Entry_Premium': self.entry_premium,
            'Underlying_Entry': self.underlying_price_at_entry,
            'Expiry_Date': self.expiry_date,
            'Quantity': self.quantity,
            'Exit_Date': self.exit_date,
            'Exit_Premium': self.exit_premium,
            'Exit_Reason': self.exit_reason,
            'PnL': self.calculate_pnl(self.exit_premium) if self.exit_premium else None,
            'PnL_Pct': self.calculate_pnl_percent(self.exit_premium) if self.exit_premium else None
        }
