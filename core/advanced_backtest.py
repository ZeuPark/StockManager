import pandas as pd
import numpy as np
import glob
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# ============================================================================
# 1. 고급 설정 (Advanced Configuration)
# ============================================================================

CONFIG = {
    # 자본 및 거래 설정
    'initial_capital': 10000000,  # 1천만원 시작 자본
    'max_positions': 3,           # 최대 보유 종목 수
    'position_size': 2000000,     # 종목당 기본 투자 금액
    
    # 거래 비용 (현실성 강화)
    'transaction_fee': 0.00015,   # 매수/매도 수수료 (0.015%)
    'transaction_tax': 0.002,     # 매도세 (0.2%)
    'slippage': 0.001,           # 슬리피지 (0.1%)
    
    # 매수 조건
    'scan_start_time': '09:00',   # 매수 스캔 시작 시간
    'scan_end_time': '15:00',     # 매수 스캔 종료 시간
    
    # 동적 손절/익절 (ATR 기반)
    'atr_multiplier_stop': 1.5,   # ATR의 1.5배만큼 아래를 손절가로 (완화)
    'atr_multiplier_profit': 3.0, # ATR의 3배만큼 위를 익절가로 (완화)
    'fixed_stop_loss': -3.0,      # 고정 손절 비율 (강화)
    'fixed_take_profit': 8.0,     # 고정 익절 비율 (현실적 조정)
    'trailing_stop': 7.0,         # 트레일링 스탑 비율
    'max_hold_days': 14,          # 최대 보유 기간 (일)
    
    # 자금 관리 (Kelly Criterion 기반)
    'risk_per_trade': 0.01,       # 총자본의 1%만 리스크 (강화)
    'max_risk_per_position': 0.03, # 종목당 최대 리스크 3% (강화)
    
    # 전략 설정
    'strategy1_threshold': 50,     # 전략1 매수 기준 점수
    'strategy2_threshold': 0.6,   # 전략2 매수 기준 점수
    'strategy3_threshold': 0.6,   # 전략3 매수 기준 점수
    
    # 백테스트 설정
    'start_date': '2025-01-01',   # 백테스트 시작일
    'end_date': '2025-07-14',     # 백테스트 종료일
    'max_stocks_to_load': 50,     # 테스트용 종목 수 제한
}

