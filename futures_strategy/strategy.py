from datetime import time
from .helpers import (
    touched_pdh, touched_pdl, touched_equal_1h_high_low,
    touched_4h_high_low, touched_1h_fvg,
    has_ifvg_cisd, broke_structure_recently,
    determine_trade_direction, get_entry_price, get_stop_price, get_target_price,
    identify_execution_poi, identify_entry_model
)

# ==============================
# CONFIG
# ==============================

MIN_RR = 1.25
MAX_DAILY_LOSSES = 3


# ==============================
# TIME FILTER
# ==============================

def in_execution_session(ts):
    """
    Allowed:
    - 9:15 to 12:00
    - 1:00 to 3:30
    """
    t = ts.time()
    return (
        (t >= time(9, 15) and t <= time(12, 0)) or
        (t >= time(13, 0) and t <= time(15, 30))
    )


# ==============================
# RISK MANAGEMENT
# ==============================

def get_risk_percent(state):
    """
    Risk scaling based on bias conviction.
    """
    if state["bias"] in ("BULLISH", "BEARISH"):
        return 0.02   # 2% risk with fixed daily bias
    return 0.01       # 1% risk when bias is neutral


# ==============================
# EXECUTION POI CHECK
# ==============================

def valid_execution_poi(row, state):
    """
    Execution is allowed if price interacts with ANY ONE of these.
    Execution-only logic (not bias, not targets).
    """
    return any([
        touched_pdh(row, state),
        touched_pdl(row, state),
        touched_equal_1h_high_low(row, state),
        touched_4h_high_low(row, state),
        touched_1h_fvg(row, state),
    ])


# ==============================
# ENTRY CONFIRMATION
# ==============================

def entry_confirmation(df, ts):
    """
    Momentum confirmation AFTER POI interaction.
    Displacement is IMPLIED here.
    """
    return any([
        has_ifvg_cisd(df, ts),
        broke_structure_recently(df, ts, lookback=5),
    ])


# ==============================
# MAIN EXECUTION LOGIC
# ==============================

def check_for_trade(row, df, ts, state, account_balance):
    """
    Core execution engine.
    Returns trade dict or None.
    """

    # ---- Time filter
    if not in_execution_session(ts):
        return None

    # ---- Daily loss limit
    if state["losses"] >= MAX_DAILY_LOSSES:
        return None

    # ---- Execution POI
    if not valid_execution_poi(row, state):
        return None

    # ---- Entry confirmation
    if not entry_confirmation(df, ts):
        return None

    # ---- Direction (contextual, not restrictive)
    direction = determine_trade_direction(row, state)

    # ---- Entry, Stop, Target
    entry = get_entry_price(row, direction)
    stop = get_stop_price(row, direction, df, ts)
    target = get_target_price(row, direction, state)

    if entry is None or stop is None or target is None:
        return None

    # ---- Risk–Reward filter
    if abs(entry - stop) == 0:
        return None
    
    rr = abs(target - entry) / abs(entry - stop)
    if rr < MIN_RR:
        return None

    # ---- Position sizing (bias-based risk)
    risk_pct = get_risk_percent(state)
    risk_amount = account_balance * risk_pct
    qty = risk_amount / abs(entry - stop)

    if qty <= 0:
        return None

    # ---- Build trade
    trade = {
        "timestamp": ts,
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "target": target,
        "rr": round(rr, 2),
        "qty": qty,
        "risk_pct": risk_pct,
        "bias": state["bias"],
        "execution_poi": identify_execution_poi(row, state),
        "entry_model": identify_entry_model(df, ts),
    }

    return trade
