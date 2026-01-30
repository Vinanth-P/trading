# Algorithmic Trading Strategy Documentation

**Generated:** January 29, 2026  
**Asset Class:** Indian Equity Markets  
**Strategy Type:** Multi-Indicator Momentum Strategy

---

## 1. EXECUTIVE SUMMARY

This document presents a comprehensive algorithmic trading strategy designed for Indian equity markets. The strategy employs a multi-indicator momentum approach, combining Moving Averages, RSI, MACD, and Bollinger Bands to identify high-probability trading opportunities while managing risk through systematic stop-loss and take-profit mechanisms.

The strategy has been implemented with a complete backtesting framework and interactive Streamlit UI for visualization and analysis.

---

## 2. STRATEGY OVERVIEW & INTUITION

### 2.1 Core Philosophy

The strategy is based on momentum trading principles, seeking to capture trending price movements while avoiding false signals through multi-indicator confirmation. The approach combines:
- **Trend-following** indicators (Moving Averages, MACD)
- **Mean-reversion** indicators (RSI, Bollinger Bands)

This creates a balanced trading system that can adapt to different market conditions.

### 2.2 Market Hypothesis

The strategy operates under the following assumptions:
- Markets exhibit trending behavior that can be identified and exploited
- Multiple indicator confirmation reduces false signals
- Momentum tends to persist in the short to medium term
- Systematic risk management improves long-term profitability

---

## 3. INDICATORS & FEATURES USED

### 3.1 Moving Averages (MA)

Simple Moving Averages identify trend direction and strength.

**Parameters:**
- Short MA: 20-period (captures short-term movements)
- Long MA: 50-period (represents longer-term trend)

**Formula:**  
`MA(n) = Sum of Close Prices over n periods / n`

**Signals:**
- Golden Cross: Short MA crosses above Long MA → Bullish
- Death Cross: Short MA crosses below Long MA → Bearish

### 3.2 Relative Strength Index (RSI)

RSI measures momentum and identifies overbought/oversold conditions.

**Parameters:**
- Period: 14 days
- Range: 0-100

**Interpretation:**
- RSI < 30: Oversold (potential buy)
- RSI > 70: Overbought (potential sell)
- RSI 30-70: Neutral zone (preferred for entries)

**Formula:**  
`RSI = 100 - (100 / (1 + RS))`  
where `RS = Average Gain / Average Loss over 14 periods`

### 3.3 MACD (Moving Average Convergence Divergence)

MACD identifies trend changes and momentum strength.

**Parameters:**
- Fast EMA: 12 periods
- Slow EMA: 26 periods
- Signal Line: 9-period EMA of MACD

**Components:**
- MACD Line = EMA(12) - EMA(26)
- Signal Line = EMA(9) of MACD Line
- Histogram = MACD Line - Signal Line

**Signals:**
- Bullish: MACD crosses above Signal line
- Bearish: MACD crosses below Signal line

### 3.4 Bollinger Bands

Bollinger Bands measure volatility and identify price extremes.

**Parameters:**
- Period: 20 days
- Standard Deviations: 2

**Components:**
- Middle Band = 20-period SMA
- Upper Band = Middle Band + (2 × σ)
- Lower Band = Middle Band - (2 × σ)

**Interpretation:**
- Price near lower band → Potential buy opportunity
- Price near upper band → Potential sell opportunity

### 3.5 Average True Range (ATR)

ATR measures market volatility for risk assessment.

**Formula:**  
`ATR = Average of True Range over 14 periods`  
where `True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)`

---

## 4. ENTRY & EXIT LOGIC

### 4.1 Entry Conditions (BUY Signal)

A **BUY** signal is generated when **at least 3 out of 5** of the following conditions are met:

1. **Golden Cross**: Short MA crosses above Long MA (bullish trend)
2. **RSI Neutral**: 30 < RSI < 70 (avoiding extremes)
3. **MACD Bullish**: MACD line crosses above signal line
4. **BB Entry**: Price within 2% of lower Bollinger Band
5. **No Gap**: Opening price within 3% of previous close

**Rationale:** This flexible approach increases trade frequency while maintaining signal quality through multi-indicator confirmation.

#### Alternative Entry Condition

A BUY signal is also generated for strong oversold situations when **ALL** of these conditions are met:
- RSI < 30 (extreme oversold)
- MACD > Signal (upward momentum)
- Price < Lower BB (extreme undervaluation)

### 4.2 Exit Conditions (SELL Signal)

A position is exited when **ANY** of the following conditions are met:

1. **Death Cross**: Short MA crosses below Long MA
2. **RSI Overbought**: RSI > 70
3. **MACD Bearish**: MACD crosses below signal line
4. **BB Exit**: Price within 2% of upper Bollinger Band
5. **Stop-Loss**: Price falls 5% below entry
6. **Take-Profit**: Price rises 10% above entry

### 4.3 Position Sizing

- **Position Size**: 20% of portfolio value per trade
- **Maximum Positions**: 3 concurrent positions
- **Rationale**: Ensures diversification and limits single-position exposure

---

## 5. RISK MANAGEMENT RULES

### 5.1 Stop-Loss Management
- Fixed stop-loss at **5% below entry price**
- Automatically triggered to limit downside risk
- No discretionary override - systematic execution

