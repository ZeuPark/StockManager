import random
import glob
import os
import pandas as pd
from parameter_optimizer import ParameterOptimizer

# === CONFIG ===
N_EXPERIMENTS = 10  # 실험 반복 횟수
TRAIN_RATIO = 0.7  # train/test 종목 비율
N_STOCKS = 30      # 한 번에 사용할 전체 종목 수
N_TRIALS = 50      # Optuna trial 수(실험 속도 고려)
TRAIN_RANGE = ('2024-01-01', '2024-12-31')
TEST_RANGE = ('2025-06-01', '2025-06-30')

# 종목 pool 준비
glob_path = os.path.join('minute_data', '*_1min.csv')
csv_files = glob.glob(glob_path)
all_codes = [os.path.basename(f).split('_')[0] for f in csv_files]

results = []

for exp in range(N_EXPERIMENTS):
    print(f"\n=== [실험 {exp+1}/{N_EXPERIMENTS}] 종목 랜덤 분리 및 최적화 ===")
    random.seed(42 + exp)  # 실험별로 seed 다르게
    codes = random.sample(all_codes, N_STOCKS)
    n_train = int(N_STOCKS * TRAIN_RATIO)
    train_codes = codes[:n_train]
    test_codes = codes[n_train:]
    print(f"Train 종목({len(train_codes)}): {train_codes}")
    print(f"Test 종목({len(test_codes)}): {test_codes}")

    # 최적화 (train set)
    optimizer = ParameterOptimizer()
    optimizer.data_path = 'minute_data'
    # train set만 사용하도록 objective 함수 임시 patch
    orig_objective = optimizer.objective
    def patched_objective(trial):
        # train set만 사용
        params = {
            'theta_spike': trial.suggest_float('theta_spike', 0.0, 0.20, step=0.002),
            'theta_spike_low': trial.suggest_float('theta_spike_low', 0.0, 0.10, step=0.001),
            'theta_15m': trial.suggest_float('theta_15m', 0.0, 0.15, step=0.002),
            'theta_vol': trial.suggest_float('theta_vol', 0.0, 0.50, step=0.005),
            'theta_pull': trial.suggest_float('theta_pull', 0.0, 0.30, step=0.005),
            'tp_pct': trial.suggest_float('tp_pct', 0.005, 0.50, step=0.005),
            'sl_pct': trial.suggest_float('sl_pct', 0.005, 0.30, step=0.002),
            'orb_delay_min': trial.suggest_int('orb_delay_min', 2, 20),
            'orb_max_min': trial.suggest_int('orb_max_min', 10, 60)
        }
        try:
            from core.gradual_rise_backtest import GradualRiseBacktest
            backtest = GradualRiseBacktest(optimizer.data_path)
            backtest.parameters.update(params)
            metrics, trades = backtest.run_backtest(stock_codes=train_codes, date_range=TRAIN_RANGE, verbose=False)
            if len(trades) == 0:
                return -2000
            sharpe = metrics['sharpe_ratio']
            win_rate = metrics['win_rate']
            total_return = metrics['total_return']
            objective_value = sharpe * 0.4 + win_rate * 0.3 + total_return * 0.3
            if len(trades) < 10:
                objective_value *= 0.2
            return objective_value
        except Exception as e:
            print(f"Trial 에러: {e}")
            return -2000
    optimizer.objective = patched_objective
    best_params = optimizer.optimize(n_trials=N_TRIALS)

    # 검증 (test set)
    from core.gradual_rise_backtest import GradualRiseBacktest
    backtest = GradualRiseBacktest('minute_data')
    backtest.parameters.update(best_params)
    test_metrics, test_trades = backtest.run_backtest(stock_codes=test_codes, date_range=TEST_RANGE, verbose=False)

    # 결과 기록
    result = {
        'exp': exp+1,
        'train_codes': train_codes,
        'test_codes': test_codes,
        'best_params': best_params,
        'test_total_trades': test_metrics.get('total_trades', 0),
        'test_win_rate': test_metrics.get('win_rate', 0),
        'test_avg_return': test_metrics.get('avg_return', 0),
        'test_sharpe_ratio': test_metrics.get('sharpe_ratio', 0),
        'test_total_return': test_metrics.get('total_return', 0)
    }
    results.append(result)
    print(f"[실험 {exp+1}] Test 성과: {test_metrics}")

# 전체 결과 DataFrame/CSV 저장
results_df = pd.DataFrame(results)
results_df.to_csv('multi_experiment_results.csv', index=False)
print("\n=== 전체 실험 결과 요약 ===")
print(results_df[['exp','test_total_trades','test_win_rate','test_avg_return','test_sharpe_ratio','test_total_return']])
print("\n평균 Test 성과:")
print(results_df[['test_total_trades','test_win_rate','test_avg_return','test_sharpe_ratio','test_total_return']].mean()) 