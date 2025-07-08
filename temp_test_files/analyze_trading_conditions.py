#!/usr/bin/env python3
"""
매매 조건 분석 스크립트
수익률이 높았던 거래들의 매매 조건을 분석하여 패턴을 찾습니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import get_database_manager
from datetime import datetime, timedelta
import sqlite3
import json

def analyze_trading_conditions():
    """매매 조건 분석"""
    try:
        db_manager = get_database_manager()
        
        print("=" * 80)
        print("📊 매매 조건 분석 - 수익률 높은 거래 패턴 찾기")
        print("=" * 80)
        
        conn = sqlite3.connect('database/stock_manager.db')
        cursor = conn.cursor()
        
        # 1. 완료된 거래 조회 (매수/매도 매칭)
        print("\n1️⃣ 완료된 거래 조회")
        print("-" * 40)
        
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
            ORDER BY o.filled_at ASC
        """)
        
        completed_orders = cursor.fetchall()
        
        if not completed_orders:
            print("   완료된 거래가 없습니다.")
            return
        
        print(f"   완료된 거래: {len(completed_orders)}개")
        
        # 2. 매수/매도 매칭하여 수익률 계산
        print("\n2️⃣ 수익률 계산 및 조건 분석")
        print("-" * 40)
        
        completed_buys = [o for o in completed_orders if o[2] == 'BUY']
        completed_sells = [o for o in completed_orders if o[2] == 'SELL']
        
        print(f"   완료된 매수: {len(completed_buys)}개")
        print(f"   완료된 매도: {len(completed_sells)}개")
        
        # 매수/매도 매칭하여 수익률 계산
        trades = []
        
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
                holding_period = (datetime.fromisoformat(sell_filled.replace('Z', '+00:00')) - 
                                datetime.fromisoformat(buy_filled.replace('Z', '+00:00')))
                
                trades.append({
                    'stock_code': sell_code,
                    'stock_name': sell_name,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'quantity': sell_qty,
                    'profit_rate': profit_rate,
                    'profit_amount': profit_amount,
                    'buy_time': buy_filled,
                    'sell_time': sell_filled,
                    'holding_period': holding_period,
                    'buy_order_id': buy_order_id,
                    'sell_order_id': sell_order_id
                })
        
        if not trades:
            print("   매칭된 거래가 없습니다.")
            return
        
        # 3. 수익률별 분류
        print(f"\n   매칭된 거래: {len(trades)}개")
        
        # 수익률별 분류
        high_profit_trades = [t for t in trades if t['profit_rate'] >= 5.0]  # 5% 이상
        medium_profit_trades = [t for t in trades if 0 <= t['profit_rate'] < 5.0]  # 0~5%
        loss_trades = [t for t in trades if t['profit_rate'] < 0]  # 손실
        
        print(f"   고수익 거래 (5% 이상): {len(high_profit_trades)}개")
        print(f"   중간 수익 거래 (0~5%): {len(medium_profit_trades)}개")
        print(f"   손실 거래: {len(loss_trades)}개")
        
        # 4. 고수익 거래 조건 분석
        if high_profit_trades:
            print("\n3️⃣ 고수익 거래 조건 분석")
            print("-" * 40)
            
            for i, trade in enumerate(high_profit_trades, 1):
                print(f"\n   🎯 고수익 거래 #{i}")
                print(f"      종목: {trade['stock_name']}({trade['stock_code']})")
                print(f"      매수: {trade['buy_price']:,}원 → 매도: {trade['sell_price']:,}원")
                print(f"      수익률: {trade['profit_rate']:.2f}% | 수익금: {trade['profit_amount']:,}원")
                print(f"      보유기간: {trade['holding_period']}")
                print(f"      매수시간: {trade['buy_time']}")
                print(f"      매도시간: {trade['sell_time']}")
                
                # 매수 시점의 시장 조건 분석
                analyze_market_conditions_at_buy(cursor, trade)
        
        # 5. 전체 통계
        print("\n4️⃣ 전체 통계")
        print("-" * 40)
        
        if trades:
            total_profit = sum(t['profit_amount'] for t in trades)
            avg_profit_rate = sum(t['profit_rate'] for t in trades) / len(trades)
            win_count = len([t for t in trades if t['profit_amount'] > 0])
            win_rate = (win_count / len(trades)) * 100
            
            print(f"   총 거래: {len(trades)}개")
            print(f"   총 수익: {total_profit:,}원")
            print(f"   평균 수익률: {avg_profit_rate:.2f}%")
            print(f"   승률: {win_rate:.1f}% ({win_count}승 {len(trades)-win_count}패)")
            
            # 보유기간 분석
            holding_periods = [t['holding_period'].total_seconds() / 3600 for t in trades]  # 시간 단위
            avg_holding_hours = sum(holding_periods) / len(holding_periods)
            print(f"   평균 보유기간: {avg_holding_hours:.1f}시간")
        
        # 6. 매매 조건 패턴 분석
        print("\n5️⃣ 매매 조건 패턴 분석")
        print("-" * 40)
        
        analyze_trading_patterns(cursor, trades)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def analyze_market_conditions_at_buy(cursor, trade):
    """매수 시점의 시장 조건 분석"""
    try:
        buy_time = datetime.fromisoformat(trade['buy_time'].replace('Z', '+00:00'))
        
        # 매수 시점 전후의 시장 데이터 조회
        cursor.execute("""
            SELECT 
                s.symbol,
                s.name,
                md.timestamp,
                md.close_price,
                md.volume,
                md.trade_value,
                md.price_change,
                md.execution_strength
            FROM market_data md
            JOIN stocks s ON md.stock_id = s.id
            WHERE s.symbol = ? 
            AND md.timestamp BETWEEN ? AND ?
            ORDER BY md.timestamp ASC
        """, (trade['stock_code'], 
              (buy_time - timedelta(hours=1)).isoformat(),
              (buy_time + timedelta(hours=1)).isoformat()))
        
        market_data = cursor.fetchall()
        
        if market_data:
            print(f"      📈 매수 시점 시장 조건:")
            
            # 매수 시점 가장 가까운 데이터
            closest_data = min(market_data, key=lambda x: abs(datetime.fromisoformat(x[2].replace('Z', '+00:00')) - buy_time))
            
            print(f"         종가: {closest_data[3]:,}원")
            print(f"         거래량: {closest_data[4]:,}")
            print(f"         거래대금: {closest_data[5]:,}원")
            print(f"         등락률: {closest_data[6]:.2f}%")
            print(f"         체결강도: {closest_data[7]:.2f}")
        else:
            print(f"      📈 매수 시점 시장 데이터 없음")
        
        # 거래량 돌파 이벤트 확인
        cursor.execute("""
            SELECT 
                vb.breakout_time,
                vb.today_volume,
                vb.prev_day_volume,
                vb.volume_ratio,
                vb.price_at_breakout,
                vb.trade_value_at_breakout
            FROM volume_breakouts vb
            JOIN stocks s ON vb.stock_id = s.id
            WHERE s.symbol = ?
            AND vb.breakout_time BETWEEN ? AND ?
            ORDER BY vb.breakout_time ASC
        """, (trade['stock_code'],
              (buy_time - timedelta(hours=2)).isoformat(),
              (buy_time + timedelta(hours=2)).isoformat()))
        
        volume_breakouts = cursor.fetchall()
        
        if volume_breakouts:
            print(f"      📊 거래량 돌파 이벤트:")
            for vb in volume_breakouts:
                print(f"         시간: {vb[0]}")
                print(f"         거래량 비율: {vb[3]:.2f}배")
                print(f"         돌파가: {vb[4]:,}원")
        
    except Exception as e:
        print(f"      ❌ 시장 조건 분석 오류: {e}")