# ============================================================================
# 2. 기술적 지표 계산 함수들
# ============================================================================

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ATR (Average True Range) 계산
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index) 계산
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD 계산
    """
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

# ============================================================================
# 3. 데이터 준비 (고급 지표 포함)
# ============================================================================

def load_market_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    코스피 지수 데이터 로드 (시장 국면 필터용)
    """
    print("시장 데이터 로딩 시작...")
    
    try:
        market_file = 'data_collection/market_data/KOSPI_daily.csv'
        if os.path.exists(market_file):
            df = pd.read_csv(market_file)
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # 기술적 지표 계산
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            df['atr'] = calculate_atr(df)
            df['rsi'] = calculate_rsi(df)
            
            print(f"✓ 시장 데이터 로드 완료: {len(df)}일")
            return df
        else:
            print(f"⚠️ 시장 데이터 파일이 없습니다: {market_file}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"✗ 시장 데이터 로드 실패: {e}")
        return pd.DataFrame()

def load_and_prepare_data(data_folder: str = 'minute_data', max_stocks: Optional[int] = None) -> Dict[str, pd.DataFrame]:
    """
    지정된 폴더의 모든 CSV 파일을 로드하고 고급 지표를 계산
    """
    print("데이터 로딩 시작...")
    
    csv_files = glob.glob(os.path.join(data_folder, '*_1min.csv'))
    if max_stocks:
        random.shuffle(csv_files)
        csv_files = csv_files[:max_stocks]
    
    print(f"총 {len(csv_files)}개 종목 데이터 로딩 중...")
    
    stock_data = {}
    for file_path in csv_files:
        try:
            stock_code = os.path.basename(file_path).split('_')[0]
            
            df = pd.read_csv(file_path)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')
            
            # 기본 지표 계산
            df['volume_ratio'] = df['volume_ratio'].fillna(0)
            df['ma5'] = df['ma5'].fillna(0)
            df['ma20'] = df['ma20'].fillna(0)
            df['ma60'] = df['close'].rolling(window=60).mean().fillna(0)
            
            # 고급 지표 계산
            df['atr'] = calculate_atr(df, period=14).fillna(0)
            df['rsi'] = calculate_rsi(df, period=14).fillna(50)
            macd_line, signal_line, histogram = calculate_macd(df)
            df['macd'] = macd_line.fillna(0)
            df['macd_signal'] = signal_line.fillna(0)
            df['macd_histogram'] = histogram.fillna(0)
            
            # 볼린저 밴드
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # 가격 변화율
            df['price_change_pct'] = df['close'].pct_change() * 100
            df['volume_increase'] = df['volume'].pct_change() * 100
            
            stock_data[stock_code] = df
            print(f"✓ {stock_code}: {len(df)}건 로드 완료")
            
        except Exception as e:
            print(f"✗ {file_path} 로드 실패: {e}")
            continue
    
    print(f"데이터 로딩 완료: {len(stock_data)}개 종목")
    return stock_data

# ============================================================================
# 4. 고급 전략 함수들
# ============================================================================

def check_market_regime(market_data: pd.DataFrame, current_date: datetime.date) -> bool:
    """
    시장 국면 필터: 코스피 지수가 20일선 위에 있는지 확인
    """
    if market_data.empty:
        return True
    
    date_data = market_data[market_data['date'].dt.date == current_date]
    
    if date_data.empty:
        date_data = market_data[market_data['date'].dt.date < current_date]
        if date_data.empty:
            return True
    
    if not date_data.empty:
        latest_data = date_data.iloc[-1]
        kospi_close = latest_data['close']
        kospi_ma20 = latest_data['ma20']
        
        return kospi_close > kospi_ma20
    
    return True

def check_strategy_1(df_slice: pd.DataFrame) -> Optional[float]:
    """
    전략1: EDA 기반 거래량 급증 전략 (개선)
    """
    if len(df_slice) < 20:
        return None

    current = df_slice.iloc[-1]
    current_date = current['datetime'].date()
    
    nine_am_data = df_slice[df_slice['datetime'].dt.time == datetime.strptime('09:00', '%H:%M').time()]
    if nine_am_data.empty:
        return None

    nine = nine_am_data.iloc[0]
    
    # 조건 1: 시초가 갭
    prev_date = current_date - timedelta(days=1)
    prev_close_data = df_slice[
        (df_slice['datetime'].dt.date == prev_date) &
        (df_slice['datetime'].dt.time == datetime.strptime('15:30', '%H:%M').time())
    ]
    
    if not prev_close_data.empty:
        prev_close = prev_close_data.iloc[0]['close']
        open_gap = (nine['open'] - prev_close) / prev_close * 100
        if not (open_gap > 0.2):
            return None
    
    # 조건 2: 거래량
    if not (nine.get('volume', 0) > 30000):
        return None

    # 조건 3: 20일선 아래에서 시작
    if not (nine.get('close', 0) < nine.get('ma20', float('inf'))):
        return None

    # 추가 조건: RSI 과매도에서 반등
    if current['rsi'] > 30 and current['rsi'] < 70:
        return 100

    return None

def check_strategy_2(df_slice: pd.DataFrame) -> Optional[float]:
    """
    전략2: 강화된 추세 추종 전략 (모든 조건 만족 필요)
    """
    if len(df_slice) < 20:  # 최소 데이터 요구사항 복원
        return None
    
    current = df_slice.iloc[-1]
    ma5 = current['ma5']
    ma20 = current['ma20']
    ma60 = current['ma60']
    price = current['close']
    ma20_distance = abs(price - ma20) / (ma20 + 1e-9) * 100
    volume_ratio = current.get('volume_ratio', 0)
    
    # --- 강화된 조건 (모든 조건 만족 필요) ---
    conditions = [
        ma5 > ma20 * 1.002,          # 5일선이 20일선보다 0.2% 이상 높음
        ma20 > ma60 * 1.001,         # 20일선이 60일선보다 0.1% 이상 높음 (정배열)
        ma20_distance < 8.0,         # 20일선 8% 이내 (적절한 눌림목)
        volume_ratio > 120           # 거래량 평균 대비 120% 이상
    ]
    
    scores = [0.3, 0.3, 0.2, 0.2]  # 각 조건별 가중치
    total_score = sum(scores[i] for i, condition in enumerate(conditions) if condition)
    
    # 모든 조건을 만족하고, 점수가 0.8점 이상일 때만 진입
    if all(conditions) and total_score >= 0.8:
        return total_score
    return None

def check_strategy_3(df_slice: pd.DataFrame) -> Optional[float]:
    """
    전략3: 강화된 돌파 전략 (모든 조건 만족 필요)
    """
    if len(df_slice) < 20:  # 최소 데이터 요구사항 복원
        return None
    
    current = df_slice.iloc[-1]
    bb_upper = current.get('bb_upper', 0)
    bb_lower = current.get('bb_lower', 0)
    price_change = current.get('price_change_pct', 0)
    volume_ratio = current.get('volume_ratio', 0)
    macd = current.get('macd', 0)
    macd_signal = current.get('macd_signal', 0)
    rsi = current.get('rsi', 50)
    
    # --- 강화된 돌파 조건 (모든 조건 만족 필요) ---
    conditions = [
        current['close'] > bb_upper * 1.001,                # 볼린저밴드 상단을 0.1% 이상 돌파
        price_change > 1.5,                                 # 전일 대비 1.5% 이상 상승
        volume_ratio > 150,                                 # 거래량 평균 대비 150% 이상
        macd > macd_signal * 1.001,                        # MACD가 시그널선을 0.1% 이상 상회
        rsi > 30 and rsi < 70                              # RSI가 적정 범위 (과매수/과매도 제외)
    ]
    
    scores = [0.25, 0.25, 0.2, 0.15, 0.15]  # 각 조건별 가중치
    total_score = sum(scores[i] for i, condition in enumerate(conditions) if condition)
    
    # 모든 조건을 만족하고, 점수가 0.8점 이상일 때만 진입
    if all(conditions) and total_score >= 0.8:
        return total_score
    return None

# 개선된 스윙 트레이딩 전략 추가
def improved_swing_strategy(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """
    수익성 분석 결과 기반 개선된 스윙 트레이딩 전략
    
    핵심 개선사항:
    1. 이동평균 정배열 필터 강화 (59.5% 고수익 종목이 정배열)
    2. 변동성 기반 필터링 (0.29% 이하 선호)
    3. RSI 중립 구간 활용 (40-70)
    4. 거래량 비율 기반 확인
    """
    # 컬럼명 확인 및 안전 처리
    if 'close' not in df.columns:
        print(f"경고: 'close' 컬럼이 없습니다. 사용 가능한 컬럼: {list(df.columns)}")
        return df
    
    # 기술적 지표 계산
    df = df.copy()
    
    # 이동평균선 (이미 있는 경우 재계산하지 않음)
    if 'ma5' not in df.columns:
        df['ma5'] = df['close'].rolling(window=5).mean()
    if 'ma20' not in df.columns:
        df['ma20'] = df['close'].rolling(window=20).mean()
    if 'ma60' not in df.columns:
        df['ma60'] = df['close'].rolling(window=60).mean()
    
    # 변동성
    if 'volatility' not in df.columns:
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean() * 100
    
    # RSI
    if 'rsi' not in df.columns:
        df['rsi'] = calculate_rsi(df['close'], 14)
    
    # ATR
    df['atr'] = calculate_atr(df, 14)
    
    # 거래량 비율
    df['volume_ma20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma20']
    df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
    
    # 이동평균 정배열 점수 계산 (0-3점)
    df['ma_alignment'] = 0
    full_alignment = (df['ma5'] > df['ma20']) & (df['ma20'] > df['ma60'])
    partial_alignment = (df['ma5'] > df['ma20']) & ~full_alignment
    long_alignment = (df['ma20'] > df['ma60']) & ~full_alignment & ~partial_alignment
    
    df.loc[full_alignment, 'ma_alignment'] = 3
    df.loc[partial_alignment, 'ma_alignment'] = 2
    df.loc[long_alignment, 'ma_alignment'] = 1
    
    # 매수 신호 생성
    df['buy_signal'] = False
    
    # 핵심 필터 (수익성 분석 결과 기반)
    ma_alignment_ok = df['ma_alignment'] >= params.get('ma_alignment_min', 1.8)
    volatility_ok = df['volatility'] <= params.get('volatility_max', 0.35)
    rsi_ok = (df['rsi'] >= params.get('rsi_min', 40)) & (df['rsi'] <= params.get('rsi_max', 70))
    volume_ok = df['volume_ratio'] >= params.get('volume_ratio_min', 1.0)
    
    # 추가 조건
    price_above_ma = df['close'] > df['ma20']
    volume_increase = df['volume'] > df['volume_ma20']
    
    # 모든 조건 만족 시 매수
    df['buy_signal'] = (ma_alignment_ok & volatility_ok & rsi_ok & 
                       volume_ok & price_above_ma & volume_increase)
    
    # 매도 신호 생성
    df['sell_signal'] = False
    
    # 익절/손절 조건
    df['return_pct'] = df['close'].pct_change() * 100
    df['cumulative_return'] = df['return_pct'].cumsum()
    
    # 익절 조건
    take_profit = params.get('take_profit_pct', 15.0)
    stop_loss = params.get('stop_loss_pct', 5.0)
    
    # 정배열 깨짐 조건
    alignment_broken = df['ma_alignment'] < 1
    
    # RSI 과매수 조건
    rsi_overbought = df['rsi'] > 80
    
    # 매도 신호
    df['sell_signal'] = (df['cumulative_return'] >= take_profit) | \
                       (df['cumulative_return'] <= -stop_loss) | \
                       alignment_broken | \
                       rsi_overbought
    
    return df

# ============================================================================
# 5. 고급 백테스팅 엔진
# ============================================================================

def calculate_position_size(current_price: float, stop_loss_price: float, cash: float) -> Tuple[int, float]:
    """
    Kelly Criterion 기반 포지션 사이징
    """
    risk_per_share = abs(current_price - stop_loss_price)
    if risk_per_share == 0:
        return 0, 0
    
    # 총자본 대비 리스크 금액
    risk_amount = cash * CONFIG['risk_per_trade']
    
    # 최대 투자 가능 주식 수
    max_shares = int(risk_amount / risk_per_share)
    
    # 기본 투자 금액으로 제한
    base_shares = int(CONFIG['position_size'] / current_price)
    
    # 더 작은 값 선택
    shares = min(max_shares, base_shares)
    
    # 실제 투자 금액
    position_value = shares * current_price
    
    return shares, position_value

def run_advanced_backtest(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Tuple[Dict, List[Dict]]:
    """
    고급 백테스팅 엔진 (거래 비용, 동적 손절/익절, 개선된 자금 관리 포함)
    """
    print("고급 백테스팅 시작...")
    
    cash = CONFIG['initial_capital']
    portfolio = {}
    trades = []
    previous_date = None
    
    # 전체 시간 범위 생성
    all_dates = set()
    for df in stock_data.values():
        all_dates.update(df['datetime'].dt.date)
    
    all_dates = sorted(list(all_dates))
    start_date = datetime.strptime(CONFIG['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(CONFIG['end_date'], '%Y-%m-%d').date()
    
    test_dates = [d for d in all_dates if start_date <= d <= end_date]
    
    print(f"백테스트 기간: {test_dates[0]} ~ {test_dates[-1]} ({len(test_dates)}일)")
    
    for current_date in test_dates:
        progress = (test_dates.index(current_date)+1) / len(test_dates) * 100
        if test_dates.index(current_date) % 10 == 0:
            print(f"진행 중: {current_date} ({test_dates.index(current_date)+1}/{len(test_dates)}) - {progress:.1f}%")
        
        # 시장 국면 필터
        is_good_market = check_market_regime(market_data, current_date)
        if not is_good_market:
            print(f"  시장 상황 나쁨: {current_date} 매매 중단")
            continue
        
        if portfolio and test_dates.index(current_date) % 10 == 0:
            print(f"  보유: {list(portfolio.keys())}")
        elif not portfolio and test_dates.index(current_date) % 10 == 0:
            print(f"  보유: 없음")
        
        if previous_date != current_date:
            daily_start_cash = cash
            previous_date = current_date
        
        # 해당 날짜의 데이터 수집
        minute_data = {}
        for stock_code, df in stock_data.items():
            day_data = df[df['datetime'].dt.date == current_date]
            if len(day_data) > 0:
                minute_data[stock_code] = day_data.sort_values('datetime')
        
        if not minute_data:
            continue
        
        all_times = set()
        for df in minute_data.values():
            all_times.update(df['datetime'].dt.time)
        
        all_times = sorted(list(all_times))
        scan_interval = 30
        filtered_times = [t for i, t in enumerate(all_times) if i % scan_interval == 0]
        
        for current_time in filtered_times:
            current_datetime = datetime.combine(current_date, current_time)
            
            # 매도 체크 (동적 손절/익절)
            stocks_to_sell = []
            for stock_code, position in portfolio.items():
                if stock_code not in minute_data:
                    continue
                
                current_data = minute_data[stock_code]
                current_price_data = current_data[current_data['datetime'] == current_datetime]
                
                if len(current_price_data) == 0:
                    continue
                
                current_price = current_price_data.iloc[0]['close']
                buy_price = position['buy_price']
                buy_time = position['buy_time']
                
                # 슬리피지 적용된 매도 가격
                sell_price = current_price * (1 - CONFIG['slippage'])
                
                if current_price > position['peak_price']:
                    position['peak_price'] = current_price
                
                profit_pct = (sell_price - buy_price) / buy_price * 100
                hold_days = (current_datetime - buy_time).days
                
                # 동적 손절/익절 (ATR 기반)
                atr_value = current_price_data.iloc[0]['atr']
                if atr_value > 0:
                    dynamic_stop_loss = buy_price - (atr_value * CONFIG['atr_multiplier_stop'])
                    dynamic_take_profit = buy_price + (atr_value * CONFIG['atr_multiplier_profit'])
                else:
                    # ATR이 없으면 고정 비율 사용
                    dynamic_stop_loss = buy_price * (1 + CONFIG['fixed_stop_loss'] / 100)
                    dynamic_take_profit = buy_price * (1 + CONFIG['fixed_take_profit'] / 100)
                
                # 트레일링 스탑
                trailing_stop_price = position['peak_price'] * (1 - CONFIG['trailing_stop'] / 100)
                
                sell_reason = None
                if sell_price <= dynamic_stop_loss:
                    sell_reason = '동적손절'
                elif sell_price >= dynamic_take_profit:
                    sell_reason = '동적익절'
                elif sell_price <= trailing_stop_price and profit_pct > 0:
                    sell_reason = '트레일링스탑'
                elif hold_days >= CONFIG['max_hold_days']:
                    sell_reason = '보유기간초과'
                
                if sell_reason:
                    stocks_to_sell.append((stock_code, sell_reason, sell_price, profit_pct))
            
            # 매도 실행 (거래 비용 적용)
            for stock_code, reason, sell_price, profit_pct in stocks_to_sell:
                position = portfolio[stock_code]
                shares = position['shares']
                buy_price = position['buy_price']
                
                # 거래 비용 차감
                proceeds = shares * sell_price * (1 - CONFIG['transaction_fee'] - CONFIG['transaction_tax'])
                cash += proceeds
                
                trades.append({
                    'datetime': current_datetime,
                    'stock_code': stock_code,
                    'action': 'SELL',
                    'reason': reason,
                    'shares': shares,
                    'price': sell_price,
                    'profit_pct': profit_pct,
                    'cash': cash
                })
                
                del portfolio[stock_code]
                
                if abs(profit_pct) > 2.0:
                    print(f"  매도: {stock_code} {reason} ({profit_pct:.2f}%)")
            
            # 매수 체크
            scan_start = datetime.strptime(CONFIG['scan_start_time'], '%H:%M').time()
            scan_end = datetime.strptime(CONFIG['scan_end_time'], '%H:%M').time()
            
            if scan_start <= current_time <= scan_end and len(portfolio) < CONFIG['max_positions']:
                buy_signals = []
                
                for stock_code, df in minute_data.items():
                    if stock_code in portfolio:
                        continue
                    
                    # 룩어헤드 편향 방지: 현재 시점 이전 데이터만 사용
                    df_slice = df[df['datetime'] < current_datetime]
                    if len(df_slice) < 20:
                        continue
                    
                    strategy1_score = check_strategy_1(df_slice)
                    strategy2_score = check_strategy_2(df_slice)
                    strategy3_score = check_strategy_3(df_slice)
                    
                    if strategy1_score is not None:
                        buy_signals.append({
                            'stock_code': stock_code,
                            'strategy': 'Strategy1',
                            'score': strategy1_score,
                            'priority': 1
                        })
                    elif strategy2_score is not None:
                        buy_signals.append({
                            'stock_code': stock_code,
                            'strategy': 'Strategy2',
                            'score': strategy2_score,
                            'priority': 2
                        })
                    elif strategy3_score is not None:
                        buy_signals.append({
                            'stock_code': stock_code,
                            'strategy': 'Strategy3',
                            'score': strategy3_score,
                            'priority': 3
                        })
                
                buy_signals.sort(key=lambda x: (x['priority'], -x['score']))
                
                for signal in buy_signals:
                    if len(portfolio) >= CONFIG['max_positions']:
                        break
                    
                    stock_code = signal['stock_code']
                    current_price_data = minute_data[stock_code][minute_data[stock_code]['datetime'] == current_datetime]
                    
                    if len(current_price_data) == 0:
                        continue
                    
                    current_price = current_price_data.iloc[0]['close']
                    
                    # 슬리피지 적용된 매수 가격
                    buy_price_with_slippage = current_price * (1 + CONFIG['slippage'])
                    
                    # 동적 손절가 계산
                    atr_value = current_price_data.iloc[0]['atr']
                    if atr_value > 0:
                        stop_loss_price = buy_price_with_slippage - (atr_value * CONFIG['atr_multiplier_stop'])
                    else:
                        stop_loss_price = buy_price_with_slippage * (1 + CONFIG['fixed_stop_loss'] / 100)
                    
                    # Kelly Criterion 기반 포지션 사이징
                    shares, position_value = calculate_position_size(buy_price_with_slippage, stop_loss_price, cash)
                    
                    if shares > 0:
                        # 거래 비용 포함한 총 비용
                        total_cost = position_value * (1 + CONFIG['transaction_fee'])
                        
                        if cash >= total_cost:
                            cash -= total_cost
                            
                            portfolio[stock_code] = {
                                'shares': shares,
                                'buy_price': buy_price_with_slippage,
                                'buy_time': current_datetime,
                                'peak_price': buy_price_with_slippage,
                                'stop_loss_price': stop_loss_price
                            }
                            
                            trades.append({
                                'datetime': current_datetime,
                                'stock_code': stock_code,
                                'action': 'BUY',
                                'reason': signal['strategy'],
                                'shares': shares,
                                'price': buy_price_with_slippage,
                                'score': signal['score'],
                                'cash': cash
                            })
                            
                            print(f"  매수: {stock_code} {signal['strategy']} ({position_value:,}원)")
        
        # 장 마감 시 미청산 포지션 강제 매도
        market_close_time = datetime.strptime('15:30', '%H:%M').time()
        market_close_datetime = datetime.combine(current_date, market_close_time)
        
        for stock_code, position in list(portfolio.items()):
            if stock_code in minute_data:
                close_data = minute_data[stock_code][minute_data[stock_code]['datetime'].dt.time == market_close_time]
                if len(close_data) > 0:
                    close_price = close_data.iloc[0]['close']
                    sell_price = close_price * (1 - CONFIG['slippage'])
                    shares = position['shares']
                    buy_price = position['buy_price']
                    profit_pct = (sell_price - buy_price) / buy_price * 100
                    
                    proceeds = shares * sell_price * (1 - CONFIG['transaction_fee'] - CONFIG['transaction_tax'])
                    cash += proceeds
                    
                    trades.append({
                        'datetime': market_close_datetime,
                        'stock_code': stock_code,
                        'action': 'SELL',
                        'reason': '장마감',
                        'shares': shares,
                        'price': sell_price,
                        'profit_pct': profit_pct,
                        'cash': cash
                    })
                    
                    del portfolio[stock_code]
    
    # 최종 결과 계산
    final_cash = cash
    for stock_code, position in portfolio.items():
        if stock_code in stock_data:
            last_price = stock_data[stock_code]['close'].iloc[-1]
            sell_price = last_price * (1 - CONFIG['slippage'])
            proceeds = position['shares'] * sell_price * (1 - CONFIG['transaction_fee'] - CONFIG['transaction_tax'])
            final_cash += proceeds
    
    results = {
        'initial_capital': CONFIG['initial_capital'],
        'final_capital': final_cash,
        'total_return': (final_cash - CONFIG['initial_capital']) / CONFIG['initial_capital'] * 100,
        'total_trades': len(trades),
        'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
        'sell_trades': len([t for t in trades if t['action'] == 'SELL']),
        'trades': trades
    }
    
    return results, trades

# ============================================================================
# 6. 고급 결과 분석
# ============================================================================

def analyze_advanced_results(results: Dict, trades: List[Dict]) -> None:
    """
    고급 백테스트 결과 분석 및 출력
    """
    print("\n" + "="*60)
    print("고급 백테스트 결과 분석")
    print("="*60)
    
    initial_capital = results['initial_capital']
    final_capital = results['final_capital']
    total_return = results['total_return']
    
    print(f"초기 자본: {initial_capital:,}원")
    print(f"최종 자본: {int(final_capital):,}원")
    print(f"총 수익률: {total_return:.2f}%")
    print(f"총 수익금: {int(final_capital - initial_capital):,}원")
    
    # 거래 통계
    total_trades = results['total_trades']
    buy_trades = results['buy_trades']
    sell_trades = results['sell_trades']
    
    print(f"\n거래 통계:")
    print(f"총 거래 횟수: {total_trades}회")
    print(f"매수 거래: {buy_trades}회")
    print(f"매도 거래: {sell_trades}회")
    
    # 수익 거래 분석
    profitable_trades = [t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) > 0]
    loss_trades = [t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) <= 0]
    
    if sell_trades > 0:
        win_rate = len(profitable_trades) / sell_trades * 100
        avg_profit = np.mean([t['profit_pct'] for t in profitable_trades]) if profitable_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in loss_trades]) if loss_trades else 0
        
        print(f"승률: {win_rate:.1f}%")
        print(f"평균 수익: {avg_profit:.2f}%")
        print(f"평균 손실: {avg_loss:.2f}%")
        
        # 손익비
        if avg_loss != 0:
            profit_loss_ratio = abs(avg_profit / avg_loss)
            print(f"손익비: {profit_loss_ratio:.2f}")
    
    # MDD 계산
    capital_history = [initial_capital]
    for trade in trades:
        if trade['action'] == 'BUY':
            capital_history.append(trade['cash'])
        else:
            capital_history.append(trade['cash'])
    
    peak = capital_history[0]
    mdd = 0
    for capital in capital_history:
        if capital > peak:
            peak = capital
        drawdown = (peak - capital) / peak * 100
        if drawdown > mdd:
            mdd = drawdown
    
    print(f"최대 낙폭 (MDD): {mdd:.2f}%")
    
    # 샤프 비율 계산 (간단한 버전)
    if len(capital_history) > 1:
        returns = []
        for i in range(1, len(capital_history)):
            daily_return = (capital_history[i] - capital_history[i-1]) / capital_history[i-1]
            returns.append(daily_return)
        
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            if std_return > 0:
                sharpe_ratio = avg_return / std_return * np.sqrt(252)  # 연율화
                print(f"샤프 비율: {sharpe_ratio:.2f}")
    
    # 전략별 성과
    strategy1_trades = [t for t in trades if t['action'] == 'BUY' and t.get('reason') == 'Strategy1']
    strategy2_trades = [t for t in trades if t['action'] == 'BUY' and t.get('reason') == 'Strategy2']
    strategy3_trades = [t for t in trades if t['action'] == 'BUY' and t.get('reason') == 'Strategy3']
    
    print(f"\n전략별 성과:")
    print(f"전략1 매수: {len(strategy1_trades)}회")
    print(f"전략2 매수: {len(strategy2_trades)}회")
    print(f"전략3 매수: {len(strategy3_trades)}회")
    
    # 매도 이유별 분석
    sell_reasons = {}
    for trade in trades:
        if trade['action'] == 'SELL':
            reason = trade.get('reason', 'Unknown')
            if reason not in sell_reasons:
                sell_reasons[reason] = []
            sell_reasons[reason].append(trade['profit_pct'])
    
    print(f"\n매도 이유별 분석:")
    for reason, profits in sell_reasons.items():
        avg_profit = np.mean(profits)
        count = len(profits)
        print(f"  {reason}: {count}회, 평균 {avg_profit:.2f}%")

# ============================================================================
# 7. 파라미터 최적화 기능
# ============================================================================

def optimize_parameters(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Dict:
    """
    파라미터 최적화: 단일 파라미터 테스트 (데이터 캐싱 적용)
    """
    print("\n" + "="*60)
    print("파라미터 최적화 시작 (데이터 캐싱 적용)")
    print("="*60)
    
    # 최적화할 파라미터 범위 정의 (단일 파라미터 테스트)
    param_ranges = {
        'atr_multiplier_stop': [1.5, 2.0, 2.5, 3.0]
    }
    
    best_result = None
    best_params = None
    best_score = float('-inf')
    
    total_combinations = 1
    for param, values in param_ranges.items():
        total_combinations *= len(values)
    
    print(f"총 {total_combinations}개 조합 테스트 중...")
    
    combination_count = 0
    
    # 단일 파라미터 테스트
    for atr_stop in param_ranges['atr_multiplier_stop']:
        combination_count += 1
        
        # CONFIG 임시 수정
        original_config = CONFIG.copy()
        CONFIG['atr_multiplier_stop'] = atr_stop
                        
        try:
            # 백테스트 실행
            results, trades = run_advanced_backtest(stock_data, market_data)
            
            # 성과 점수 계산 (수익률 + 샤프비율 + 승률의 조합)
            total_return = results['total_return']
            total_trades = results['total_trades']
            
            if total_trades > 0:
                # 승률 계산
                sell_trades = len([t for t in trades if t['action'] == 'SELL'])
                profitable_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) > 0])
                win_rate = profitable_trades / sell_trades if sell_trades > 0 else 0
                
                # 샤프 비율 계산 (간단한 버전)
                capital_history = [CONFIG['initial_capital']]
                for trade in trades:
                    capital_history.append(trade['cash'])
                
                returns = []
                for i in range(1, len(capital_history)):
                    daily_return = (capital_history[i] - capital_history[i-1]) / capital_history[i-1]
                    returns.append(daily_return)
                
                sharpe_ratio = 0
                if returns:
                    avg_return = np.mean(returns)
                    std_return = np.std(returns)
                    if std_return > 0:
                        sharpe_ratio = avg_return / std_return * np.sqrt(252)
                
                # 종합 점수 (수익률 50% + 샤프비율 30% + 승률 20%)
                score = (total_return * 0.5) + (sharpe_ratio * 10 * 0.3) + (win_rate * 0.2)
                
                if score > best_score:
                    best_score = score
                    best_result = results
                    best_params = {
                        'atr_multiplier_stop': atr_stop
                    }
                
                print(f"ATR Stop {atr_stop}: 점수 {score:.2f} (수익률: {total_return:.2f}%, 승률: {win_rate:.1f}%)")
    
        except Exception as e:
            print(f"ATR Stop {atr_stop} 실행 중 오류: {e}")
            continue
        
        finally:
            # CONFIG 복원
            CONFIG.update(original_config)
    
    print(f"\n최적화 완료!")
    print(f"최고 점수: {best_score:.2f}")
    print(f"최적 파라미터:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    
    return best_params, best_result

def run_improved_swing_backtest(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Tuple[Dict, List[Dict]]:
    """
    개선된 스윙 트레이딩 전략으로 백테스트 실행
    """
    print("개선된 스윙 트레이딩 전략 백테스트 시작...")
    
    # 개선된 파라미터 (수익성 분석 결과 기반)
    improved_params = {
        'ma_alignment_min': 3.0,      # 정배열 조건 극단 강화 (3점만)
        'volatility_max': 0.2,       # 변동성 제한 극단 강화 (0.2 이하만)
        'rsi_min': 50,               # RSI 하한 극단 강화 (50 이상)
        'rsi_max': 60,               # RSI 상한 극단 강화 (60 이하)
        'volume_ratio_min': 1.5,     # 거래량 조건 극단 강화 (1.5 이상)
        'take_profit_pct': 10.0,     # 익절 목표 단축 (10%)
        'stop_loss_pct': 3.0,        # 손절 범위 극단 축소 (3%)
        'atr_multiplier_stop': 1.0,  # ATR 손절 배수 극단 축소 (1.0)
    }
    
    print("📊 개선된 파라미터:")
    for key, value in improved_params.items():
        print(f"  • {key}: {value}")
    
    # 개선된 전략으로 백테스트 실행
    cash = CONFIG['initial_capital']
    portfolio = {}
    trades = []
    
    # 전체 시간 범위 생성
    all_dates = set()
    for df in stock_data.values():
        all_dates.update(df['datetime'].dt.date)
    
    all_dates = sorted(list(all_dates))
    start_date = datetime.strptime(CONFIG['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(CONFIG['end_date'], '%Y-%m-%d').date()
    
    test_dates = [d for d in all_dates if start_date <= d <= end_date]
    
    print(f"백테스트 기간: {test_dates[0]} ~ {test_dates[-1]} ({len(test_dates)}일)")
    
    for current_date in test_dates:
        progress = (test_dates.index(current_date)+1) / len(test_dates) * 100
        if test_dates.index(current_date) % 10 == 0:
            print(f"진행 중: {current_date} ({test_dates.index(current_date)+1}/{len(test_dates)}) - {progress:.1f}%")
        
        # 해당 날짜의 데이터 수집
        minute_data = {}
        for stock_code, df in stock_data.items():
            day_data = df[df['datetime'].dt.date == current_date]
            if len(day_data) > 0:
                minute_data[stock_code] = day_data.sort_values('datetime')
        
        if not minute_data:
            continue
        
        all_times = set()
        for df in minute_data.values():
            all_times.update(df['datetime'].dt.time)
        
        all_times = sorted(list(all_times))
        scan_interval = 10  # 10분 간격으로 스캔 (매분 → 10분)
        filtered_times = [t for i, t in enumerate(all_times) if i % scan_interval == 0]
        
        for current_time in filtered_times:
            current_datetime = datetime.combine(current_date, current_time)
            
            # 매도 체크
            stocks_to_sell = []
            for stock_code, position in portfolio.items():
                if stock_code not in minute_data:
                    continue
                
                current_data = minute_data[stock_code]
                current_price_data = current_data[current_data['datetime'] == current_datetime]
                
                if len(current_price_data) == 0:
                    continue
                
                current_price = current_price_data.iloc[0]['close']
                buy_price = position['buy_price']
                
                # 개선된 전략으로 매도 신호 확인
                df_slice = current_data[current_data['datetime'] <= current_datetime]
                if len(df_slice) > 0:
                    # 개선된 전략 적용
                    df_with_signals = improved_swing_strategy(df_slice, improved_params)
                    current_signal = df_with_signals.iloc[-1]
                    
                    if current_signal['sell_signal']:
                        sell_price = current_price * (1 - CONFIG['slippage'])
                        profit_pct = (sell_price - buy_price) / buy_price * 100
                        stocks_to_sell.append((stock_code, '개선된전략', sell_price, profit_pct))
            
            # 매도 실행
            for stock_code, reason, sell_price, profit_pct in stocks_to_sell:
                position = portfolio[stock_code]
                shares = position['shares']
                
                proceeds = shares * sell_price * (1 - CONFIG['transaction_fee'] - CONFIG['transaction_tax'])
                cash += proceeds
                
                trades.append({
                    'datetime': current_datetime,
                    'stock_code': stock_code,
                    'action': 'SELL',
                    'reason': reason,
                    'shares': shares,
                    'price': sell_price,
                    'profit_pct': profit_pct,
                    'cash': cash
                })
                
                del portfolio[stock_code]
                
                if abs(profit_pct) > 2.0:
                    print(f"  매도: {stock_code} {reason} ({profit_pct:.2f}%)")
            
            # 매수 체크
            if len(portfolio) < CONFIG['max_positions']:
                buy_signals = []
                
                for stock_code, df in minute_data.items():
                    if stock_code in portfolio:
                        continue
                    
                    # 개선된 전략으로 매수 신호 확인
                    df_slice = df[df['datetime'] <= current_datetime]
                    if len(df_slice) > 0:
                        df_with_signals = improved_swing_strategy(df_slice, improved_params)
                        current_signal = df_with_signals.iloc[-1]
                        
                        if current_signal['buy_signal']:
                            buy_signals.append({
                                'stock_code': stock_code,
                                'strategy': 'Improved_Swing',
                                'score': current_signal['ma_alignment'],
                                'priority': 1
                            })
                
                buy_signals.sort(key=lambda x: -x['score'])
                
                for signal in buy_signals:
                    if len(portfolio) >= CONFIG['max_positions']:
                        break
                    
                    stock_code = signal['stock_code']
                    current_price_data = minute_data[stock_code][minute_data[stock_code]['datetime'] == current_datetime]
                    
                    if len(current_price_data) == 0:
                        continue
                    
                    current_price = current_price_data.iloc[0]['close']
                    buy_price_with_slippage = current_price * (1 + CONFIG['slippage'])
                    
                    # 포지션 사이징
                    shares = int(CONFIG['position_size'] / buy_price_with_slippage)
                    
                    if shares > 0:
                        total_cost = shares * buy_price_with_slippage * (1 + CONFIG['transaction_fee'])
                        
                        if cash >= total_cost:
                            cash -= total_cost
                            
                            portfolio[stock_code] = {
                                'shares': shares,
                                'buy_price': buy_price_with_slippage,
                                'buy_time': current_datetime,
                                'peak_price': buy_price_with_slippage
                            }
                            
                            trades.append({
                                'datetime': current_datetime,
                                'stock_code': stock_code,
                                'action': 'BUY',
                                'reason': signal['strategy'],
                                'shares': shares,
                                'price': buy_price_with_slippage,
                                'score': signal['score'],
                                'cash': cash
                            })
                            
                            print(f"  매수: {stock_code} {signal['strategy']} (정배열점수: {signal['score']})")
    
    # 최종 결과 계산
    final_cash = cash
    for stock_code, position in portfolio.items():
        if stock_code in stock_data:
            last_price = stock_data[stock_code]['close'].iloc[-1]
            sell_price = last_price * (1 - CONFIG['slippage'])
            proceeds = position['shares'] * sell_price * (1 - CONFIG['transaction_fee'] - CONFIG['transaction_tax'])
            final_cash += proceeds
    
    results = {
        'initial_capital': CONFIG['initial_capital'],
        'final_capital': final_cash,
        'total_return': (final_cash - CONFIG['initial_capital']) / CONFIG['initial_capital'] * 100,
        'total_trades': len(trades),
        'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
        'sell_trades': len([t for t in trades if t['action'] == 'SELL']),
        'trades': trades
    }
    
    return results, trades

def run_optimized_backtest(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Tuple[Dict, List[Dict]]:
    """
    최적화된 파라미터로 백테스트 실행
    """
    print("최적화된 파라미터로 백테스트 실행...")
    
    # 파라미터 최적화 실행 (최적 파라미터와 결과를 함께 받음)
    best_params, best_result = optimize_parameters(stock_data, market_data)
    
    # 최적 파라미터로 CONFIG 업데이트
    CONFIG.update(best_params)
    
    print(f"\n최적화된 설정:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    
    # 최적화 과정에서 이미 얻은 결과를 반환
    return best_result, best_result['trades']

# ============================================================================
# 8. 고급 최적화 알고리즘
# ============================================================================

def random_search_optimization(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None, n_iterations: int = 50) -> Dict:
    """
    랜덤 서치 최적화: 지정된 횟수만큼 랜덤한 파라미터 조합을 테스트
    """
    print("\n" + "="*60)
    print(f"랜덤 서치 최적화 시작 ({n_iterations}회 반복)")
    print("="*60)
    
    # 파라미터 범위 정의
    param_ranges = {
        'atr_multiplier_stop': (1.0, 4.0),
        'atr_multiplier_profit': (2.0, 8.0),
        'trailing_stop': (3.0, 15.0),
        'max_hold_days': (7, 30),
        'risk_per_trade': (0.01, 0.08)
    }
    
    best_result = None
    best_params = None
    best_score = float('-inf')
    
    print(f"총 {n_iterations}회 랜덤 테스트 중...")
    
    for i in range(n_iterations):
        # 랜덤 파라미터 생성
        random_params = {}
        for param, (min_val, max_val) in param_ranges.items():
            if isinstance(min_val, int):
                random_params[param] = random.randint(min_val, max_val)
            else:
                random_params[param] = round(random.uniform(min_val, max_val), 2)
        
        # CONFIG 임시 수정
        original_config = CONFIG.copy()
        CONFIG.update(random_params)
        
        try:
            # 백테스트 실행
            results, trades = run_advanced_backtest(stock_data, market_data)
            
            # 성과 점수 계산
            total_return = results['total_return']
            total_trades = results['total_trades']
            
            if total_trades > 0:
                # 승률 계산
                sell_trades = len([t for t in trades if t['action'] == 'SELL'])
                profitable_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) > 0])
                win_rate = profitable_trades / sell_trades if sell_trades > 0 else 0
                
                # 샤프 비율 계산
                capital_history = [CONFIG['initial_capital']]
                for trade in trades:
                    capital_history.append(trade['cash'])
                
                returns = []
                for j in range(1, len(capital_history)):
                    daily_return = (capital_history[j] - capital_history[j-1]) / capital_history[j-1]
                    returns.append(daily_return)
                
                sharpe_ratio = 0
                if returns:
                    avg_return = np.mean(returns)
                    std_return = np.std(returns)
                    if std_return > 0:
                        sharpe_ratio = avg_return / std_return * np.sqrt(252)
                
                # 종합 점수
                score = (total_return * 0.5) + (sharpe_ratio * 10 * 0.3) + (win_rate * 0.2)
                
                if score > best_score:
                    best_score = score
                    best_result = results
                    best_params = random_params.copy()
                
                if (i + 1) % 10 == 0:
                    print(f"진행률: {i+1}/{n_iterations} - 현재 최고점수: {best_score:.2f}")
                    print(f"  최고 파라미터: {best_params}")
        
        except Exception as e:
            print(f"반복 {i+1} 실행 중 오류: {e}")
            continue
        
        finally:
            # CONFIG 복원
            CONFIG.update(original_config)
    
    print(f"\n랜덤 서치 최적화 완료!")
    print(f"최고 점수: {best_score:.2f}")
    print(f"최적 파라미터:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    
    return best_params, best_result

def stepwise_optimization(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Dict:
    """
    단계별 최적화: 파라미터를 하나씩 순차적으로 최적화
    """
    print("\n" + "="*60)
    print("단계별 최적화 시작")
    print("="*60)
    
    # 최적화할 파라미터 순서 (중요도 순)
    param_sequence = [
        ('atr_multiplier_stop', [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
        ('atr_multiplier_profit', [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
        ('trailing_stop', [3.0, 5.0, 7.0, 10.0, 12.0, 15.0]),
        ('max_hold_days', [7, 10, 14, 21, 28, 30]),
        ('risk_per_trade', [0.01, 0.02, 0.03, 0.05, 0.08])
    ]
    
    best_params = {}
    
    for param_name, param_values in param_sequence:
        print(f"\n{param_name} 최적화 중...")
        
        best_value = None
        best_score = float('-inf')
        best_result = None
        
        for value in param_values:
            # 현재까지의 최적 파라미터 + 새로운 값으로 테스트
            test_params = best_params.copy()
            test_params[param_name] = value
            
            # CONFIG 임시 수정
            original_config = CONFIG.copy()
            CONFIG.update(test_params)
            
            try:
                # 백테스트 실행
                results, trades = run_advanced_backtest(stock_data, market_data)
                
                # 성과 점수 계산
                total_return = results['total_return']
                total_trades = results['total_trades']
                
                if total_trades > 0:
                    # 승률 계산
                    sell_trades = len([t for t in trades if t['action'] == 'SELL'])
                    profitable_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) > 0])
                    win_rate = profitable_trades / sell_trades if sell_trades > 0 else 0
                    
                    # 샤프 비율 계산
                    capital_history = [CONFIG['initial_capital']]
                    for trade in trades:
                        capital_history.append(trade['cash'])
                    
                    returns = []
                    for j in range(1, len(capital_history)):
                        daily_return = (capital_history[j] - capital_history[j-1]) / capital_history[j-1]
                        returns.append(daily_return)
                    
                    sharpe_ratio = 0
                    if returns:
                        avg_return = np.mean(returns)
                        std_return = np.std(returns)
                        if std_return > 0:
                            sharpe_ratio = avg_return / std_return * np.sqrt(252)
                    
                    # 종합 점수
                    score = (total_return * 0.5) + (sharpe_ratio * 10 * 0.3) + (win_rate * 0.2)
                    
                    print(f"  {param_name}={value}: 점수 {score:.2f} (수익률: {total_return:.2f}%, 승률: {win_rate:.1f}%)")
                    
                    if score > best_score:
                        best_score = score
                        best_value = value
                        best_result = results
            
            except Exception as e:
                print(f"  {param_name}={value} 실행 중 오류: {e}")
                continue
            
            finally:
                # CONFIG 복원
                CONFIG.update(original_config)
        
        # 최적 값 저장
        best_params[param_name] = best_value
        print(f"✓ {param_name} 최적값: {best_value} (점수: {best_score:.2f})")
    
    print(f"\n단계별 최적화 완료!")
    print(f"최종 파라미터:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    
    return best_params, best_result

def coarse_fine_optimization(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Dict:
    """
    Coarse-Fine 최적화: 넓은 범위 → 좁은 범위 순차 탐색
    """
    print("\n" + "="*60)
    print("Coarse-Fine 최적화 시작")
    print("="*60)
    
    # 1단계: Coarse Search (넓은 범위)
    print("1단계: Coarse Search (넓은 범위 탐색)")
    coarse_ranges = {
        'atr_multiplier_stop': [1.0, 2.0, 3.0, 4.0],
        'atr_multiplier_profit': [2.0, 4.0, 6.0, 8.0],
        'trailing_stop': [5.0, 10.0, 15.0],
        'max_hold_days': [10, 20, 30],
        'risk_per_trade': [0.02, 0.05, 0.08]
    }
    
    best_coarse_params = {}
    
    for param_name, param_values in coarse_ranges.items():
        print(f"\n{param_name} Coarse Search...")
        
        best_value = None
        best_score = float('-inf')
        
        for value in param_values:
            # 단일 파라미터 테스트
            test_params = best_coarse_params.copy()
            test_params[param_name] = value
            
            # CONFIG 임시 수정
            original_config = CONFIG.copy()
            CONFIG.update(test_params)
            
            try:
                results, trades = run_advanced_backtest(stock_data, market_data)
                
                total_return = results['total_return']
                total_trades = results['total_trades']
                
                if total_trades > 0:
                    sell_trades = len([t for t in trades if t['action'] == 'SELL'])
                    profitable_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) > 0])
                    win_rate = profitable_trades / sell_trades if sell_trades > 0 else 0
                    
                    score = total_return * 0.7 + win_rate * 0.3  # 간단한 점수
                    
                    print(f"  {param_name}={value}: 점수 {score:.2f} (수익률: {total_return:.2f}%)")
                    
                    if score > best_score:
                        best_score = score
                        best_value = value
            
            except Exception as e:
                print(f"  {param_name}={value} 실행 중 오류: {e}")
                continue
            
            finally:
                CONFIG.update(original_config)
        
        best_coarse_params[param_name] = best_value
        print(f"✓ {param_name} Coarse 최적값: {best_value}")
    
    # 2단계: Fine Search (좁은 범위)
    print(f"\n2단계: Fine Search (좁은 범위 탐색)")
    print(f"Coarse 결과: {best_coarse_params}")
    
    fine_ranges = {}
    for param_name, best_value in best_coarse_params.items():
        if param_name == 'atr_multiplier_stop':
            fine_ranges[param_name] = [max(1.0, best_value - 0.5), best_value - 0.25, best_value, best_value + 0.25, min(5.0, best_value + 0.5)]
        elif param_name == 'atr_multiplier_profit':
            fine_ranges[param_name] = [max(1.0, best_value - 1.0), best_value - 0.5, best_value, best_value + 0.5, min(10.0, best_value + 1.0)]
        elif param_name == 'trailing_stop':
            fine_ranges[param_name] = [max(2.0, best_value - 2.0), best_value - 1.0, best_value, best_value + 1.0, min(20.0, best_value + 2.0)]
        elif param_name == 'max_hold_days':
            fine_ranges[param_name] = [max(5, best_value - 5), best_value - 2, best_value, best_value + 2, min(40, best_value + 5)]
        elif param_name == 'risk_per_trade':
            fine_ranges[param_name] = [max(0.005, best_value - 0.01), best_value - 0.005, best_value, best_value + 0.005, min(0.1, best_value + 0.01)]
    
    best_fine_params = {}
    
    for param_name, param_values in fine_ranges.items():
        print(f"\n{param_name} Fine Search...")
        
        best_value = None
        best_score = float('-inf')
        best_result = None
        
        for value in param_values:
            test_params = best_fine_params.copy()
            test_params[param_name] = value
            
            original_config = CONFIG.copy()
            CONFIG.update(test_params)
            
            try:
                results, trades = run_advanced_backtest(stock_data, market_data)
                
                total_return = results['total_return']
                total_trades = results['total_trades']
                
                if total_trades > 0:
                    sell_trades = len([t for t in trades if t['action'] == 'SELL'])
                    profitable_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('profit_pct', 0) > 0])
                    win_rate = profitable_trades / sell_trades if sell_trades > 0 else 0
                    
                    # 샤프 비율 계산
                    capital_history = [CONFIG['initial_capital']]
                    for trade in trades:
                        capital_history.append(trade['cash'])
                    
                    returns = []
                    for j in range(1, len(capital_history)):
                        daily_return = (capital_history[j] - capital_history[j-1]) / capital_history[j-1]
                        returns.append(daily_return)
                    
                    sharpe_ratio = 0
                    if returns:
                        avg_return = np.mean(returns)
                        std_return = np.std(returns)
                        if std_return > 0:
                            sharpe_ratio = avg_return / std_return * np.sqrt(252)
                    
                    score = (total_return * 0.5) + (sharpe_ratio * 10 * 0.3) + (win_rate * 0.2)
                    
                    print(f"  {param_name}={value:.3f}: 점수 {score:.2f} (수익률: {total_return:.2f}%, 승률: {win_rate:.1f}%)")
                    
                    if score > best_score:
                        best_score = score
                        best_value = value
                        best_result = results
            
            except Exception as e:
                print(f"  {param_name}={value} 실행 중 오류: {e}")
                continue
            
            finally:
                CONFIG.update(original_config)
        
        best_fine_params[param_name] = best_value
        print(f"✓ {param_name} Fine 최적값: {best_value:.3f}")
    
    print(f"\nCoarse-Fine 최적화 완료!")
    print(f"최종 파라미터:")
    for param, value in best_fine_params.items():
        print(f"  {param}: {value}")
    
    return best_fine_params, best_result

def show_menu():
    """
    메뉴 표시 및 선택
    """
    print("\n" + "="*60)
    print("고급 백테스트 시스템")
    print("="*60)
    print("1. 일반 모드 (최적화 없음) - 빠른 테스트")
    print("2. 개선된 스윙 트레이딩 전략 - 수익성 분석 기반")
    print("3. 랜덤 서치 최적화 - 30회 랜덤 조합")
    print("4. 단계별 최적화 - 파라미터 순차 최적화")
    print("5. Coarse-Fine 최적화 - 넓은 범위 → 좁은 범위")
    print("6. 설정 보기")
    print("0. 종료")
    print("="*60)
    
    while True:
        try:
            choice = input("선택하세요 (0-6): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6']:
                return choice
            else:
                print("잘못된 선택입니다. 0-6 사이의 숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            exit()
        except:
            print("잘못된 입력입니다. 다시 시도해주세요.")

def show_config():
    """
    현재 설정 출력
    """
    print("\n" + "="*60)
    print("현재 설정")
    print("="*60)
    for key, value in CONFIG.items():
        print(f"  {key}: {value}")
    print("="*60)

def run_backtest_with_mode(mode: str, stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None):
    """
    선택된 모드로 백테스트 실행
    """
    if mode == '1':
        print("\n일반 모드로 실행...")
        return run_advanced_backtest(stock_data, market_data)
    
    elif mode == '2':
        print("\n개선된 스윙 트레이딩 전략으로 실행...")
        return run_improved_swing_backtest(stock_data, market_data)
    
    elif mode == '3':
        print("\n랜덤 서치 최적화 모드로 실행...")
        best_params, best_result = random_search_optimization(stock_data, market_data, n_iterations=30)
        return best_result, best_result['trades']
    
    elif mode == '4':
        print("\n단계별 최적화 모드로 실행...")
        best_params, best_result = stepwise_optimization(stock_data, market_data)
        return best_result, best_result['trades']
    
    elif mode == '5':
        print("\nCoarse-Fine 최적화 모드로 실행...")
        best_params, best_result = coarse_fine_optimization(stock_data, market_data)
        return best_result, best_result['trades']
    
    else:
        print("알 수 없는 모드입니다.")
        return None, None

# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    print("고급 백테스트 시스템 시작")
    print("="*60)
    
    # 1. 데이터 로드 (한 번만 실행하여 캐싱)
    print("데이터 로딩 중...")
    stock_data = load_and_prepare_data(
        data_folder='minute_data',
        max_stocks=20  # 종목 수 제한 (50 → 20)
    )
    
    if not stock_data:
        print("데이터가 없습니다. 먼저 데이터를 수집해주세요.")
        exit()
    
    # 2. 시장 데이터 로드
    print("시장 데이터 로딩 중...")
    market_data = load_market_data(CONFIG['start_date'], CONFIG['end_date'])
    
    print("데이터 로딩 완료!")
    
    # 3. 메뉴 시스템
    while True:
        choice = show_menu()
        
        if choice == '0':
            print("프로그램을 종료합니다.")
            break
        
        elif choice == '6':
            show_config()
            continue
        
        else:
            # 백테스트 실행
            results, trades = run_backtest_with_mode(choice, stock_data, market_data)
            
            if results and trades:
                # 결과 분석
                analyze_advanced_results(results, trades)
                
                # 계속할지 묻기
                while True:
                    try:
                        continue_choice = input("\n다른 모드로 다시 테스트하시겠습니까? (y/n): ").strip().lower()
                        if continue_choice in ['y', 'yes', '예']:
                            break
                        elif continue_choice in ['n', 'no', '아니오']:
                            print("프로그램을 종료합니다.")
                            exit()
                        else:
                            print("y 또는 n을 입력해주세요.")
                    except KeyboardInterrupt:
                        print("\n프로그램을 종료합니다.")
                        exit()
                    except:
                        print("잘못된 입력입니다. y 또는 n을 입력해주세요.")
            else:
                print("백테스트 실행 중 오류가 발생했습니다.")
                continue 