#!/usr/bin/env python3
"""
Strategy 2 Analyzer Test
전략 2 분석기 테스트 스크립트
"""

import sys
import os
import asyncio
sys.path.append('.')

from config.settings import Settings
from analysis.strategy2_analyzer import Strategy2Analyzer, Strategy2Candidate
from utils.token_manager import TokenManager
from datetime import datetime

async def test_strategy2_analyzer():
    """전략 2 분석기 테스트"""
    print("=== 전략 2 분석기 테스트 ===")
    
    # 설정 로드
    settings = Settings("simulation")
    token_manager = TokenManager(settings)
    
    # 전략 2 분석기 초기화
    analyzer = Strategy2Analyzer(settings, token_manager)
    
    print(f"전략 2 분석기 초기화 완료")
    print(f"핵심 조건: {analyzer.core_conditions}")
    print(f"추가 조건: {analyzer.additional_conditions}")
    print(f"전략 로직: {analyzer.strategy_logic}")
    print()
    
    # 테스트 데이터 생성
    test_stock_data = {
        "stk_cd": "005930",  # 삼성전자
        "stk_nm": "삼성전자",
        "cur_prc": "75000",
        "flu_rt": 1.5,  # 등락률 +1.5%
        "sdnin_rt": "80.0%",  # 거래량비율 80%
        "prev_trde_qty": 1000000,
        "now_trde_qty": 1800000
    }
    
    print("테스트 종목 데이터:")
    print(f"  종목코드: {test_stock_data['stk_cd']}")
    print(f"  종목명: {test_stock_data['stk_nm']}")
    print(f"  현재가: {test_stock_data['cur_prc']}원")
    print(f"  등락률: {test_stock_data['flu_rt']}%")
    print(f"  거래량비율: {test_stock_data['sdnin_rt']}")
    print()
    
    # 개별 종목 분석 테스트
    print("개별 종목 분석 테스트...")
    candidate = await analyzer.analyze_stock(test_stock_data)
    
    if candidate:
        print(f"분석 결과:")
        print(f"  핵심 조건 만족: {candidate.core_conditions_met}")
        print(f"  추가 조건 만족: {candidate.additional_conditions_met}")
        print(f"  최종 매수 신호: {candidate.final_signal}")
        print(f"  신뢰도 점수: {candidate.confidence_score:.2f}")
        print(f"  거래대금: {candidate.market_amount/100000000:.1f}억원")
        print(f"  이동평균선: {candidate.ma_short:.0f} > {candidate.ma_long:.0f}")
    else:
        print("분석 실패")
    
    print()
    
    # 조건 확인 테스트
    print("조건 확인 테스트...")
    
    # 핵심 조건 테스트
    core_result = analyzer.check_core_conditions(1.5, 80.0)
    print(f"핵심 조건 (등락률 1.5%, 거래량비율 80%): {core_result}")
    
    core_result2 = analyzer.check_core_conditions(5.0, 150.0)
    print(f"핵심 조건 (등락률 5.0%, 거래량비율 150%): {core_result2}")
    
    # 추가 조건 테스트
    additional_result = analyzer.check_additional_conditions(200_000_000, 75000, 74000)
    print(f"추가 조건 (거래대금 2억원, MA5 > MA20): {additional_result}")
    
    additional_result2 = analyzer.check_additional_conditions(100_000_000, 74000, 75000)
    print(f"추가 조건 (거래대금 1억원, MA5 < MA20): {additional_result2}")
    
    print()
    
    # 신뢰도 점수 계산 테스트
    print("신뢰도 점수 계산 테스트...")
    confidence = analyzer.calculate_confidence_score(1.5, 80.0, 200_000_000, 75000, 74000)
    print(f"신뢰도 점수: {confidence:.2f}")
    
    print()
    
    # 상태 조회 테스트
    print("상태 조회 테스트...")
    status = analyzer.get_auto_trade_status()
    print(f"자동매매 상태: {status}")
    
    print()
    print("=== 전략 2 분석기 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(test_strategy2_analyzer()) 