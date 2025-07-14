import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import itertools
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 전략 최적화 도구
# 현재 백테스트 결과 기반 개선
# ============================================================================

class StrategyOptimizer:
    """
    전략 최적화 도구
    현재 결과: 승률 27.7%, 수익률 -34.18% → 개선 필요
    """
    
    def __init__(self):
        self.best_params = None
        self.best_result = None
        
    def get_optimization_ranges(self) -> Dict:
        """최적화할 파라미터 범위 (현재 결과 기반 완화)"""
        return {
            # 핵심 필터 완화
            'ma_alignment_min': [1.0, 1.5, 1.8, 2.0],  # 정배열 조건 완화
            'volatility_max': [0.4, 0.5, 0.6, 0.7],    # 변동성 허용 범위 확대
            'rsi_min': [30, 35, 40, 45],               # RSI 하한 완화
            'rsi_max': [65, 70, 75, 80],               # RSI 상한 완화
            'volume_ratio_min': [0.8, 1.0, 1.2],       # 거래량 조건 완화
            
            # 매매 조건 완화
            'take_profit_pct': [10.0, 12.0, 15.0, 18.0],  # 익절 목표 하향
            'stop_loss_pct': [3.0, 4.0, 5.0, 6.0],        # 손절 범위 확대
            'atr_multiplier_stop': [1.5, 2.0, 2.5, 3.0],  # ATR 손절 완화
            
            # 추가 조건
            'min_holding_days': [1, 2, 3],              # 최소 보유 기간 단축
            'max_holding_days': [20, 25, 30],           # 최대 보유 기간 조정
        }
    
    def create_improved_strategy(self, params: Dict) -> Dict:
        """개선된 전략 생성"""
        return {
            'name': 'Improved_Swing_Strategy',
            'params': {
                # 핵심 필터 (완화된 조건)
                'ma_alignment_min': params.get('ma_alignment_min', 1.5),
                'volatility_max': params.get('volatility_max', 0.5),
                'rsi_min': params.get('rsi_min', 35),
                'rsi_max': params.get('rsi_max', 75),
                'volume_ratio_min': params.get('volume_ratio_min', 0.8),
                
                # 매매 조건
                'take_profit_pct': params.get('take_profit_pct', 12.0),
                'stop_loss_pct': params.get('stop_loss_pct', 4.0),
                'atr_multiplier_stop': params.get('atr_multiplier_stop', 2.0),
                'min_holding_days': params.get('min_holding_days', 2),
                'max_holding_days': params.get('max_holding_days', 25),
                
                # 추가 개선사항
                'use_trailing_stop': True,              # 트레일링 스탑 추가
                'trailing_stop_pct': 3.0,               # 트레일링 스탑 비율
                'use_volume_confirmation': True,        # 거래량 확인 강화
                'use_momentum_filter': True,            # 모멘텀 필터 추가
            }
        }
    
    def evaluate_strategy(self, results: Dict) -> float:
        """전략 평가 점수 계산"""
        if not results or results.get('num_trades', 0) == 0:
            return -999
        
        # 기본 지표
        total_return = results.get('total_return', 0)
        win_rate = results.get('win_rate', 0)
        num_trades = results.get('num_trades', 0)
        max_drawdown = results.get('max_drawdown', 100)
        
        # 거래 횟수 가중치 (너무 적으면 불리)
        trade_penalty = max(0, (50 - num_trades) * 0.1)
        
        # 승률 가중치 (50% 이상이면 보너스)
        win_rate_bonus = max(0, (win_rate - 50) * 0.5)
        
        # 최대 낙폭 페널티
        drawdown_penalty = max_drawdown * 0.5
        
        # 종합 점수
        score = (total_return * 0.4 + 
                win_rate * 0.3 + 
                win_rate_bonus - 
                trade_penalty - 
                drawdown_penalty)
        
        return score
    
    def optimize_strategy(self, test_function, max_combinations: int = 100) -> Dict:
        """전략 최적화 실행"""
        print("전략 최적화 시작...")
        print("="*60)
        
        ranges = self.get_optimization_ranges()
        
        # 조합 생성 (최대 개수 제한)
        param_names = list(ranges.keys())
        param_values = list(ranges.values())
        
        # 모든 조합 생성
        all_combinations = list(itertools.product(*param_values))
        
        # 조합 수 제한
        if len(all_combinations) > max_combinations:
            # 랜덤 샘플링
            np.random.seed(42)
            selected_indices = np.random.choice(
                len(all_combinations), 
                max_combinations, 
                replace=False
            )
            all_combinations = [all_combinations[i] for i in selected_indices]
        
        print(f"테스트할 조합 수: {len(all_combinations)}")
        
        best_score = -999
        best_params = None
        best_results = None
        
        for i, combination in enumerate(all_combinations):
            # 파라미터 딕셔너리 생성
            params = dict(zip(param_names, combination))
            
            # 전략 생성
            strategy = self.create_improved_strategy(params)
            
            # 백테스트 실행
            try:
                results = test_function(strategy['params'])
                
                # 점수 계산
                score = self.evaluate_strategy(results)
                
                # 최고 점수 업데이트
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_results = results
                    
                    print(f"\n🎯 새로운 최고 점수 발견! (조합 {i+1}/{len(all_combinations)})")
                    print(f"점수: {score:.2f}")
                    print(f"수익률: {results.get('total_return', 0):.2f}%")
                    print(f"승률: {results.get('win_rate', 0):.1f}%")
                    print(f"거래 횟수: {results.get('num_trades', 0)}")
                    print(f"최대 낙폭: {results.get('max_drawdown', 0):.2f}%")
                
                if (i + 1) % 20 == 0:
                    print(f"진행률: {i+1}/{len(all_combinations)} ({((i+1)/len(all_combinations)*100):.1f}%)")
                    
            except Exception as e:
                print(f"조합 {i+1} 실행 실패: {e}")
                continue
        
        # 최적 결과 저장
        self.best_params = best_params
        self.best_result = best_results
        
        return {
            'best_params': best_params,
            'best_results': best_results,
            'best_score': best_score
        }
    
    def print_optimization_results(self, results: Dict):
        """최적화 결과 출력"""
        print("\n" + "="*80)
        print("전략 최적화 결과")
        print("="*80)
        
        if not results:
            print("최적화 결과가 없습니다.")
            return
        
        best_params = results['best_params']
        best_results = results['best_results']
        best_score = results['best_score']
        
        print(f"\n🏆 최고 점수: {best_score:.2f}")
        
        print(f"\n📊 최적 파라미터:")
        for key, value in best_params.items():
            print(f"  • {key}: {value}")
        
        print(f"\n📈 백테스트 결과:")
        print(f"  • 총 수익률: {best_results.get('total_return', 0):.2f}%")
        print(f"  • 승률: {best_results.get('win_rate', 0):.1f}%")
        print(f"  • 거래 횟수: {best_results.get('num_trades', 0)}")
        print(f"  • 평균 수익: {best_results.get('avg_return', 0):.2f}%")
        print(f"  • 최대 낙폭: {best_results.get('max_drawdown', 0):.2f}%")
        print(f"  • 샤프 비율: {best_results.get('sharpe_ratio', 0):.2f}")
        
        # 개선사항 분석
        print(f"\n🔧 개선 제안:")
        if best_results.get('win_rate', 0) < 50:
            print(f"  • 승률이 낮음 ({best_results.get('win_rate', 0):.1f}%) → 매수 조건 완화 필요")
        
        if best_results.get('max_drawdown', 0) > 20:
            print(f"  • 최대 낙폭이 높음 ({best_results.get('max_drawdown', 0):.2f}%) → 손절 조건 강화 필요")
        
        if best_results.get('num_trades', 0) < 20:
            print(f"  • 거래 횟수가 적음 ({best_results.get('num_trades', 0)}) → 매수 조건 완화 필요")
        
        if best_results.get('total_return', 0) < 0:
            print(f"  • 수익률이 음수 ({best_results.get('total_return', 0):.2f}%) → 전략 전면 재검토 필요")

