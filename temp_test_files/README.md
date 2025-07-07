# Test Files Directory

This directory contains test scripts for development and debugging purposes.

## Available Test Scripts

### Account Management
- `quick_account_check.py` - Quick account status check (balance, holdings, profit/loss)
- `account_monitor.py` - Real-time account monitoring (periodic updates)
- `check_orders.py` - Order history and status check

### Trading Logic
- `test_trading_logic.py` - Complete trading logic test (scan → filter → signal → order)
- `test_sell_monitor.py` - Sell monitoring logic test

## Usage

```bash
# Check account status
python temp_test_files/quick_account_check.py

# Test trading logic
python temp_test_files/test_trading_logic.py

# Test sell monitoring
python temp_test_files/test_sell_monitor.py
```

## Note

These files are for development and testing purposes only. Actual trading is executed through `main.py`. 