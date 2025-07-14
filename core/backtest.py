import pandas as pd
import numpy as np
import glob
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# ============================================================================
# 1. 주요 설정 (Configuration)
# ============================================================================

CONFIG = {
    # 자본 및 거래 설정
    'initial_capital': 10000000,  # 1천만원 시작 자본
    'max_positions': 2,           # 최대 보유 종목 수 (리스크 관리 강화)
    'position_size': 1500000,     # 종목당 투자 금액 (리스크 관리 강화)
    
    # 매수 조건 (스윙 트레이딩은 시간 제한 없음)
    'scan_start_time': '09:00',   # 매수 스캔 시작 시간
    'scan_end_time': '15:00',     # 매수 스캔 종료 시간 (전일 거래 시간)
    
    # 매도 조건 (스윙 트레이딩에 맞게 조정)
    'stop_loss': -5.0,            # 손절 비율 (-5%로 강화 - 리스크 관리)
    'take_profit': 15.0,          # 익절 비율 (+15%로 조정 - 현실적 목표)
    'trailing_stop': 7.0,         # 트레일링 스탑 비율 (고점 대비 -7%)
    'max_hold_days': 10,          # 최대 보유 기간 (일) - 단축
    'max_daily_loss': None,       # 일일 최대 손실 제한 없음 (스윙 트레이딩은 일별 손실 제한 불필요)
    
    # 전략 설정 (스윙 트레이딩에 맞게 조정)
    'strategy1_threshold': 50,     # 전략1 매수 기준 점수 (강화)
    'strategy2_threshold': 0.7,   # 전략2 매수 기준 점수 (강화)
    
    # 백테스트 설정
    'start_date': '2025-01-01',   # 백테스트 시작일 (더 긴 기간)
    'end_date': '2025-07-14',     # 백테스트 종료일 (1년)
    'max_stocks_to_load': 50,     # 테스트용 종목 수 제한 (품질 우선)
}

# ============================================================================
# 2. 데이터 준비 (load_and_prepare_data, load_market_data)
# ============================================================================

