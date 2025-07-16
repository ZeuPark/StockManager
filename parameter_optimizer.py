import optuna
import pandas as pd
import numpy as np
from gradual_rise_backtest import GradualRiseBacktest
import warnings
import glob
import os
import random
import datetime
warnings.filterwarnings('ignore')

# === 1. minute_data에서 랜덤하게 20개 종목 추출 (실행 시 한 번만) ===
csv_files = glob.glob(os.path.join("minute_data", "*_1min.csv"))
all_codes = [os.path.basename(f).split('_')[0] for f in csv_files]
random.seed(42)  # 재현성
TEST_CODES = random.sample(all_codes, 20)
print("최적화에 사용할 종목:", TEST_CODES)

class ParameterOptimizer:
    """파라미터 최적화 클래스"""
    
    def __init__(self, data_path="minute_data"):
        self.data_path = data_path
        self.best_params = None
        self.best_value = -np.inf
        
    def objective(self, trial):
        """Optuna 목표 함수"""
        
        # === 2. 파라미터 탐색 범위 전반적으로 더 넓힘 ===
        params = {
            'theta_spike': trial.suggest_float('theta_spike', 0.001, 0.15, step=0.002),
            'theta_spike_low': trial.suggest_float('theta_spike_low', 0.0, 0.05, step=0.001),
            'theta_15m': trial.suggest_float('theta_15m', 0.0, 0.10, step=0.002),
            'theta_vol': trial.suggest_float('theta_vol', 0.005, 0.30, step=0.005),
            'theta_pull': trial.suggest_float('theta_pull', 0.01, 0.20, step=0.005),
            'tp_pct': trial.suggest_float('tp_pct', 0.01, 0.40, step=0.005),  # 익절 최대 40%
            'sl_pct': trial.suggest_float('sl_pct', 0.005, 0.20, step=0.002), # 손절 최대 20%
            'orb_delay_min': trial.suggest_int('orb_delay_min', 3, 20),
            'orb_max_min': trial.suggest_int('orb_max_min', 10, 60)
        }
        
        try:
            # 백테스트 실행 (항상 동일한 test_codes 사용)
            backtest = GradualRiseBacktest(self.data_path)
            backtest.parameters.update(params)
            # 2025년 6월 한 달만 대상으로 백테스트
            metrics, trades = backtest.run_backtest(stock_codes=TEST_CODES, date_range=('2025-06-01', '2025-06-30'))
            
            if len(trades) == 0:
                return -1000  # 거래가 없으면 매우 낮은 점수
            
            # 목표 함수: Sharpe Ratio + Win Rate + Total Return
            sharpe = metrics['sharpe_ratio']
            win_rate = metrics['win_rate']
            total_return = metrics['total_return']
            
            objective_value = sharpe * 0.4 + win_rate * 0.3 + total_return * 0.3
            if len(trades) < 10:
                objective_value *= 0.5
            
            print(f"Trial {trial.number}: Sharpe={sharpe:.3f}, WinRate={win_rate:.2%}, "
                  f"Return={total_return:.2%}, Trades={len(trades)}, Obj={objective_value:.3f}")
            
            return objective_value
            
        except Exception as e:
            print(f"Trial {trial.number} 에러: {e}")
            return -1000
    
    def optimize(self, n_trials=100):
        """파라미터 최적화 실행"""
        print("=== 파라미터 최적화 시작 ===")
        
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        study.optimize(self.objective, n_trials=n_trials)
        
        # 최적 파라미터 저장
        self.best_params = study.best_params
        self.best_value = study.best_value
        
        print(f"\n최적 파라미터:")
        for param, value in self.best_params.items():
            print(f"  {param}: {value}")
        print(f"최적 목표값: {self.best_value:.3f}")
        
        return self.best_params
    
    def validate_best_params(self, stock_codes=None):
        """최적 파라미터로 전체 검증"""
        print("\n=== 최적 파라미터 검증 ===")
        
        backtest = GradualRiseBacktest(self.data_path)
        backtest.parameters.update(self.best_params)
        # 2025년 6월 한 달만 대상으로 전체 검증
        metrics, trades = backtest.run_backtest(stock_codes=TEST_CODES, date_range=('2025-06-01', '2025-06-30'))
        
        # 결과 저장 (실행 시간 및 파일명에 날짜+시간 추가)
        if len(trades) > 0:
            run_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_dt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            trades['run_time'] = run_time
            csv_name = f'optimized_trades_{file_dt}.csv'
            trades.to_csv(csv_name, index=False)
            print(f"최적화된 거래 내역이 '{csv_name}'에 저장되었습니다.")
        
        return metrics, trades

def main():
    """메인 실행 함수"""
    optimizer = ParameterOptimizer()
    
    # 1. 파라미터 최적화
    best_params = optimizer.optimize(n_trials=50)
    
    # 2. 최적 파라미터로 전체 검증
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