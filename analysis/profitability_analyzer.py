import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# 설정
# ============================================================================

CONFIG = {
    'data_folder': 'minute_data',
    'start_date': '2025-01-01',
    'end_date': '2025-07-14',
    'min_data_points': 1000,  # 최소 데이터 포인트
    'profit_threshold': 5.0,  # 수익 기준 (5% 이상)
    'loss_threshold': -5.0,   # 손실 기준 (-5% 이하)
}

# ============================================================================
# 데이터 로드 및 전처리
# ============================================================================

def load_stock_data(data_folder: str = 'minute_data') -> Dict[str, pd.DataFrame]:
    """
    모든 주식 데이터 로드
    """
    print("주식 데이터 로딩 중...")
    
    csv_files = glob.glob(os.path.join(data_folder, '*_1min.csv'))
    stock_data = {}
    
    for file_path in csv_files:
        try:
            stock_code = os.path.basename(file_path).split('_')[0]
            
            df = pd.read_csv(file_path)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')
            
            # 기본 지표 계산
            df['price_change_pct'] = df['close'].pct_change() * 100
            
            # 거래량 비율 재계산 (20일 평균 대비)
            df['volume_ma20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma20']
            df['volume_ratio'] = df['volume_ratio'].fillna(1.0)  # NaN을 1.0으로 채움
            
            # 이동평균선 계산
            df['ma5'] = df['close'].rolling(window=5).mean().fillna(0)
            df['ma20'] = df['close'].rolling(window=20).mean().fillna(0)
            df['ma60'] = df['close'].rolling(window=60).mean().fillna(0)
            
            # 기술적 지표 추가
            df['atr'] = calculate_atr(df)
            df['rsi'] = calculate_rsi(df)
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculate_bollinger_bands(df)
            df['macd'], df['macd_signal'], _ = calculate_macd(df)
            
            # 거래량 관련 지표
            df['volume_ma20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio_ma'] = df['volume'] / df['volume_ma20']
            
            # 가격 변동성
            df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean() * 100
            
            stock_data[stock_code] = df
            print(f"✓ {stock_code}: {len(df)}건 로드")
            
        except Exception as e:
            print(f"✗ {file_path} 로드 실패: {e}")
            continue
    
    print(f"총 {len(stock_data)}개 종목 로드 완료")
    return stock_data

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR 계산"""
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
    """RSI 계산"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """볼린저 밴드 계산"""
    ma = df['close'].rolling(window=period).mean()
    std_dev = df['close'].rolling(window=period).std()
    
    upper = ma + (std_dev * std)
    lower = ma - (std_dev * std)
    
    return upper, ma, lower

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD 계산"""
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    
    return macd, signal_line, histogram

# ============================================================================
# 수익성 분석
# ============================================================================

