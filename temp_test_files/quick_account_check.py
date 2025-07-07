#!/usr/bin/env python3
"""
간단한 계좌 상태 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from monitor.sell_monitor import SellMonitor

def main():
    print("=" * 60)
    print("📊 계좌 상태 확인")
    print("=" * 60)
    
    # 설정 초기화
    settings = Settings()
    kiwoom_client = KiwoomClient(settings)
    sell_monitor = SellMonitor(settings, kiwoom_client)
    
    # 계좌 정보 조회
    account_info = kiwoom_client.get_account_info()
    if not account_info:
        print("❌ 계좌 정보 조회 실패")
        return
    
    # 계좌 요약
    print(f"📋 환경: {settings.ENVIRONMENT}")
    
    if "prsm_dpst_aset_amt" in account_info:
        cash = int(account_info["prsm_dpst_aset_amt"])
        print(f"💰 예수금: {cash:,}원")
    
    if "tot_evlt_pl" in account_info:
        total_pnl = int(account_info["tot_evlt_pl"])
        pnl_emoji = "🔴" if total_pnl < 0 else "🟢"
        print(f"{pnl_emoji} 총 평가손익: {total_pnl:,}원")
    
    if "tot_prft_rt" in account_info:
        total_profit_rate = float(account_info["tot_prft_rt"]) / 100
        rate_emoji = "🔴" if total_profit_rate < 0 else "🟢"
        print(f"{rate_emoji} 총 수익률: {total_profit_rate*100:.2f}%")
    
    print()
    
    # 보유 종목 확인
    holdings = sell_monitor._extract_holdings(account_info)
    if holdings:
        print(f"📊 보유 종목 ({len(holdings)}개):")
        for stock_code, holding in holdings.items():
            stock_name = holding["stock_name"]
            quantity = holding["quantity"]
            profit_rate = holding["profit_rate"]
            
            # 상태 표시
            if profit_rate < -0.03:
                status = "🔴 손절대상"
            elif profit_rate > 0.06:
                status = "🟢 익절대상"
            elif profit_rate < 0:
                status = "🟡 손실"
            else:
                status = "🟢 수익"
            
            print(f"  {stock_name}({stock_code}) - {quantity}주 - {profit_rate*100:.2f}% {status}")
    else:
        print("📭 보유 종목 없음")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main() 