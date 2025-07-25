import optuna
import pandas as pd
import numpy as np
from core.gradual_rise_backtest import GradualRiseBacktest
import warnings
import glob
import os
import random
import datetime
warnings.filterwarnings('ignore')

# === CONFIG: 실험 구간/파라미터/종목 수 조정 ===
TRAIN_RANGE = ('2024-01-01', '2024-12-31')
TEST_RANGE = ('2025-06-01', '2025-06-30')
N_TRIALS = 100
N_STOCKS = 20

# === 1. minute_data에서 랜덤하게 20개 종목 추출 (실행 시 한 번만) ===
csv_files = glob.glob(os.path.join("minute_data", "*_1min.csv"))
all_codes = [os.path.basename(f).split('_')[0] for f in csv_files]
random.seed(42)  # 재현성
TEST_CODES = random.sample(all_codes, N_STOCKS)
print("최적화에 사용할 종목:", TEST_CODES)

class ParameterOptimizer:
    """파라미터 최적화 클래스"""
    
    def __init__(self, data_path="minute_data"):
        self.data_path = data_path
        self.best_params = None
        self.best_value = -np.inf
        
    def objective(self, trial):
        """Optuna 목표 함수 (새로운 feature 파라미터 추가)"""
        # === 파라미터 탐색 범위 대폭 확장 (새로운 feature 포함) ===
        params = {
            # 기본 파라미터 (전략 목적에 맞게 조정)
            'theta_spike': trial.suggest_float('theta_spike', 0.15, 0.25, step=0.005),  # 시초 급등 제외 (15-25%)
            'theta_spike_low': trial.suggest_float('theta_spike_low', 0.01, 0.05, step=0.001),  # 최소 상승률 (1-5%)
            'theta_15m': trial.suggest_float('theta_15m', 0.10, 0.20, step=0.005),  # 천천히 상승 (10-20%)
            'theta_vol': trial.suggest_float('theta_vol', 0.02, 0.20, step=0.005),
            'theta_pull': trial.suggest_float('theta_pull', 0.10, 0.25, step=0.005),
            'tp_pct': trial.suggest_float('tp_pct', 0.05, 0.15, step=0.005),  # 익절 (5-15%)
            'sl_pct': trial.suggest_float('sl_pct', 0.03, 0.10, step=0.002),  # 손절 (3-10%)
            'orb_delay_min': trial.suggest_int('orb_delay_min', 3, 15),
            'orb_max_min': trial.suggest_int('orb_max_min', 20, 45),
            
            # 새로운 기술적 지표 파라미터
            'rsi_min': trial.suggest_float('rsi_min', 30, 60, step=1),  # RSI 하한 완화
            'rsi_max': trial.suggest_float('rsi_max', 70, 85, step=1),  # RSI 상한 완화
            'bb_position_min': trial.suggest_float('bb_position_min', 0.2, 0.5, step=0.01),  # 볼린저 밴드 중간 위치
            'bb_position_max': trial.suggest_float('bb_position_max', 0.5, 0.8, step=0.01),
            'momentum_threshold': trial.suggest_float('momentum_threshold', 0.02, 0.15, step=0.005),  # 양의 모멘텀 강화
            
            # 거래량 파라미터
            'volume_ratio_min': trial.suggest_float('volume_ratio_min', 0.8, 3.0, step=0.1),  # 거래량 조건 강화
            'volume_momentum_threshold': trial.suggest_float('volume_momentum_threshold', 0.0, 0.3, step=0.01),
            
            # 시장상황 파라미터
            'kospi_return_min': trial.suggest_float('kospi_return_min', -0.03, 0.01, step=0.001),
            'kospi_volatility_max': trial.suggest_float('kospi_volatility_max', 0.02, 0.08, step=0.001),
            
            # 시간대별 파라미터
            'time_opening_weight': trial.suggest_float('time_opening_weight', 1.0, 3.0, step=0.1),  # 장 시작 시간대 강화
            'time_lunch_weight': trial.suggest_float('time_lunch_weight', 0.1, 0.8, step=0.1),
            'time_closing_weight': trial.suggest_float('time_closing_weight', 0.1, 0.8, step=0.1),
            
            # Feature 조합 파라미터
            'price_volume_momentum_threshold': trial.suggest_float('price_volume_momentum_threshold', 0.01, 0.3, step=0.01),
            'rsi_volume_interaction_threshold': trial.suggest_float('rsi_volume_interaction_threshold', 0, 200, step=5),
            'bb_volume_interaction_threshold': trial.suggest_float('bb_volume_interaction_threshold', 0.1, 1.5, step=0.05)
        }
        
        try:
            # 백테스트 실행 (항상 동일한 test_codes 사용)
            backtest = GradualRiseBacktest(self.data_path)
            backtest.parameters.update(params)
            # === train/test 분리: train 구간에서만 최적화 ===
            metrics, trades = backtest.run_backtest(stock_codes=TEST_CODES, date_range=TRAIN_RANGE, verbose=False)
            
            if len(trades) == 0:
                return -2000  # 거래가 없으면 더 강한 패널티
            
            # 목표 함수: Sharpe + WinRate + TotalReturn
            sharpe = metrics['sharpe_ratio']
            win_rate = metrics['win_rate']
            total_return = metrics['total_return']
            
            objective_value = sharpe * 0.4 + win_rate * 0.3 + total_return * 0.3
            
            # 거래 수가 적으면 패널티
            if len(trades) < 10:
                objective_value *= 0.2  # 거래 적으면 더 강한 패널티
            elif len(trades) < 20:
                objective_value *= 0.8  # 적당한 거래 수면 약간의 패널티
            
            print(f"Trial {trial.number}: Sharpe={sharpe:.3f}, WinRate={win_rate:.2%}, "
                  f"Return={total_return:.2%}, Trades={len(trades)}, Obj={objective_value:.3f}")
            
            return objective_value
            
        except Exception as e:
            print(f"Trial {trial.number} 에러: {e}")
            return -2000
    
    def optimize(self, n_trials=N_TRIALS):
        """파라미터 최적화 실행"""
        print("=== 파라미터 최적화 시작 ===")
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        study.optimize(self.objective, n_trials=n_trials)
        self.best_params = study.best_params
        self.best_value = study.best_value
        print(f"\n최적 파라미터:")
        for param, value in self.best_params.items():
            print(f"  {param}: {value}")
        print(f"최적 목표값: {self.best_value:.3f}")
        return self.best_params
    
    def validate_best_params(self, stock_codes=None):
        """최적 파라미터로 전체 검증 (train/test 분리)"""
        print("\n=== 최적 파라미터 검증 (train/test) ===")
        backtest = GradualRiseBacktest(self.data_path)
        backtest.parameters.update(self.best_params)
        # train/test 분리 실행
        (train_metrics, train_trades), (test_metrics, test_trades) = backtest.run_train_test_split(
            stock_codes=TEST_CODES, train_range=TRAIN_RANGE, test_range=TEST_RANGE)
        # 결과 저장 (test 결과)
        if len(test_trades) > 0:
            run_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_dt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            test_trades['run_time'] = run_time
            csv_name = f'optimized_trades_{file_dt}.csv'
            test_trades.to_csv(csv_name, index=False)
            print(f"최적화된 거래 내역이 '{csv_name}'에 저장되었습니다.")
        return test_metrics, test_trades

def main():
    """메인 실행 함수"""
    optimizer = ParameterOptimizer()
    # 1. 파라미터 최적화
    best_params = optimizer.optimize(n_trials=N_TRIALS)
    # 2. 최적 파라미터로 전체 검증 (train/test)
    metrics, trades = optimizer.validate_best_params()
    # 3. 결과 요약
    print(f"\n=== 최종 결과 ===")
    if metrics and 'total_trades' in metrics:
        print(f"총 거래: {metrics['total_trades']}")
        print(f"승률: {metrics['win_rate']:.2%}")
        print(f"평균 수익률: {metrics['avg_return']:.2%}")
        print(f"샤프 비율: {metrics['sharpe_ratio']:.3f}")
        print(f"총 수익률: {metrics['total_return']:.2%}")
    else:
        print("거래가 없습니다.")

if __name__ == "__main__":
    main() 