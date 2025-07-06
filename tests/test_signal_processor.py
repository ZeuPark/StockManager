#!/usr/bin/env python3
"""
Signal Processor Test
신호 처리기 테스트 스크립트
"""

import sys
import os
import asyncio
sys.path.append('.')

from config.settings import Settings
from orders.signal_processor import SignalProcessor
from analysis.momentum_analyzer import StockData, ConditionResult
from datetime import datetime

async def test_signal_processor():
    """신호 처리기 테스트"""
    print("=== 신호 처리기 테스트 ===")
    
    # 설정 로드
    settings = Settings("simulation")
    processor = SignalProcessor(settings)
    
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
    
    # 테스트 조건 결과 생성
    test_conditions = {
        "volume_spike": ConditionResult(
            condition_name="volume_spike",
            is_satisfied=True,
            current_value=1.5,
            threshold=1.2,
            description="거래량 급증 조건",
            timestamp=datetime.now()
        ),
        "execution_strength": ConditionResult(
            condition_name="execution_strength",
            is_satisfied=True,
            current_value=2.0,
            threshold=1.5,
            description="체결강도 조건",
            timestamp=datetime.now()
        ),
        "price_breakout": ConditionResult(
            condition_name="price_breakout",
            is_satisfied=True,
            current_value=0.01,
            threshold=0.005,
            description="가격 돌파 조건",
            timestamp=datetime.now()
        )
    }
    
    print(f"테스트 데이터: {test_data.code} @ {test_data.current_price:,}원")
    print()
    
    # 신뢰도 계산 테스트
    print("--- 신뢰도 계산 테스트 ---")
    confidence = processor.calculate_confidence(test_conditions)
    print(f"신뢰도: {confidence:.3f}")
    
    # 포지션 크기 계산 테스트
    print("\n--- 포지션 크기 계산 테스트 ---")
    position_size = processor.calculate_position_size(test_data)
    print(f"계산된 포지션 크기: {position_size}주")
    print(f"예상 투자 금액: {position_size * test_data.current_price:,}원")
    
    # 계좌 정보 업데이트
    processor.update_account_info(
        balance=10000000,  # 1천만원
        positions=[]
    )
    
    # 리스크 한도 체크 테스트
    print("\n--- 리스크 한도 체크 테스트 ---")
    risk_check = processor.check_risk_limits(test_data, "buy")
    print(f"리스크 한도 통과: {'✅' if risk_check else '❌'}")
    
    # 중복 신호 체크 테스트
    print("\n--- 중복 신호 체크 테스트 ---")
    is_duplicate = processor.is_duplicate_signal(test_data.code)
    print(f"중복 신호 여부: {'✅' if is_duplicate else '❌'}")
    
    # 신호 처리 테스트
    print("\n--- 신호 처리 테스트 ---")
    await processor.process_trading_signal(test_data, test_conditions)
    
    # 신호 요약 테스트
    print("\n--- 신호 요약 테스트 ---")
    summary = processor.get_signal_summary()
    print(f"총 신호 수: {summary.get('total_signals', 0)}")
    print(f"최근 신호 수: {summary.get('recent_signals', 0)}")
    print(f"평균 신뢰도: {summary.get('average_confidence', 0):.3f}")
    
    if summary.get('signal_types'):
        print("신호 타입별 통계:")
        for signal_type, count in summary['signal_types'].items():
            print(f"  {signal_type}: {count}개")
    
    if summary.get('top_stocks'):
        print("상위 종목별 통계:")
        for stock, count in summary['top_stocks'].items():
            print(f"  {stock}: {count}개")

async def test_different_scenarios():
    """다양한 시나리오 테스트"""
    print("\n=== 다양한 시나리오 테스트 ===")
    
    settings = Settings("simulation")
    processor = SignalProcessor(settings)
    
    # 시나리오 1: 낮은 신뢰도
    print("\n--- 시나리오 1: 낮은 신뢰도 ---")
    low_confidence_conditions = {
        "volume_spike": ConditionResult(
            condition_name="volume_spike",
            is_satisfied=True,
            current_value=1.1,  # 낮은 값
            threshold=1.2,
            description="거래량 급증 조건",
            timestamp=datetime.now()
        )
    }
    
    test_data = StockData(
        code="000660",
        current_price=150000,
        volume=1000000,
        execution_strength=1.0,
        high_price=151000,
        low_price=149000,
        open_price=150500,
        prev_close=150000,
        timestamp=datetime.now()
    )
    
    confidence = processor.calculate_confidence(low_confidence_conditions)
    print(f"낮은 신뢰도: {confidence:.3f}")
    
    # 시나리오 2: 중복 신호
    print("\n--- 시나리오 2: 중복 신호 ---")
    processor.recent_signals["005930"] = datetime.now()  # 최근 신호 기록
    is_duplicate = processor.is_duplicate_signal("005930")
    print(f"중복 신호 여부: {'✅' if is_duplicate else '❌'}")
    
    # 시나리오 3: 리스크 한도 초과
    print("\n--- 시나리오 3: 리스크 한도 초과 ---")
    processor.current_loss = 500000  # 50만원 손실 (한도 초과)
    risk_check = processor.check_risk_limits(test_data, "buy")
    print(f"리스크 한도 통과: {'✅' if risk_check else '❌'}")

if __name__ == "__main__":
    asyncio.run(test_signal_processor())
    asyncio.run(test_different_scenarios())
    print("\n✅ 신호 처리기 테스트 완료!") 