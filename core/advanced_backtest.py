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
    파라미터 최적화: 여러 파라미터 조합을 테스트하여 최적의 설정을 찾음
    """
    print("\n" + "="*60)
    print("파라미터 최적화 시작")
    print("="*60)
    
    # 최적화할 파라미터 범위 정의
    param_ranges = {
        'atr_multiplier_stop': [1.0, 1.5, 2.0, 2.5, 3.0],
        'atr_multiplier_profit': [2.0, 3.0, 4.0, 5.0, 6.0],
        'trailing_stop': [3.0, 5.0, 7.0, 10.0, 15.0],
        'max_hold_days': [7, 10, 14, 21, 30],
        'risk_per_trade': [0.01, 0.02, 0.03, 0.05, 0.08]
    }
    
    best_result = None
    best_params = None
    best_score = float('-inf')
    
    total_combinations = 1
    for param, values in param_ranges.items():
        total_combinations *= len(values)
    
    print(f"총 {total_combinations}개 조합 테스트 중...")
    
    combination_count = 0
    
    # 모든 조합 테스트
    for atr_stop in param_ranges['atr_multiplier_stop']:
        for atr_profit in param_ranges['atr_multiplier_profit']:
            for trailing in param_ranges['trailing_stop']:
                for hold_days in param_ranges['max_hold_days']:
                    for risk in param_ranges['risk_per_trade']:
                        combination_count += 1
                        
                        # CONFIG 임시 수정
                        original_config = CONFIG.copy()
                        CONFIG['atr_multiplier_stop'] = atr_stop
                        CONFIG['atr_multiplier_profit'] = atr_profit
                        CONFIG['trailing_stop'] = trailing
                        CONFIG['max_hold_days'] = hold_days
                        CONFIG['risk_per_trade'] = risk
                        
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
                                        'atr_multiplier_stop': atr_stop,
                                        'atr_multiplier_profit': atr_profit,
                                        'trailing_stop': trailing,
                                        'max_hold_days': hold_days,
                                        'risk_per_trade': risk
                                    }
                                
                                if combination_count % 10 == 0:
                                    print(f"진행률: {combination_count}/{total_combinations} - 현재 최고점수: {best_score:.2f}")
                        
                        except Exception as e:
                            print(f"조합 {combination_count} 실행 중 오류: {e}")
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

def run_optimized_backtest(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Tuple[Dict, List[Dict]]:
    """
    최적화된 파라미터로 백테스트 실행
    """
    print("최적화된 파라미터로 백테스트 실행...")
    
    # 파라미터 최적화 실행
    best_params, _ = optimize_parameters(stock_data, market_data)
    
    # 최적 파라미터로 CONFIG 업데이트
    CONFIG.update(best_params)
    
    print(f"\n최적화된 설정으로 백테스트 실행:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    
    # 최적화된 파라미터로 백테스트 실행
    results, trades = run_advanced_backtest(stock_data, market_data)
    
    return results, trades

# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    print("고급 백테스트 시스템 시작")
    print("="*60)
    
    # 설정 출력
    print("설정:")
    for key, value in CONFIG.items():
        print(f"  {key}: {value}")
    print()
    
    # 1. 데이터 로드
    stock_data = load_and_prepare_data(
        data_folder='minute_data',
        max_stocks=CONFIG['max_stocks_to_load']
    )
    
    if not stock_data:
        print("데이터가 없습니다. 먼저 데이터를 수집해주세요.")
        exit()
    
    # 2. 시장 데이터 로드
    market_data = load_market_data(CONFIG['start_date'], CONFIG['end_date'])
    
    # 3. 최적화된 백테스트 실행 (기본값)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--no-optimize':
        print("일반 모드로 실행...")
        results, trades = run_advanced_backtest(stock_data, market_data)
    else:
        print("파라미터 최적화 모드로 실행...")
        results, trades = run_optimized_backtest(stock_data, market_data)
    
    # 4. 고급 결과 분석
    analyze_advanced_results(results, trades)
    
    print("\n고급 백테스트 완료!") 