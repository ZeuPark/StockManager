import pandas as pd
import numpy as np
from glob import glob
from tqdm import tqdm
import matplotlib.pyplot as plt
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

        # 진입 조건별 카운트 (조건 강화)
        for idx, row in entry_window.iterrows():
            # 30고가로 강화
            lookback = min(30, idx)
            high_30 = df.loc[idx-lookback:idx-1, 'high'].max() if idx > 0 else 0
            is_break_high = row['high'] > high_30 if high_30 > 0 else False
            
            vol_spike = row['volume'] > 2 * row['vol_ma5']
            # VWAP 대비 0.3% 이상 상회로 변경
            vwap_ok = row['close'] > row['vwap'] * 1.03
            # RSI 범위 63-68 좁히기
            rsi_ok = 63 <= row['rsi'] <= 68
            
            if is_break_high:
                condition_counts['new_high'] += 1
            if vol_spike:
                condition_counts['vol_spike'] += 1
            if vwap_ok:
                condition_counts['vwap_ok'] += 1
            if rsi_ok:
                condition_counts['rsi_ok'] += 1
            # 조건 조합: 핵심2개(고점돌파 또는 거래량급증) + 보조 2개(RSI적정)
            if (is_break_high or vol_spike) and vwap_ok and rsi_ok:
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
                # ▼▼▼ 기본 청산 로직 (안정적 버전) ▼▼▼
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
                    
                    # VWAP 이탈 손절: 봉 종가 기준으로 변경 (false break 대응)
                    if price < srow['vwap'] * 0.997:
                        sell_price = price
                        sell_time = srow['datetime']
                        sell_reason = 'VWAP Break'
                        position = 0.0
                        break
                    
                    # Target Profit(2%) 익절로 조정 (close 기준)
                    elif (price - buy_price) / buy_price >= 0.02:
                        sell_price = price
                        sell_time = srow['datetime']
                        sell_reason = 'Target Profit'
                        position = 0.0
                        break
                    
                    # 부분청산: 1 도달 시 40% 청산 (비중 확대)
                    elif not partial_sell and (price - buy_price) / buy_price >= 0.01:
                        partial_sell = True
                        partial_sell_price = price
                        partial_sell_time = srow['datetime']
                        partial_sell_reason = 'Partial Profit 1%'
                        position = 0.6  # 40% 청산 후 60% 보유
                        # 나머지 60%는 계속 보유
                    
                    # 복합 익절: RSI > 70 and return > 0.8% (조건 완화)
                    if not trailing_active and srow['rsi'] > 70 and ret_now > 0.008:
                        trailing_active = True
                        peak_price = high
                        continue
                    
                    # 트레일링 스탑: 최고가 대비 -1% 하락, 단 최소 수익률 1.5% 이상 (조건 완화)
                    if trailing_active:
                        if high > peak_price:
                            peak_price = high
                        if (peak_price - buy_price) / buy_price >= 0.015:
                            if price <= peak_price * 0.99:
                                sell_price = price
                                sell_time = srow['datetime']
                                sell_reason = 'Trailing Stop'
                                position = 0.0
                                break
                    
                    # 🔹 1단계: 조건부 EOD 청산 (손실 중인 포지션만 마감)
                    if srow['datetime'].time() >= pd.to_datetime('15:00').time():
                        if ret_now < 0:
                            sell_price = price
                            sell_time = srow['datetime']
                            sell_reason = 'EOD Loss'
                            position = 0.0
                            break
                        else:
                            # 수익 중이면 오버나잇 보유
                            continue
                    
                    # 🔹 2단계: 마감 30분 전 타이트 트레일링 스탑 (14:30~15:00)
                    if srow['datetime'].time() >= pd.to_datetime('14:30').time():
                        if ret_now > 0.005:  # 0.5% 이상 수익 중일 때만
                            if price < peak_price * 0.992:  # 고점 대비 0.8% 이탈
                                sell_price = price
                                sell_time = srow['datetime']
                                sell_reason = 'Tight Trailing Before Close'
                                position = 0.0
                                break
                    
                    # 🔹 3단계: 익일 자동 청산 로직 (09:10 체크)
                    if srow['datetime'].time() == pd.to_datetime('09:10').time():
                        if ret_now > 0.01:  # 1% 이상 수익 중이면 익일 청산
                            sell_price = price
                            sell_time = srow['datetime']
                            sell_reason = 'Overnight Profit'
                            position = 0.0
                            break
                        elif drawdown < -0.03:  # 3% 이상 손실 시 갭다운 손절
                            sell_price = price
                            sell_time = srow['datetime']
                            sell_reason = 'Gap Down Stop Loss'
                            position = 0.0
                            break
                
                # 결과 기록
                if not np.isnan(sell_price):
                    ret = (sell_price - buy_price) / buy_price * position
                    max_profit = (max_price - buy_price) / buy_price
                    drawdown = (min_price - buy_price) / buy_price
                    # 부분청산 수익 포함
                    if partial_sell:
                        ret = 0.4 * ((partial_sell_price - buy_price) / buy_price) + 0.6 * ((sell_price - buy_price) / buy_price)
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