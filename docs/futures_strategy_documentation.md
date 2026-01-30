# Futures Trading Strategy Documentation
## Smart Money Concepts (SMC) for NIFTY Futures

### Strategy Overview

This futures trading strategy implements **Smart Money Concepts (SMC)** to identify high-probability trade setups in NIFTY Futures. The strategy focuses on institutional trading patterns, key price levels, and market structure to generate trading signals.

**Core Philosophy**: Follow institutional "smart money" footprints by trading from premium supply zones and discount demand zones, using break of structure (BoS) as confirmation.

---

## Strategy Components

### 1. Execution POIs (Points of Interest)

The strategy identifies key price levels where institutional traders are likely to place orders:

#### **PDH/PDL (Previous Day High/Low)**
- **Previous Day High (PDH)**: Resistance level from previous trading day
- **Previous Day Low (PDL)**: Support level from previous trading day
- **Usage**: Primary execution zones for reversal trades
- **Logic**: Institutional traders often defend these levels aggressively

```python
# Daily levels calculation
PDH = daily.loc[day, "PDH"]
PDL = daily.loc[day, "PDL"]
```

#### **Equal Highs/Lows (1H & 4H)**
- **1-Hour Equal Highs/Lows**: Multiple touches at same price level within 1H timeframe
- **4-Hour High/Low**: Significant swing highs/lows on 4H chart
- **Tolerance**: 0.1% for equal high/low detection
- **Usage**: Liquidity pools where stop losses accumulate

#### **Fair Value Gaps (FVG)**
- **Definition**: Price gaps where orderflow imbalance occurred
- **Identification**: Gap between candle 1 high and candle 3 low (or vice versa)
- **Usage**: Price tends to return to fill these gaps, providing entry opportunities
- **Timeframe**: 1-Hour FVGs tracked

---

### 2. Entry Confirmation Models

The strategy requires confirmation before entering trades:

#### **Break of Structure (BoS)** ⭐ Mandatory
- **Bullish BoS**: Price breaks above recent swing highs
- **Bearish BoS**: Price breaks below recent swing lows
- **Lookback Period**: 5 candles
- **Purpose**: Confirms trend direction and momentum shift

```python
def broke_structure_recently(df, ts, lookback=5):
    recent = df.iloc[idx - lookback:idx]
    return (
        df.iloc[idx].high > recent.high.max() or
        df.iloc[idx].low < recent.low.min()
    )
```

#### **iFVG + CISD (Optional Enhancement)**
- **Internal Fair Value Gap (iFVG)**: FVG within a larger price move
- **CISD (Change in State of Delivery)**: Candle pattern showing momentum shift
- **Entry Model Tag**: Trades tagged as "iFVG+CISD" or "BoS" for analysis

---

### 3. Trade Direction Logic

```python
def determine_trade_direction(row, state):
    if state["bias"] == "BULLISH":
        return "LONG"
    if state["bias"] == "BEARISH":
        return "SHORT"
    # Neutral: follow candle direction
    return "LONG" if row.close > row.open else "SHORT"
```

**Bias States**:
- **BULLISH**: Favor long trades from discount zones
- **BEARISH**: Favor short trades from premium zones  
- **NEUTRAL**: Follow immediate price action (default)

---

### 4. Risk Management

#### **Stop Loss Placement**
```python
def get_stop_price(row, direction, df, ts):
    lookback = 6  # Recent 6 candles
    recent = df.iloc[max(0, idx - lookback):idx]
    
    if direction == "LONG":
        return recent.low.min()  # Below recent lows
    else:
        return recent.high.max()  # Above recent highs
```

**Stop Loss Logic**:
- **LONG**: Below recent swing low (6 candles)
- **SHORT**: Above recent swing high (6 candles)
- **Minimum Distance**: 10 points (configurable)

#### **Target Setting**
```python
def get_target_price(row, direction, state):
    if direction == "LONG":
        return state["pdh"]  # Target PDH for longs
    else:
        return state["pdl"]  # Target PDL for shorts
```

**Target Logic**:
- **LONG trades**: Target Previous Day High (PDH)
- **SHORT trades**: Target Previous Day Low (PDL)
- **Rationale**: Day's range provides natural profit target

#### **Risk-Reward Requirements**
- **Minimum R:R**: 1.1:1 (configurable, default)
- **Calculation**: `RR = (Target - Entry) / (Entry - Stop)`
- **Filter**: Trades below minimum R:R are rejected

#### **Position Sizing**
```python
risk_amount = account_balance * risk_percent
qty = risk_amount / stop_distance
```

**Dynamic Risk**:
- **Biased Market** (Bullish/Bearish): 2% risk per trade
- **Neutral Market**: 1% risk per trade
- **Purpose**: Increase size when conviction is higher

---

### 5. Trade Management Rules

#### **Daily Loss Limit**
- **Max Losses Per Day**: 3 (configurable)
- **Action**: Stop trading for the day after 3 losing trades
- **Purpose**: Prevent emotional revenge trading

