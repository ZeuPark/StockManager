#!/usr/bin/env python3
"""
매수/매도 수익률 분석 스크립트
DB에서 거래 내역을 조회하고 수익률을 계산합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import get_database_manager
from datetime import datetime, timedelta
import sqlite3

def analyze_profits():
    """수익률 분석"""
    try:
        db_manager = get_database_manager()
        
        print("=" * 80)
        print("📊 매수/매도 수익률 분석")
        print("=" * 80)
        
        # 1. 전체 주문 내역 조회
        print("\n1️⃣ 전체 주문 내역")
        print("-" * 40)
        
        conn = sqlite3.connect('database/stock_manager.db')
        cursor = conn.cursor()
        
        # 주문 내역 조회 (JOIN으로 종목 정보 포함)
        cursor.execute("""
            SELECT 
                s.symbol as stock_code,
                s.name as stock_name,
                o.order_type,
                o.quantity,
                o.price,
                o.status,
                o.created_at,
                o.filled_at,
                o.order_id
            FROM orders o
            JOIN stocks s ON o.stock_id = s.id
            ORDER BY o.created_at DESC
            LIMIT 50
        """)
        
        orders = cursor.fetchall()
        
        if not orders:
            print("   주문 내역이 없습니다.")
        else:
            print(f"   총 {len(orders)}개의 주문 내역")
            print()
            
            # 매수/매도 분류
            buy_orders = []
            sell_orders = []
            
            for order in orders:
                stock_code, stock_name, order_type, quantity, price, status, created_at, filled_at, order_id = order
                
                if order_type == 'BUY':
                    buy_orders.append(order)
                elif order_type == 'SELL':
                    sell_orders.append(order)
                
                price_str = f"{price:,}원" if price and price > 0 else "미정"
                status_str = f"{status} ({filled_at})" if filled_at else status
                print(f"   {created_at} | {stock_name}({stock_code}) | {order_type} | {quantity}주 @ {price_str} | {status_str}")
        
        print(f"\n   매수 주문: {len(buy_orders)}개")
        print(f"   매도 주문: {len(sell_orders)}개")
        
        # 2. 완료된 거래 분석
        print("\n2️⃣ 완료된 거래 분석")
        print("-" * 40)
        
        # 완료된 주문만 조회
        cursor.execute("""
            SELECT 
                s.symbol as stock_code,
                s.name as stock_name,
                o.order_type,
                o.quantity,
                o.price,
                o.status,
                o.created_at,
                o.filled_at,
                o.order_id
            FROM orders o
            JOIN stocks s ON o.stock_id = s.id
            WHERE o.status = 'FILLED' AND o.price > 0
            ORDER BY o.filled_at DESC
        """)
        
        completed_orders = cursor.fetchall()
        
        if not completed_orders:
            print("   완료된 거래가 없습니다.")
        else:
            print(f"   완료된 거래: {len(completed_orders)}개")
            print()
            
            # 매수/매도 분류
            completed_buys = [o for o in completed_orders if o[2] == 'BUY']
            completed_sells = [o for o in completed_orders if o[2] == 'SELL']
            
            print(f"   완료된 매수: {len(completed_buys)}개")
            print(f"   완료된 매도: {len(completed_sells)}개")
            
            # 3. 수익률 계산
            print("\n3️⃣ 수익률 분석")
            print("-" * 40)
            
            # 매수/매도 매칭하여 수익률 계산
            profits = []
            
            for sell_order in completed_sells:
                sell_code, sell_name, sell_type, sell_qty, sell_price, sell_status, sell_created, sell_filled, sell_order_id = sell_order
                
                # 해당 종목의 매수 주문 찾기
                matching_buy = None
                for buy_order in completed_buys:
                    buy_code, buy_name, buy_type, buy_qty, buy_price, buy_status, buy_created, buy_filled, buy_order_id = buy_order
                    
                    if buy_code == sell_code and buy_filled < sell_filled:
                        matching_buy = buy_order
                        break
                
                if matching_buy:
                    buy_code, buy_name, buy_type, buy_qty, buy_price, buy_status, buy_created, buy_filled, buy_order_id = matching_buy
                    
                    # 수익률 계산
                    profit_rate = ((sell_price - buy_price) / buy_price) * 100
                    profit_amount = (sell_price - buy_price) * sell_qty
                    
                    profits.append({
                        'stock_code': sell_code,
                        'stock_name': sell_name,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'quantity': sell_qty,
                        'profit_rate': profit_rate,
                        'profit_amount': profit_amount,
                        'buy_time': buy_filled,
                        'sell_time': sell_filled
                    })
            
            if profits:
                print(f"   매칭된 거래: {len(profits)}개")
                print()
                
                total_profit = 0
                total_profit_rate = 0
                win_count = 0
                loss_count = 0
                
                for profit in profits:
                    total_profit += profit['profit_amount']
                    total_profit_rate += profit['profit_rate']
                    
                    if profit['profit_amount'] > 0:
                        win_count += 1
                    else:
                        loss_count += 1
                    
                    status = "✅" if profit['profit_amount'] > 0 else "❌"
                    print(f"   {status} {profit['stock_name']}({profit['stock_code']})")
                    print(f"      매수: {profit['buy_price']:,}원 → 매도: {profit['sell_price']:,}원")
                    print(f"      수익률: {profit['profit_rate']:.2f}% | 수익금: {profit['profit_amount']:,}원")
                    print(f"      보유기간: {profit['buy_time']} ~ {profit['sell_time']}")
                    print()
                
                # 전체 통계
                avg_profit_rate = total_profit_rate / len(profits) if profits else 0
                win_rate = (win_count / len(profits)) * 100 if profits else 0
                
                print("📈 전체 통계")
                print(f"   총 수익: {total_profit:,}원")
                print(f"   평균 수익률: {avg_profit_rate:.2f}%")
                print(f"   승률: {win_rate:.1f}% ({win_count}승 {loss_count}패)")
            else:
                print("   매칭된 거래가 없습니다.")
        
        # 4. 현재 보유 종목 현황
        print("\n4️⃣ 현재 보유 종목 현황")
        print("-" * 40)
        
        # 보유 종목 조회 (매수했지만 아직 매도하지 않은 종목)
        cursor.execute("""
            SELECT 
                s.symbol as stock_code,
                s.name as stock_name,
                SUM(CASE WHEN o.order_type = 'BUY' THEN o.quantity ELSE -o.quantity END) as net_quantity,
                AVG(CASE WHEN o.order_type = 'BUY' THEN o.price END) as avg_buy_price
            FROM orders o
            JOIN stocks s ON o.stock_id = s.id
            WHERE o.status = 'FILLED'
            GROUP BY s.symbol, s.name
            HAVING net_quantity > 0
            ORDER BY net_quantity DESC
        """)
        
        holdings = cursor.fetchall()
        
        if holdings:
            print(f"   현재 보유 종목: {len(holdings)}개")
            print()
            
            for holding in holdings:
                stock_code, stock_name, net_qty, avg_price = holding
                avg_price_str = f"{avg_price:,.0f}원" if avg_price else "미정"
                print(f"   {stock_name}({stock_code}): {net_qty}주 @ 평균 {avg_price_str}")
        else:
            print("   현재 보유 종목이 없습니다.")
        
        # 5. 대기 중인 주문 현황
        print("\n5️⃣ 대기 중인 주문 현황")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                s.symbol as stock_code,
                s.name as stock_name,
                o.order_type,
                o.quantity,
                o.price,
                o.created_at,
                o.order_id
            FROM orders o
            JOIN stocks s ON o.stock_id = s.id
            WHERE o.status = 'PENDING'
            ORDER BY o.created_at DESC
        """)
        
        pending_orders = cursor.fetchall()
        
        if pending_orders:
            print(f"   대기 중인 주문: {len(pending_orders)}개")
            print()
            
            for order in pending_orders:
                stock_code, stock_name, order_type, quantity, price, created_at, order_id = order
                price_str = f"{price:,}원" if price and price > 0 else "시장가"
                print(f"   {created_at} | {stock_name}({stock_code}) | {order_type} | {quantity}주 @ {price_str}")
        else:
            print("   대기 중인 주문이 없습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_profits() 