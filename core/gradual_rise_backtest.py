import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# === CONFIG: 주요 파라미터/구간/종목 수 조정 ===
DEFAULT_PARAMETERS = {
    'theta_spike': 0.15,      # 시초 급등 제외 (15% 이상 급등 제외)
    'theta_spike_low': 0.02,  # 최소 상승률 (2% 이상)
    'theta_15m': 0.10,        # 15분 누적상승 (10% 이상 - 천천히 상승하는 종목)
    'theta_vol': 0.05,        # 거래량비 (5% 이상)
    'theta_pull': 0.15,       # 저점 하락폭 (15% 이내)
    'tp_pct': 0.08,           # 익절 (8%)
    'sl_pct': 0.05,           # 손절 (5%)
    'orb_delay_min': 5,       # ORB 최소 대기 (5분)
    'orb_max_min': 30         # ORB 최대 대기 (30분)
}
# 테스트/최적화 구간
TRAIN_RANGE = ('2024-11-01', '2024-11-30')
TEST_RANGE = ('2025-06-01', '2025-06-30')

class GradualRiseBacktest:
    """
    완만 상승 패턴 백테스트 시스템
    
    전략 목적: 
    - 시초 급등 종목(20-25% 급등)을 제외
    - 천천히 10-20% 상승하는 종목을 찾아 ORB 진입
    
    핵심 조건:
    1. Opening Spike 제외 (첫 1분 15% 이상 급등 제외)
    2. Gradual Rise 확인 (15분 누적 10-20% 상승)
    3. Volume Confirmation (거래량 확인)
    4. ORB Delay (30분 이내 고가 돌파)
    5. 기술적 지표 활용 (RSI, 볼린저 밴드, 모멘텀 등)
    """
    
    def __init__(self, data_path="minute_data"):
        self.data_path = data_path
        self.results = []
        self.parameters = DEFAULT_PARAMETERS.copy()
    
    def load_data(self, stock_codes=None, date_range=None):
        """1분봉 데이터 로드 (기간 필터링 지원)"""
        print("데이터 로딩 중...")
        
        all_data = []
        import pandas as pd
        csv_files = glob.glob(os.path.join(self.data_path, "*_1min.csv"))
        
        if stock_codes:
            csv_files = [f for f in csv_files if any(code in f for code in stock_codes)]
        
        for file_path in csv_files:
            try:
                stock_code = os.path.basename(file_path).split('_')[0]
                df = pd.read_csv(file_path)
                df['stock_code'] = stock_code
                df['datetime'] = pd.to_datetime(df['datetime'])
                df['date'] = df['datetime'].dt.date
                df['time'] = df['datetime'].dt.time
                
                # 거래일별로 정렬
                df = df.sort_values(['date', 'time'])
                
                # 기간 필터링
                if date_range is not None:
                    start, end = date_range
                    df = df[(df['date'] >= pd.to_datetime(start).date()) & (df['date'] <= pd.to_datetime(end).date())]
                
                all_data.append(df)
                print(f"로드 완료: {stock_code} ({len(df)} rows)")
                
            except Exception as e:
                print(f"에러 - {file_path}: {e}")
                continue
        
        if not all_data:
            raise ValueError("로드된 데이터가 없습니다.")
        
        self.data = pd.concat(all_data, ignore_index=True)
        print(f"총 {len(self.data)} rows, {self.data['stock_code'].nunique()} 종목 로드 완료")
        
        return self.data
    
    def calculate_features(self, df):
        """Feature Engineering (대폭 개선: 기술적 지표, 거래량 패턴, 시간대별 특성 등 추가)"""
        import pandas as pd
        import numpy as np
        from scipy import stats
        
        # KOSPI 일별 데이터 로드
        kospi_path = os.path.join('data_collection', 'market_data', 'KOSPI_daily.csv')
        kospi_df = pd.read_csv(kospi_path)
        kospi_df['date'] = pd.to_datetime(kospi_df['date']).dt.date
        kospi_df = kospi_df.sort_values('date')
        kospi_df['prev_close'] = kospi_df['close'].shift(1)
        kospi_df['kospi_return'] = (kospi_df['close'] / kospi_df['prev_close']) - 1
        kospi_df['kospi_volatility'] = (kospi_df['high'] - kospi_df['low']) / kospi_df['prev_close']
        kospi_map = kospi_df.set_index('date')[['kospi_return', 'kospi_volatility']].to_dict('index')

        # === opening_gap 계산을 위한 prev_close 컬럼 추가 ===
        df = df.sort_values(['stock_code', 'date', 'time'])
        df['prev_close'] = df.groupby('stock_code')['close'].shift(1)

        features = []
        
        for (stock_code, date), day_df in df.groupby(['stock_code', 'date']):
            if len(day_df) < 30:  # 최소 30분 데이터 필요
                continue
                
            # 기본 정보
            open_price = day_df.iloc[0]['open']
            close_1min = day_df.iloc[0]['close']
            prev_close = day_df.iloc[0]['prev_close']
            if pd.notnull(prev_close) and prev_close != 0:
                opening_gap = (open_price / prev_close) - 1
            else:
                opening_gap = 0
            
            # === 1. 기본 가격 Feature ===
            r_1 = (close_1min / open_price) - 1  # 첫 1분 수익률
            
            if len(day_df) >= 15:
                close_15min = day_df.iloc[14]['close']
                cum_r_15 = (close_15min / open_price) - 1  # 15분 누적 수익률
            else:
                cum_r_15 = np.nan
            
            # === 2. 거래량 Feature (개선) ===
            volume_15min = day_df.iloc[:15]['volume'].sum()
            volume_5min = day_df.iloc[:5]['volume'].sum()
            volume_10min = day_df.iloc[:10]['volume'].sum()
            
            # 거래량 이동평균
            volume_sma_5 = day_df.iloc[:15]['volume'].rolling(5).mean().iloc[-1]
            volume_sma_10 = day_df.iloc[:15]['volume'].rolling(10).mean().iloc[-1]
            
            # 거래량 비율 (전일 대비 추정)
            v_ratio_15 = volume_15min / (volume_sma_10 * 15) if volume_sma_10 > 0 else 1
            v_ratio_5 = volume_5min / (volume_sma_5 * 5) if volume_sma_5 > 0 else 1
            
            # === 3. 기술적 지표 (RSI, MACD, 볼린저 밴드 등) ===
            if len(day_df) >= 15:
                closes = day_df.iloc[:15]['close'].values
                volumes = day_df.iloc[:15]['volume'].values
                
                # RSI (14기간)
                if len(closes) >= 14:
                    delta = np.diff(closes)
                    gain = np.where(delta > 0, delta, 0)
                    loss = np.where(delta < 0, -delta, 0)
                    avg_gain = np.mean(gain[-14:])
                    avg_loss = np.mean(loss[-14:])
                    rs = avg_gain / avg_loss if avg_loss != 0 else 0
                    rsi_15 = 100 - (100 / (1 + rs))
                else:
                    rsi_15 = np.nan
                
                # MACD (12, 26, 9)
                if len(closes) >= 26:
                    ema_12 = pd.Series(closes).ewm(span=12).mean().iloc[-1]
                    ema_26 = pd.Series(closes).ewm(span=26).mean().iloc[-1]
                    macd_line = ema_12 - ema_26
                    macd_signal = pd.Series([macd_line]).ewm(span=9).mean().iloc[-1]
                    macd_histogram = macd_line - macd_signal
                else:
                    macd_line = macd_signal = macd_histogram = np.nan
                
                # 볼린저 밴드 (20기간, 2표준편차)
                if len(closes) >= 20:
                    sma_20 = np.mean(closes[-20:])
                    std_20 = np.std(closes[-20:])
                    bb_upper = sma_20 + (2 * std_20)
                    bb_lower = sma_20 - (2 * std_20)
                    bb_position = (close_15min - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                    bb_width = (bb_upper - bb_lower) / sma_20
                else:
                    bb_position = bb_width = np.nan
                
                # 스토캐스틱 (14기간)
                if len(closes) >= 14:
                    high_14 = np.max(closes[-14:])
                    low_14 = np.min(closes[-14:])
                    k_percent = 100 * (close_15min - low_14) / (high_14 - low_14) if high_14 != low_14 else 50
                    d_percent = k_percent  # 단순화
                else:
                    k_percent = d_percent = np.nan
                
                # 모멘텀 지표
                momentum_5 = (close_15min / closes[-5]) - 1 if len(closes) >= 5 else np.nan
                momentum_10 = (close_15min / closes[-10]) - 1 if len(closes) >= 10 else np.nan
                
                # 추세 강도
                if len(closes) >= 10:
                    x = np.arange(len(closes))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, closes)
                    trend_strength = abs(r_value)
                else:
                    trend_strength = np.nan
                
            else:
                rsi_15 = macd_line = macd_signal = macd_histogram = np.nan
                bb_position = bb_width = k_percent = d_percent = np.nan
                momentum_5 = momentum_10 = trend_strength = np.nan
            
            # === 4. 변동성/리스크 지표 ===
            high_15min = day_df.iloc[:15]['high'].max()
            low_15min = day_df.iloc[:15]['low'].min()
            max_drawdown_15 = (low_15min / high_15min) - 1
            volatility_15 = high_15min - low_15min
            atr_15 = np.mean([high - low for high, low in zip(day_df.iloc[:15]['high'], day_df.iloc[:15]['low'])])
            
            # === 5. 시간대별 특성 ===
            time_15min = day_df.iloc[14]['time']
            time_minutes = time_15min.hour * 60 + time_15min.minute
            
            # 장 시작 시간대 (9:00-9:30)
            is_opening = 1 if 540 <= time_minutes <= 570 else 0
            # 점심 시간대 (11:30-13:00)
            is_lunch = 1 if 690 <= time_minutes <= 780 else 0
            # 장 마감 시간대 (15:00-15:30)
            is_closing = 1 if 900 <= time_minutes <= 930 else 0
            
            # === 6. 가격 패턴 ===
            if len(day_df) >= 15:
                # Higher-Low Score
                sma_5 = pd.Series(closes).rolling(5).mean().values
                hl_score = np.sum(closes[4:] > sma_5[3:-1]) / 11 if len(sma_5) >= 11 else np.nan
                
                # VWAP Gap
                vwap_15 = (day_df.iloc[:15]['close'] * day_df.iloc[:15]['volume']).sum() / volume_15min
                vwap_gap = (close_15min - vwap_15) / vwap_15
                
                # 선형 회귀 기울기
                x = np.arange(15)
                y = day_df.iloc[:15]['close'].values
                slope_15 = np.polyfit(x, y, 1)[0]
            else:
                hl_score = vwap_gap = opening_gap = slope_15 = np.nan
            
            # === 7. 시장상황 Feature ===
            kospi_return_15 = 0
            kospi_volatility_15 = 0
            if date in kospi_map:
                kospi_return_15 = kospi_map[date]['kospi_return']
                kospi_volatility_15 = kospi_map[date]['kospi_volatility']
            
            # === 8. Feature 조합/상호작용 ===
            price_volume_momentum = momentum_5 * v_ratio_5 if not np.isnan(momentum_5) and not np.isnan(v_ratio_5) else 0
            rsi_volume_interaction = rsi_15 * v_ratio_15 if not np.isnan(rsi_15) and not np.isnan(v_ratio_15) else 0
            bb_volume_interaction = bb_position * v_ratio_15 if not np.isnan(bb_position) and not np.isnan(v_ratio_15) else 0
            
            features.append({
                'stock_code': stock_code,
                'date': date,
                'open_price': open_price,
                
                # 기본 가격
                'r_1': r_1,
                'cum_r_15': cum_r_15,
                'opening_gap': opening_gap,
                
                # 거래량
                'volume_15min': volume_15min,
                'volume_5min': volume_5min,
                'volume_10min': volume_10min,
                'v_ratio_15': v_ratio_15,
                'v_ratio_5': v_ratio_5,
                'volume_sma_5': volume_sma_5,
                'volume_sma_10': volume_sma_10,
                
                # 기술적 지표
                'rsi_15': rsi_15,
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram,
                'bb_position': bb_position,
                'bb_width': bb_width,
                'k_percent': k_percent,
                'd_percent': d_percent,
                'momentum_5': momentum_5,
                'momentum_10': momentum_10,
                'trend_strength': trend_strength,
                
                # 변동성/리스크
                'max_drawdown_15': max_drawdown_15,
                'volatility_15': volatility_15,
                'atr_15': atr_15,
                'slope_15': slope_15,
                'hl_score': hl_score,
                'vwap_gap': vwap_gap,
                
                # 시간대별
                'is_opening': is_opening,
                'is_lunch': is_lunch,
                'is_closing': is_closing,
                'time_minutes': time_minutes,
                
                # 시장상황
                'kospi_return_15': kospi_return_15,
                'kospi_volatility_15': kospi_volatility_15,
                
                # Feature 조합
                'price_volume_momentum': price_volume_momentum,
                'rsi_volume_interaction': rsi_volume_interaction,
                'bb_volume_interaction': bb_volume_interaction,
                
                'day_data': day_df
            })
        
        return pd.DataFrame(features)
    
    def apply_filters(self, features_df):
        """패턴 필터 적용 (대폭 개선: 새로운 feature 활용, 동적 파라미터)"""
        filtered = features_df.copy()
        
        print(f"초기 데이터: {len(filtered)} 건")
        
        # === 1. 기본 필터 (기존) ===
        # Opening Spike 제외
        spike_mask = filtered['r_1'] >= self.parameters['theta_spike']
        filtered = filtered[~spike_mask]
        print(f"Opening Spike 제외: {spike_mask.sum()} 건")
        
        # 첫 1분 최소 수익률 확인
        min_r1_mask = filtered['r_1'] >= self.parameters['theta_spike_low']
        filtered = filtered[min_r1_mask]
        print(f"최소 수익률 필터: {len(filtered)} 건")
        
        # 15분 누적 수익률 확인
        r15_mask = filtered['cum_r_15'] >= self.parameters['theta_15m']
        filtered = filtered[r15_mask]
        print(f"15분 누적 수익률 필터: {len(filtered)} 건")
        
        # 저점 하락폭 확인
        pull_mask = filtered['max_drawdown_15'] >= -self.parameters['theta_pull']
        filtered = filtered[pull_mask]
        print(f"저점 하락폭 필터: {len(filtered)} 건")
        
        # === 2. 거래량 필터 (동적 파라미터) ===
        # 거래량 비율 확인
        if 'theta_vol' in self.parameters:
            vol_mask = filtered['v_ratio_15'] >= self.parameters['theta_vol']
            filtered = filtered[vol_mask]
            print(f"거래량 비율 필터: {len(filtered)} 건")
        
        # 추가 거래량 필터
        if 'volume_ratio_min' in self.parameters:
            vol_ratio_mask = filtered['v_ratio_15'] >= self.parameters['volume_ratio_min']
            filtered = filtered[vol_ratio_mask]
            print(f"거래량 비율 최소값 필터: {len(filtered)} 건")
        
        # === 3. 기술적 지표 필터 (동적 파라미터) ===
        # RSI 필터 (동적 범위)
        if 'rsi_min' in self.parameters and 'rsi_max' in self.parameters:
            rsi_mask = (filtered['rsi_15'] >= self.parameters['rsi_min']) & (filtered['rsi_15'] <= self.parameters['rsi_max'])
            filtered = filtered[rsi_mask]
            print(f"RSI 필터 ({self.parameters['rsi_min']}-{self.parameters['rsi_max']}): {len(filtered)} 건")
        else:
            # 기본 RSI 필터
            rsi_mask = (filtered['rsi_15'] >= 20) & (filtered['rsi_15'] <= 80)
            filtered = filtered[rsi_mask]
            print(f"RSI 필터 (20-80): {len(filtered)} 건")
        
        # 볼린저 밴드 위치 필터 (동적 범위)
        if 'bb_position_min' in self.parameters and 'bb_position_max' in self.parameters:
            bb_mask = (filtered['bb_position'] >= self.parameters['bb_position_min']) & (filtered['bb_position'] <= self.parameters['bb_position_max'])
            filtered = filtered[bb_mask]
            print(f"볼린저 밴드 위치 필터 ({self.parameters['bb_position_min']:.2f}-{self.parameters['bb_position_max']:.2f}): {len(filtered)} 건")
        else:
            # 기본 볼린저 밴드 필터
            bb_mask = (filtered['bb_position'] >= 0.1) & (filtered['bb_position'] <= 0.9)
            filtered = filtered[bb_mask]
            print(f"볼린저 밴드 위치 필터: {len(filtered)} 건")
        
        # 모멘텀 필터 (동적 임계값)
        if 'momentum_threshold' in self.parameters:
            momentum_mask = filtered['momentum_5'] > self.parameters['momentum_threshold']
            filtered = filtered[momentum_mask]
            print(f"모멘텀 필터 (>{self.parameters['momentum_threshold']:.3f}): {len(filtered)} 건")
        else:
            # 기본 모멘텀 필터
            momentum_mask = filtered['momentum_5'] > 0
            filtered = filtered[momentum_mask]
            print(f"모멘텀 필터 (양의 모멘텀): {len(filtered)} 건")
        
        # === 4. 시간대별 필터 (가중치 적용) ===
        # 장 시작 시간대 우선 (가중치 적용)
        if 'time_opening_weight' in self.parameters:
            opening_weight = self.parameters['time_opening_weight']
            # 시간대별 가중치를 점수로 변환
            time_score = (filtered['is_opening'] * opening_weight + 
                         filtered['is_lunch'] * self.parameters.get('time_lunch_weight', 0.5) +
                         filtered['is_closing'] * self.parameters.get('time_closing_weight', 0.5))
            time_mask = time_score > 0.5  # 가중 평균이 0.5 이상
            filtered = filtered[time_mask]
            print(f"시간대별 가중치 필터: {len(filtered)} 건")
        else:
            # 기본 시간대 필터
            opening_mask = filtered['is_opening'] == 1
            filtered = filtered[opening_mask]
            print(f"장 시작 시간대 필터: {len(filtered)} 건")
        
        # === 5. 시장상황 필터 (동적 파라미터) ===
        # KOSPI 수익률 필터
        if 'kospi_return_min' in self.parameters:
            kospi_mask = filtered['kospi_return_15'] > self.parameters['kospi_return_min']
            filtered = filtered[kospi_mask]
            print(f"KOSPI 수익률 필터 (>{self.parameters['kospi_return_min']:.3f}): {len(filtered)} 건")
        else:
            # 기본 KOSPI 필터
            kospi_mask = filtered['kospi_return_15'] > -0.02
            filtered = filtered[kospi_mask]
            print(f"KOSPI 시장상황 필터: {len(filtered)} 건")
        
        # KOSPI 변동성 필터
        if 'kospi_volatility_max' in self.parameters:
            kospi_vol_mask = filtered['kospi_volatility_15'] < self.parameters['kospi_volatility_max']
            filtered = filtered[kospi_vol_mask]
            print(f"KOSPI 변동성 필터 (<{self.parameters['kospi_volatility_max']:.3f}): {len(filtered)} 건")
        
        # === 6. Feature 조합 필터 (동적 파라미터) ===
        # 가격-거래량 모멘텀 조합
        if 'price_volume_momentum_threshold' in self.parameters:
            pv_momentum_mask = filtered['price_volume_momentum'] > self.parameters['price_volume_momentum_threshold']
            filtered = filtered[pv_momentum_mask]
            print(f"가격-거래량 모멘텀 필터 (>{self.parameters['price_volume_momentum_threshold']:.3f}): {len(filtered)} 건")
        else:
            # 기본 가격-거래량 모멘텀 필터
            pv_momentum_mask = filtered['price_volume_momentum'] > 0
            filtered = filtered[pv_momentum_mask]
            print(f"가격-거래량 모멘텀 필터: {len(filtered)} 건")
        
        # RSI-거래량 상호작용
        if 'rsi_volume_interaction_threshold' in self.parameters:
            rsi_vol_mask = filtered['rsi_volume_interaction'] > self.parameters['rsi_volume_interaction_threshold']
            filtered = filtered[rsi_vol_mask]
            print(f"RSI-거래량 상호작용 필터 (>{self.parameters['rsi_volume_interaction_threshold']}): {len(filtered)} 건")
        else:
            # 기본 RSI-거래량 상호작용 필터
            rsi_vol_mask = filtered['rsi_volume_interaction'] > 0
            filtered = filtered[rsi_vol_mask]
            print(f"RSI-거래량 상호작용 필터: {len(filtered)} 건")
        
        # 볼린저 밴드-거래량 상호작용
        if 'bb_volume_interaction_threshold' in self.parameters:
            bb_vol_mask = filtered['bb_volume_interaction'] > self.parameters['bb_volume_interaction_threshold']
            filtered = filtered[bb_vol_mask]
            print(f"볼린저 밴드-거래량 상호작용 필터 (>{self.parameters['bb_volume_interaction_threshold']:.3f}): {len(filtered)} 건")
        
        return filtered
    
    def find_orb_entries(self, filtered_df):
        """ORB 진입점 찾기"""
        entries = []
        
        for _, row in filtered_df.iterrows():
            day_df = row['day_data']
            
            # ORB High 계산 (첫 5분 고가)
            orb_high = day_df.iloc[:self.parameters['orb_delay_min']]['high'].max()
            
            # ORB 돌파 지점 찾기 (5분 이후 ~ 30분)
            entry_window = day_df.iloc[self.parameters['orb_delay_min']:self.parameters['orb_max_min']]
            
            for idx, bar in entry_window.iterrows():
                if bar['high'] > orb_high:
                    # 진입가: 다음 봉 시가 (보수적)
                    entry_price = bar['open']
                    entry_time = bar['datetime']
                    
                    # TP/SL 계산
                    tp_price = entry_price * (1 + self.parameters['tp_pct'])
                    sl_price = entry_price * (1 - self.parameters['sl_pct'])
                    
                    entries.append({
                        'stock_code': row['stock_code'],
                        'date': row['date'],
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price,
                        'orb_high': orb_high,
                        'features': row
                    })
                    break  # 첫 번째 돌파에서 진입
        
        return pd.DataFrame(entries)
    
    def simulate_trades(self, entries_df):
        """거래 시뮬레이션 (수수료/슬리피지 반영)"""
        trades = []
        commission = 0.001  # 0.1%
        slippage = 0.001    # 0.1%
        
        for _, entry in entries_df.iterrows():
            stock_code = entry['stock_code']
            date = entry['date']
            entry_time = entry['entry_time']
            
            # 해당 일의 데이터 가져오기
            day_data = entry['features']['day_data']
            
            # 진입 시점 이후 데이터
            entry_idx = day_data[day_data['datetime'] >= entry_time].index[0]
            remaining_data = day_data.loc[entry_idx:]
            
            # 진입/청산가에 슬리피지 반영
            entry_price = entry['entry_price'] * (1 + slippage)
            tp_price = entry['tp_price'] * (1 - slippage)
            sl_price = entry['sl_price'] * (1 - slippage)
            
            # 청산 조건 확인
            exit_price = None
            exit_time = None
            exit_reason = None
            
            for _, bar in remaining_data.iterrows():
                # TP 도달
                if bar['high'] >= tp_price:
                    exit_price = tp_price
                    exit_time = bar['datetime']
                    exit_reason = 'TP'
                    break
                
                # SL 도달
                if bar['low'] <= sl_price:
                    exit_price = sl_price
                    exit_time = bar['datetime']
                    exit_reason = 'SL'
                    break
            
            # 종가 청산 (TP/SL 미도달)
            if exit_price is None:
                exit_price = remaining_data.iloc[-1]['close'] * (1 - slippage)
                exit_time = remaining_data.iloc[-1]['datetime']
                exit_reason = 'Close'
            
            # 수수료 반영 (진입+청산)
            pnl = (exit_price / entry_price) - 1 - 2 * commission
            
            trades.append({
                'stock_code': stock_code,
                'date': date,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': exit_reason
            })
        
        return pd.DataFrame(trades)
    
    def calculate_metrics(self, trades_df):
        """성과 지표 계산"""
        if len(trades_df) == 0:
            return {}
        
        metrics = {
            'total_trades': len(trades_df),
            'win_rate': (trades_df['pnl'] > 0).mean(),
            'avg_return': trades_df['pnl'].mean(),
            'std_return': trades_df['pnl'].std(),
            'sharpe_ratio': trades_df['pnl'].mean() / trades_df['pnl'].std() if trades_df['pnl'].std() > 0 else 0,
            'max_drawdown': trades_df['pnl'].cumsum().min(),
            'total_return': trades_df['pnl'].sum(),
            'expectancy': trades_df['pnl'].mean() * len(trades_df),
            'best_trade': trades_df['pnl'].max(),
            'worst_trade': trades_df['pnl'].min()
        }
        
        return metrics
    
    def run_backtest(self, stock_codes=None, date_range=None, verbose=True):
        """전체 백테스트 실행 (기간 필터링 지원)"""
        if verbose:
            print("=== 완만 상승 패턴 백테스트 시작 ===")
        # 1. 데이터 로드
        data = self.load_data(stock_codes, date_range=date_range)
        # 2. Feature 계산
        if verbose:
            print("\nFeature 계산 중...")
        features = self.calculate_features(data)
        if verbose:
            print(f"Feature 계산 완료: {len(features)} 일")
        # 3. 필터 적용
        if verbose:
            print("\n패턴 필터 적용 중...")
        filtered = self.apply_filters(features)
        if verbose:
            print(f"필터 적용 완료: {len(filtered)} 건")
        # 4. ORB 진입점 찾기
        if verbose:
            print("\nORB 진입점 탐색 중...")
        entries = self.find_orb_entries(filtered)
        if verbose:
            print(f"진입점 발견: {len(entries)} 건")
        # 5. 거래 시뮬레이션
        if verbose:
            print("\n거래 시뮬레이션 중...")
        trades = self.simulate_trades(entries)
        if verbose:
            print(f"거래 완료: {len(trades)} 건")
        # 6. 성과 지표 계산
        if verbose:
            print("\n성과 지표 계산 중...")
        metrics = self.calculate_metrics(trades)
        # 7. 결과 출력
        if verbose:
            self.print_results(metrics, trades)
        # 8. 신호/거래 수 적으면 경고
        if len(trades) < 30:
            print("[경고] 거래 수가 30건 미만입니다. 파라미터/기간/종목 수를 확장하거나 조건을 완화하세요.")
        return metrics, trades
    
    def run_train_test_split(self, stock_codes=None, train_range=None, test_range=None):
        """train/test 분리 백테스트 (과적합 방지)"""
        print("\n=== [Train/Test Split] 백테스트 ===")
        print(f"Train: {train_range}, Test: {test_range}")
        print("[Train] 최적화 구간 결과:")
        train_metrics, train_trades = self.run_backtest(stock_codes, train_range)
        print("\n[Test] 검증 구간 결과:")
        test_metrics, test_trades = self.run_backtest(stock_codes, test_range)
        print("\n[비교] Train/Test 주요 지표:")
        for k in ['total_trades','win_rate','avg_return','sharpe_ratio','total_return']:
            tval = train_metrics.get(k, None)
            sval = test_metrics.get(k, None)
            print(f"{k}: Train={tval}, Test={sval}")
        return (train_metrics, train_trades), (test_metrics, test_trades)
    
    def print_results(self, metrics, trades_df):
        """결과 출력"""
        print("\n" + "="*50)
        print("백테스트 결과")
        print("="*50)
        
        if len(trades_df) == 0:
            print("거래가 없습니다.")
            return
        
        print(f"총 거래 수: {metrics['total_trades']}")
        print(f"승률: {metrics['win_rate']:.2%}")
        print(f"평균 수익률: {metrics['avg_return']:.2%}")
        print(f"총 수익률: {metrics['total_return']:.2%}")
        print(f"샤프 비율: {metrics['sharpe_ratio']:.3f}")
        print(f"최대 손실: {metrics['max_drawdown']:.2%}")
        print(f"기대값: {metrics['expectancy']:.2%}")
        print(f"최고 수익: {metrics['best_trade']:.2%}")
        print(f"최저 수익: {metrics['worst_trade']:.2%}")
        
        # 월별 성과
        if len(trades_df) > 0:
            trades_df['date'] = pd.to_datetime(trades_df['date'])
            trades_df['month'] = trades_df['date'].dt.to_period('M')
            monthly_perf = trades_df.groupby('month')['pnl'].sum()
            print(f"\n월별 성과:")
            for month, pnl in monthly_perf.items():
                print(f"  {month}: {pnl:.2%}")

def main():
    """메인 실행 함수"""
    # 백테스트 인스턴스 생성
    backtest = GradualRiseBacktest()
    # 파라미터 설정 (필요시 조정)
    # backtest.parameters.update({...})  # config에서 조정
    # 백테스트 실행
    metrics, trades = backtest.run_backtest()
    # 결과 저장
    if len(trades) > 0:
        trades.to_csv('gradual_rise_trades.csv', index=False)
        print(f"\n거래 내역이 'gradual_rise_trades.csv'에 저장되었습니다.")
    # train/test 분리 예시 실행 (주석 해제시 동작)
    # backtest.run_train_test_split(stock_codes=None, train_range=TRAIN_RANGE, test_range=TEST_RANGE)

if __name__ == "__main__":
    main() 