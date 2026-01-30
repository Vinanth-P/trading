import os
import pandas as pd

# =========================
# CONFIG
# =========================

DATA_DIR = "data"
RAW_INPUT_FILE = "futures_minute.csv"
CLEAN_OUTPUT_FILE = "futures_minute_clean.csv"


def normalize_csv():
    input_path = os.path.join(DATA_DIR, RAW_INPUT_FILE)
    output_path = os.path.join(DATA_DIR, CLEAN_OUTPUT_FILE)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"{input_path} not found")

    print(f"Reading raw data: {input_path}")

    df = pd.read_csv(input_path)
    df.columns = [c.lower().strip() for c in df.columns]

    # =========================
    # HANDLE DATETIME
    # =========================

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])

    elif "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"])

    elif "date" in df.columns and "time" in df.columns:
        df["datetime"] = pd.to_datetime(
            df["date"].astype(str) + " " + df["time"].astype(str)
        )

    else:
        raise ValueError(
            "CSV must contain either:\n"
            "- datetime\n"
            "- timestamp\n"
            "- date + time columns"
        )

    # =========================
    # VALIDATE PRICE COLUMNS
    # =========================

    rename_map = {
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
    }
    df.rename(columns=rename_map, inplace=True)

    required = {"open", "high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing required OHLC columns: {required}")

    # =========================
    # CLEAN DATA
    # =========================

    df = df[["datetime", "open", "high", "low", "close"]]
    df.sort_values("datetime", inplace=True)
    df.drop_duplicates("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)

    df.to_csv(output_path, index=False)

    print(f"✅ Clean data saved → {output_path}")
    print(f"Rows: {len(df)}")
    print(f"Range: {df.datetime.min()} → {df.datetime.max()}")


if __name__ == "__main__":
    normalize_csv()