def analyze_trading_patterns(cursor, trades):
    """매매 패턴 분석"""
    try:
        print("   🔍 매매 패턴 분석:")
        
        # 1. 시간대별 분석
        buy_hours = [datetime.fromisoformat(t['buy_time'].replace('Z', '+00:00')).hour for t in trades]
        hour_counts = {}
        for hour in buy_hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])
        print(f"      가장 활발한 매수 시간대: {most_active_hour[0]}시 ({most_active_hour[1]}회)")
        
        # 2. 보유기간별 분석
        holding_hours = [t['holding_period'].total_seconds() / 3600 for t in trades]
        short_term = [h for h in holding_hours if h <= 1]  # 1시간 이하
        medium_term = [h for h in holding_hours if 1 < h <= 24]  # 1~24시간
        long_term = [h for h in holding_hours if h > 24]  # 24시간 이상
        
        print(f"      단기 보유 (1시간 이하): {len(short_term)}회")
        print(f"      중기 보유 (1~24시간): {len(medium_term)}회")
        print(f"      장기 보유 (24시간 이상): {len(long_term)}회")
        
        # 3. 수익률별 보유기간 분석
        high_profit_trades = [t for t in trades if t['profit_rate'] >= 5.0]
        if high_profit_trades:
            high_profit_holding = [t['holding_period'].total_seconds() / 3600 for t in high_profit_trades]
            avg_high_profit_holding = sum(high_profit_holding) / len(high_profit_holding)
            print(f"      고수익 거래 평균 보유기간: {avg_high_profit_holding:.1f}시간")
        
    except Exception as e:
        print(f"   ❌ 패턴 분석 오류: {e}")

if __name__ == "__main__":
    analyze_trading_conditions() 