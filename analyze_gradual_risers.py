import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 분석 조건
SPIKE_THRESHOLD = 0.05   # 9:00~9:30 급등 5% 초과 제외
GRADUAL_RISE_THRESHOLD = 0.03  # 10~11시 3% 이상 상승
MINUTES_PATH = 'minute_data'
SECTOR_PATH = 'sector_info.csv'  # 종목코드,섹터,시가총액 등 정보가 담긴 csv (있으면 merge)

results = []

for csv_path in glob.glob(os.path.join(MINUTES_PATH, '*_1min.csv')):
    try:
        df = pd.read_csv(csv_path)
        if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        df = df.sort_values('datetime')
        code = os.path.basename(csv_path).split('_')[0]

        # 1. 9:00~9:30 급등 여부 체크
        mask_9 = (df['datetime'].dt.time >= pd.to_datetime('09:00').time()) & (df['datetime'].dt.time <= pd.to_datetime('09:30').time())
        df_9 = df[mask_9]
        if df_9.empty:
            continue
        open_9 = df_9.iloc[0]['open']
        high_9_30 = df_9['high'].max()
        r_9_spike = (high_9_30 / open_9) - 1
        if r_9_spike >= SPIKE_THRESHOLD:
            continue  # 급등 종목 제외

        # 2. 10:00~11:00 점진적 상승 체크
        mask_10_11 = (df['datetime'].dt.time >= pd.to_datetime('10:00').time()) & (df['datetime'].dt.time <= pd.to_datetime('11:00').time())
        df_10_11 = df[mask_10_11]
        if df_10_11.empty:
            continue
        open_10 = df_10_11.iloc[0]['open']
        close_11 = df_10_11.iloc[-1]['close']
        r_10_11 = (close_11 / open_10) - 1
        if r_10_11 < GRADUAL_RISE_THRESHOLD:
            continue  # 점진적 상승 미달

        # 3. 11:00~15:00 오후 흐름 분석
        mask_11_15 = (df['datetime'].dt.time >= pd.to_datetime('11:00').time()) & (df['datetime'].dt.time <= pd.to_datetime('15:00').time())
        df_11_15 = df[mask_11_15]
        if not df_11_15.empty:
            open_11 = df_11_15.iloc[0]['open']
            close_15 = df_11_15.iloc[-1]['close']
            r_11_15 = (close_15 / open_11) - 1
        else:
            r_11_15 = np.nan

        # 4. 10:10~10:30 매수 타이밍 feature
        mask_1010_1030 = (df['datetime'].dt.time >= pd.to_datetime('10:10').time()) & (df['datetime'].dt.time <= pd.to_datetime('10:30').time())
        df_1010_1030 = df[mask_1010_1030]
        if not df_1010_1030.empty:
            buy_strength = df_1010_1030['volume'].sum() / len(df_1010_1030)
            buy_cumvol = df_1010_1030['volume'].sum()
            buy_high_break = int((df_1010_1030['high'] > open_10).any())
        else:
            buy_strength = buy_cumvol = buy_high_break = np.nan

        # 5. 10~11시 기술적 지표 (RSI, 볼린저밴드, VWAP)
        def calc_rsi(series, period=14):
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period, min_periods=1).mean()
            avg_loss = loss.rolling(window=period, min_periods=1).mean()
            rs = avg_gain / (avg_loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))
            return rsi
        rsi_10_11 = calc_rsi(df_10_11['close']).iloc[-1] if len(df_10_11) >= 14 else np.nan
        bb_mean = df_10_11['close'].mean()
        bb_std = df_10_11['close'].std()
        bb_upper = bb_mean + 2 * bb_std
        bb_break = int((df_10_11['close'] > bb_upper).any())
        vwap = (df_10_11['close'] * df_10_11['volume']).sum() / (df_10_11['volume'].sum() + 1e-9)
        vwap_break = int(close_11 > vwap)

        # 6. 9~10시 거래량
        mask_9_10 = (df['datetime'].dt.time >= pd.to_datetime('09:00').time()) & (df['datetime'].dt.time < pd.to_datetime('10:00').time())
        vol_9_10 = df[mask_9_10]['volume'].sum()
        # 10~11시 변동성
        vol_10_11 = df_10_11['high'].max() - df_10_11['low'].min()
        # 10~11시 평균 거래량
        avg_vol_10_11 = df_10_11['volume'].mean()
        # 10~11시 고가/저가 대비 시가/종가 위치
        high_10_11 = df_10_11['high'].max()
        low_10_11 = df_10_11['low'].min()
        open_pos = (open_10 - low_10_11) / (high_10_11 - low_10_11) if high_10_11 != low_10_11 else 0.5
        close_pos = (close_11 - low_10_11) / (high_10_11 - low_10_11) if high_10_11 != low_10_11 else 0.5

        results.append({
            'stock_code': code,
            'r_9_spike': r_9_spike,
            'r_10_11': r_10_11,
            'r_11_15': r_11_15,
            'vol_9_10': vol_9_10,
            'vol_10_11': vol_10_11,
            'avg_vol_10_11': avg_vol_10_11,
            'open_pos_10_11': open_pos,
            'close_pos_10_11': close_pos,
            'buy_strength': buy_strength,
            'buy_cumvol': buy_cumvol,
            'buy_high_break': buy_high_break,
            'rsi_10_11': rsi_10_11,
            'bb_break': bb_break,
            'vwap_break': vwap_break
        })
    except Exception as e:
        print(f"{csv_path} 에러: {e}")

# 결과 DataFrame
if results:
    df_res = pd.DataFrame(results)

    # 섹터/시총 merge (있을 경우)
    if os.path.exists(SECTOR_PATH):
        sector_df = pd.read_csv(SECTOR_PATH)
        df_res = df_res.merge(sector_df, how='left', left_on='stock_code', right_on='stock_code')

    # 1. r_11_15 boxplot (close_pos_10_11 > 0.9 vs <= 0.9)
    df_res['close_pos_group'] = (df_res['close_pos_10_11'] > 0.9).astype(int)
    plt.figure(figsize=(8,5))
    sns.boxplot(x='close_pos_group', y='r_11_15', data=df_res)
    plt.title('오전 고가마감 여부별 오후 수익률(r_11_15)')
    plt.xlabel('close_pos_10_11 > 0.9 (1=Yes, 0=No)')
    plt.ylabel('r_11_15 (11~15시 수익률)')
    plt.tight_layout()
    plt.savefig('r11_15_boxplot.png')
    plt.close()

    # 2. 매수 타이밍/기술적지표/섹터/시총 분포 요약
    print('조건에 부합하는 종목 수:', len(df_res))
    print(df_res[['stock_code', 'r_9_spike', 'r_10_11', 'r_11_15', 'close_pos_10_11', 'buy_strength', 'buy_cumvol', 'buy_high_break', 'rsi_10_11', 'bb_break', 'vwap_break']])
    print('\n=== 공통점(평균) ===')
    print(df_res.mean(numeric_only=True))
    if 'sector' in df_res.columns:
        print('\n섹터 분포:')
        print(df_res['sector'].value_counts())
    if 'market_cap' in df_res.columns:
        print('\n시가총액 분포(백만 단위):')
        print(df_res['market_cap'].describe())

    # CSV 저장
    df_res.to_csv('gradual_risers_analysis.csv', index=False)
    print("\n분석 결과가 'gradual_risers_analysis.csv'에 저장되었습니다.")
    print("r_11_15 boxplot이 'r11_15_boxplot.png'로 저장되었습니다.")
else:
    print('조건에 부합하는 종목이 없습니다.') 