#!/usr/bin/env python3
"""
실제 거래량 스캐너 테스트
실제 API를 호출하여 조건을 만족하는 종목들이 발견되는지 테스트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from analysis.volume_scanner import VolumeScanner
from utils.token_manager import TokenManager
from utils.logger import get_logger

logger = get_logger("volume_scanner_test")

async def test_volume_scanner():
    """실제 거래량 스캐너 테스트"""
    print("=== 실제 거래량 스캐너 테스트 ===")
    
    # 설정 로드
    settings = Settings()
    token_manager = TokenManager(settings)
    
    # 스캐너 초기화
    scanner = VolumeScanner(settings, token_manager)
    
    print(f"환경: {settings.ENVIRONMENT}")
    print(f"스캔 간격: {scanner.scan_interval}초")
    print(f"최소 거래량 비율: {scanner.min_volume_ratio}")
    print(f"최소 거래대금: {scanner.min_trade_value:,}원")
    print(f"최소 등락률: {scanner.min_price_change:.1%}")
    print(f"최소 체결강도: {scanner.min_execution_strength}")
    print()
    
    try:
        print("거래량 급증 종목 스캔 시작...")
        
        # 실제 스캔 실행
        candidates = await scanner.scan_volume_candidates()
        
        if candidates:
            print(f"\n🎯 발견된 후보 종목: {len(candidates)}개")
            print("=" * 80)
            
            for i, candidate in enumerate(candidates, 1):
                print(f"\n{i}. {candidate.stock_name}({candidate.stock_code})")
                print(f"   현재가: {candidate.current_price:,}원")
                print(f"   거래량비율: {candidate.volume_ratio:.1f}%")
                print(f"   등락률: {candidate.price_change:.2f}%")
                print(f"   거래대금: {candidate.trade_value:,}원")
                print(f"   체결강도: {candidate.score:.1f}%")
                print(f"   시가상승: {'예' if candidate.is_breakout else '아니오'}")
                print(f"   추세: {candidate.ma_trend}")
                print(f"   발견시간: {candidate.timestamp.strftime('%H:%M:%S')}")
        else:
            print("\n❌ 조건을 만족하는 후보 종목이 없습니다.")
            print("   - 현재 시장 상황에서 조건이 너무 엄격할 수 있습니다.")
            print("   - 조건을 조정하거나 다른 시간대에 다시 시도해보세요.")
        
        # 후보 종목 요약
        summary = scanner.get_candidates_summary()
        print(f"\n📊 누적 후보 종목: {len(summary)}개")
        
        # 자동매매 상태
        status = scanner.get_auto_trade_status()
        print(f"🤖 자동매매 상태: {status}")
        
    except Exception as e:
        print(f"\n❌ 스캐닝 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_volume_scanner()) 