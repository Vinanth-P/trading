import numpy as np

# ==============================
# EXECUTION POIs
# ==============================

def touched_pdh(row, state):
    return row.high >= state["pdh"]

def touched_pdl(row, state):
    return row.low <= state["pdl"]

def touched_equal_1h_high_low(row, state, tol=0.001):
    for h in state.get("h1_highs", []):
        if abs(row.high - h) / h < tol:
            return True
    for l in state.get("h1_lows", []):
        if abs(row.low - l) / l < tol:
            return True
    return False

def touched_4h_high_low(row, state):
    for h in state.get("h4_highs", []):
        if row.high >= h:
            return True
    for l in state.get("h4_lows", []):
        if row.low <= l:
            return True
    return False

def touched_1h_fvg(row, state):
    for low, high in state.get("h1_fvgs", []):
        if row.low <= high and row.high >= low:
            return True
    return False

# ==============================
# ENTRY CONFIRMATION
# ==============================

def broke_structure_recently(df, ts, lookback=5):
    idx = df.index.get_loc(ts)
    if idx < lookback:
        return False
    recent = df.iloc[idx - lookback:idx]
    return (
        df.iloc[idx].high > recent.high.max() or
        df.iloc[idx].low < recent.low.min()
    )

def has_ifvg_cisd(df, ts):
    idx = df.index.get_loc(ts)
    if idx < 3:
        return False

    c1, c2, c3 = df.iloc[idx-2], df.iloc[idx-1], df.iloc[idx]
    bullish = c2.low < c1.low and c3.close > c2.high
    bearish = c2.high > c1.high and c3.close < c2.low
    return bullish or bearish

# ==============================
# TRADE CONSTRUCTION
# ==============================

def determine_trade_direction(row, state):
    if state["bias"] == "BULLISH":
        return "LONG"
    if state["bias"] == "BEARISH":
        return "SHORT"
    return "LONG" if row.close > row.open else "SHORT"

def get_entry_price(row, direction):
    return row.close

# 🔧 SHORTER STRUCTURAL STOP (more trades)
def get_stop_price(row, direction, df, ts):
    idx = df.index.get_loc(ts)
    lookback = 6  # ↓ was 10

    recent = df.iloc[max(0, idx - lookback):idx]
    if recent.empty:
        return None

    return recent.low.min() if direction == "LONG" else recent.high.max()

def get_target_price(row, direction, state):
    return state["pdh"] if direction == "LONG" else state["pdl"]

# ==============================
# TAGGING
# ==============================

def identify_execution_poi(row, state):
    if touched_pdh(row, state): return "PDH"
    if touched_pdl(row, state): return "PDL"
    if touched_1h_fvg(row, state): return "1H_FVG"
    if touched_4h_high_low(row, state): return "4H_LEVEL"
    return "OTHER"

def identify_entry_model(df, ts):
    return "iFVG+CISD" if has_ifvg_cisd(df, ts) else "BoS"