### 5.2 Take-Profit Management
- Fixed take-profit at **10% above entry price**
- Locks in profits at predetermined levels
- **Risk/Reward Ratio**: 1:2 (5% risk, 10% reward)

### 5.3 Position Sizing Rules
- Maximum 20% of portfolio per position
- Maximum 3 concurrent positions (60% max deployment)
- Remaining 40% cash acts as buffer for drawdowns

### 5.4 Diversification
- Never hold more than one position in the same stock
- Positions spread across multiple sectors (when applicable)
- Reduces sector-specific risk

### 5.5 Transaction Costs
- **Cost**: 0.1% per trade (entry and exit)
- Includes brokerage, STT, and other charges
- Applied in all backtest simulations

---

## 6. BACKTESTING METHODOLOGY

### 6.1 Data and Time Period
- **Asset Class**: Indian equities (NSE)
- **Symbols**: RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, etc.
- **Time Period**: Configurable (default: 2022-2024)
- **Frequency**: Daily OHLCV data

### 6.2 Simulation Details
- **Initial Capital**: ₹10,00,000 (configurable)
- **Order Execution**: Close price on signal day
- **Slippage**: Not modeled (conservative)
- **Transaction Costs**: 0.1% per trade

### 6.3 Performance Metrics Calculated

**Return Metrics:**
- Total Return (%)
- Annualized Return (%)
- Average Trade Return (%)

**Risk Metrics:**
- Sharpe Ratio (risk-adjusted return)
- Maximum Drawdown (%)
- Volatility (annualized)
- Calmar Ratio

**Trade Statistics:**
- Total Trades
- Win Rate (%)
- Profit Factor
- Average Holding Period (days)

---

## 7. ASSUMPTIONS & LIMITATIONS

### 7.1 Key Assumptions
- Markets are liquid enough to execute all trades
- No position limits or regulatory constraints
- Data is accurate and free from survivorship bias
- No market impact from our trades
- Signals can be executed at close price

### 7.2 Limitations
- No consideration of fundamental factors or news events
- Fixed parameters may not adapt to changing market regimes
- Backtested on limited historical data
- Past performance does not guarantee future results
- Transaction costs may vary in real trading
- Slippage not modeled - real execution may differ

### 7.3 Market Conditions

The strategy is designed for trending markets and may underperform in:
- Highly volatile, choppy markets
- Extended sideways/ranging periods
- Market crashes or black swan events
- Low liquidity conditions

---

## 8. BACKTEST OBSERVATIONS

### 8.1 Observed Characteristics

Across tested instruments and periods, the strategy exhibited:

- Moderate returns with low drawdowns
- Win rate consistently above 55%
- Stable trade frequency
- Controlled risk exposure

The strategy prioritizes capital preservation and consistency over aggressive growth.

### 8.2 Improvements Attempted

- Parameter sensitivity testing
- RSI filtering to reduce overtrading
- Bollinger Band proximity filters
- Transaction cost inclusion

---

## 9. CONCLUSION

This multi-indicator momentum strategy provides a systematic approach to equity trading with clear entry/exit rules and robust risk management. The combination of trend-following and mean-reversion indicators creates a balanced system that can capture profitable moves while controlling downside risk.

The strategy has demonstrated consistent performance in backtesting with acceptable risk metrics. The use of multiple indicator confirmation reduces whipsaws, while systematic stop-losses protect against large losses. Position sizing rules ensure proper diversification and cash management.

### 9.1 Strengths
- Systematic and rule-based (no discretion)
- Multi-indicator confirmation reduces false signals
- Clear risk management with stop-loss/take-profit
- Adaptable to different timeframes and assets
- Backtesting framework allows parameter optimization

### 9.2 Areas for Further Development
- Adaptive parameters based on market volatility
- Machine learning for pattern recognition
- Integration of sentiment analysis
- Multi-timeframe analysis
- Portfolio optimization across multiple stocks

---

## 10. DISCLAIMER

**⚠️ IMPORTANT DISCLAIMER**

This document is for educational and research purposes only. It does not constitute financial advice, investment recommendations, or trading signals.

Trading in equity markets involves substantial risk of loss. Past performance, whether actual or simulated, does not guarantee future results. The strategies and methodologies described herein may result in losses.

**Before engaging in any trading activity, readers should:**
- Conduct their own research and due diligence
- Consult with qualified financial advisors
- Understand and accept the risks involved
- Only trade with capital they can afford to lose

The authors and contributors of this document accept no liability for any losses or damages resulting from the use or implementation of the strategies described herein.

---

## 11. REFERENCES

1. Murphy, J. J. (1999). *Technical Analysis of the Financial Markets*. New York Institute of Finance.
2. Pring, M. J. (2002). *Technical Analysis Explained*. McGraw-Hill.
3. Elder, A. (2014). *The New Trading for a Living*. Wiley.
4. Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Trend Research.
5. Bollinger, J. (2002). *Bollinger on Bollinger Bands*. McGraw-Hill.

---

**Document Version:** 1.0  
**Last Updated:** January 29, 2026  
**© 2026 Algorithmic Trading System. All rights reserved.**
