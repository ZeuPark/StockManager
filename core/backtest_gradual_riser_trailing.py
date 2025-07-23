import pandas as pd
import numpy as np
from glob import glob
from tqdm import tqdm
import matplotlib.pyplot as plt
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.indicators import calc_vwap, calc_rsi

minute_files = glob('minute_data/*.csv')
results = []
total_files = len(minute_files)
processed_files = 0
condition_counts = {'new_high': 0, 'vol_spike': 0, 'vwap_ok': 0, 'rsi_ok': 0, 'all_conditions': 0}
tp_analysis = {
    'total_trades': 0,
    'tp_0.5_reached': 0,
    'tp_1.0_reached': 0,
    'tp_1.5_reached': 0,
    'tp_2.0_reached': 0,
    'tp_2.5_reached': 0,
    'max_profit_distribution': []
}

print(f"Total files to process: {total_files}")

for file in tqdm(minute_files, desc="Processing files"):
    try:
        df = pd.read_csv(file, parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        df = df.dropna(subset=['datetime', 'close', 'high', 'low', 'volume'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        if len(df) < 100:
            continue

        # 데이터 전처리 강화: 가격 필터
        if df['close'].mean() < 50 or df['close'].mean() > 500000:
            continue
            
        # 거래대금 하한 설정: 일평균 10억원 이상
        daily_volume = df['volume'].sum() * df['close'].mean()
        if daily_volume < 10000000000: # 10억원
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

        # 진입 조건별 카운트 (조건 강화 → 점진 상승 패턴으로 수정)
        for idx, row in entry_window.iterrows():
            lookback = min(30, idx)
            high_30 = df.loc[idx-lookback:idx-1, 'high'].max() if idx > 0 else 0
            # 점진 상승: 3분 이상 우상향
            price_rise = df['close'].iloc[idx] > df['close'].iloc[idx - 3] if idx >= 3 else False
            vwap_ok = row['close'] > row['vwap']
            rsi_ok = row['rsi'] > 60
            vol_spike = row['volume'] > 1.5 * row['vol_ma5']
            is_break_high = row['high'] > high_30 if high_30 > 0 else False
            # 기존 카운트 유지 (원하면 수정 가능)
            if is_break_high:
                condition_counts['new_high'] += 1
            if vol_spike:
                condition_counts['vol_spike'] += 1
            if vwap_ok:
                condition_counts['vwap_ok'] += 1
            if rsi_ok:
                condition_counts['rsi_ok'] += 1
            # 조건 조합: 급등 배제, 점진 상승 강화
            if price_rise and (is_break_high or vol_spike) and vwap_ok and rsi_ok:
                condition_counts['all_conditions'] += 1
                buy_time = row['datetime']
                buy_price = row['close']
                buy_idx = idx
                ten = df[(df['datetime'].dt.time >= pd.to_datetime('10:00').time()) &
                         (df['datetime'].dt.time < pd.to_datetime('11:00').time())]
                high_10_11 = ten['high'].max()
                close_10_11 = ten['close'].iloc[-1]
                close_pos_10_11 = close_10_11 / high_10_11 if high_10_11 > 0 else np.nan
                buy_strength = df[(df['datetime'].dt.time >= pd.to_datetime('10:10').time()) &
                                  (df['datetime'].dt.time <= pd.to_datetime('10:30').time())]['volume'].sum()

                # ▼▼▼ 기본 청산 로직 (TP/Trailing 완화) ▼▼▼
                sell_price = np.nan
                sell_time = None
                sell_reason = None
                max_price = buy_price
                min_price = buy_price
                trailing_active = False
                peak_price = buy_price
                position = 1.0
                max_profit_reached = 0.0

                sell_window = df[df.index > buy_idx]
                for _, srow in sell_window.iterrows():
                    price = srow['close']
                    high = srow['high']
                    low = srow['low']
                    max_price = max(max_price, high)
                    min_price = min(min_price, low)
                    current_return = (price - buy_price) / buy_price
                    max_profit = (max_price - buy_price) / buy_price
                    # max_profit_reached를 루프 내에서 지속 갱신
                    max_profit_reached = max(max_profit_reached, max_profit)

                    # Smart Trailing Stop 활성화 조건 (완화)
                    smart_trailing_active = max_profit > 0.015
                    trailing_threshold = max_price * 0.985  # 고점 대비 -1.5%

                    # 1. 고정 목표 수익 (1.0%로 하향)
                    if current_return >= 0.01:
                        sell_reason = "Fixed TP 1.0%"
                        sell_price = price
                        sell_time = srow['datetime']
                        break

                    # 2. Smart Trailing Stop (조건부)
                    elif smart_trailing_active and price < trailing_threshold:
                        sell_reason = "Smart Trailing -1.5%"
                        sell_price = price
                        sell_time = srow['datetime']
                        break

                    # 3. Hard Stop Loss
                    elif current_return <= -0.015:
                        sell_reason = "Hard Stop Loss -1.5%"
                        sell_price = price
                        sell_time = srow['datetime']
                        break

                    # 4. EOD (익일 청산 조건 보완)
                    elif srow['datetime'].time() > pd.to_datetime('15:00').time():
                        if current_return < 0.005:
                            sell_reason = "EOD Cut Small Gain"
                            sell_price = price
                            sell_time = srow['datetime']
                            break
                        else:
                            sell_reason = "Overnight Profit"
                            sell_price = price  # 임시로 현재가 사용
                            sell_time = srow['datetime']
                            break

                # TP 도달률 분석 기록 (실제 청산된 거래만, 1.0% 기준으로 수정)
                if not np.isnan(sell_price):
                    tp_analysis['total_trades'] += 1
                    tp_analysis['max_profit_distribution'].append(max_profit_reached)
                    if max_profit_reached >= 0.005:
                        tp_analysis['tp_0.5_reached'] += 1
                    if max_profit_reached >= 0.01:
                        tp_analysis['tp_1.0_reached'] += 1
                    if max_profit_reached >= 0.015:
                        tp_analysis['tp_1.5_reached'] += 1
                    if max_profit_reached >= 0.02:
                        tp_analysis['tp_2.0_reached'] += 1
                    if max_profit_reached >= 0.025:
                        tp_analysis['tp_2.5_reached'] += 1

                # 결과 기록
                if not np.isnan(sell_price):
                    max_profit = (max_price - buy_price) / buy_price
                    drawdown = (min_price - buy_price) / buy_price
                    ret = (sell_price - buy_price) / buy_price
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
                # ▲▲▲ 기본 청산 로직 (안정적 버전) ▲▲▲
    except Exception as e:
        continue

# 결과 집계 및 저장
print(f"\n=== Processing Summary ===")
print(f"Total files: {total_files}")
print(f"Processed files: {processed_files}")
print(f"Condition counts:")
for condition, count in condition_counts.items():
    print(f"  {condition}: {count}")

# TP 도달률 분석 출력
print(f"\n=== Target Profit 도달률 분석 ===")
total_trades = tp_analysis['total_trades']
if total_trades > 0:
    print(f"총 거래 수: {total_trades}")
    print(f"0.5% 도달률: {tp_analysis['tp_0.5_reached']} ({tp_analysis['tp_0.5_reached']/total_trades*100:.1f}%)")
    print(f"1.0% 도달률: {tp_analysis['tp_1.0_reached']} ({tp_analysis['tp_1.0_reached']/total_trades*100:.1f}%)")
    print(f"1.5% 도달률: {tp_analysis['tp_1.5_reached']} ({tp_analysis['tp_1.5_reached']/total_trades*100:.1f}%)")
    print(f"2.0% 도달률: {tp_analysis['tp_2.0_reached']} ({tp_analysis['tp_2.0_reached']/total_trades*100:.1f}%)")
    print(f"2.5% 도달률: {tp_analysis['tp_2.5_reached']} ({tp_analysis['tp_2.5_reached']/total_trades*100:.1f}%)")
    
    # 최대 수익률 분포 분석
    max_profits = np.array(tp_analysis['max_profit_distribution'])
    print(f"\n최대 수익률 통계:")
    print(f"평균 최대 수익률: {max_profits.mean():.3f}")
    print(f"중간값 최대 수익률: {np.median(max_profits):.3f}")
    print(f"0.1% 이하: {(max_profits <= 0.001).sum()} ({np.mean(max_profits <= 0.001)*100:.1f}%)")
    print(f"0.3% 이하: {(max_profits <= 0.003).sum()} ({np.mean(max_profits <= 0.003)*100:.1f}%)")
    print(f"0.5% 이하: {(max_profits <= 0.005).sum()} ({np.mean(max_profits <= 0.005)*100:.1f}%)")
    print(f"1.0% 이하: {(max_profits <= 0.01).sum()} ({np.mean(max_profits <= 0.01)*100:.1f}%)")

if results:
    results_df = pd.DataFrame(results)
    print(f"\n=== Backtest Results ===")
    print(f"Total trades: {len(results)}")
    print(results_df.describe())
    
    # 리포트 자동화: sell_reason별 수익률 분석
    print("\n--- Sell Reason Analysis ---")
    sell_reason_analysis = results_df.groupby('sell_reason')['return'].describe()
    print(sell_reason_analysis)
    
    print("\n--- Sell Reason Distribution ---")
    print(results_df['sell_reason'].value_counts(normalize=True))
    
    # 익절 vs 손절 비교 분석
    profit_trades = results_df[results_df['return'] > 0]
    loss_trades = results_df[results_df['return'] <= 0]
    print(f"\n--- Profit vs Loss Analysis ---")
    print(f"Profit trades: {len(profit_trades)} ({len(profit_trades)/len(results_df)*100:0.1f}%)")
    print(f"Loss trades: {len(loss_trades)} ({len(loss_trades)/len(results_df)*100:0.1f}%)")
    print(f"Average profit: {profit_trades['return'].mean():.4f}")
    print(f"Average loss: {loss_trades['return'].mean():.4f}")
    
    # 수익률 분포 히스토그램 시각화
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.hist(results_df['return'], bins=50, alpha=0.7, color='blue')
    plt.title('Return Distribution')
    plt.xlabel('Return')
    plt.ylabel('Frequency')
    
    plt.subplot(2, 2, 2)
    sell_reason_counts = results_df['sell_reason'].value_counts()
    plt.pie(sell_reason_counts.values, labels=sell_reason_counts.index, autopct='%1.1f%%')
    plt.title('Sell Reason Distribution')
    
    plt.subplot(2, 2, 3)
    plt.scatter(results_df['max_profit'], results_df['return'], alpha=0.6)
    plt.xlabel('Max Profit')
    plt.ylabel('Actual Return')
    plt.title('Max Profit vs Actual Return')
    
    plt.subplot(2, 2, 4)
    plt.scatter(results_df['drawdown'], results_df['return'], alpha=0.6)
    plt.xlabel('Drawdown')
    plt.ylabel('Return')
    plt.title('Drawdown vs Return')
    
    plt.tight_layout()
    plt.savefig('backtest_analysis_plots.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    results_df.to_csv('backtest_gradual_riser_advanced.csv', index=False, encoding='utf-8-sig')
    print(f"\nResults saved to: backtest_gradual_riser_advanced.csv")
    print(f"Analysis plots saved to: backtest_analysis_plots.png")
else:
    print("\nNo trades were executed under the current strategy conditions.")
    print("Consider relaxing the entry conditions or checking data quality.") 

# ▼▼▼ 진입 후 20~60분 가격 분포 분석 및 시각화 ▼▼▼
from datetime import timedelta

drift_records = []

for trade in results:
    entry_time = trade['buy_time']
    stock = trade['stock']
    try:
        df = pd.read_csv(f'minute_data/{stock}.csv', parse_dates=['datetime'])
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        df = df.dropna(subset=['datetime', 'close'])
        df = df.sort_values('datetime')

        sub = df[(df['datetime'] > entry_time) & 
                 (df['datetime'] <= entry_time + timedelta(minutes=60))].copy()
        sub['delta_minutes'] = (sub['datetime'] - entry_time).dt.total_seconds() / 60
        sub['pct_change'] = (sub['close'] - trade['buy_price']) / trade['buy_price']

        drift_records.append(sub[['delta_minutes', 'pct_change']])
    except Exception as e:
        continue

# 통합 분석
if drift_records:
    all_drift = pd.concat(drift_records, ignore_index=True)
    drift_summary = all_drift.groupby('delta_minutes')['pct_change'].agg(['mean', 'median', 'std'])
    
    plt.figure(figsize=(10, 6))
    plt.plot(drift_summary.index, drift_summary['mean'], label='Mean')
    plt.plot(drift_summary.index, drift_summary['median'], label='Median')
    plt.fill_between(drift_summary.index,
                     drift_summary['mean'] - drift_summary['std'],
                     drift_summary['mean'] + drift_summary['std'],
                     color='gray', alpha=0.3, label='±1 STD')
    plt.axhline(0, color='black', linestyle='--')
    plt.title('Drift Pattern After Entry (0–60min)')
    plt.xlabel('Minutes After Entry')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('drift_pattern.png')
    plt.show() 