"""
ICT Strategy Helper Functions
All referenced helpers for strategy.py execution logic.
"""

import pandas as pd
import numpy as np

# ==============================
# EXECUTION POI CHECKS
# ==============================

def touched_pdh(row, state):
    """Check if price touched Previous Day High"""
    try:
        pdh = state.get("pdh")
        if pdh is None:
            return False
        return row.high >= pdh
    except:
        return False


def touched_pdl(row, state):
    """Check if price touched Previous Day Low"""
    try:
        pdl = state.get("pdl")
        if pdl is None:
            return False
        return row.low <= pdl
    except:
        return False


def touched_equal_1h_high_low(row, state):
    """Check if price touched equal 1H highs or lows (liquidity pools)"""
    try:
        h1_highs = state.get("h1_highs", [])
        h1_lows = state.get("h1_lows", [])
        tolerance = 0.001
        
        for level in h1_highs:
            if row.high >= level * (1 - tolerance):
                return True
        
        for level in h1_lows:
            if row.low <= level * (1 + tolerance):
                return True
        
        return False
    except:
        return False


def touched_4h_high_low(row, state):
    """Check if price touched 4H swing high or low"""
    try:
        h4_highs = state.get("h4_highs", [])
        h4_lows = state.get("h4_lows", [])
        tolerance = 0.002
        
        for level in h4_highs:
            if row.high >= level * (1 - tolerance):
                return True
        
        for level in h4_lows:
            if row.low <= level * (1 + tolerance):
                return True
        
        return False
    except:
        return False


def touched_1h_fvg(row, state):
    """Check if price entered a 1H Fair Value Gap"""
    try:
        h1_fvgs = state.get("h1_fvgs", [])
        
        for fvg_low, fvg_high in h1_fvgs:
            if row.low <= fvg_high and row.high >= fvg_low:
                return True
        
        return False
    except:
        return False


# ==============================
# ENTRY CONFIRMATION
# ==============================

def has_ifvg_cisd(df, ts):
    """Detect inverse FVG with Change in State of Delivery"""
    try:
        idx = df.index.get_loc(ts)
        if idx < 10:
            return False
        
        recent = df.iloc[idx-10:idx]
        
        for i in range(len(recent) - 2):
            c1, c2, c3 = recent.iloc[i], recent.iloc[i+1], recent.iloc[i+2]
            
            if c1.low > c3.high:
                if c3.close > c2.close > c1.close:
                    return True
            
            if c1.high < c3.low:
                if c3.close < c2.close < c1.close:
                    return True
        
        return False
    except:
        return False


def broke_structure_recently(df, ts, lookback=5):
    """Simple Break of Structure detection"""
    try:
        idx = df.index.get_loc(ts)
        if idx < lookback + 2:
            return False
        
        current = df.iloc[idx]
        recent = df.iloc[idx-lookback:idx]
        
        swing_high = recent.high.max()
        swing_low = recent.low.min()
        
        if current.high > swing_high:
            return True
        
        if current.low < swing_low:
            return True
        
        return False
    except:
        return False


# ==============================
# TRADE CONSTRUCTION
# ==============================

def determine_trade_direction(row, state):
    """Determine trade direction based on bias or structure"""
    try:
        bias = state.get("bias", "NEUTRAL")
        
        if bias == "BULLISH":
            return "LONG"
        elif bias == "BEARISH":
            return "SHORT"
        else:
            pdh = state.get("pdh", row.close)
            pdl = state.get("pdl", row.close)
            mid = (pdh + pdl) / 2
            
            if row.close > mid:
                return "LONG"
            else:
                return "SHORT"
    except:
        return "LONG"


def get_entry_price(row, direction):
    """Get entry price - use close price"""
    try:
        return row.close
    except:
        return None


def get_stop_price(row, direction, df, ts):
    """Get stop price based on recent swing high/low"""
    try:
        idx = df.index.get_loc(ts)
        lookback = min(10, idx)
        
        if lookback < 3:
            if direction == "LONG":
                return row.low
            else:
                return row.high
        
        recent = df.iloc[idx-lookback:idx]
        
        if direction == "LONG":
            return recent.low.min()
        else:
            return recent.high.max()
    except:
        return None


def get_target_price(row, direction, state):
    """Get target price - nearest opposing liquidity level"""
    try:
        pdh = state.get("pdh", row.close * 1.01)
        pdl = state.get("pdl", row.close * 0.99)
        h4_highs = state.get("h4_highs", [])
        h4_lows = state.get("h4_lows", [])
        
        if direction == "LONG":
            candidates = [pdh] + [h for h in h4_highs if h > row.close]
            if candidates:
                return min(candidates)
            return pdh
        else:
            candidates = [pdl] + [l for l in h4_lows if l < row.close]
            if candidates:
                return max(candidates)
            return pdl
    except:
        return None


# ==============================
# TAGGING / ANALYTICS
# ==============================

def identify_execution_poi(row, state):
    """Identify which POI triggered the execution"""
    if touched_pdh(row, state):
        return "PDH"
    if touched_pdl(row, state):
        return "PDL"
    if touched_equal_1h_high_low(row, state):
        return "1H_EQ"
    if touched_4h_high_low(row, state):
        return "4H_LEVEL"
    if touched_1h_fvg(row, state):
        return "1H_FVG"
    return "UNKNOWN"


def identify_entry_model(df, ts):
    """Identify which entry model triggered"""
    if has_ifvg_cisd(df, ts):
        return "iFVG+CISD"
    if broke_structure_recently(df, ts, lookback=5):
        return "BoS"
    return "UNKNOWN"
