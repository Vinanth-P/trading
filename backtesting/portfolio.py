"""
Portfolio management module.
Tracks positions, calculates P&L, enforces position sizing and risk management.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Position:
    """Represents an open trading position."""
    symbol: str
    entry_date: datetime
    entry_price: float
    quantity: int
    stop_loss: float
    take_profit: float
    position_value: float
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate current profit/loss."""
        return (current_price - self.entry_price) * self.quantity
    
    def calculate_return(self, current_price: float) -> float:
        """Calculate return percentage."""
        return (current_price - self.entry_price) / self.entry_price
    
    def should_exit(self, current_price: float) -> Tuple[bool, str]:
        """
        Check if position should be exited based on stop-loss or take-profit.
        
        Returns:
            Tuple of (should_exit, reason)
        """
        if current_price <= self.stop_loss:
            return True, "Stop Loss"
        elif current_price >= self.take_profit:
            return True, "Take Profit"
        return False, ""


class Portfolio:
    """Manages portfolio positions and cash."""
    
    def __init__(
        self,
        initial_capital: float = 1000000,
        position_size: float = 0.20,
        max_positions: int = 3,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10,
        transaction_cost: float = 0.001
    ):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Starting cash
            position_size: Fraction of portfolio per trade (0.20 = 20%)
            max_positions: Maximum concurrent positions
            stop_loss_pct: Stop loss percentage (0.05 = 5% below entry)
            take_profit_pct: Take profit percentage (0.10 = 10% above entry)
            transaction_cost: Transaction cost per trade (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position_size = position_size
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.transaction_cost = transaction_cost
        
        # Active positions
        self.positions: Dict[str, Position] = {}
        
        # Trade history
        self.trade_history: List[Dict] = []
        
        # Portfolio value history
        self.portfolio_values: List[Dict] = []
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value (cash + positions).
        
        Args:
            current_prices: Dict of {symbol: current_price}
            
        Returns:
            Total portfolio value
        """
        position_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.entry_price)
            for pos in self.positions.values()
        )
        return self.cash + position_value
    
    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position."""
        # Already have position in this symbol
        if symbol in self.positions:
            return False
        
        # Already at max positions
        if len(self.positions) >= self.max_positions:
            return False
        
        # Not enough cash
        position_value = self.cash * self.position_size
        if position_value < 100:  # Minimum trade size
            return False
        
        return True
    
    def open_position(
        self, 
        symbol: str, 
        date: datetime, 
        price: float
    ) -> Optional[Position]:
        """
        Open a new position.
        
        Args:
            symbol: Stock symbol
            date: Entry date
            price: Entry price
            
        Returns:
            Position object if opened, None if couldn't open
        """
        if not self.can_open_position(symbol):
            return None
        
        # Calculate position size
        position_value = self.cash * self.position_size
        
        # Apply transaction cost
        cost_multiplier = 1 + self.transaction_cost
        effective_cost = price * cost_multiplier
        
        # Calculate quantity (round down to whole shares)
        quantity = int(position_value / effective_cost)
        
        if quantity < 1:
            return None
        
        # Calculate actual cost
        total_cost = quantity * effective_cost
        
        # Check if we have enough cash
        if total_cost > self.cash:
            return None
        
        # Calculate stop loss and take profit
        stop_loss = price * (1 - self.stop_loss_pct)
        take_profit = price * (1 + self.take_profit_pct)
        
        # Create position
        position = Position(
            symbol=symbol,
            entry_date=date,
            entry_price=price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_value=total_cost
        )
        
        # Update portfolio
        self.cash -= total_cost
        self.positions[symbol] = position
        
        return position
    
    def close_position(
        self, 
        symbol: str, 
        date: datetime, 
        price: float, 
        reason: str = "Signal"
    ) -> Optional[Dict]:
        """
        Close a position.
        
        Args:
            symbol: Stock symbol
            date: Exit date
            price: Exit price
            reason: Reason for exit
            
        Returns:
            Trade record dict if closed, None if no position
        """
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # Calculate proceeds (after transaction cost)
        gross_proceeds = position.quantity * price
        transaction_cost = gross_proceeds * self.transaction_cost
        net_proceeds = gross_proceeds - transaction_cost
        
        # Calculate P&L
        pnl = net_proceeds - position.position_value
        pnl_pct = pnl / position.position_value
        
        # Update cash
        self.cash += net_proceeds
        
        # Create trade record
        trade = {
            'Symbol': symbol,
            'Entry_Date': position.entry_date,
            'Exit_Date': date,
            'Entry_Price': position.entry_price,
            'Exit_Price': price,
            'Quantity': position.quantity,
            'Position_Value': position.position_value,
            'Exit_Value': net_proceeds,
            'PnL': pnl,
            'PnL_Pct': pnl_pct,
            'Duration_Days': (date - position.entry_date).days,
            'Exit_Reason': reason
        }
        
        self.trade_history.append(trade)
        
        # Remove position
        del self.positions[symbol]
        
        return trade
    
    def check_exit_conditions(
        self, 
        date: datetime, 
        current_prices: Dict[str, float]
    ) -> List[Dict]:
        """
        Check if any positions should be exited due to stop-loss or take-profit.
        
        Args:
            date: Current date
            current_prices: Dict of {symbol: current_price}
            
        Returns:
            List of closed trade records
        """
        closed_trades = []
        symbols_to_close = []
        
        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            should_exit, reason = position.should_exit(current_price)
            
            if should_exit:
                symbols_to_close.append((symbol, reason))
        
        # Close positions
        for symbol, reason in symbols_to_close:
            trade = self.close_position(symbol, date, current_prices[symbol], reason)
            if trade:
                closed_trades.append(trade)
        
        return closed_trades
    
    def record_portfolio_value(
        self, 
        date: datetime, 
        current_prices: Dict[str, float]
    ):
        """Record portfolio value for this date."""
        portfolio_value = self.get_portfolio_value(current_prices)
        
        self.portfolio_values.append({
            'Date': date,
            'Portfolio_Value': portfolio_value,
            'Cash': self.cash,
            'Positions_Value': portfolio_value - self.cash,
            'Num_Positions': len(self.positions)
        })
    
    def get_trade_history_df(self) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        if not self.trade_history:
            return pd.DataFrame()
        return pd.DataFrame(self.trade_history)
    
    def get_portfolio_history_df(self) -> pd.DataFrame:
        """Get portfolio value history as DataFrame."""
        if not self.portfolio_values:
            return pd.DataFrame()
        return pd.DataFrame(self.portfolio_values)


if __name__ == "__main__":
    # Test portfolio
    portfolio = Portfolio(initial_capital=1000000)
    
    # Test opening position
    pos = portfolio.open_position('RELIANCE', pd.Timestamp('2023-01-01'), 2500)
    print(f"Opened position: {pos}")
    print(f"Cash remaining: ₹{portfolio.cash:,.2f}")
    
    # Test portfolio value
    current_prices = {'RELIANCE': 2600}
    pv = portfolio.get_portfolio_value(current_prices)
    print(f"Portfolio value: ₹{pv:,.2f}")
    
    # Test closing position
    trade = portfolio.close_position('RELIANCE', pd.Timestamp('2023-01-10'), 2650)
    print(f"\nClosed trade: {trade}")
    print(f"Cash after close: ₹{portfolio.cash:,.2f}")
