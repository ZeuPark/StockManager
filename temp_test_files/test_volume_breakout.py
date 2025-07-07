#!/usr/bin/env python3
"""
전일 거래량 돌파 감지 테스트
실시간으로 전일 거래량을 돌파하는 종목들을 감지하는 기능을 테스트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from utils.token_manager import TokenManager
from analysis.volume_scanner import VolumeScanner
from utils.logger import get_logger

logger = get_logger("volume_breakout_test")

async def test_volume_breakout():
    """전일 거래량 돌파 감지 테스트"""
    print("=== 전일 거래량 돌파 감지 테스트 ===")
    
    # 설정 로드
    settings = Settings()
    token_manager = TokenManager(settings)
    
    # 스캐너 초기화
    scanner = VolumeScanner(settings, token_manager)
    
    print(f"환경: {settings.ENVIRONMENT}")
    print(f"스캔 간격: {scanner.scan_interval}초")
    print(f"최소 등락률: {scanner.min_price_change:.1%}")
    print(f"최소 거래대금: {scanner.min_trade_value:,}원")
    print(f"최소 체결강도: {scanner.min_execution_strength:.1%}")
    print()
    
    try:
        print("=== 전일 거래량 돌파 감지 시작 ===")
        print("(돌파 순간을 감지하면 즉시 알림이 표시됩니다)")
        print()
        
        # 3회 스캔 실행 (실제로는 무한 루프)
        for i in range(3):
            print(f"\n=== {i+1}번째 스캔 시작 ===")
            
            # 거래량 후보 스캔
            candidates = await scanner.scan_volume_candidates()
            
            if candidates:
                print(f"[FOUND] 발견된 후보 종목: {len(candidates)}개")
                for candidate in candidates:
                    print(f"\n  [STOCK] {candidate.stock_name}({candidate.stock_code})")
                    print(f"     현재가: {candidate.current_price:,}원")
                    print(f"     등락률: {candidate.price_change:.2f}%")
                    print(f"     거래대금: {candidate.trade_value:,}원")
                    print(f"     체결강도: {candidate.score:.1f}%")
                    print(f"     추세: {candidate.ma_trend}")
            else:
                print("[EMPTY] 조건을 만족하는 후보 종목이 없습니다.")
            
            # 돌파 현황 요약
            breakout_summary = scanner.get_breakout_summary()
            print(f"\n[SUMMARY] 돌파 현황:")
            print(f"   총 돌파 종목: {breakout_summary['total_breakouts']}개")
            print(f"   돌파 종목 목록: {breakout_summary['breakout_stocks'][:10]}...")  # 상위 10개만 표시
            
            if i < 2:  # 마지막 스캔이 아니면 대기
                print(f"\n{scanner.scan_interval}초 후 다음 스캔...")
                await asyncio.sleep(scanner.scan_interval)
        
        print("\n=== 테스트 완료 ===")
        
        # 최종 돌파 현황
        final_summary = scanner.get_breakout_summary()
        print(f"\n[FINAL] 최종 돌파 현황:")
        print(f"   총 돌파 종목: {final_summary['total_breakouts']}개")
        if final_summary['breakout_stocks']:
            print(f"   돌파 종목들:")
            for i, stock_code in enumerate(final_summary['breakout_stocks'], 1):
                print(f"     {i}. {stock_code}")
        
    except Exception as e:
        print(f"\n[ERROR] 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_volume_breakout()) 