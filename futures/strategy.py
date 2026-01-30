from datetime import time
from .helpers import *

MIN_RR = 1.1              # ↓ was 1.25
MAX_DAILY_LOSSES = 3
MIN_STOP_POINTS = 10      # ↓ was 20 (more trades)


def in_execution_session(ts):
    t = ts.time()
    return (
        (t >= time(9, 15) and t <= time(12, 0)) or
        (t >= time(13, 0) and t <= time(15, 30))
    )


def get_risk_percent(state):
    return 0.02 if state["bias"] in ("BULLISH", "BEARISH") else 0.01


def check_for_trade(row, df, ts, state, account_balance):

    if not in_execution_session(ts):
        return None

    if state["losses"] >= MAX_DAILY_LOSSES:
        return None

    # Execution POI (unchanged)
    if not any([
        touched_pdh(row, state),
        touched_pdl(row, state),
        touched_equal_1h_high_low(row, state),
        touched_4h_high_low(row, state),
        touched_1h_fvg(row, state),
    ]):
        return None

    # 🔧 ONLY BoS is mandatory now (more trades)
    if not broke_structure_recently(df, ts):
        return None

    direction = determine_trade_direction(row, state)

    entry = get_entry_price(row, direction)
    stop = get_stop_price(row, direction, df, ts)
    target = get_target_price(row, direction, state)

    if stop is None:
        return None

    stop_distance = abs(entry - stop)
    if stop_distance < MIN_STOP_POINTS:
        return None

    rr = abs(target - entry) / stop_distance
    if rr < MIN_RR:
        return None

    risk_amount = account_balance * get_risk_percent(state)
    qty = risk_amount / stop_distance

    return {
        "entry_time": ts,
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "target": target,
        "qty": qty,
        "rr": round(rr, 2),
        "bias": state["bias"],
        "execution_poi": identify_execution_poi(row, state),
        "entry_model": identify_entry_model(df, ts),
    }