# ============================================================================
# 빠른 개선 제안
# ============================================================================

def get_quick_improvements() -> Dict:
    """현재 결과 기반 빠른 개선 제안"""
    return {
        'immediate_fixes': {
            'ma_alignment_min': 1.0,      # 1.8 → 1.0 (정배열 조건 완화)
            'volatility_max': 0.6,        # 0.35 → 0.6 (변동성 허용 확대)
            'rsi_min': 30,                # 40 → 30 (RSI 하한 완화)
            'rsi_max': 80,                # 70 → 80 (RSI 상한 완화)
            'volume_ratio_min': 0.8,      # 1.0 → 0.8 (거래량 조건 완화)
            'take_profit_pct': 10.0,      # 15.0 → 10.0 (익절 목표 하향)
            'stop_loss_pct': 4.0,         # 5.0 → 4.0 (손절 범위 축소)
        },
        'reasoning': {
            'ma_alignment': "정배열 조건이 너무 엄격해서 거래 기회가 적음",
            'volatility': "변동성 필터가 너무 엄격해서 좋은 기회 놓침",
            'rsi': "RSI 범위가 너무 좁아서 매수 기회 제한",
            'volume': "거래량 조건이 너무 엄격함",
            'take_profit': "익절 목표가 너무 높아서 실현 기회 적음",
            'stop_loss': "손절 범위를 좁혀서 손실 최소화"
        }
    }

if __name__ == "__main__":
    print("전략 최적화 도구")
    print("="*60)
    
    optimizer = StrategyOptimizer()
    
    # 빠른 개선 제안
    improvements = get_quick_improvements()
    
    print("🚀 빠른 개선 제안:")
    for param, value in improvements['immediate_fixes'].items():
        reason = improvements['reasoning'].get(param, "")
        print(f"  • {param}: {value} ({reason})")
    
    print(f"\n✅ 이 파라미터들로 다시 백테스트를 실행해보세요!")
    print(f"   기대 효과: 거래 기회 증가, 승률 향상, 손실 최소화") 