def analyze_stock_profitability(stock_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """
    각 종목의 수익성 분석
    """
    print("\n수익성 분석 시작...")
    
    profitability_data = {}
    
    for stock_code, df in stock_data.items():
        if len(df) < CONFIG['min_data_points']:
            continue
            
        # 백테스트 기간 필터링
        start_date = datetime.strptime(CONFIG['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(CONFIG['end_date'], '%Y-%m-%d').date()
        
        df_filtered = df[
            (df['datetime'].dt.date >= start_date) & 
            (df['datetime'].dt.date <= end_date)
        ]
        
        if len(df_filtered) < 100:  # 최소 100개 데이터 포인트
            continue
        
        # 수익률 계산 (시작가 대비 종가)
        start_price = df_filtered.iloc[0]['close']
        end_price = df_filtered.iloc[-1]['close']
        total_return = (end_price - start_price) / start_price * 100
        
        # 최고점, 최저점
        max_price = df_filtered['high'].max()
        min_price = df_filtered['low'].min()
        max_return = (max_price - start_price) / start_price * 100
        min_return = (min_price - start_price) / start_price * 100
        
        # 변동성
        volatility = df_filtered['close'].pct_change().std() * 100
        
        # 거래량 분석
        avg_volume = df_filtered['volume'].mean()
        volume_volatility = df_filtered['volume'].std() / avg_volume
        
        # 기술적 지표 평균값
        avg_rsi = df_filtered['rsi'].mean()
        avg_atr = df_filtered['atr'].mean()
        avg_volume_ratio = df_filtered['volume_ratio'].mean()
        
        # 이동평균선 상태
        final_ma5 = df_filtered.iloc[-1]['ma5']
        final_ma20 = df_filtered.iloc[-1]['ma20']
        final_ma60 = df_filtered.iloc[-1]['ma60']
        final_price = df_filtered.iloc[-1]['close']
        
        ma_alignment = 0  # 정배열 점수
        if final_ma5 > final_ma20 > final_ma60:
            ma_alignment = 3  # 완전 정배열
        elif final_ma5 > final_ma20:
            ma_alignment = 2  # 부분 정배열
        elif final_ma20 > final_ma60:
            ma_alignment = 1  # 장기 정배열
        
        # 수익성 분류
        if total_return >= CONFIG['profit_threshold']:
            category = 'high_profit'
        elif total_return <= CONFIG['loss_threshold']:
            category = 'high_loss'
        else:
            category = 'neutral'
        
        # 추가 지표 계산
        price_range = (max_price - min_price) / start_price * 100
        win_rate = len(df_filtered[df_filtered['price_change_pct'] > 0]) / len(df_filtered) * 100
        
        profitability_data[stock_code] = {
            'total_return': total_return,
            'max_return': max_return,
            'min_return': min_return,
            'price_range': price_range,
            'win_rate': win_rate,
            'volatility': volatility,
            'avg_volume': avg_volume,
            'volume_volatility': volume_volatility,
            'avg_rsi': avg_rsi,
            'avg_atr': avg_atr,
            'avg_volume_ratio': avg_volume_ratio,
            'ma_alignment': ma_alignment,
            'final_price': final_price,
            'final_ma5': final_ma5,
            'final_ma20': final_ma20,
            'final_ma60': final_ma60,
            'category': category,
            'data_points': len(df_filtered)
        }
    
    print(f"수익성 분석 완료: {len(profitability_data)}개 종목")
    return profitability_data

def find_common_patterns(profitability_data: Dict[str, Dict]) -> Dict:
    """
    수익성 종목들의 공통점 분석
    """
    print("\n공통점 분석 시작...")
    
    # 카테고리별 분류
    high_profit = {k: v for k, v in profitability_data.items() if v['category'] == 'high_profit'}
    high_loss = {k: v for k, v in profitability_data.items() if v['category'] == 'high_loss'}
    neutral = {k: v for k, v in profitability_data.items() if v['category'] == 'neutral'}
    
    print(f"고수익 종목: {len(high_profit)}개")
    print(f"고손실 종목: {len(high_loss)}개")
    print(f"중립 종목: {len(neutral)}개")
    
    # 공통점 분석
    patterns = {}
    
    if high_profit:
        # 고수익 종목들의 평균값
        profit_df = pd.DataFrame(high_profit).T
        
        patterns['high_profit_avg'] = {
            'avg_return': profit_df['total_return'].mean(),
            'avg_volatility': profit_df['volatility'].mean(),
            'avg_volume': profit_df['avg_volume'].mean(),
            'avg_rsi': profit_df['avg_rsi'].mean(),
            'avg_atr': profit_df['avg_atr'].mean(),
            'avg_volume_ratio': profit_df['avg_volume_ratio'].mean(),
            'ma_alignment_avg': profit_df['ma_alignment'].mean(),
            'count': len(high_profit)
        }
        
        # 고수익 종목들의 특징
        patterns['high_profit_features'] = {
            'high_ma_alignment': len(profit_df[profit_df['ma_alignment'] >= 2]),
            'high_volume_ratio': len(profit_df[profit_df['avg_volume_ratio'] > 1.5]),
            'moderate_rsi': len(profit_df[(profit_df['avg_rsi'] > 40) & (profit_df['avg_rsi'] < 70)]),
            'high_volatility': len(profit_df[profit_df['volatility'] > profit_df['volatility'].median()])
        }
    
    if high_loss:
        # 고손실 종목들의 평균값
        loss_df = pd.DataFrame(high_loss).T
        
        patterns['high_loss_avg'] = {
            'avg_return': loss_df['total_return'].mean(),
            'avg_volatility': loss_df['volatility'].mean(),
            'avg_volume': loss_df['avg_volume'].mean(),
            'avg_rsi': loss_df['avg_rsi'].mean(),
            'avg_atr': loss_df['avg_atr'].mean(),
            'avg_volume_ratio': loss_df['avg_volume_ratio'].mean(),
            'ma_alignment_avg': loss_df['ma_alignment'].mean(),
            'count': len(high_loss)
        }
    
    return patterns

def print_analysis_results(profitability_data: Dict[str, Dict], patterns: Dict):
    """
    분석 결과 출력
    """
    print("\n" + "="*80)
    print("수익성 분석 결과")
    print("="*80)
    
    # 고수익 종목 리스트
    high_profit = {k: v for k, v in profitability_data.items() if v['category'] == 'high_profit'}
    high_loss = {k: v for k, v in profitability_data.items() if v['category'] == 'high_loss'}
    
    print(f"\n📈 고수익 종목 ({len(high_profit)}개):")
    if high_profit:
        profit_sorted = sorted(high_profit.items(), key=lambda x: x[1]['total_return'], reverse=True)
        for i, (code, data) in enumerate(profit_sorted[:10], 1):
            print(f"  {i:2d}. {code}: {data['total_return']:6.2f}% (변동성: {data['volatility']:5.2f}%, RSI: {data['avg_rsi']:5.1f})")
    
    print(f"\n📉 고손실 종목 ({len(high_loss)}개):")
    if high_loss:
        loss_sorted = sorted(high_loss.items(), key=lambda x: x[1]['total_return'])
        for i, (code, data) in enumerate(loss_sorted[:10], 1):
            print(f"  {i:2d}. {code}: {data['total_return']:6.2f}% (변동성: {data['volatility']:5.2f}%, RSI: {data['avg_rsi']:5.1f})")
    
    # 공통점 분석
    if 'high_profit_avg' in patterns:
        print(f"\n🔍 고수익 종목들의 공통점:")
        avg = patterns['high_profit_avg']
        features = patterns['high_profit_features']
        
        print(f"  • 평균 수익률: {avg['avg_return']:.2f}%")
        print(f"  • 평균 변동성: {avg['avg_volatility']:.2f}%")
        print(f"  • 평균 거래량 비율: {avg['avg_volume_ratio']:.2f}")
        print(f"  • 평균 RSI: {avg['avg_rsi']:.1f}")
        print(f"  • 평균 ATR: {avg['avg_atr']:.2f}")
        print(f"  • 이동평균 정배열 점수: {avg['ma_alignment_avg']:.1f}")
        
        print(f"\n  📊 특징 분석:")
        print(f"    - 정배열 종목: {features['high_ma_alignment']}/{avg['count']} ({features['high_ma_alignment']/avg['count']*100:.1f}%)")
        print(f"    - 높은 거래량: {features['high_volume_ratio']}/{avg['count']} ({features['high_volume_ratio']/avg['count']*100:.1f}%)")
        print(f"    - 적정 RSI: {features['moderate_rsi']}/{avg['count']} ({features['moderate_rsi']/avg['count']*100:.1f}%)")
        print(f"    - 높은 변동성: {features['high_volatility']}/{avg['count']} ({features['high_volatility']/avg['count']*100:.1f}%)")
    
    if 'high_loss_avg' in patterns:
        print(f"\n⚠️  고손실 종목들의 특징:")
        avg = patterns['high_loss_avg']
        print(f"  • 평균 손실률: {avg['avg_return']:.2f}%")
        print(f"  • 평균 변동성: {avg['avg_volatility']:.2f}%")
        print(f"  • 평균 거래량 비율: {avg['avg_volume_ratio']:.2f}")
        print(f"  • 평균 RSI: {avg['avg_rsi']:.1f}")
        print(f"  • 이동평균 정배열 점수: {avg['ma_alignment_avg']:.1f}")

def suggest_strategy_improvements(patterns: Dict):
    """
    전략 개선 제안
    """
    print(f"\n💡 전략 개선 제안:")
    
    if 'high_profit_avg' in patterns:
        avg = patterns['high_profit_avg']
        features = patterns['high_profit_features']
        
        print(f"\n1. 📈 매수 조건 강화:")
        print(f"   • 이동평균 정배열 필터: {avg['ma_alignment_avg']:.1f}점 이상")
        print(f"   • 거래량 비율: {avg['avg_volume_ratio']:.2f} 이상")
        print(f"   • RSI 범위: 40-70 (현재 평균: {avg['avg_rsi']:.1f})")
        
        print(f"\n2. 🎯 리스크 관리:")
        print(f"   • 변동성 기반 포지션 사이징 (평균: {avg['avg_volatility']:.2f}%)")
        print(f"   • ATR 기반 손절가 설정 (평균: {avg['avg_atr']:.2f})")
        
        print(f"\n3. 📊 우선순위:")
        if features['high_ma_alignment']/avg['count'] > 0.7:
            print(f"   • 이동평균 정배열이 가장 중요한 지표 ({features['high_ma_alignment']/avg['count']*100:.1f}%)")
        if features['high_volume_ratio']/avg['count'] > 0.6:
            print(f"   • 거래량 증가가 두 번째 중요한 지표 ({features['high_volume_ratio']/avg['count']*100:.1f}%)")

# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    print("수익성 분석 시스템 시작")
    print("="*60)
    
    # 1. 데이터 로드
    stock_data = load_stock_data(CONFIG['data_folder'])
    
    if not stock_data:
        print("데이터가 없습니다.")
        exit()
    
    # 2. 수익성 분석
    profitability_data = analyze_stock_profitability(stock_data)
    
    if not profitability_data:
        print("분석할 데이터가 없습니다.")
        exit()
    
    # 3. 공통점 분석
    patterns = find_common_patterns(profitability_data)
    
    # 4. 결과 출력
    print_analysis_results(profitability_data, patterns)
    
    # 5. 전략 개선 제안
    suggest_strategy_improvements(patterns)
    
    print(f"\n분석 완료!") 