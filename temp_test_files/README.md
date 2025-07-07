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

---

# 테스트 파일 디렉토리

이 디렉토리는 개발 및 디버깅을 위한 테스트 스크립트들을 포함합니다.

## 사용 가능한 테스트 스크립트

### 계좌 관리
- `quick_account_check.py` - 빠른 계좌 상태 확인 (잔고, 보유종목, 손익)
- `account_monitor.py` - 실시간 계좌 모니터링 (주기적 업데이트)
- `check_orders.py` - 주문 내역 및 상태 확인

### 거래 로직
- `test_trading_logic.py` - 전체 거래 로직 테스트 (스캔 → 필터링 → 신호 → 주문)
- `test_sell_monitor.py` - 매도 모니터링 로직 테스트

## 사용법

```bash
# 계좌 상태 확인
python temp_test_files/quick_account_check.py

# 거래 로직 테스트
python temp_test_files/test_trading_logic.py

# 매도 모니터링 테스트
python temp_test_files/test_sell_monitor.py
```

## 참고사항

이 파일들은 개발 및 테스트 목적으로만 사용하세요. 실제 거래는 `main.py`를 통해 실행됩니다. 