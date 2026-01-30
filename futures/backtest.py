import os
import pandas as pd
from datetime import timedelta
from .strategy import check_for_trade

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "futures_minute_clean.csv")

INITIAL_EQUITY = 1_000_000
PRINT_TRADES = False


def run_backtest():
    df = pd.read_csv(DATA_FILE, parse_dates=["datetime"])
    df.set_index("datetime", inplace=True)
    df["date"] = df.index.date

    daily = df.groupby("date").agg(
        PDH=("high", "max"),
        PDL=("low", "min")
    )

    equity = INITIAL_EQUITY
    trades_log = []
    open_trade = None
    state = None

    for ts, row in df.iterrows():

        if open_trade:
            elapsed = ts - open_trade["entry_time"]
            exit_price = None

            if open_trade["direction"] == "LONG":
                if row.low <= open_trade["stop"]:
                    exit_price = open_trade["stop"]
                elif row.high >= open_trade["target"]:
                    exit_price = open_trade["target"]
            else:
                if row.high >= open_trade["stop"]:
                    exit_price = open_trade["stop"]
                elif row.low <= open_trade["target"]:
                    exit_price = open_trade["target"]

            if exit_price is None and elapsed >= timedelta(hours=24):
                exit_price = row.close

            if exit_price is not None:
                pnl = open_trade["qty"] * (
                    exit_price - open_trade["entry"]
                    if open_trade["direction"] == "LONG"
                    else open_trade["entry"] - exit_price
                )

                equity += pnl
                if pnl < 0:
                    state["losses"] += 1

                trades_log.append({
                    **open_trade,
                    "exit_time": ts,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "equity": equity,
                })

                open_trade = None
            continue

        day = ts.date()
        state = {
            "equity": equity,
            "losses": 0,
            "bias": "NEUTRAL",
            "pdh": daily.loc[day, "PDH"],
            "pdl": daily.loc[day, "PDL"],
            "h1_highs": [],
            "h1_lows": [],
            "h4_highs": [],
            "h4_lows": [],
            "h1_fvgs": [],
        }

        trade = check_for_trade(row, df, ts, state, equity)
        if trade:
            open_trade = trade

    results = pd.DataFrame(trades_log)
    results.to_csv("backtest_results.csv", index=False)

    print("\n========== BACKTEST SUMMARY ==========")
    print(f"Total Trades : {len(results)}")
    print(f"Net PnL      : {results.pnl.sum():.2f}")
    print(f"Win Rate     : {(results.pnl > 0).mean() * 100:.2f}%")
    print(f"Average RR   : {results.rr.mean():.2f}")
    print(f"Final Equity : {equity:.2f}")
    print("=====================================")


if __name__ == "__main__":
    run_backtest()
