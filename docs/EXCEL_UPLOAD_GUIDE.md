# Manual Data Upload Guide

## Overview

You can now upload your own trading data using Excel files! This feature allows you to backtest strategies on custom data without relying on the API.

## How to Upload Data

### Step 1: Select Upload Option
1. Open the Streamlit app
2. In the sidebar, under **"Data Source"**, select **"Upload Excel"**
3. Click the **"Upload Data File"** button

### Step 2: Prepare Your Excel File

Your Excel file must contain the following columns (case-insensitive):

| Column | Description | Format | Example |
|--------|-------------|--------|---------|
| **Date** | Trading date | YYYY-MM-DD, DateTime, or Timestamp | 2023-01-15 |
| **Symbol** | Stock ticker | Text (uppercase preferred) | RELIANCE, TCS |
| **Open** | Opening price | Numeric (decimal) | 2450.50 |
| **High** | Highest price | Numeric (decimal) | 2475.00 |
| **Low** | Lowest price | Numeric (decimal) | 2440.25 |
| **Close** | Closing price | Numeric (decimal) | 2465.75 |
| **Volume** | Trading volume | Integer | 1500000 |

### Step 3: Download Sample Template

Click the **"📥 Download Sample Template"** button in the sidebar to get a pre-formatted Excel file with sample data.

### Step 4: Fill in Your Data

1. Open the downloaded template
2. Replace the sample data with your actual trading data
3. Ensure all required columns are present
4. Save the file

### Step 5: Upload and Run

1. Upload your Excel file
2. The app will automatically detect symbols in your data
3. Click **"🚀 Run Backtest"**

## Data Validation

The system automatically validates your data for:

✅ **Required Columns** - All 7 columns must be present  
✅ **Date Format** - Dates are converted to standard format  
✅ **Numeric Values** - OHLC and Volume must be numbers  
✅ **OHLC Relationships** - High >= max(Open, Close), Low <= min(Open, Close)  
✅ **Positive Values** - Prices and volume must be positive  

Invalid rows are automatically removed with a warning message.

## Excel Format Examples

### Single Stock Example
```
Date        Symbol    Open     High     Low      Close    Volume
2023-01-02  RELIANCE  2450.00  2475.00  2440.00  2465.00  1500000
2023-01-03  RELIANCE  2465.00  2480.00  2455.00  2470.00  1600000
2023-01-04  RELIANCE  2470.00  2490.00  2465.00  2485.00  1700000
```

### Multiple Stocks Example
```
Date        Symbol    Open     High     Low      Close    Volume
2023-01-02  RELIANCE  2450.00  2475.00  2440.00  2465.00  1500000
2023-01-02  TCS       3500.00  3520.00  3490.00  3510.00  800000
2023-01-03  RELIANCE  2465.00  2480.00  2455.00  2470.00  1600000
2023-01-03  TCS       3510.00  3530.00  3500.00  3525.00  850000
```

## Alternative Column Names

The system recognizes these alternative names:

- **Date**: `Date`, `DateTime`, `Timestamp`
- **Symbol**: `Symbol`, `Stock`, `Ticker`, `TradingSymbol`, `tradingsymbol`
- **Volume**: `Volume`, `Vol`
- **Time**: `time` column is optional and will be ignored if present

## Common Issues and Solutions

### Issue: "Missing required columns"
**Solution**: Ensure your Excel has all 7 required columns with correct spellings

### Issue: "Invalid date format"
**Solution**: Use YYYY-MM-DD format (e.g., 2023-01-15) or Excel date format

### Issue: "No valid data remaining"
**Solution**: Check for:
- Missing values (blanks)
- Invalid OHLC relationships (High < Low, etc.)
- Negative prices or volumes

### Issue: "Removed X rows with invalid OHLC relationships"
**Solution**: This is normal. The system removes bad data automatically.

## Tips for Best Results

1. **Use Business Days Only** - Exclude weekends and holidays
2. **Sort by Date** - Data will be auto-sorted, but pre-sorting helps
3. **Consistent Symbols** - Use the same ticker format throughout
4. **Clean Data** - Remove rows with missing or zero values
5. **Sufficient History** - Include at least 60 days of data for indicators

## Data Sources

You can get historical stock data from:
- NSE/BSE websites
- Yahoo Finance
- Trading platforms (Zerodha, Upstox, etc.)
- Financial data providers

## File Size Limits

- **Maximum file size**: 200 MB (Streamlit default)
- **Recommended**: Keep under 10 MB for fast processing
- **Typical usage**: 1 year of daily data = ~250-500 KB per stock

## Privacy & Security

⚠️ **Your data stays local**: Uploaded files are processed in memory and not stored on any server.

## Support

If you encounter issues:
1. Check the validation messages
2. Download and examine the sample template
3. Verify your data against the format requirements
4. Contact support with error messages

---

## Quick Start

1. Click "Upload Excel" in sidebar
2. Download sample template
3. Add your data to the template
4. Upload and  run backtest!

**Ready to upload?** Click the "Upload Excel" option in the sidebar to get started! 📊
