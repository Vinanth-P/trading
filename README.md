# Algorithmic Trading System 📈

A comprehensive algorithmic trading system for backtesting momentum-based trading strategies on Indian equity markets, featuring a professional Streamlit UI dashboard.

## 🎯 Overview

This project implements a multi-indicator momentum trading strategy with:
- **Technical Indicators**: Moving Averages, RSI, MACD, Bollinger Bands
- **Risk Management**: Stop-loss, take-profit, position sizing
- **Comprehensive Backtesting**: Portfolio simulation with transaction costs
- **Professional UI**: Interactive Streamlit dashboard with real-time visualizations

## 📁 Project Structure

```
hacka/
├── data/
│   ├── fetcher.py          # Data fetching from API/sample generation
│   └── preprocessor.py     # Data cleaning and validation
├── strategy/
│   ├── indicators.py       # Technical indicator calculations
│   └── signals.py          # Buy/sell signal generation
├── backtesting/
│   ├── portfolio.py        # Position and portfolio management
│   ├── engine.py           # Backtesting simulation engine
│   └── metrics.py          # Performance metrics calculation
├── ui/
│   └── streamlit_app.py    # Streamlit dashboard
├── docs/
│   └── strategy_documentation.pdf  # (To be generated)
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Running the Application

1. **Launch the Streamlit dashboard:**
```bash
streamlit run ui/streamlit_app.py
```

2. **Configure your backtest:**
   - Select stocks from the sidebar (e.g., RELIANCE, TCS, INFY)
   - Choose date range (e.g., 2022-2024)
   - Adjust strategy parameters (optional)
   - Set risk management rules
   - Click "Run Backtest"

3. **Analyze results:**
   - View price charts with buy/sell signals
   - Track portfolio performance over time
   - Review performance metrics and risk indicators
   - Examine detailed trade log

## 📊 Trading Strategy

### Strategy: Multi-Indicator Momentum

**Entry Conditions (BUY):**
- Short MA crosses above Long MA (Golden Cross)
- RSI between 30-70 (neutral zone)
- MACD line crosses above signal line
- Price near lower Bollinger Band
- No large price gaps

**Exit Conditions (SELL):**
- Short MA crosses below Long MA (Death Cross)
- RSI > 70 (overbought)
- MACD bearish crossover
- Price at upper Bollinger Band
- Stop-loss triggered (default: 5%)
- Take-profit triggered (default: 10%)

### Risk Management

- **Position Size**: 20% of portfolio per trade (configurable)
- **Max Positions**: 3 concurrent positions (configurable)
- **Stop Loss**: 5% below entry (configurable)
- **Take Profit**: 10% above entry (configurable)
- **Transaction Cost**: 0.1% per trade

## 📈 Features

### Data Components
- **Equity data fetching** from Hackathon API (with mock data fallback)
- **Excel file upload** - Upload your own custom trading data
- Data preprocessing and validation
- Outlier removal and missing value handling
- Sample Excel template generator

### Strategy Components
- Technical indicators: MA, RSI, MACD, Bollinger Bands, ATR
- Multi-condition signal generation
- Signal strength calculation

### Backtesting Engine
- Realistic portfolio simulation
- Position tracking with stop-loss/take-profit
- Transaction cost modeling
- Trade history recording

### Performance Metrics
- **Returns**: Total return, annualized return
- **Risk**: Sharpe ratio, volatility, max drawdown
- **Trade Stats**: Win rate, profit factor, average trade duration
- **Advanced**: Calmar ratio, drawdown duration

### Streamlit UI
- **Interactive Charts**: Candlestick with indicators overlay
- **Portfolio Tracking**: Value over time, drawdown analysis
- **Trade Analysis**: P&L distribution, exit reasons
- **Risk Dashboard**: Comprehensive metrics display
- **Trade Log**: Downloadable CSV export

## 🎨 UI Features

- **Dark Theme**: Professional financial dashboard aesthetic
- **Real-time Charts**: Interactive Plotly visualizations
- **Responsive Design**: Works on desktop and tablets
- **Parameter Controls**: Adjust strategy settings on the fly
- **Performance Overview**: Key metrics at a glance

## 📋 Requirements

- Python 3.8+
- streamlit >= 1.30.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- plotly >= 5.18.0
- requests >= 2.31.0
- pandas-ta >= 0.3.14b

(See `requirements.txt` for full list)

## 🧪 Testing

Run individual components:

```bash
# Test data fetcher
python data/fetcher.py

# Test indicators
python strategy/indicators.py

# Test signal generation
python strategy/signals.py

# Test backtest engine
python backtesting/engine.py
```

## 📄 Documentation

Comprehensive strategy documentation (PDF) will include:
- Strategy overview and rationale
- Mathematical formulas for indicators
- Entry/exit logic with examples
- Backtesting methodology
- Risk management framework
- Performance analysis
- Assumptions and limitations

## ⚙️ Configuration

All strategy parameters are configurable via the Streamlit sidebar:

- **Technical Indicators**: MA periods, RSI thresholds, MACD parameters
- **Risk Management**: Position size, stop-loss, take-profit
- **Portfolio**: Initial capital, max positions

## 🎯 Use Cases

1. **Strategy Development**: Test and refine trading strategies
2. **Parameter Optimization**: Find optimal indicator settings
3. **Risk Assessment**: Evaluate drawdown and volatility
4. **Performance Analysis**: Compare strategies and time periods
5. **Education**: Learn about technical analysis and backtesting

## 📊 Sample Results

A typical backtest with default parameters might show:
- Total Return: 15-25% (depends on market conditions)
- Sharpe Ratio: 1.5-2.5
- Win Rate: 55-65%
- Max Drawdown: 8-15%

*Note: Past performance does not guarantee future results*

## 🚨 Disclaimer

This is a research and educational tool. Do NOT use this for actual trading without:
1. Thorough testing and validation
2. Understanding of market risks
3. Consultation with financial advisors
4. Proper risk management

**Trading involves substantial risk of loss.**

## 📝 License

This project is for educational and research purposes only.

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements.

## 📧 Contact

For questions or feedback, please open an issue in the repository.

---

**Built with ❤️ for algorithmic trading enthusiasts**
