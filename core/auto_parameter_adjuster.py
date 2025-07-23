import random
import glob
import os
import pandas as pd
from core.gradual_rise_backtest import GradualRiseBacktest
import datetime

# === CONFIG ===
MAX_ITERATIONS = 10  # 최대 반복 횟수
TARGET_SIGNALS = 30  # 목표 신호 수
MIN_SIGNALS = 10     # 최소 신호 수 (이보다 적으면 경고)
PARAMETER_RELAX_RATIO = 0.8  # 파라미터 완화 비율 (0.8 = 20% 완화)
N_STOCKS = 30       # 사용할 종목 수
TEST_RANGE = ('2025-06-01', '2025-06-30')

# 종목 pool 준비
glob_path = os.path.join('minute_data', '*_1min.csv')
csv_files = glob.glob(glob_path)
all_codes = [os.path.basename(f).split('_')[0] for f in csv_files]
random.seed(42)
TEST_CODES = random.sample(all_codes, N_STOCKS)

class AutoParameterAdjuster:
    """파라미터 자동 완화 루프"""
    
    def __init__(self):
        self.backtest = GradualRiseBacktest()
        self.iteration_results = []
        self.current_params = self.backtest.parameters.copy()
        
    def adjust_parameters(self, current_params, relax_ratio=0.8):
        """파라미터 완화"""
        adjusted_params = current_params.copy()
        
        # 완화할 파라미터들 (임계값을 낮춤)
        relax_params = {
            'theta_spike': 0.9,        # 시초 급등 제외 완화 (90%)
            'theta_spike_low': 0.7,    # 최소 상승률 완화 (70%)
            'theta_15m': 0.7,          # 15분 누적상승 완화 (70%)
            'theta_vol': 0.8,          # 거래량 완화 (80%)
            'theta_pull': 1.2,         # 저점 하락폭 완화 (120%)
            'tp_pct': 1.1,             # 익절 완화 (110%)
            'sl_pct': 1.1,             # 손절 완화 (110%)
        }
        
        # 기술적 지표 파라미터 완화
        tech_relax_params = {
            'rsi_min': 0.8,            # RSI 하한 완화 (80%)
            'rsi_max': 1.1,            # RSI 상한 완화 (110%)
            'bb_position_min': 0.8,    # 볼린저 밴드 하한 완화 (80%)
            'bb_position_max': 1.1,    # 볼린저 밴드 상한 완화 (110%)
            'momentum_threshold': 0.7, # 모멘텀 임계값 완화 (70%)
            'volume_ratio_min': 0.8,   # 거래량 비율 완화 (80%)
        }
        
        # 파라미터 완화 적용
        for param, ratio in relax_params.items():
            if param in adjusted_params:
                if param in ['theta_spike', 'theta_spike_low', 'theta_15m', 'theta_vol']:
                    # 임계값을 낮춤 (조건 완화)
                    adjusted_params[param] *= ratio
                elif param in ['theta_pull']:
                    # 하락폭 허용 범위를 늘림
                    adjusted_params[param] *= ratio
                elif param in ['tp_pct', 'sl_pct']:
                    # 익절/손절 범위를 늘림
                    adjusted_params[param] *= ratio
        
        # 기술적 지표 파라미터 완화
        for param, ratio in tech_relax_params.items():
            if param in adjusted_params:
                if param in ['rsi_min', 'bb_position_min']:
                    # 하한을 낮춤
                    adjusted_params[param] *= ratio
                elif param in ['rsi_max', 'bb_position_max']:
                    # 상한을 높임
                    adjusted_params[param] *= ratio
                elif param in ['momentum_threshold']:
                    # 임계값을 낮춤
                    adjusted_params[param] *= ratio
                elif param in ['volume_ratio_min']:
                    # 거래량 조건 완화
                    adjusted_params[param] *= ratio
        
        return adjusted_params
    
    def run_iteration(self, iteration, params):
        """한 번의 반복 실행"""
        print(f"\n=== [반복 {iteration}] 파라미터 자동 완화 ===")
        print(f"현재 파라미터:")
        for key, value in params.items():
            if key in ['theta_spike', 'theta_spike_low', 'theta_15m', 'theta_vol', 'theta_pull', 'tp_pct', 'sl_pct']:
                print(f"  {key}: {value:.4f}")
        
        # 백테스트 실행
        self.backtest.parameters.update(params)
        metrics, trades = self.backtest.run_backtest(stock_codes=TEST_CODES, date_range=TEST_RANGE, verbose=False)
        
        # 결과 기록
        result = {
            'iteration': iteration,
            'params': params.copy(),
            'total_trades': metrics.get('total_trades', 0),
            'win_rate': metrics.get('win_rate', 0),
            'avg_return': metrics.get('avg_return', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'total_return': metrics.get('total_return', 0),
            'max_drawdown': metrics.get('max_drawdown', 0)
        }
        
        print(f"결과: 거래={result['total_trades']}, 승률={result['win_rate']:.2%}, "
              f"수익률={result['total_return']:.2%}, 샤프={result['sharpe_ratio']:.3f}")
        
        return result
    
    def auto_adjust_loop(self):
        """자동 완화 루프 실행"""
        print("=== 파라미터 자동 완화 루프 시작 ===")
        print(f"목표 신호 수: {TARGET_SIGNALS}, 최소 신호 수: {MIN_SIGNALS}")
        
        current_params = self.backtest.parameters.copy()
        
        for iteration in range(1, MAX_ITERATIONS + 1):
            # 현재 파라미터로 테스트
            result = self.run_iteration(iteration, current_params)
            self.iteration_results.append(result)
            
            signals = result['total_trades']
            
            # 목표 달성 체크
            if signals >= TARGET_SIGNALS:
                print(f"\n🎉 목표 달성! 신호 수: {signals} (목표: {TARGET_SIGNALS})")
                break
            
            # 최소 신호 수 미달 경고
            if signals < MIN_SIGNALS:
                print(f"⚠️  경고: 신호 수가 너무 적습니다 ({signals} < {MIN_SIGNALS})")
            
            # 파라미터 완화
            if iteration < MAX_ITERATIONS:
                print(f"파라미터 완화 중... (신호 수: {signals} < 목표: {TARGET_SIGNALS})")
                current_params = self.adjust_parameters(current_params, PARAMETER_RELAX_RATIO)
            else:
                print(f"최대 반복 횟수 도달 ({MAX_ITERATIONS})")
        
        # 최종 결과 리포트
        self.print_final_report()
        
        return self.iteration_results
    
    def print_final_report(self):
        """최종 결과 리포트"""
        print(f"\n{'='*60}")
        print("=== 파라미터 자동 완화 루프 최종 결과 ===")
        print(f"{'='*60}")
        
        # 결과 요약 테이블
        print(f"{'반복':<4} {'신호수':<6} {'승률':<8} {'평균수익률':<10} {'총수익률':<10} {'샤프비율':<8}")
        print("-" * 60)
        
        for result in self.iteration_results:
            print(f"{result['iteration']:<4} {result['total_trades']:<6} "
                  f"{result['win_rate']:.2%} {result['avg_return']:.2%} "
                  f"{result['total_return']:.2%} {result['sharpe_ratio']:.3f}")
        
        # 최적 결과 찾기
        best_result = max(self.iteration_results, key=lambda x: x['total_trades'])
        print(f"\n🏆 최적 결과 (반복 {best_result['iteration']}):")
        print(f"  신호 수: {best_result['total_trades']}")
        print(f"  승률: {best_result['win_rate']:.2%}")
        print(f"  총 수익률: {best_result['total_return']:.2%}")
        print(f"  샤프 비율: {best_result['sharpe_ratio']:.3f}")
        
        # 파라미터 변화 추이
        print(f"\n📊 파라미터 변화 추이:")
        key_params = ['theta_spike', 'theta_15m', 'theta_vol', 'tp_pct']
        for param in key_params:
            values = [r['params'].get(param, 0) for r in self.iteration_results]
            print(f"  {param}: {values}")
        
        # CSV 저장
        results_df = pd.DataFrame(self.iteration_results)
        file_dt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_name = f'auto_parameter_adjustment_{file_dt}.csv'
        results_df.to_csv(csv_name, index=False)
        print(f"\n📁 결과가 '{csv_name}'에 저장되었습니다.")

def main():
    """메인 실행 함수"""
    adjuster = AutoParameterAdjuster()
    results = adjuster.auto_adjust_loop()
    
    return results

if __name__ == "__main__":
    main() 