#!/usr/bin/env python3
"""
최적화된 매수 조건 테스트 스크립트
분석 결과를 바탕으로 개선된 매수 조건을 시뮬레이션합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings
from analysis.volume_scanner import VolumeScanner
from utils.token_manager import TokenManager
import asyncio
import pandas as pd

async def test_optimized_conditions():
    """최적화된 매수 조건 테스트"""
    print("=" * 80)
    print("🚀 최적화된 매수 조건 테스트")
    print("=" * 80)
    
    # 설정 로드
    settings = get_settings()
    token_manager = TokenManager(settings)
    
    # VolumeScanner 초기화
    scanner = VolumeScanner(settings, token_manager)
    
    print("\n📊 현재 매수 조건:")
    print(f"   거래량비율 범위: {scanner.min_volume_ratio:.1f}% ~ {scanner.max_volume_ratio:.1f}%")
    print(f"   거래대금 범위: {scanner.min_trade_value/1e8:.1f}억원 ~ {scanner.max_trade_value/1e8:.1f}억원")
    print(f"   최적 거래량비율: {scanner.optimal_volume_ratio_range[0]:.1f}% ~ {scanner.optimal_volume_ratio_range[1]:.1f}%")
    print(f"   최적 거래대금: {scanner.optimal_trade_value_range[0]/1e8:.1f}억원 ~ {scanner.optimal_trade_value_range[1]/1e8:.1f}억원")
    print(f"   최소 등락률: {scanner.min_price_change*100:.1f}%")
    print(f"   최소 체결강도: {scanner.min_execution_strength*100:.1f}%")
    
    # CSV 데이터로 시뮬레이션
    print("\n📈 CSV 데이터 기반 시뮬레이션:")
    print("-" * 50)
    
    try:
        # CSV 파일 읽기
        df = pd.read_csv('2025-07-08_당일매매손익표_utf8.csv', encoding='utf-8-sig')
        df['종목코드'] = df['종목코드'].astype(str).str.replace("'", "")
        df['수익률'] = df['수익률'].astype(str).str.replace('%', '').astype(float)
        
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
        
        # 시뮬레이션 실행
        passed_count = 0
        optimal_count = 0
        
        for _, row in df.iterrows():
            stock_code = str(row['종목코드']).strip()
            stock_name = str(row['종목명']).strip()
            profit_rate = float(row['수익률'])
            
            if stock_code in stock_data:
                volume_ratio = stock_data[stock_code]['거래량비율']
                trade_value = stock_data[stock_code]['거래대금']
                
                # 기본 조건 체크
                basic_passed = (
                    scanner.min_volume_ratio <= volume_ratio <= scanner.max_volume_ratio and
                    scanner.min_trade_value <= trade_value <= scanner.max_trade_value
                )
                
                # 최적 조건 체크
                optimal_passed = (
                    scanner.optimal_volume_ratio_range[0] <= volume_ratio <= scanner.optimal_volume_ratio_range[1] and
                    scanner.optimal_trade_value_range[0] <= trade_value <= scanner.optimal_trade_value_range[1]
                )
                
                if basic_passed:
                    passed_count += 1
                    if optimal_passed:
                        optimal_count += 1
                    
                    status = "✅ 최적" if optimal_passed else "✅ 기본"
                    print(f"{status} {stock_code} {stock_name}: {profit_rate:.2f}% (거래량: {volume_ratio:.1f}%, 거래대금: {trade_value/1e8:.1f}억원)")
                else:
                    print(f"❌ 제외 {stock_code} {stock_name}: {profit_rate:.2f}% (거래량: {volume_ratio:.1f}%, 거래대금: {trade_value/1e8:.1f}억원)")
        
        print(f"\n📊 시뮬레이션 결과:")
        print(f"   기본 조건 통과: {passed_count}개")
        print(f"   최적 조건 통과: {optimal_count}개")
        print(f"   전체 종목: {len(df)}개")
        
        # 수익률 분석
        if passed_count > 0:
            passed_stocks = [row for _, row in df.iterrows() if str(row['종목코드']).strip() in stock_data and 
                           scanner.min_volume_ratio <= stock_data[str(row['종목코드']).strip()]['거래량비율'] <= scanner.max_volume_ratio and
                           scanner.min_trade_value <= stock_data[str(row['종목코드']).strip()]['거래대금'] <= scanner.max_trade_value]
            
            if passed_stocks:
                avg_profit = sum(float(row['수익률']) for row in passed_stocks) / len(passed_stocks)
                print(f"   기본 조건 평균 수익률: {avg_profit:.2f}%")
        
        if optimal_count > 0:
            optimal_stocks = [row for _, row in df.iterrows() if str(row['종목코드']).strip() in stock_data and 
                            scanner.optimal_volume_ratio_range[0] <= stock_data[str(row['종목코드']).strip()]['거래량비율'] <= scanner.optimal_volume_ratio_range[1] and
                            scanner.optimal_trade_value_range[0] <= stock_data[str(row['종목코드']).strip()]['거래대금'] <= scanner.optimal_trade_value_range[1]]
            
            if optimal_stocks:
                avg_profit = sum(float(row['수익률']) for row in optimal_stocks) / len(optimal_stocks)
                print(f"   최적 조건 평균 수익률: {avg_profit:.2f}%")
    
    except Exception as e:
        print(f"❌ 시뮬레이션 오류: {e}")
    
    print("\n✅ 최적화된 매수 조건 테스트 완료!")

if __name__ == "__main__":
    import re
    asyncio.run(test_optimized_conditions()) 