#!/usr/bin/env python3
"""
DB에서 거래 분석 스크립트
trades, trade_conditions 테이블을 JOIN하여 한 번에 모든 거래 정보를 분석합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def analyze_trades_from_db():
    """DB에서 거래 데이터 분석"""
    print("=" * 80)
    print("📊 DB 거래 분석 - trades + trade_conditions JOIN")
    print("=" * 80)
    
    try:
        # DB 연결
        conn = sqlite3.connect('database/stock_manager.db')
        
        # 1. 전체 거래 조회 (JOIN)
        print("\n1️⃣ 전체 거래 조회")
        print("-" * 50)
        
        query = """
        SELECT 
            t.id,
            t.stock_code,
            t.stock_name,
            t.buy_price,
            t.sell_price,
            t.quantity,
            t.buy_time,
            t.sell_time,
            t.profit_rate,
            t.profit_amount,
            t.result,
            c.volume_ratio,
            c.trade_value,
            c.execution_strength,
            c.price_change,
            c.market_cap
        FROM trades t
        LEFT JOIN trade_conditions c ON t.id = c.trade_id
        ORDER BY t.buy_time DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("   거래 데이터가 없습니다.")
            return
        
        print(f"   전체 거래: {len(df)}건")
        
        # 2. 완료된 거래만 필터링 (매도 완료)
        completed_trades = df[df['sell_price'].notna()].copy()
        
        if completed_trades.empty:
            print("   완료된 거래가 없습니다.")
            return
        
        print(f"   완료된 거래: {len(completed_trades)}건")
        
        # 3. 수익/손실 분리
        profit_trades = completed_trades[completed_trades['profit_rate'] > 0]
        loss_trades = completed_trades[completed_trades['profit_rate'] <= 0]
        
        print(f"   수익 거래: {len(profit_trades)}건")
        print(f"   손실 거래: {len(loss_trades)}건")
        
        # 4. 상세 분석
        print("\n2️⃣ 상세 분석")
        print("-" * 50)
        
        if not profit_trades.empty:
            print("\n✅ 수익 거래 상세:")
            print(f"   평균 수익률: {profit_trades['profit_rate'].mean():.2f}%")
            print(f"   최고 수익률: {profit_trades['profit_rate'].max():.2f}%")
            print(f"   최저 수익률: {profit_trades['profit_rate'].min():.2f}%")
            
            # 거래량비율 분석
            if 'volume_ratio' in profit_trades.columns:
                vol_ratio = profit_trades['volume_ratio'].dropna()
                if not vol_ratio.empty:
                    print(f"   평균 거래량비율: {vol_ratio.mean():.2f}%")
                    print(f"   거래량비율 범위: {vol_ratio.min():.2f}% ~ {vol_ratio.max():.2f}%")
            
            # 거래대금 분석
            if 'trade_value' in profit_trades.columns:
                trade_val = profit_trades['trade_value'].dropna()
                if not trade_val.empty:
                    print(f"   평균 거래대금: {trade_val.mean()/1e8:.1f}억원")
                    print(f"   거래대금 범위: {trade_val.min()/1e8:.1f}억원 ~ {trade_val.max()/1e8:.1f}억원")
        
        if not loss_trades.empty:
            print("\n❌ 손실 거래 상세:")
            print(f"   평균 손실률: {loss_trades['profit_rate'].mean():.2f}%")
            print(f"   최대 손실률: {loss_trades['profit_rate'].min():.2f}%")
            print(f"   최소 손실률: {loss_trades['profit_rate'].max():.2f}%")
            
            # 거래량비율 분석
            if 'volume_ratio' in loss_trades.columns:
                vol_ratio = loss_trades['volume_ratio'].dropna()
                if not vol_ratio.empty:
                    print(f"   평균 거래량비율: {vol_ratio.mean():.2f}%")
                    print(f"   거래량비율 범위: {vol_ratio.min():.2f}% ~ {vol_ratio.max():.2f}%")
            
            # 거래대금 분석
            if 'trade_value' in loss_trades.columns:
                trade_val = loss_trades['trade_value'].dropna()
                if not trade_val.empty:
                    print(f"   평균 거래대금: {trade_val.mean()/1e8:.1f}억원")
                    print(f"   거래대금 범위: {trade_val.min()/1e8:.1f}억원 ~ {trade_val.max()/1e8:.1f}억원")
        
        # 5. 조건별 분석
        print("\n3️⃣ 조건별 분석")
        print("-" * 50)
        
        if 'volume_ratio' in completed_trades.columns and 'trade_value' in completed_trades.columns:
            # 거래량비율 구간별 분석
            print("\n📊 거래량비율 구간별 성공률:")
            vol_ratio_ranges = [
                (0, 0.5, "0.0~0.5%"),
                (0.5, 1.0, "0.5~1.0%"),
                (1.0, 1.5, "1.0~1.5%"),
                (1.5, 2.0, "1.5~2.0%"),
                (2.0, float('inf'), "2.0% 이상")
            ]
            
            for min_ratio, max_ratio, label in vol_ratio_ranges:
                if max_ratio == float('inf'):
                    mask = (completed_trades['volume_ratio'] >= min_ratio) & (completed_trades['volume_ratio'].notna())
                else:
                    mask = (completed_trades['volume_ratio'] >= min_ratio) & (completed_trades['volume_ratio'] < max_ratio) & (completed_trades['volume_ratio'].notna())
                
                range_trades = completed_trades[mask]
                if not range_trades.empty:
                    success_rate = (range_trades['profit_rate'] > 0).mean() * 100
                    count = len(range_trades)
                    print(f"   {label}: {success_rate:.1f}% ({count}건)")
            
            # 거래대금 구간별 분석
            print("\n💰 거래대금 구간별 성공률:")
            trade_value_ranges = [
                (0, 1e8, "1억원 미만"),
                (1e8, 5e8, "1~5억원"),
                (5e8, 10e8, "5~10억원"),
                (10e8, 20e8, "10~20억원"),
                (20e8, float('inf'), "20억원 이상")
            ]
            
            for min_val, max_val, label in trade_value_ranges:
                if max_val == float('inf'):
                    mask = (completed_trades['trade_value'] >= min_val) & (completed_trades['trade_value'].notna())
                else:
                    mask = (completed_trades['trade_value'] >= min_val) & (completed_trades['trade_value'] < max_val) & (completed_trades['trade_value'].notna())
                
                range_trades = completed_trades[mask]
                if not range_trades.empty:
                    success_rate = (range_trades['profit_rate'] > 0).mean() * 100
                    count = len(range_trades)
                    print(f"   {label}: {success_rate:.1f}% ({count}건)")
        
        # 6. 최근 거래 현황
        print("\n4️⃣ 최근 거래 현황")
        print("-" * 50)
        
        recent_trades = completed_trades.head(10)
        for _, trade in recent_trades.iterrows():
            result_icon = "✅" if trade['profit_rate'] > 0 else "❌"
            print(f"   {result_icon} {trade['stock_code']} {trade['stock_name']}: {trade['profit_rate']:.2f}% "
                  f"(거래량: {trade.get('volume_ratio', 'N/A'):.1f}%, "
                  f"거래대금: {trade.get('trade_value', 0)/1e8:.1f}억원)")
        
        # 7. 보유 중인 거래 (미완료)
        print("\n5️⃣ 보유 중인 거래")
        print("-" * 50)
        
        holding_trades = df[df['sell_price'].isna()]
        if not holding_trades.empty:
            print(f"   보유 중인 거래: {len(holding_trades)}건")
            for _, trade in holding_trades.iterrows():
                print(f"   📈 {trade['stock_code']} {trade['stock_name']}: "
                      f"매수가 {trade['buy_price']:,}원 "
                      f"(거래량: {trade.get('volume_ratio', 'N/A'):.1f}%, "
                      f"거래대금: {trade.get('trade_value', 0)/1e8:.1f}억원)")
        else:
            print("   보유 중인 거래가 없습니다.")
        
        conn.close()
        
        print("\n✅ DB 거래 분석 완료!")
        
    except Exception as e:
        print(f"❌ 분석 오류: {e}")

def export_trades_to_csv():
    """DB 거래 데이터를 CSV로 내보내기"""
    try:
        conn = sqlite3.connect('database/stock_manager.db')
        
        query = """
        SELECT 
            t.stock_code,
            t.stock_name,
            t.buy_price,
            t.sell_price,
            t.quantity,
            t.buy_time,
            t.sell_time,
            t.profit_rate,
            t.profit_amount,
            t.result,
            c.volume_ratio,
            c.trade_value,
            c.execution_strength,
            c.price_change,
            c.market_cap
        FROM trades t
        LEFT JOIN trade_conditions c ON t.id = c.trade_id
        ORDER BY t.buy_time DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            filename = f"trades_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"📄 CSV 내보내기 완료: {filename}")
        else:
            print("   내보낼 거래 데이터가 없습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ CSV 내보내기 오류: {e}")

if __name__ == "__main__":
    analyze_trades_from_db()
    
    # CSV 내보내기 여부 확인
    response = input("\n📄 CSV로 내보내시겠습니까? (y/n): ")
    if response.lower() == 'y':
        export_trades_to_csv() 