import pandas as pd
from datetime import datetime


def simulate_trade(minute_csv_path, entry_time, entry_price, profit_target=0.10, stop_loss=0.05):
    """
    분봉 데이터를 이용해 진입가 대비 +10% 익절, -5% 손절 중 먼저 도달한 시점에 청산.
    Args:
        minute_csv_path (str): 분봉 CSV 파일 경로
        entry_time (str or datetime): 진입 시각 (뉴스 신호 발생 시각)
        entry_price (float): 진입가 (진입 시점의 close)
        profit_target (float): 익절률 (default 0.10)
        stop_loss (float): 손절률 (default 0.05)
    Returns:
        dict: {'entry_time', 'entry_price', 'exit_time', 'exit_price', 'return', 'result'}
    """
    df = pd.read_csv(minute_csv_path, parse_dates=['datetime'])
    if isinstance(entry_time, str):
        entry_time = pd.to_datetime(entry_time)
    # 신호 발생 이후 데이터만 필터
    df = df[df['datetime'] > entry_time].sort_values('datetime')
    target_price = entry_price * (1 + profit_target)
    stop_price = entry_price * (1 - stop_loss)
    exit_time, exit_price, result = None, None, None
    for _, row in df.iterrows():
        high = row['high']
        low = row['low']
        if high >= target_price:
            exit_time = row['datetime']
            exit_price = target_price
            result = '익절'
            break
        if low <= stop_price:
            exit_time = row['datetime']
            exit_price = stop_price
            result = '손절'
            break
    if exit_time is None:
        # 끝까지 도달 못하면 마지막 close로 청산
        last_row = df.iloc[-1] if not df.empty else None
        if last_row is not None:
            exit_time = last_row['datetime']
            exit_price = last_row['close']
            result = '미청산'
        else:
            exit_time = entry_time
            exit_price = entry_price
            result = '데이터없음'
    ret = (exit_price - entry_price) / entry_price
    return {
        'entry_time': entry_time,
        'entry_price': entry_price,
        'exit_time': exit_time,
        'exit_price': exit_price,
        'return': ret,
        'result': result
    } 