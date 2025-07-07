#!/usr/bin/env python3
"""
매도 모니터링 테스트 스크립트
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from monitor.sell_monitor import SellMonitor
import json

async def test_sell_monitor():
    print("=" * 60)
    print("🧪 매도 모니터링 테스트")
    print("=" * 60)
    
    # 설정 초기화
    settings = Settings()
    print(f"📋 환경: {settings.ENVIRONMENT}")
    
    # 매도 설정 확인
    sell_settings = settings.SELL_SETTINGS
    print(f"🔧 매도 설정:")
    print(f"  - 활성화: {sell_settings['enabled']}")
    print(f"  - 모니터링 주기: {sell_settings['monitoring_interval']}초")
    print(f"  - 손절 기준: {sell_settings['stop_loss_percent']}%")
    print(f"  - 익절 기준: {sell_settings['take_profit_percent']}%")
    print(f"  - 최소 보유 시간: {sell_settings['min_hold_time']}초")
    
    # KiwoomClient 초기화
    kiwoom_client = KiwoomClient(settings)
    
    # SellMonitor 초기화
    sell_monitor = SellMonitor(settings, kiwoom_client)
    
    print("\n💰 현재 보유 종목 확인...")
    
    # 계좌 정보 조회
    account_info = kiwoom_client.get_account_info()
    if account_info:
        print("✅ 계좌 정보 조회 성공")
        
        # 보유 종목 추출
        holdings = sell_monitor._extract_holdings(account_info)
        
        if holdings:
            print(f"\n📊 보유 종목 {len(holdings)}개:")
            for stock_code, holding in holdings.items():
                stock_name = holding["stock_name"]
                quantity = holding["quantity"]
                purchase_price = holding["purchase_price"]
                current_price = holding["current_price"]
                profit_rate = holding["profit_rate"]
                
                print(f"  📈 {stock_name}({stock_code})")
                print(f"     - 보유 수량: {quantity}주")
                print(f"     - 매수 가격: {purchase_price:,}원")
                print(f"     - 현재 가격: {current_price:,}원")
                print(f"     - 수익률: {profit_rate*100:.2f}%")
                
                # 매도 조건 확인
                if profit_rate <= sell_settings["stop_loss_percent"] / 100:
                    print(f"     ⚠️  손절 조건 만족!")
                elif profit_rate >= sell_settings["take_profit_percent"] / 100:
                    print(f"     🎯 익절 조건 만족!")
                else:
                    print(f"     ✅ 매도 조건 미만족")
                print()
        else:
            print("📭 보유 종목이 없습니다.")
    else:
        print("❌ 계좌 정보 조회 실패")
    
    print("\n🧪 매도 모니터링 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_sell_monitor()) 