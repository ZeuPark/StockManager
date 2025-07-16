import pandas as pd
import numpy as np
from glob import glob
from utils.indicators import calc_vwap, calc_rsi

minute_files = glob('minute_data/*.csv')
results = []

for file in minute_files:
    df = pd.read_csv(file, parse_dates=['datetime'])
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['datetime', 'close', 'high', 'low', 'volume'])
    df = df.sort_values('datetime').reset_index(drop=True)
    if len(df) < 100:
        continue

    stock_code = file.split('/')[-1].replace('.csv','')

    # 지표 계산
    df['vwap'] = calc_vwap(df)
    df['rsi'] = calc_rsi(df['close'])
    df = df.dropna()

    # 매수 탐색 구간
    buy_window = df[(df['datetime'].dt.time >= pd.to_datetime('10:15').time()) &
                    (df['datetime'].dt.time <= pd.to_datetime('10:45').time())]
    if buy_window.empty:
        continue

    # 10~11시 고가, 종가, 거래량 등
    ten = df[(df['datetime'].dt.time >= pd.to_datetime('10:00').time()) &
             (df['datetime'].dt.time < pd.to_datetime('11:00').time())]
    high_10_11 = ten['high'].max()
    close_10_11 = ten['close'].iloc[-1]
    close_pos_10_11 = close_10_11 / high_10_11 if high_10_11 > 0 else np.nan

    # 10:10~10:30 매수강도 proxy
    buy_strength = df[(df['datetime'].dt.time >= pd.to_datetime('10:10').time()) &
                      (df['datetime'].dt.time <= pd.to_datetime('10:30').time())]['volume'].sum()

    # 진입 조건
    for idx, row in buy_window.iterrows():
        if (row['close'] > row['vwap'] and
            close_pos_10_11 >= 0.9 and
            buy_strength > 100 and
            row['rsi'] < 70):

            buy_time = row['datetime']
            buy_price = row['close']

            # ▼▼▼ 개선된 청산 및 수익/리스크 기록 ▼▼▼
            sell_price = np.nan
            sell_time = None
            sell_reason = ''
            max_price = buy_price
            min_price = buy_price

            sell_window = df[df.index > idx]
            for _, srow in sell_window.iterrows():
                price = srow['close']
                high = srow['high']
                low = srow['low']
                max_price = max(max_price, high)
                min_price = min(min_price, low)

                if price < srow['vwap'] * 0.997:
                    sell_price = price
                    sell_time = srow['datetime']
                    sell_reason = 'VWAP Break'
                    break
                elif srow['rsi'] >= 75:
                    sell_price = price
                    sell_time = srow['datetime']
                    sell_reason = 'RSI Overheat'
                    break
                elif (high - buy_price) / buy_price >= 0.03:
                    sell_price = high
                    sell_time = srow['datetime']
                    sell_reason = 'Target Profit'
                    break
                elif srow['datetime'].time() >= pd.to_datetime('15:00').time():
                    sell_price = price
                    sell_time = srow['datetime']
                    sell_reason = 'End of Day'
                    break

            if not np.isnan(sell_price):
                ret = (sell_price - buy_price) / buy_price
                max_profit = (max_price - buy_price) / buy_price
                drawdown = (min_price - buy_price) / buy_price

                results.append({
                    'stock': stock_code,
                    'buy_time': buy_time,
                    'buy_price': buy_price,
                    'sell_time': sell_time,
                    'sell_price': sell_price,
                    'return': ret,
                    'sell_reason': sell_reason,
                    'close_pos_10_11': close_pos_10_11,
                    'buy_strength': buy_strength,
                    'rsi_at_buy': row['rsi'],
                    'max_profit': max_profit,
                    'drawdown': drawdown,
                })
                break  # 1일 1매수
            # ▲▲▲ 개선된 청산 및 리스크 기록 ▲▲▲

# 결과 집계 및 저장
results_df = pd.DataFrame(results)
print(results_df.describe())
print("\n--- Sell Reason Distribution ---")
print(results_df['sell_reason'].value_counts(normalize=True))
results_df.to_csv('backtest_gradual_riser_combined.csv', index=False, encoding='utf-8-sig') 