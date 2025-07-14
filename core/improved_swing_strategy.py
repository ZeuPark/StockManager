import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 개선된 스윙 트레이딩 전략
# 수익성 분석 결과 기반 최적화
# ============================================================================

class ImprovedSwingStrategy:
    """
    수익성 분석 결과를 바탕으로 개선된 스윙 트레이딩 전략
    
    핵심 개선사항:
    1. 이동평균 정배열 필터 강화 (59.5% 고수익 종목이 정배열)
    2. 변동성 기반 필터링 (0.29% 이하 선호)
    3. RSI 중립 구간 활용 (40-70)
    4. 거래량 비율 기반 확인
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """기본 설정값 (수익성 분석 결과 기반)"""
        return {
            # 핵심 필터 (수익성 분석 결과 기반)
            'ma_alignment_min': 1.8,      # 이동평균 정배열 최소 점수
            'volatility_max': 0.35,       # 최대 변동성 (고손실 종목 평균)
            'rsi_min': 40,                # RSI 최소값
            'rsi_max': 70,                # RSI 최대값
            'volume_ratio_min': 1.0,      # 최소 거래량 비율
            
            # 추가 조건
            'atr_period': 14,             # ATR 계산 기간
            'rsi_period': 14,             # RSI 계산 기간
            'ma_short': 5,                # 단기 이동평균
            'ma_mid': 20,                 # 중기 이동평균
            'ma_long': 60,                # 장기 이동평균
            
            # 매매 조건
            'min_holding_days': 3,        # 최소 보유 기간
            'max_holding_days': 30,       # 최대 보유 기간
            'stop_loss_pct': 5.0,         # 손절 비율
            'take_profit_pct': 15.0,      # 익절 비율
            'atr_stop_multiplier': 2.0,   # ATR 기반 손절 배수
            
            # 포지션 사이징
            'max_position_size': 0.1,     # 최대 포지션 크기 (10%)
            'volatility_position_sizing': True,  # 변동성 기반 포지션 사이징
        }
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        # 이동평균선
        df['ma5'] = df['close'].rolling(window=self.config['ma_short']).mean()
        df['ma20'] = df['close'].rolling(window=self.config['ma_mid']).mean()
        df['ma60'] = df['close'].rolling(window=self.config['ma_long']).mean()
        
        # 변동성
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean() * 100
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.config['rsi_period'])
        
        # ATR
        df['atr'] = self._calculate_atr(df, self.config['atr_period'])
        
        # 거래량 비율
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
        
        # 이동평균 정배열 점수
        df['ma_alignment'] = self._calculate_ma_alignment(df)
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
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
    
    def _calculate_ma_alignment(self, df: pd.DataFrame) -> pd.Series:
        """이동평균 정배열 점수 계산 (0-3점)"""
        alignment = pd.Series(0, index=df.index)
        
        # 완전 정배열: MA5 > MA20 > MA60 (3점)
        full_alignment = (df['ma5'] > df['ma20']) & (df['ma20'] > df['ma60'])
        alignment[full_alignment] = 3
        
        # 부분 정배열: MA5 > MA20 (2점)
        partial_alignment = (df['ma5'] > df['ma20']) & ~full_alignment
        alignment[partial_alignment] = 2
        
        # 장기 정배열: MA20 > MA60 (1점)
        long_alignment = (df['ma20'] > df['ma60']) & ~full_alignment & ~partial_alignment
        alignment[long_alignment] = 1
        
        return alignment
    
    def check_entry_conditions(self, df: pd.DataFrame, current_idx: int) -> Tuple[bool, Dict]:
        """매수 조건 확인"""
        if current_idx < 60:  # 충분한 데이터가 없으면 False
            return False, {}
        
        current = df.iloc[current_idx]
        
        # 1. 핵심 필터 (수익성 분석 결과 기반)
        ma_alignment_ok = current['ma_alignment'] >= self.config['ma_alignment_min']
        volatility_ok = current['volatility'] <= self.config['volatility_max']
        rsi_ok = (current['rsi'] >= self.config['rsi_min']) and (current['rsi'] <= self.config['rsi_max'])
        volume_ok = current['volume_ratio'] >= self.config['volume_ratio_min']
        
        # 2. 추가 조건
        price_above_ma = current['close'] > current['ma20']  # 20일선 위
        volume_increase = current['volume'] > current['volume_ma20']  # 거래량 증가
        
        # 3. 모멘텀 확인
        price_momentum = (current['close'] - df.iloc[current_idx-5]['close']) / df.iloc[current_idx-5]['close'] * 100
        
        # 모든 조건 만족 시 매수
        entry_signal = (ma_alignment_ok and volatility_ok and rsi_ok and 
                       volume_ok and price_above_ma and volume_increase)
        
        signal_info = {
            'ma_alignment': current['ma_alignment'],
            'volatility': current['volatility'],
            'rsi': current['rsi'],
            'volume_ratio': current['volume_ratio'],
            'price_momentum': price_momentum,
            'atr': current['atr']
        }
        
        return entry_signal, signal_info
    
    def check_exit_conditions(self, df: pd.DataFrame, entry_idx: int, current_idx: int, 
                            entry_price: float, current_price: float) -> Tuple[bool, str]:
        """매도 조건 확인"""
        if current_idx <= entry_idx:
            return False, ""
        
        # 수익률 계산
        return_pct = (current_price - entry_price) / entry_price * 100
        
        # 1. 익절 조건
        if return_pct >= self.config['take_profit_pct']:
            return True, "익절"
        
        # 2. 손절 조건
        if return_pct <= -self.config['stop_loss_pct']:
            return True, "손절"
        
        # 3. 이동평균 정배열 깨짐
        current = df.iloc[current_idx]
        if current['ma_alignment'] < 1:  # 정배열이 깨지면
            return True, "정배열 깨짐"
        
        # 4. 최대 보유 기간 초과
        holding_days = (current_idx - entry_idx) / 1440  # 분 단위를 일 단위로 변환
        if holding_days >= self.config['max_holding_days']:
            return True, "최대 보유 기간"
        
        # 5. RSI 과매수
        if current['rsi'] > 80:
            return True, "RSI 과매수"
        
        return False, ""
    
    def calculate_position_size(self, df: pd.DataFrame, current_idx: int, 
                              available_capital: float) -> float:
        """포지션 사이징 계산"""
        if not self.config['volatility_position_sizing']:
            return available_capital * self.config['max_position_size']
        
        current = df.iloc[current_idx]
        
        # 변동성 기반 포지션 사이징 (낮은 변동성일수록 큰 포지션)
        volatility_factor = max(0.1, 1 - (current['volatility'] / 1.0))  # 0.1-1.0
        
        # 정배열 점수 기반 보정
        alignment_factor = current['ma_alignment'] / 3.0  # 0-1.0
        
        # 최종 포지션 크기
        position_size = (available_capital * self.config['max_position_size'] * 
                        volatility_factor * alignment_factor)
        
        return min(position_size, available_capital * self.config['max_position_size'])
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """매매 신호 생성"""
        df = self.calculate_technical_indicators(df.copy())
        
        signals = []
        
        for i in range(60, len(df)):
            current = df.iloc[i]
            
            # 매수 신호 확인
            entry_signal, signal_info = self.check_entry_conditions(df, i)
            
            if entry_signal:
                signals.append({
                    'datetime': current['datetime'],
                    'action': 'BUY',
                    'price': current['close'],
                    'volume': current['volume'],
                    'ma_alignment': signal_info['ma_alignment'],
                    'volatility': signal_info['volatility'],
                    'rsi': signal_info['rsi'],
                    'volume_ratio': signal_info['volume_ratio'],
                    'price_momentum': signal_info['price_momentum'],
                    'atr': signal_info['atr']
                })
        
        return pd.DataFrame(signals)
    
    def backtest_strategy(self, df: pd.DataFrame, initial_capital: float = 10000000) -> Dict:
        """전략 백테스트"""
        df = self.calculate_technical_indicators(df.copy())
        
        capital = initial_capital
        position = None
        trades = []
        
        for i in range(60, len(df)):
            current = df.iloc[i]
            
            # 포지션이 없으면 매수 신호 확인
            if position is None:
                entry_signal, signal_info = self.check_entry_conditions(df, i)
                
                if entry_signal:
                    position_size = self.calculate_position_size(df, i, capital)
                    shares = int(position_size / current['close'])
                    
                    if shares > 0:
                        position = {
                            'entry_idx': i,
                            'entry_price': current['close'],
                            'shares': shares,
                            'entry_date': current['datetime'],
                            'signal_info': signal_info
                        }
                        
                        capital -= shares * current['close']
            
            # 포지션이 있으면 매도 신호 확인
            elif position is not None:
                exit_signal, exit_reason = self.check_exit_conditions(
                    df, position['entry_idx'], i, 
                    position['entry_price'], current['close']
                )
                
                if exit_signal:
                    # 거래 기록
                    trade_return = (current['close'] - position['entry_price']) / position['entry_price'] * 100
                    trade_profit = position['shares'] * (current['close'] - position['entry_price'])
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': current['datetime'],
                        'entry_price': position['entry_price'],
                        'exit_price': current['close'],
                        'shares': position['shares'],
                        'return_pct': trade_return,
                        'profit': trade_profit,
                        'exit_reason': exit_reason,
                        'ma_alignment': position['signal_info']['ma_alignment'],
                        'volatility': position['signal_info']['volatility'],
                        'rsi': position['signal_info']['rsi']
                    })
                    
                    # 자본 복원
                    capital += position['shares'] * current['close']
                    position = None
        
        # 최종 자본 계산
        final_capital = capital
        if position is not None:
            final_capital += position['shares'] * df.iloc[-1]['close']
        
        # 성과 분석
        total_return = (final_capital - initial_capital) / initial_capital * 100
        num_trades = len(trades)
        
        if num_trades > 0:
            winning_trades = [t for t in trades if t['return_pct'] > 0]
            win_rate = len(winning_trades) / num_trades * 100
            avg_return = sum(t['return_pct'] for t in trades) / num_trades
            max_profit = max(t['return_pct'] for t in trades) if trades else 0
            max_loss = min(t['return_pct'] for t in trades) if trades else 0
        else:
            win_rate = 0
            avg_return = 0
            max_profit = 0
            max_loss = 0
        
        return {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'trades': trades
        }

# ============================================================================
# 전략 테스트 및 최적화
# ============================================================================

def test_improved_strategy():
    """개선된 전략 테스트"""
    print("개선된 스윙 트레이딩 전략 테스트")
    print("="*60)
    
    # 전략 인스턴스 생성
    strategy = ImprovedSwingStrategy()
    
    print("📊 전략 설정:")
    for key, value in strategy.config.items():
        print(f"  • {key}: {value}")
    
    print(f"\n🎯 핵심 개선사항:")
    print(f"  • 이동평균 정배열 필터: {strategy.config['ma_alignment_min']}점 이상")
    print(f"  • 변동성 필터: {strategy.config['volatility_max']}% 이하")
    print(f"  • RSI 범위: {strategy.config['rsi_min']}-{strategy.config['rsi_max']}")
    print(f"  • 거래량 비율: {strategy.config['volume_ratio_min']} 이상")
    print(f"  • 변동성 기반 포지션 사이징: {strategy.config['volatility_position_sizing']}")
    
    return strategy

if __name__ == "__main__":
    strategy = test_improved_strategy()
    print(f"\n✅ 개선된 스윙 트레이딩 전략이 준비되었습니다!")
    print(f"   이제 이 전략을 백테스트에 적용할 수 있습니다.") 