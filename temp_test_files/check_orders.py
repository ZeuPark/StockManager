#!/usr/bin/env python3
"""
주문 내역 조회 스크립트
DB에 저장된 모든 주문 내역을 조회합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import get_database_manager
from datetime import datetime, timedelta

def check_orders():
    """주문 내역 조회"""
    try:
        db_manager = get_database_manager()
        
        print("=" * 80)
        print("📋 주문 내역 조회")
        print("=" * 80)
        
        # 최근 30일 주문 내역 조회
        orders = db_manager.get_orders(days=30)
        
        if not orders:
            print("❌ 최근 30일간 주문 내역이 없습니다.")
            return
        
        print(f"✅ 총 {len(orders)}건의 주문 내역을 찾았습니다.\n")
        
        # 주문 타입별 통계
        buy_count = sum(1 for order in orders if order['order_type'] == 'BUY')
        sell_count = sum(1 for order in orders if order['order_type'] == 'SELL')
        
        print(f"📊 주문 통계:")
        print(f"   매수: {buy_count}건")
        print(f"   매도: {sell_count}건")
        print()
        
        # 최근 주문 내역 (최대 10건)
        recent_orders = orders[:10]
        
        print("📝 최근 주문 내역:")
        print("-" * 80)
        print(f"{'주문ID':<20} {'종목코드':<10} {'종목명':<15} {'타입':<6} {'수량':<8} {'가격':<12} {'상태':<10} {'주문시간'}")
        print("-" * 80)
        
        for order in recent_orders:
            order_id = order.get('order_id', 'N/A')[:18] + '...' if len(order.get('order_id', '')) > 18 else order.get('order_id', 'N/A')
            stock_code = order.get('symbol', 'N/A')
            stock_name = order.get('name', 'N/A')
            order_type = order.get('order_type', 'N/A')
            quantity = order.get('quantity', 0)
            price = order.get('price', 0)
            status = order.get('status', 'N/A')
            created_at = order.get('created_at', 'N/A')
            
            if isinstance(created_at, str):
                created_at = created_at[:19]  # YYYY-MM-DD HH:MM:SS 형식으로 자르기
            
            print(f"{order_id:<20} {stock_code:<10} {stock_name:<15} {order_type:<6} {quantity:<8} {price:<12,} {status:<10} {created_at}")
        
        print("-" * 80)
        
        # 종목별 주문 통계
        print("\n📈 종목별 주문 통계:")
        stock_stats = {}
        for order in orders:
            stock_code = order.get('symbol', 'N/A')
            order_type = order.get('order_type', 'N/A')
            
            if stock_code not in stock_stats:
                stock_stats[stock_code] = {'BUY': 0, 'SELL': 0}
            
            stock_stats[stock_code][order_type] += 1
        
        for stock_code, stats in stock_stats.items():
            print(f"   {stock_code}: 매수 {stats['BUY']}건, 매도 {stats['SELL']}건")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ 주문 내역 조회 실패: {e}")

if __name__ == "__main__":
    check_orders() 