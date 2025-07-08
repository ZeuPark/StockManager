#!/usr/bin/env python3
"""
종합 데이터 조회 스크립트
DB에 저장된 모든 데이터를 조회합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import get_database_manager
from datetime import datetime, timedelta

def check_all_data():
    """모든 데이터 조회"""
    try:
        db_manager = get_database_manager()
        
        print("=" * 80)
        print("📊 종합 데이터 조회")
        print("=" * 80)
        
        # 1. 데이터베이스 통계
        print("1️⃣ 데이터베이스 통계")
        print("-" * 40)
        stats = db_manager.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()
        
        # 2. 주문 내역
        print("2️⃣ 주문 내역 (최근 7일)")
        print("-" * 40)
        orders = db_manager.get_orders(days=7)
        if orders:
            print(f"   총 {len(orders)}건의 주문")
            buy_count = sum(1 for order in orders if order['order_type'] == 'BUY')
            sell_count = sum(1 for order in orders if order['order_type'] == 'SELL')
            print(f"   매수: {buy_count}건, 매도: {sell_count}건")
        else:
            print("   주문 내역 없음")
        print()
        
        # 3. 거래량 후보 종목
        print("3️⃣ 거래량 후보 종목")
        print("-" * 40)
        candidates = db_manager.get_active_candidates()
        if candidates:
            print(f"   활성 후보: {len(candidates)}개")
            for candidate in candidates[:5]:  # 최대 5개만 표시
                print(f"   - {candidate.get('symbol', 'N/A')}: 거래량비율 {candidate.get('volume_ratio', 0):.1f}배")
        else:
            print("   활성 후보 없음")
        print()
        
        # 4. 거래량 돌파 이벤트
        print("4️⃣ 거래량 돌파 이벤트 (최근 7일)")
        print("-" * 40)
        breakouts = db_manager.get_volume_breakouts(days=7)
        if breakouts:
            print(f"   총 {len(breakouts)}건의 돌파 이벤트")
            for breakout in breakouts[:3]:  # 최대 3개만 표시
                print(f"   - {breakout.get('symbol', 'N/A')}: {breakout.get('volume_ratio', 0):.1f}배")
        else:
            print("   돌파 이벤트 없음")
        print()
        
        # 5. 시스템 로그
        print("5️⃣ 시스템 로그 (최근 10건)")
        print("-" * 40)
        logs = db_manager.get_system_logs(days=1)
        if logs:
            for log in logs[:10]:
                level = log.get('level', 'INFO')
                message = log.get('message', '')[:50] + '...' if len(log.get('message', '')) > 50 else log.get('message', '')
                created_at = log.get('created_at', '')
                print(f"   [{level}] {message}")
        else:
            print("   로그 없음")
        print()
        
        # 6. 거래량 분석
        print("6️⃣ 거래량 분석 (최근 30일)")
        print("-" * 40)
        volume_analysis = db_manager.get_volume_analysis(days=30)
        if volume_analysis:
            print(f"   분석 데이터: {len(volume_analysis)}건")
            # 상위 3개 종목 표시
            top_volume = sorted(volume_analysis, key=lambda x: x.get('avg_volume_ratio', 0), reverse=True)[:3]
            for item in top_volume:
                print(f"   - {item.get('symbol', 'N/A')}: 평균 거래량비율 {item.get('avg_volume_ratio', 0):.1f}배")
        else:
            print("   분석 데이터 없음")
        print()
        
        print("=" * 80)
        print("✅ 모든 데이터 조회 완료!")
        
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")

if __name__ == "__main__":
    check_all_data() 