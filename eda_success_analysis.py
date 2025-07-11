import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 분석 파라미터
DATA_FOLDER = 'minute_data'
SUCCESS_THRESHOLD = 7.0  # 시가 대비 +7% 이상 고가
START_TIME = '09:00'
END_TIME = '11:00'

# 1. 데이터 로딩
csv_files = glob.glob(os.path.join(DATA_FOLDER, '*_1min.csv'))
print(f"총 {len(csv_files)}개 종목 데이터 분석 중...")

success_features = []
failure_features = []

for i, file_path in enumerate(csv_files):
    # 진행률 표시
    progress = (i + 1) / len(csv_files) * 100
    print(f"진행률: {progress:.1f}% ({i+1}/{len(csv_files)}) - {os.path.basename(file_path)}")
    
    try:
        stock_code = os.path.basename(file_path).split('_')[0]
        df = pd.read_csv(file_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        
        # 날짜별로 그룹화
        for date, day_df in df.groupby(df['datetime'].dt.date):
            day_df = day_df.copy()
            day_df['time'] = day_df['datetime'].dt.time
            
            # 9시~11시 데이터만 추출
            mask = (day_df['datetime'].dt.time >= datetime.strptime(START_TIME, '%H:%M').time()) & \
                   (day_df['datetime'].dt.time <= datetime.strptime(END_TIME, '%H:%M').time())
            scan_df = day_df[mask]
            if scan_df.empty:
                continue
            
            # 9시 정각 데이터
            nine_df = day_df[day_df['datetime'].dt.time == datetime.strptime('09:00', '%H:%M').time()]
            if nine_df.empty:
                continue
            nine = nine_df.iloc[0]
            
            # 전일 종가
            prev_day = date - timedelta(days=1)
            prev_close = None
            prev_df = df[df['datetime'].dt.date == prev_day]
            if not prev_df.empty:
                prev_close = prev_df.iloc[-1]['close']
            
            # 9~11시 고가
            high = scan_df['high'].max()
            open_price = nine['open']
            
            # 성공 여부 판정
            if open_price > 0:
                high_return = (high - open_price) / open_price * 100
            else:
                high_return = 0
            is_success = high_return >= SUCCESS_THRESHOLD
            
            # 9시 특징 추출
            feature = {
                'stock_code': stock_code,
                'date': date,
                'open': open_price,
                'high': high,
                'high_return': high_return,
                'prev_close': prev_close,
                'open_gap': (open_price - prev_close) / prev_close * 100 if prev_close else np.nan,
                'volume_9': nine['volume'],
                'volume_ratio_9': nine.get('volume_ratio', np.nan),
                'ma5_9': nine.get('ma5', np.nan),
                'ma20_9': nine.get('ma20', np.nan),
                'close_9': nine['close'],
                'above_ma20_9': int(nine['close'] > nine.get('ma20', 0)),
            }
            if is_success:
                success_features.append(feature)
            else:
                failure_features.append(feature)
    except Exception as e:
        print(f"  {file_path} 분석 실패: {e}")
        continue

# 2. 데이터프레임 변환
success_df = pd.DataFrame(success_features)
failure_df = pd.DataFrame(failure_features)

print(f"성공 케이스: {len(success_df)}개, 실패 케이스: {len(failure_df)}개")

# 3. 통계 비교
compare_cols = ['open_gap', 'volume_9', 'volume_ratio_9', 'ma5_9', 'ma20_9', 'close_9', 'above_ma20_9']
print("\n[성공/실패 그룹별 9시 특징 평균]")
print("특징\t\t성공\t\t실패")
for col in compare_cols:
    s_mean = success_df[col].mean() if col in success_df else np.nan
    f_mean = failure_df[col].mean() if col in failure_df else np.nan
    print(f"{col:12s}\t{s_mean:8.3f}\t{f_mean:8.3f}")

# 4. 히스토그램 시각화 (예시: 거래량, 거래량비율, open_gap)
import matplotlib.pyplot as plt
plt.figure(figsize=(15,4))
for i, col in enumerate(['open_gap', 'volume_9', 'volume_ratio_9']):
    plt.subplot(1,3,i+1)
    plt.hist(success_df[col].dropna(), bins=30, alpha=0.5, label='Success')
    plt.hist(failure_df[col].dropna(), bins=30, alpha=0.5, label='Failure')
    plt.title(col)
    plt.legend()
plt.tight_layout()
plt.show() 