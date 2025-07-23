#!/usr/bin/env python3
"""
완만 상승 패턴 백테스트 테스트 스크립트
"""

from core.gradual_rise_backtest import GradualRiseBacktest
import time

def test_basic_backtest():
    """기본 백테스트 테스트"""
    print("=== 기본 백테스트 테스트 시작 ===")
    
    # 백테스트 인스턴스 생성
    backtest = GradualRiseBacktest()
    
    # 테스트용 파라미터 설정 (보수적)
    backtest.parameters.update({
        'theta_spike': 0.03,      # 3% - 더 관대하게
        'theta_15m': 0.005,       # 0.5% - 더 관대하게
        'tp_pct': 0.03,           # 3%
        'sl_pct': 0.015,          # 1.5%
    })
    
    # 일부 종목으로만 테스트 (속도 향상)
    test_codes = ['000100', '000150', '000200', '000250', '000300']
    
    start_time = time.time()
    
    try:
        # 백테스트 실행
        metrics, trades = backtest.run_backtest(stock_codes=test_codes)
        
        end_time = time.time()
        print(f"\n테스트 완료 시간: {end_time - start_time:.2f}초")
        
        # 결과 요약
        if len(trades) > 0:
            print(f"\n=== 테스트 결과 요약 ===")
            print(f"총 거래: {metrics['total_trades']}")
            print(f"승률: {metrics['win_rate']:.2%}")
            print(f"평균 수익률: {metrics['avg_return']:.2%}")
            print(f"샤프 비율: {metrics['sharpe_ratio']:.3f}")
            print(f"총 수익률: {metrics['total_return']:.2%}")
            
            # 거래 내역 저장
            trades.to_csv('test_trades.csv', index=False)
            print(f"테스트 거래 내역이 'test_trades.csv'에 저장되었습니다.")
        else:
            print("거래가 발생하지 않았습니다. 파라미터를 조정해보세요.")
            
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_parameter_sensitivity():
    """파라미터 민감도 테스트"""
    print("\n=== 파라미터 민감도 테스트 ===")
    
    backtest = GradualRiseBacktest()
    test_codes = ['000100', '000150', '000200']
    
    # 파라미터 조합 테스트
    param_combinations = [
        {'theta_spike': 0.025, 'theta_15m': 0.003, 'tp_pct': 0.02, 'sl_pct': 0.01},
        {'theta_spike': 0.03, 'theta_15m': 0.005, 'tp_pct': 0.03, 'sl_pct': 0.015},
        {'theta_spike': 0.035, 'theta_15m': 0.008, 'tp_pct': 0.04, 'sl_pct': 0.02},
    ]
    
    results = []
    
    for i, params in enumerate(param_combinations):
        print(f"\n--- 파라미터 조합 {i+1} ---")
        print(f"파라미터: {params}")
        
        backtest.parameters.update(params)
        
        try:
            metrics, trades = backtest.run_backtest(stock_codes=test_codes)
            
            if len(trades) > 0:
                result = {
                    'params': params,
                    'total_trades': metrics['total_trades'],
                    'win_rate': metrics['win_rate'],
                    'avg_return': metrics['avg_return'],
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'total_return': metrics['total_return']
                }
                results.append(result)
                
                print(f"거래 수: {metrics['total_trades']}")
                print(f"승률: {metrics['win_rate']:.2%}")
                print(f"평균 수익률: {metrics['avg_return']:.2%}")
                print(f"샤프 비율: {metrics['sharpe_ratio']:.3f}")
            else:
                print("거래 없음")
                
        except Exception as e:
            print(f"오류: {e}")
    
    # 결과 비교
    if results:
        print(f"\n=== 파라미터 비교 ===")
        for i, result in enumerate(results):
            print(f"조합 {i+1}: 거래={result['total_trades']}, "
                  f"승률={result['win_rate']:.2%}, "
                  f"수익률={result['avg_return']:.2%}, "
                  f"샤프={result['sharpe_ratio']:.3f}")

def main():
    """메인 실행 함수"""
    print("완만 상승 패턴 백테스트 테스트 시작")
    
    # 1. 기본 백테스트 테스트
    test_basic_backtest()
    
    # 2. 파라미터 민감도 테스트
    test_parameter_sensitivity()
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    main() 