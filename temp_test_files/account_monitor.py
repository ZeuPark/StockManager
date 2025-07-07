#!/usr/bin/env python3
"""
실시간 계좌 모니터링 스크립트
"""

import sys
import os
import asyncio
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from monitor.sell_monitor import SellMonitor
import json

class AccountMonitor:
    """실시간 계좌 모니터링 클래스"""
    
    def __init__(self):
        self.settings = Settings()
        self.kiwoom_client = KiwoomClient(self.settings)
        self.sell_monitor = SellMonitor(self.settings, self.kiwoom_client)
        self.monitoring_interval = 30  # 30초마다 업데이트
        
    def print_header(self):
        """헤더 출력"""
        print("\n" + "=" * 80)
        print(f"🏦 실시간 계좌 모니터링 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def print_account_summary(self, account_info):
        """계좌 요약 정보 출력"""
        print(f"📋 환경: {self.settings.ENVIRONMENT}")
        print(f"🌐 API: {self.settings.get_api_config(self.settings.ENVIRONMENT).get('host', 'N/A')}")
        print()
        
        # 예수금 정보
        if "prsm_dpst_aset_amt" in account_info:
            cash = int(account_info["prsm_dpst_aset_amt"])
            print(f"💰 예수금: {cash:,}원")
        
        # 총 매수금액
        if "tot_pur_amt" in account_info:
            total_purchase = int(account_info["tot_pur_amt"])
            print(f"📈 총 매수금액: {total_purchase:,}원")
        
        # 총 평가금액
        if "tot_evlt_amt" in account_info:
            total_evaluation = int(account_info["tot_evlt_amt"])
            print(f"📊 총 평가금액: {total_evaluation:,}원")
        
        # 총 평가손익
        if "tot_evlt_pl" in account_info:
            total_pnl = int(account_info["tot_evlt_pl"])
            pnl_color = "🔴" if total_pnl < 0 else "🟢"
            print(f"{pnl_color} 총 평가손익: {total_pnl:,}원")
        
        # 총 수익률
        if "tot_prft_rt" in account_info:
            total_profit_rate = float(account_info["tot_prft_rt"]) / 100
            rate_color = "🔴" if total_profit_rate < 0 else "🟢"
            print(f"{rate_color} 총 수익률: {total_profit_rate*100:.2f}%")
        
        print()
    
    def print_holdings(self, holdings):
        """보유 종목 정보 출력"""
        if not holdings:
            print("📭 보유 종목이 없습니다.")
            return
        
        print(f"📊 보유 종목 ({len(holdings)}개):")
        print("-" * 80)
        
        total_value = 0
        total_profit = 0
        
        for stock_code, holding in holdings.items():
            stock_name = holding["stock_name"]
            quantity = holding["quantity"]
            purchase_price = holding["purchase_price"]
            current_price = holding["current_price"]
            profit_loss = holding["profit_loss"]
            profit_rate = holding["profit_rate"]
            purchase_amount = holding["purchase_amount"]
            
            total_value += purchase_amount
            total_profit += profit_loss
            
            # 수익률에 따른 색상
            if profit_rate < -0.03:  # -3% 미만
                status = "🔴 손절대상"
            elif profit_rate > 0.06:  # +6% 초과
                status = "🟢 익절대상"
            elif profit_rate < 0:
                status = "🟡 손실"
            else:
                status = "🟢 수익"
            
            print(f"📈 {stock_name}({stock_code})")
            print(f"    수량: {quantity}주 | 매수가: {purchase_price:,}원 | 현재가: {current_price:,}원")
            print(f"    손익: {profit_loss:,}원 | 수익률: {profit_rate*100:.2f}% | {status}")
            print()
        
        print(f"💼 총 보유 가치: {total_value:,}원")
        print(f"📈 총 평가손익: {total_profit:,}원")
        print()
    
    def print_sell_settings(self):
        """매도 설정 정보 출력"""
        sell_settings = self.settings.SELL_SETTINGS
        print("⚙️  매도 설정:")
        print(f"   - 자동 매도: {'활성화' if sell_settings['enabled'] else '비활성화'}")
        print(f"   - 모니터링 주기: {sell_settings['monitoring_interval']}초")
        print(f"   - 손절 기준: {sell_settings['stop_loss_percent']}%")
        print(f"   - 익절 기준: {sell_settings['take_profit_percent']}%")
        print(f"   - 최소 보유 시간: {sell_settings['min_hold_time']}초")
        print()
    
    async def monitor_account(self):
        """계좌 모니터링 시작"""
        print("🚀 실시간 계좌 모니터링 시작...")
        print("   (Ctrl+C로 종료)")
        
        try:
            while True:
                # 화면 클리어 (Windows)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # 헤더 출력
                self.print_header()
                
                # 계좌 정보 조회
                account_info = self.kiwoom_client.get_account_info()
                if account_info:
                    # 계좌 요약 출력
                    self.print_account_summary(account_info)
                    
                    # 보유 종목 정보 추출 및 출력
                    holdings = self.sell_monitor._extract_holdings(account_info)
                    self.print_holdings(holdings)
                    
                    # 매도 설정 출력
                    self.print_sell_settings()
                    
                    # 다음 업데이트 시간
                    next_update = datetime.now().timestamp() + self.monitoring_interval
                    print(f"⏰ 다음 업데이트: {datetime.fromtimestamp(next_update).strftime('%H:%M:%S')}")
                    
                else:
                    print("❌ 계좌 정보 조회 실패")
                
                # 대기
                await asyncio.sleep(self.monitoring_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 모니터링 종료")
        except Exception as e:
            print(f"\n❌ 모니터링 오류: {e}")

async def main():
    """메인 함수"""
    monitor = AccountMonitor()
    await monitor.monitor_account()

if __name__ == "__main__":
    asyncio.run(main()) 