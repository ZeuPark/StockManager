import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

def check_settings():
    s = get_settings()
    
    print("🔧 패턴 분석 기반 설정 적용 확인")
    print("=" * 50)
    
    print(f"📈 익절 기준: {s.SELL_SETTINGS['take_profit_percent']}%")
    print(f"💰 최대 거래대금: {s.RISK_MANAGEMENT['max_trade_amount']:,}원")
    # print(f"📦 최대 보유수량: {s.RISK_MANAGEMENT['max_quantity_per_stock']}주")
    print(f"🛑 손절 기준: {s.SELL_SETTINGS['stop_loss_percent']}%")
    print(f"💵 최소 거래대금: {s.RISK_MANAGEMENT['min_trade_amount']:,}원")
    
    print("\n✅ 설정이 성공적으로 적용되었습니다!")
    print("💡 이제 main.py를 실행하면 새로운 설정이 적용됩니다.")

if __name__ == "__main__":
    check_settings() 