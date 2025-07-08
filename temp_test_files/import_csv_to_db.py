#!/usr/bin/env python3
"""
CSV 데이터를 DB에 임시로 넣는 스크립트
기존 CSV 파일의 데이터를 trades, trade_conditions 테이블에 넣어서 분석 스크립트를 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
import re
from datetime import datetime

def import_csv_to_db():
    """CSV 데이터를 DB에 임시로 넣기"""
    print("=" * 80)
    print("📥 CSV 데이터를 DB에 임시로 넣기")
    print("=" * 80)
    
    try:
        # CSV 파일 읽기
        df = pd.read_csv('2025-07-08_당일매매손익표_utf8.csv', encoding='utf-8-sig')
        df['종목코드'] = df['종목코드'].astype(str).str.replace("'", "")
        df['수익률'] = df['수익률'].astype(str).str.replace('%', '').astype(float)
        
        print(f"   CSV 데이터: {len(df)}건")
        
        # 로그에서 매수 조건 데이터 추출
        stock_data = {}
        with open('logs/stock_manager.log', 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        for line in log_lines:
            # 1차 필터 통과 패턴 찾기
            filter_match = re.search(r'(\d{6})\)\] 1차 필터 통과', line)
            if filter_match:
                stock_code = filter_match.group(1)
                
                # 같은 줄에서 거래량비율, 거래대금 추출
                volume_ratio_match = re.search(r'거래량비율: ([\d.]+)%', line)
                trade_value_match = re.search(r'거래대금: ([\d,]+)원', line)
                
                if volume_ratio_match and trade_value_match:
                    volume_ratio = float(volume_ratio_match.group(1))
                    trade_value = int(trade_value_match.group(1).replace(',', ''))
                    
                    stock_data[stock_code] = {
                        '거래량비율': volume_ratio,
                        '거래대금': trade_value
                    }
        
        print(f"   로그에서 추출한 조건 데이터: {len(stock_data)}건")
        
        # DB 연결
        conn = sqlite3.connect('database/stock_manager.db')
        cursor = conn.cursor()
        
        # 기존 데이터 삭제 (테스트용)
        cursor.execute("DELETE FROM trade_conditions")
        cursor.execute("DELETE FROM trades")
        conn.commit()
        
        # 데이터 삽입
        inserted_count = 0
        
        for _, row in df.iterrows():
            stock_code = str(row['종목코드']).strip()
            stock_name = str(row['종목명']).strip()
            profit_rate = float(row['수익률'])
            
            # 매수가 추정 (로그에서 찾기)
            buy_price = None
            for line in log_lines:
                if stock_code in line and "현재가:" in line:
                    price_match = re.search(r'현재가: ([\d,]+)원', line)
                    if price_match:
                        buy_price = int(price_match.group(1).replace(',', ''))
                        break
            
            if buy_price is None:
                buy_price = 50000  # 기본값
            
            # 매도가 계산
            sell_price = int(buy_price * (1 + profit_rate / 100))
            
            # 거래 시간 (임시)
            buy_time = datetime.now() - pd.Timedelta(hours=len(df) - inserted_count)
            sell_time = buy_time + pd.Timedelta(minutes=30)
            
            # trades 테이블에 삽입
            cursor.execute("""
                INSERT INTO trades (stock_code, stock_name, buy_price, sell_price, quantity, buy_time, sell_time, profit_rate, profit_amount, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stock_code,
                stock_name,
                buy_price,
                sell_price,
                100,  # 기본 수량
                buy_time,
                sell_time,
                profit_rate,
                (sell_price - buy_price) * 100,
                "익절" if profit_rate > 0 else "손절"
            ))
            
            trade_id = cursor.lastrowid
            
            # trade_conditions 테이블에 삽입
            if stock_code in stock_data:
                cond = stock_data[stock_code]
                cursor.execute("""
                    INSERT INTO trade_conditions (trade_id, volume_ratio, trade_value, execution_strength, price_change, market_cap)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    trade_id,
                    cond['거래량비율'],
                    cond['거래대금'],
                    110.0,  # 기본 체결강도
                    1.5,    # 기본 등락률
                    None    # 시가총액
                ))
            
            inserted_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   DB 삽입 완료: {inserted_count}건")
        print("✅ CSV 데이터 임시 삽입 완료!")
        
    except Exception as e:
        print(f"❌ 삽입 오류: {e}")

if __name__ == "__main__":
    import_csv_to_db() 