def load_market_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    코스피 지수 데이터 로드 (시장 국면 필터용)
    """
    print("시장 데이터 로딩 시작...")
    
    try:
        # 코스피 지수 CSV 파일 로드 (예: KOSPI_daily.csv)
        market_file = 'data_collection/market_data/KOSPI_daily.csv'
        if os.path.exists(market_file):
            df = pd.read_csv(market_file)
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # 20일 이동평균선 계산
            df['ma20'] = df['close'].rolling(window=20).mean()
            
            print(f"✓ 시장 데이터 로드 완료: {len(df)}일")
            return df
        else:
            print(f"⚠️ 시장 데이터 파일이 없습니다: {market_file}")
            print("시장 국면 필터를 사용하지 않습니다.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"✗ 시장 데이터 로드 실패: {e}")
        print("시장 국면 필터를 사용하지 않습니다.")
        return pd.DataFrame()

def load_and_prepare_data(data_folder: str = 'minute_data', max_stocks: Optional[int] = None) -> Dict[str, pd.DataFrame]:
    """
    지정된 폴더의 모든 CSV 파일을 로드하고 전략에 필요한 지표를 계산
    """
    print("데이터 로딩 시작...")
    
    # CSV 파일 목록 가져오기
    csv_files = glob.glob(os.path.join(data_folder, '*_1min.csv'))
    if max_stocks:
        # 랜덤으로 max_stocks개 선택
        random.shuffle(csv_files)
        csv_files = csv_files[:max_stocks]
    
    print(f"총 {len(csv_files)}개 종목 데이터 로딩 중...")
    
    stock_data = {}
    for file_path in csv_files:
        try:
            # 파일명에서 종목코드 추출
            stock_code = os.path.basename(file_path).split('_')[0]
            
            # CSV 로드
            df = pd.read_csv(file_path)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')
            
            # 전략에 필요한 지표 계산
            df['volume_ratio'] = df['volume_ratio'].fillna(0)
            df['ma5'] = df['ma5'].fillna(0)
            df['ma20'] = df['ma20'].fillna(0)
            
            # 60일 이동평균선 계산 (스윙 트레이딩용)
            df['ma60'] = df['close'].rolling(window=60).mean().fillna(0)
            
            # 가격 변화율 계산
            df['price_change_pct'] = df['close'].pct_change() * 100
            
            # 거래량 증가율 계산
            df['volume_increase'] = df['volume'].pct_change() * 100
            
            stock_data[stock_code] = df
            print(f"✓ {stock_code}: {len(df)}건 로드 완료")
            
        except Exception as e:
            print(f"✗ {file_path} 로드 실패: {e}")
            continue
    
    print(f"데이터 로딩 완료: {len(stock_data)}개 종목")
    return stock_data

# ============================================================================
# 3. 전략 함수 (check_strategy_1, check_strategy_2, check_market_regime)
# ============================================================================

def check_market_regime(market_data: pd.DataFrame, current_date: datetime.date) -> bool:
    """
    시장 국면 필터: 코스피 지수가 20일선 위에 있는지 확인
    """
    if market_data.empty:
        return True  # 시장 데이터가 없으면 필터 비활성화
    
    # 해당 날짜의 시장 데이터 찾기
    date_data = market_data[market_data['date'].dt.date == current_date]
    
    if date_data.empty:
        # 해당 날짜 데이터가 없으면 이전 데이터 사용
        date_data = market_data[market_data['date'].dt.date < current_date]
        if date_data.empty:
            return True  # 데이터가 없으면 필터 비활성화
    
    if not date_data.empty:
        latest_data = date_data.iloc[-1]
        kospi_close = latest_data['close']
        kospi_ma20 = latest_data['ma20']
        
        # 코스피 지수가 20일선 위에 있는지 확인
        is_good_market = kospi_close > kospi_ma20
        
        return is_good_market
    
    return True  # 기본값은 필터 비활성화

def check_strategy_1(df_slice: pd.DataFrame) -> Optional[float]:
    """
    전략1: EDA 기반의 '거래량 급증 + 시초가 갭' 전략
    """
    if len(df_slice) < 20:
        return None

    # 현재 시점의 데이터 (마지막 데이터)
    current = df_slice.iloc[-1]
    current_date = current['datetime'].date()
    
    # 9시 데이터 찾기 (시초가와 거래량 확인용)
    nine_am_data = df_slice[df_slice['datetime'].dt.time == datetime.strptime('09:00', '%H:%M').time()]
    if nine_am_data.empty:
        return None

    nine = nine_am_data.iloc[0]

    # --- EDA 분석 결과 기반의 새로운 조건 ---

    # 조건 1: 시초가 갭이 0.2% 이상인가? (완화)
    # 전일 종가 계산 - 전날의 15:30 데이터를 전일 종가로 사용
    prev_date = current_date - timedelta(days=1)
    
    # 전날의 15:30 데이터 찾기 (전일 종가로 사용)
    prev_close_data = df_slice[
        (df_slice['datetime'].dt.date == prev_date) &
        (df_slice['datetime'].dt.time == datetime.strptime('15:30', '%H:%M').time())
    ]
    
    if not prev_close_data.empty:
        prev_close = prev_close_data.iloc[0]['close']
        open_gap = (nine['open'] - prev_close) / prev_close * 100
        if not (open_gap > 0.2):  # 0.25% → 0.2%로 완화
            return None
    else:
        # 전일 15:30 데이터가 없으면 조건 스킵
        pass
        
    # 조건 2: 9시 첫 거래량이 30,000주 이상인가? (완화)
    if not (nine.get('volume', 0) > 30000):  # 40,000 → 30,000으로 완화
        return None

    # 조건 3: 20일 이동평균선 아래에서 시작했는가? (역발상: 성공 케이스는 16.2%만 20일선 위)
    if not (nine.get('close', 0) < nine.get('ma20', float('inf'))):
        return None

    # 위 모든 '엘리트 조건'을 통과하면, 점수를 부여할 필요 없이 바로 매수 신호로 간주
    return 100  # 임의의 높은 점수

def check_strategy_2(df_slice: pd.DataFrame) -> Optional[float]:
    """
    전략2: 스윙 트레이딩용 '추세 추종' 전략 (조건 대폭 완화)
    """
    if len(df_slice) < 20:
        return None
    
    current = df_slice.iloc[-1]
    
    # --- 완화된 스윙 트레이딩 조건 ---
    conditions = []
    scores = []
    
    # 조건 1: 정배열 확인 (5일선 > 20일선, 0.1%만 높아도 인정)
    ma5 = current['ma5']
    ma20 = current['ma20']
    if ma5 > ma20 * 0.999:
        conditions.append(True)
        scores.append(0.4)
    else:
        conditions.append(False)
        scores.append(0)
    
    # 조건 2: 눌림목 확인 (20일선 10% 이내)
    price = current['close']
    ma20_distance = abs(price - ma20) / ma20 * 100
    if ma20_distance < 10.0:
        conditions.append(True)
        scores.append(0.3)
    else:
        conditions.append(False)
        scores.append(0)
    
    # 조건 3: 거래량 증가 확인 (평균 대비 80% 이상)
    if current['volume_ratio'] > 80:
        conditions.append(True)
        scores.append(0.3)
    else:
        conditions.append(False)
        scores.append(0)
    
    total_score = sum(scores)
    # 모든 조건을 만족하고, 점수가 0.6점 이상일 때만 진입 (더 완화)
    if all(conditions) and total_score >= 0.6:
        return total_score
    return None

def check_strategy_3(df_slice: pd.DataFrame) -> Optional[float]:
    """
    전략3: 스윙 트레이딩용 '돌파' 전략 (조건 대폭 완화)
    """
    if len(df_slice) < 10:
        return None
    
    current = df_slice.iloc[-1]
    
    # --- 돌파 전략 조건 ---
    conditions = []
    scores = []
    
    # 조건 1: 장대양봉 확인 (전일 대비 1% 이상 상승)
    if len(df_slice) >= 2:
        prev_close = df_slice.iloc[-2]['close']
        price_change = (current['close'] - prev_close) / prev_close * 100
        if price_change > 1.0:
            conditions.append(True)
            scores.append(0.4)
        else:
            conditions.append(False)
            scores.append(0)
    # 조건 2: 거래량 급증 확인 (평균 대비 100% 이상)
    if current['volume_ratio'] > 100:
        conditions.append(True)
        scores.append(0.3)
    else:
        conditions.append(False)
        scores.append(0)
    # 조건 3: 저항선 돌파 확인 (20일선 위로 상승)
    if current['close'] > current['ma20']:
        conditions.append(True)
        scores.append(0.3)
    else:
        conditions.append(False)
        scores.append(0)
    total_score = sum(scores)
    # 모든 조건을 만족하고, 점수가 0.6점 이상일 때만 진입 (더 완화)
    if all(conditions) and total_score >= 0.6:
        return total_score
    return None

# ============================================================================
# 4. 백테스팅 실행 (run_backtest)
# ============================================================================

def run_backtest(stock_data: Dict[str, pd.DataFrame], market_data: pd.DataFrame = None) -> Tuple[Dict, List[Dict]]:
    """
    백테스팅 핵심 엔진 (시장 국면 필터 포함)
    """
    print("백테스팅 시작...")
    
    # 초기 상태 설정
    cash = CONFIG['initial_capital']
    portfolio = {}  # {stock_code: {'shares': int, 'buy_price': float, 'buy_time': datetime, 'peak_price': float}}
    trades = []
    previous_date = None  # 이전 날짜 추적
    
    # 전체 시간 범위 생성
    all_dates = set()
    for df in stock_data.values():
        all_dates.update(df['datetime'].dt.date)
    
    all_dates = sorted(list(all_dates))
    start_date = datetime.strptime(CONFIG['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(CONFIG['end_date'], '%Y-%m-%d').date()
    
    # 백테스트 기간 필터링
    test_dates = [d for d in all_dates if start_date <= d <= end_date]
    
    print(f"백테스트 기간: {test_dates[0]} ~ {test_dates[-1]} ({len(test_dates)}일)")
    
    # 일별 백테스팅
    for current_date in test_dates:
        progress = (test_dates.index(current_date)+1) / len(test_dates) * 100
        if test_dates.index(current_date) % 10 == 0:  # 10일마다만 출력
            print(f"진행 중: {current_date} ({test_dates.index(current_date)+1}/{len(test_dates)}) - {progress:.1f}%")
        
        # --- 시장 국면 필터 적용 ---
        is_good_market = check_market_regime(market_data, current_date)
        if not is_good_market:
            print(f"  시장 상황 나쁨: {current_date} 매매 중단")
            continue  # 시장이 나쁘면 그날은 아무것도 하지 않고 넘어감
        # ---------------------------
        
        # 현재 포트폴리오 상태 출력 (간결하게)
        if portfolio and test_dates.index(current_date) % 10 == 0:  # 10일마다만 출력
            print(f"  보유: {list(portfolio.keys())}")
        elif not portfolio and test_dates.index(current_date) % 10 == 0:
            print(f"  보유: 없음")
        
        # 새로운 날짜 시작 시 일일 자본 초기화
        if previous_date != current_date:
            daily_start_cash = cash  # 새로운 날의 시작 자본을 기록
            previous_date = current_date
        
        # 해당 날짜의 모든 1분 데이터 수집
        minute_data = {}
        for stock_code, df in stock_data.items():
            day_data = df[df['datetime'].dt.date == current_date]
            if len(day_data) > 0:
                minute_data[stock_code] = day_data.sort_values('datetime')
        
        if not minute_data:
            continue
        
        # 해당 날짜의 모든 시간대 순회
        all_times = set()
        for df in minute_data.values():
            all_times.update(df['datetime'].dt.time)
        
        all_times = sorted(list(all_times))
        
        # 30분 간격으로 스캔 (스윙 트레이딩은 더 큰 간격으로 충분)
        scan_interval = 30  # 30분 간격
        filtered_times = [t for i, t in enumerate(all_times) if i % scan_interval == 0]
        
        for current_time in filtered_times:
            current_datetime = datetime.combine(current_date, current_time)
            
            # 매도 체크 (보유 종목들)
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
                
                # 고점 가격 업데이트
                if current_price > position['peak_price']:
                    position['peak_price'] = current_price
                
                # 손절/익절/트레일링 스탑 체크
                profit_pct = (current_price - buy_price) / buy_price * 100
                hold_days = (current_datetime - buy_time).days  # 일 단위로 변경
                
                # 트레일링 스탑 계산
                trailing_stop_price = position['peak_price'] * (1 - CONFIG['trailing_stop'] / 100)
                
                sell_reason = None
                if profit_pct <= CONFIG['stop_loss']:
                    sell_reason = '손절'
                elif profit_pct >= CONFIG['take_profit']:
                    sell_reason = '익절'
                elif current_price <= trailing_stop_price and profit_pct > 0:
                    sell_reason = '트레일링스탑'
                elif hold_days >= CONFIG['max_hold_days']:  # 보유 기간 체크 (일 단위)
                    sell_reason = '보유기간초과'
                
                if sell_reason:
                    stocks_to_sell.append((stock_code, sell_reason, current_price, profit_pct))
            
            # 매도 실행
            for stock_code, reason, sell_price, profit_pct in stocks_to_sell:
                position = portfolio[stock_code]
                shares = position['shares']
                buy_price = position['buy_price']
                
                # 현금 회수
                cash += shares * sell_price
                
                # 거래 기록
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
                
                # 포트폴리오에서 제거
                del portfolio[stock_code]
                
                # 매도 로그 출력 (큰 손익만)
                if abs(profit_pct) > 2.0:
                    print(f"  매도: {stock_code} {reason} ({profit_pct:.2f}%)")
            
            # 매수 체크 (스캔 시간대에만)
            scan_start = datetime.strptime(CONFIG['scan_start_time'], '%H:%M').time()
            scan_end = datetime.strptime(CONFIG['scan_end_time'], '%H:%M').time()
            
            # 일일 손실 제한 체크 (제한 없음)
            if CONFIG['max_daily_loss'] is not None:
                daily_loss_pct = (cash - daily_start_cash) / daily_start_cash * 100
                if daily_loss_pct <= CONFIG['max_daily_loss']:
                    # 일일 손실 한도 초과 시 매수 중단 (로그 추가)
                    if current_time == scan_start:  # 스캔 시작 시간에만 로그 출력
                        print(f"  일일 손실 한도 초과: {daily_loss_pct:.2f}%")
                    continue
            
            if scan_start <= current_time <= scan_end and len(portfolio) < CONFIG['max_positions']:
                # 매수 신호 스캔
                buy_signals = []
                
                for stock_code, df in minute_data.items():
                    if stock_code in portfolio:
                        continue
                    
                    # 현재 시점까지의 데이터 슬라이스
                    df_slice = df[df['datetime'] <= current_datetime]
                    if len(df_slice) < 20:
                        continue
                    
                    # 전략 체크
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
                
                # 신호 정렬 (전략1 우선, 높은 점수 우선)
                buy_signals.sort(key=lambda x: (x['priority'], -x['score']))
                
                # 매수 실행
                for signal in buy_signals:
                    if len(portfolio) >= CONFIG['max_positions']:
                        break
                    
                    stock_code = signal['stock_code']
                    current_price_data = minute_data[stock_code][minute_data[stock_code]['datetime'] == current_datetime]
                    
                    if len(current_price_data) == 0:
                        continue
                    
                    current_price = current_price_data.iloc[0]['close']
                    
                    # 동적 포지션 사이징: 점수에 따른 투자 금액 조정
                    base_position_size = CONFIG['position_size']
                    if signal['strategy'] == 'Strategy1':
                        # 전략1은 점수가 100이므로 최대 투자
                        position_size = base_position_size
                    elif signal['strategy'] == 'Strategy2':
                        # 전략2는 점수에 따라 투자 금액 조정
                        score = signal['score']
                        if score >= 0.8:
                            position_size = base_position_size  # 최대 투자
                        elif score >= 0.6:
                            position_size = base_position_size * 0.7  # 70% 투자
                        else:
                            position_size = base_position_size * 0.5  # 50% 투자
                    elif signal['strategy'] == 'Strategy3':
                        # 전략3은 돌파 전략이므로 최대 투자
                        position_size = base_position_size
                    else:
                        position_size = base_position_size
                    
                    shares = position_size // current_price
                    
                    if shares > 0 and cash >= shares * current_price:
                        # 매수 실행
                        cash -= shares * current_price
                        
                        portfolio[stock_code] = {
                            'shares': shares,
                            'buy_price': current_price,
                            'buy_time': current_datetime,
                            'peak_price': current_price  # 고점 가격 초기화
                        }
                        
                        # 거래 기록
                        trades.append({
                            'datetime': current_datetime,
                            'stock_code': stock_code,
                            'action': 'BUY',
                            'reason': signal['strategy'],
                            'shares': shares,
                            'price': current_price,
                            'score': signal['score'],
                            'cash': cash
                        })
                        
                        # 매수 로그 출력 (투자 금액 포함)
                        print(f"  매수: {stock_code} {signal['strategy']} ({position_size:,}원)")
        
        # 장 마감 시 미청산 포지션 강제 매도
        market_close_time = datetime.strptime('15:30', '%H:%M').time()
        market_close_datetime = datetime.combine(current_date, market_close_time)
        
        for stock_code, position in list(portfolio.items()):
            if stock_code in minute_data:
                close_data = minute_data[stock_code][minute_data[stock_code]['datetime'].dt.time == market_close_time]
                if len(close_data) > 0:
                    close_price = close_data.iloc[0]['close']
                    shares = position['shares']
                    buy_price = position['buy_price']
                    profit_pct = (close_price - buy_price) / buy_price * 100
                    
                    cash += shares * close_price
                    
                    trades.append({
                        'datetime': market_close_datetime,
                        'stock_code': stock_code,
                        'action': 'SELL',
                        'reason': '장마감',
                        'shares': shares,
                        'price': close_price,
                        'profit_pct': profit_pct,
                        'cash': cash
                    })
                    
                    del portfolio[stock_code]
    
    # 최종 결과 계산
    final_cash = cash
    for stock_code, position in portfolio.items():
        # 마지막 가격으로 청산
        if stock_code in stock_data:
            last_price = stock_data[stock_code]['close'].iloc[-1]
            final_cash += position['shares'] * last_price
    
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
# 5. 결과 분석 (analyze_results)
# ============================================================================

def analyze_results(results: Dict, trades: List[Dict]) -> None:
    """
    백테스트 결과 분석 및 출력
    """
    print("\n" + "="*60)
    print("백테스트 결과 분석")
    print("="*60)
    
    # 기본 성과 지표
    initial_capital = results['initial_capital']
    final_capital = results['final_capital']
    total_return = results['total_return']
    
    print(f"초기 자본: {initial_capital:,}원")
    print(f"최종 자본: {final_capital:,}원")
    print(f"총 수익률: {total_return:.2f}%")
    print(f"총 수익금: {final_capital - initial_capital:,}원")
    
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
    
    # MDD (Maximum Drawdown) 계산
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
    
    # 전략별 성과
    strategy1_trades = [t for t in trades if t['action'] == 'BUY' and t.get('reason') == 'Strategy1']
    strategy2_trades = [t for t in trades if t['action'] == 'BUY' and t.get('reason') == 'Strategy2']
    strategy3_trades = [t for t in trades if t['action'] == 'BUY' and t.get('reason') == 'Strategy3']
    
    print(f"\n전략별 성과:")
    print(f"전략1 매수: {len(strategy1_trades)}회")
    print(f"전략2 매수: {len(strategy2_trades)}회")
    print(f"전략3 매수: {len(strategy3_trades)}회")

# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    print("백테스트 시스템 시작")
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
    
    # 1-1. 시장 데이터 로드
    market_data = load_market_data(CONFIG['start_date'], CONFIG['end_date'])
    
    # 2. 백테스트 실행
    results, trades = run_backtest(stock_data, market_data)
    
    # 3. 결과 분석
    analyze_results(results, trades)
    
    print("\n백테스트 완료!") 