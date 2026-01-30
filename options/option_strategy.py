"""
Option Exit Strategy
====================

Decides WHEN to close an option position.

🎓 FOR BEGINNERS:
After buying an option, we need rules for when to sell it:
1. PROFIT TARGET: Close if option gains +50% (lock in profits)
2. STOP LOSS: Close if option loses -30% (limit losses)
3. SIGNAL REVERSAL: Close if equity signal flips (strategy changed mind)
4. EXPIRY: Close before expiry (avoid complications)

⚠️ HACKATHON SIMPLIFICATION:
- No complex Greeks-based exits
- No theta decay modeling
- Simple percentage-based targets
- Early exit on signal reversal
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from options.option_contract import OptionContract, OptionType


@dataclass
class ExitConditions:
    """
    Configuration for option exit rules.
    
    Attributes:
        profit_target_pct: Exit when profit reaches this % (default: 50%)
        stop_loss_pct: Exit when loss reaches this % (default: -30%)
        days_before_expiry: Exit this many days before expiry (default: 5)
        exit_on_opposite_signal: Exit if equity signal reverses (default: True)
    """
    profit_target_pct: float = 50.0   # Exit at +50% profit
    stop_loss_pct: float = -30.0      # Exit at -30% loss
    days_before_expiry: int = 5       # Exit 5 days before expiry
    exit_on_opposite_signal: bool = True  # Exit if signal flips


class OptionExitStrategy:
    """
    Determines when to exit an option position.
    
    Exit Logic (in order of priority):
    1. Stop Loss Hit → Exit immediately to limit loss
    2. Profit Target Hit → Exit to lock in gains
    3. Opposite Signal → Strategy reversed, exit position
    4. Near Expiry → Exit to avoid expiry complications
    
    ⚠️ SIMPLIFIED for hackathon:
    - Uses simple % targets, not Greeks
    - No rolling to next expiry
    - No partial exits
    """
    
    def __init__(self, conditions: Optional[ExitConditions] = None):
        """
        Initialize exit strategy with conditions.
        
        Args:
            conditions: Exit rules (uses defaults if None)
        """
        self.conditions = conditions or ExitConditions()
    
    def should_exit(
        self,
        option: OptionContract,
        current_date: datetime,
        current_underlying_price: float,
        current_equity_signal: int = 0
    ) -> Tuple[bool, str, float]:
        """
        Check if we should exit the option position.
        
        Args:
            option: The option contract to evaluate
            current_date: Today's date
            current_underlying_price: Current stock price
            current_equity_signal: Current equity signal (+1, -1, 0)
            
        Returns:
            Tuple of:
            - should_exit: True if we should close the position
            - exit_reason: Why we're exiting (for logging)
            - exit_premium: The premium at exit
            
        Exit Priority:
        1. Stop Loss (most important - protect capital)
        2. Profit Target (second - lock gains)
        3. Opposite Signal (third - strategy changed)
        4. Near Expiry (last - avoid complications)
        """
        # Calculate current option value
        current_premium = option.calculate_current_premium(current_underlying_price)
        pnl_pct = option.calculate_pnl_percent(current_premium)
        
        # 1. CHECK STOP LOSS (highest priority)
        if pnl_pct <= self.conditions.stop_loss_pct:
            return True, f"Stop Loss ({pnl_pct:.1f}%)", current_premium
        
        # 2. CHECK PROFIT TARGET
        if pnl_pct >= self.conditions.profit_target_pct:
            return True, f"Profit Target ({pnl_pct:.1f}%)", current_premium
        
        # 3. CHECK OPPOSITE SIGNAL
        if self.conditions.exit_on_opposite_signal and current_equity_signal != 0:
            # CALL should exit on SELL signal
            # PUT should exit on BUY signal
            if option.option_type == OptionType.CALL and current_equity_signal == -1:
                return True, "Opposite Signal (SELL)", current_premium
            elif option.option_type == OptionType.PUT and current_equity_signal == 1:
                return True, "Opposite Signal (BUY)", current_premium
        
        # 4. CHECK EXPIRY APPROACHING
        days_to_expiry = (option.expiry_date - current_date).days
        if days_to_expiry <= self.conditions.days_before_expiry:
            return True, f"Near Expiry ({days_to_expiry} days)", current_premium
        
        # No exit condition met
        return False, "", current_premium
    
    def explain_exit(self, reason: str, pnl: float, pnl_pct: float) -> str:
        """
        Generate human-readable exit explanation.
        
        Used for trade log and UI display.
        """
        profit_loss = "PROFIT" if pnl >= 0 else "LOSS"
        emoji = "✅" if pnl >= 0 else "❌"
        
        return (
            f"{emoji} Option Exit: {reason}\n"
            f"   • P&L: ₹{pnl:.2f} ({pnl_pct:.1f}%)\n"
            f"   • Result: {profit_loss}"
        )


def create_default_exit_strategy() -> OptionExitStrategy:
    """
    Create exit strategy with hackathon-optimized defaults.
    
    Returns:
        OptionExitStrategy with:
        - +50% profit target
        - -30% stop loss
        - Exit on opposite signal
        - Exit 5 days before expiry
    """
    return OptionExitStrategy(ExitConditions(
        profit_target_pct=50.0,
        stop_loss_pct=-30.0,
        days_before_expiry=5,
        exit_on_opposite_signal=True
    ))
