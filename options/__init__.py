# Options module for hackathon demo
# Converts equity signals to options trades with simplified pricing

"""
🎯 OPTIONS MODULE - HACKATHON VERSION

This module adds options trading support by REUSING equity signals:
- Equity BUY signal  → Buy a CALL option (bet price goes UP)
- Equity SELL signal → Buy a PUT option (bet price goes DOWN)

⚠️ SIMPLIFIED ASSUMPTIONS (for hackathon demo):
1. Option premium = 2% of stock price (no Black-Scholes)
2. Strike price = current stock price (ATM options)
3. No Greeks, no theta decay, no bid-ask spread
4. Exit when: +50% profit, -30% loss, or opposite signal

This is NOT production-ready. It demonstrates the CONCEPT of
converting directional equity signals into options trades.
"""

from options.option_contract import OptionContract, OptionType
from options.option_selector import OptionSelector
from options.option_strategy import OptionExitStrategy
from options.option_backtester import OptionsBacktester, run_options_backtest
