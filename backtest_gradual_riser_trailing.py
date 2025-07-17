import pandas as pd
import numpy as np
from glob import glob
from tqdm import tqdm
from utils.indicators import calc_vwap, calc_rsi

minute_files = glob('minute_data/*.csv')
results = []
total_files = len(minute_files)
processed_files = 0
condition_counts = {'new_high': 0, 'vol_spike': 0, 'vwap_ok': 0, 'rsi_ok': 0, 'all_conditions': 0}

print(f"Total files to process: {total_files}")

for file in tqdm(minute_files, desc="Processing files"):
    try:
        df = pd.read_csv(file, parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        df = df.dropna(subset=['datetime', 'close', 'high', 'low', 'volume'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        if len(df) < 100:
            continue

        stock_code = file.split('/')[-1].replace('.csv','')
        processed_files += 1

        # 지표 계산
        df['vwap'] = calc_vwap(df)
        df['rsi'] = calc_rsi(df['close'])
        df = df.dropna()

        # 5분 이동평균 거래량 계산
        df['vol_ma5'] = df['volume'].rolling(window=5, min_periods=1).mean()
        df['cummax_high'] = df['high'].cummax()

        # 9:30~11:00 구간에서 실시간 진입 조건 탐색 (시간 구간 확장)
        entry_window = df[(df['datetime'].dt.time >= pd.to_datetime('9:30').time()) &
                          (df['datetime'].dt.time <= pd.to_datetime('11:00').time())]
        if entry_window.empty:
            continue

        # 진입 조건별 카운트 (조건 완화)
        for idx, row in entry_window.iterrows():
            # 당일 고점 근처(99%) 조건으로 완화
            is_near_high = row['high'] >= df.loc[:idx, 'high'].max() * 0.99 if idx > 0 else False
            vol_spike = row['volume'] > 2 * row['vol_ma5']
            vwap_ok = row['close'] > row['vwap']
            rsi_ok = 60 <= row['rsi'] <= 70
            
            if is_near_high:
                condition_counts['new_high'] += 1
            if vol_spike:
                condition_counts['vol_spike'] += 1
            if vwap_ok:
                condition_counts['vwap_ok'] += 1
            if rsi_ok:
                condition_counts['rsi_ok'] += 1
            # 조건 조합 완화: 핵심2개(고점근처 또는 거래량급증) + 보조 2개(VWAP상회, RSI적정)
            if (is_near_high or vol_spike) and vwap_ok and rsi_ok:
                condition_counts['all_conditions'] += 1
                buy_time = row['datetime']
                buy_price = row['close']
                buy_idx = idx
                # 10~11 등
                ten = df[(df['datetime'].dt.time >= pd.to_datetime('10:00').time()) &
                         (df['datetime'].dt.time < pd.to_datetime('11:00').time())]
                high_10_11 = ten['high'].max()
                close_10_11 = ten['close'].iloc[-1]
                close_pos_10_11 = close_10_11 / high_10_11 if high_10_11 > 0 else np.nan
                # 10:10~10:30 매수강도 proxy
                buy_strength = df[(df['datetime'].dt.time >= pd.to_datetime('10:10').time()) &
                                  (df['datetime'].dt.time <= pd.to_datetime('10:30').time())]['volume'].sum()
                # ▼▼▼ 부분청산 + 트레일링스탑 + 복합 익절 ▼▼▼
                sell_price = np.nan
                sell_time = None
                sell_reason = ''
                max_price = buy_price
                min_price = buy_price
                trailing_active = False
                peak_price = buy_price
                position = 1.0  # 1=전량, 0.5=부분청산 후
                partial_sell = False
                partial_sell_price = np.nan
                partial_sell_time = None
                partial_sell_reason = ''
                sell_window = df[df.index > buy_idx]
                for _, srow in sell_window.iterrows():
                    price = srow['close']
                    high = srow['high']
                    low = srow['low']
                    max_price = max(max_price, high)
                    min_price = min(min_price, low)
                    ret_now = (price - buy_price) / buy_price
                    # VWAP 이탈 손절
                    if price < srow['vwap'] * 0.997:
                        sell_price = price
                        sell_time = srow['datetime']
                        sell_reason = 'VWAP Break'
                        position = 0.0
                        break
                    # Target Profit(3%) 익절 (close 기준)
                    elif (price - buy_price) / buy_price >= 0.03:
                        sell_price = price
                        sell_time = srow['datetime']
                        sell_reason = 'Target Profit'
                        position = 0.0
                        break
                    # 부분청산: 1.5% 도달 시 50% 청산
                    elif not partial_sell and (price - buy_price) / buy_price >= 0.015:
                        partial_sell = True
                        partial_sell_price = price
                        partial_sell_time = srow['datetime']
                        partial_sell_reason = 'Partial Profit 1.5%'
                        position = 0.5
                        # 나머지 50%는 계속 보유
                    # 복합 익절: RSI > 72 and return > 1%
                    if not trailing_active and srow['rsi'] > 72 and ret_now > 0.01:
                        trailing_active = True
                        peak_price = high
                        continue
                    # 트레일링 스탑: 최고가 대비 -1.5% 하락, 단 최소 수익률 2% 이상
                    if trailing_active:
                        if high > peak_price:
                            peak_price = high
                        if (peak_price - buy_price) / buy_price >= 0.02:
                            if price <= peak_price * 0.985:
                                sell_price = price
                                sell_time = srow['datetime']
                                sell_reason = 'Trailing Stop'
                                position = 0.0
                                break
                    # 15시 도달 시 청산
                    if srow['datetime'].time() >= pd.to_datetime('15:00').time():
                        sell_price = price
                        sell_time = srow['datetime']
                        sell_reason = 'End of Day'
                        position = 0.0
                        break
                # 결과 기록
                if not np.isnan(sell_price):
                    ret = (sell_price - buy_price) / buy_price * position
                    max_profit = (max_price - buy_price) / buy_price
                    drawdown = (min_price - buy_price) / buy_price
                    # 부분청산 수익 포함
                    if partial_sell:
                        ret = 0.5 * ((partial_sell_price - buy_price) / buy_price) + 0.5 * ((sell_price - buy_price) / buy_price)
                    results.append({
                        'stock': stock_code,
                        'buy_time': buy_time,
                        'buy_price': buy_price,
                        'sell_time': sell_time,
                        'sell_price': sell_price,
                        'return': ret,
                        'sell_reason': sell_reason,
                        'partial_sell': partial_sell,
                        'partial_sell_price': partial_sell_price,
                        'partial_sell_time': partial_sell_time,
                        'partial_sell_reason': partial_sell_reason,
                        'close_pos_10_11': close_pos_10_11,
                        'buy_strength': buy_strength,
                        'rsi_at_buy': row['rsi'],
                        'max_profit': max_profit,
                        'drawdown': drawdown,
                    })
                    break  # 1일 1매수
                # ▲▲▲ 부분청산 + 트레일링스탑 + 복합 익절 ▲▲▲
    except Exception as e:
        continue

# 결과 집계 및 저장
print(f"\n=== Processing Summary ===")
print(f"Total files: {total_files}")
print(f"Processed files: {processed_files}")
print(f"Condition counts:")
for condition, count in condition_counts.items():
    print(f"  {condition}: {count}")

if results:
    results_df = pd.DataFrame(results)
    print(f"\n=== Backtest Results ===")
    print(f"Total trades: {len(results)}")
    print(results_df.describe())
    print("\n--- Sell Reason Distribution ---")
    print(results_df['sell_reason'].value_counts(normalize=True))
    results_df.to_csv('backtest_gradual_riser_advanced.csv', index=False, encoding='utf-8-sig')
    print(f"\nResults saved to: backtest_gradual_riser_advanced.csv")
else:
    print("\nNo trades were executed under the current strategy conditions.")
    print("Consider relaxing the entry conditions or checking data quality.") 