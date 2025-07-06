#!/usr/bin/env python3
"""
Momentum Analyzer Test
모멘텀 분석기 테스트 스크립트
"""

import sys
import os
sys.path.append('.')

from config.settings import Settings
from analysis.momentum_analyzer import MomentumAnalyzer, StockData
from datetime import datetime

def test_momentum_analyzer():
    """모멘텀 분석기 테스트"""
    print("=== 모멘텀 분석기 테스트 ===")
    
    # 설정 로드
    settings = Settings("simulation")
    analyzer = MomentumAnalyzer(settings)
    
    # 테스트 데이터 생성
    test_data = StockData(
        code="005930",  # 삼성전자
        current_price=75000,
        volume=1000000,
        execution_strength=2.0,
        high_price=75500,
        low_price=74500,
        open_price=74800,
        prev_close=74700,
        timestamp=datetime.now()
    )
    
    print(f"테스트 데이터: {test_data.code} @ {test_data.current_price:,}원")
    print(f"거래량: {test_data.volume:,}")
    print(f"체결강도: {test_data.execution_strength}")
    print()
    
    # 개별 조건 테스트
    print("--- 개별 조건 테스트 ---")
    
    # 거래량 급증 조건
    volume_result = analyzer.check_volume_spike(test_data)
    print(f"거래량 급증: {volume_result.is_satisfied} (값: {volume_result.current_value:.3f})")
    
    # 체결강도 조건
    strength_result = analyzer.check_execution_strength(test_data)
    print(f"체결강도: {strength_result.is_satisfied} (값: {strength_result.current_value:.3f})")
    
    # 가격 돌파 조건
    breakout_result = analyzer.check_price_breakout(test_data)
    print(f"가격 돌파: {breakout_result.is_satisfied} (값: {breakout_result.current_value:.3f})")
    
    print()
    
    # 전체 조건 분석
    print("--- 전체 조건 분석 ---")
    is_signal, results = analyzer.is_trading_signal(test_data)
    print(f"매매 신호 발생: {is_signal}")
    
    for condition_name, result in results.items():
        status = "✅" if result.is_satisfied else "❌"
        print(f"  {status} {result.description}: {result.current_value:.3f} >= {result.threshold}")
    
    print()
    
    # 조건 요약
    summary = analyzer.get_condition_summary(test_data.code)
    print("--- 조건 요약 ---")
    print(f"종목: {summary['stock_code']}")
    print(f"현재가: {summary['current_price']:,}원")
    print(f"시간: {summary['timestamp']}")
    
    for condition_name, condition in summary['conditions'].items():
        status = "✅" if condition['satisfied'] else "❌"
        print(f"  {status} {condition['description']}: {condition['current_value']:.3f}")

def test_different_conditions():
    """다양한 조건으로 테스트"""
    print("\n=== 다양한 조건 테스트 ===")
    
    settings = Settings("simulation")
    analyzer = MomentumAnalyzer(settings)
    
    # 조건별로 다른 테스트 데이터
    test_cases = [
        {
            "name": "모든 조건 만족",
            "data": StockData(
                code="000660",  # SK하이닉스
                current_price=150000,
                volume=2000000,
                execution_strength=2.5,
                high_price=151000,
                low_price=149000,
                open_price=150500,
                prev_close=149500,
                timestamp=datetime.now()
            )
        },
        {
            "name": "거래량 부족",
            "data": StockData(
                code="035420",  # NAVER
                current_price=200000,
                volume=500000,  # 낮은 거래량
                execution_strength=1.8,
                high_price=201000,
                low_price=199000,
                open_price=200500,
                prev_close=200000,
                timestamp=datetime.now()
            )
        },
        {
            "name": "체결강도 부족",
            "data": StockData(
                code="051910",  # LG화학
                current_price=500000,
                volume=1500000,
                execution_strength=1.0,  # 낮은 체결강도
                high_price=501000,
                low_price=499000,
                open_price=500500,
                prev_close=500000,
                timestamp=datetime.now()
            )
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        data = test_case['data']
        
        is_signal, results = analyzer.is_trading_signal(data)
        print(f"종목: {data.code} @ {data.current_price:,}원")
        print(f"신호 발생: {'✅' if is_signal else '❌'}")
        
        for condition_name, result in results.items():
            status = "✅" if result.is_satisfied else "❌"
            print(f"  {status} {result.description}: {result.current_value:.3f}")

if __name__ == "__main__":
    test_momentum_analyzer()
    test_different_conditions()
    print("\n✅ 모멘텀 분석기 테스트 완료!") 