#### **Time-Based Exit**
- **Max Hold Time**: 24 hours
- **Action**: Close position at market after 24 hours
- **Purpose**: Avoid overnight risk and stale positions

#### **Execution Session**
```python
def in_execution_session(ts):
    t = ts.time()
    return (
        (t >= time(9, 15) and t <= time(12, 0)) or
        (t >= time(13, 0) and t <= time(15, 30))
    )
```

**Trading Hours**:
- **Morning Session**: 9:15 AM - 12:00 PM
- **Afternoon Session**: 1:00 PM - 3:30 PM
- No trading during lunch break (12:00 PM - 1:00 PM)

---

## Trade Execution Flow

### Entry Checklist
```
1. ✓ Is it within execution hours?
2. ✓ Have we hit max daily losses?
3. ✓ Is price touching a POI? (PDH/PDL/FVG/Equal H/L)
4. ✓ Is there a Break of Structure?
5. ✓ Is stop distance >= minimum points?
6. ✓ Is R:R >= minimum ratio?
7. ✓ Execute trade
```

### Exit Checklist
```
1. Check if stop loss hit → Exit at stop
2. Check if target hit → Exit at target
3. Check if 24 hours elapsed → Exit at market
4. Otherwise → Hold position
```

---

## Strategy Parameters (Configurable)

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `MIN_RR` | 1.1 | 1.0 - 3.0 | Minimum risk-reward ratio |
| `MAX_DAILY_LOSSES` | 3 | 1 - 5 | Max losing trades per day |
| `MIN_STOP_POINTS` | 10 | 5 - 30 | Minimum stop distance (points) |
| `risk_percent_bullish` | 2% | 0.5% - 5% | Risk per trade when biased |
| `risk_percent_neutral` | 1% | 0.5% - 3% | Risk per trade when neutral |
| `initial_capital` | ₹10,00,000 | ₹1L - ₹1Cr | Starting capital |

---

## Strategy Strengths

✅ **Institutional Alignment**: Trades with smart money, not against it  
✅ **Clear Structure**: Objective rules for entry and exit  
✅ **Risk-Defined**: Every trade has predefined stop and target  
✅ **Adaptive Position Sizing**: Larger positions when confident  
✅ **Loss Protection**: Daily loss limit prevents blowups  

---

## Strategy Limitations

⚠️ **Range-Bound Markets**: Less effective in tight consolidation  
⚠️ **Gap Risk**: 24-hour holds expose to overnight gaps  
⚠️ **Fixed Targets**: PDH/PDL may be too far in trending markets  
⚠️ **No Multi-Timeframe**: Currently single timeframe analysis  

---

## Performance Metrics

When backtesting, the strategy tracks:

- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of winning trades
- **Net P&L**: Total profit/loss in ₹
- **Average R:R**: Mean risk-reward ratio achieved
- **Final Equity**: Ending account balance

**Execution POI Breakdown**:
- PDH, PDL, 1H_FVG, 4H_LEVEL, OTHER

**Entry Model Distribution**:
- iFVG+CISD vs BoS

---

## Example Trade

**Setup**:
- Price touches PDL (₹21,450) at 10:30 AM
- Recent Break of Structure to upside (5-candle high broken)
- Bias: NEUTRAL

**Trade Details**:
- **Direction**: LONG
- **Entry**: ₹21,455 (market price)
- **Stop**: ₹21,420 (recent 6-candle low)
- **Target**: ₹21,680 (PDH)
- **Stop Distance**: 35 points
- **R:R**: (21,680 - 21,455) / 35 = 6.43
- **Risk**: 1% (neutral bias) = ₹10,000
- **Quantity**: ₹10,000 / 35 = 285 lots

**Outcome**:
- Target hit at 2:15 PM
- **P&L**: 285 × (21,680 - 21,455) = **₹64,125** ✅

---

## Code Reference

**Strategy Files**:
- [`futures/strategy.py`](file:///c:/Users/asus/OneDrive/Desktop/hacka/futures/strategy.py) - Main strategy logic
- [`futures/helpers.py`](file:///c:/Users/asus/OneDrive/Desktop/hacka/futures/helpers.py) - POI detection functions
- [`futures/backtest.py`](file:///c:/Users/asus/OneDrive/Desktop/hacka/futures/backtest.py) - Backtesting engine
- [`backtesting/futures_engine.py`](file:///c:/Users/asus/OneDrive/Desktop/hacka/backtesting/futures_engine.py) - UI integration wrapper

---

## Further Reading

**Smart Money Concepts**:
- Order Blocks and Fair Value Gaps
- Liquidity Sweeps and Stop Hunts
- Break of Structure vs Change of Character
- Premium vs Discount Pricing

**Recommended Resources**:
- ICT (Inner Circle Trader) methodology
- Market structure analysis
- Institutional order flow

---

*Last Updated: 2026-01-31*  
*Version: 1.0*
