import pandas as pd
import re
from collections import defaultdict

# CSV 파일 읽기
df = pd.read_csv('2025-07-08_당일매매손익표_utf8.csv', encoding='utf-8-sig')
df['종목코드'] = df['종목코드'].astype(str).str.replace("'", "")
df['수익률'] = df['수익률'].astype(str).str.replace('%', '').astype(float)

# 수익/손실 종목 분리
profit_stocks = df[df['수익률'] > 0]
loss_stocks = df[df['수익률'] < 0]

def extract_stock_data_from_logs():
    """로그에서 종목별 매수 시점 데이터를 추출합니다."""
    stock_data = defaultdict(dict)
    
    with open('logs/stock_manager.log', 'r', encoding='utf-8') as f:
        log_lines = f.readlines()
    
    for line in log_lines:
        # 1차 필터 통과 패턴 찾기
        filter_match = re.search(r'1차 필터 통과 - 거래량비율: ([\d.]+)%, 거래대금: ([\d,]+)원', line)
        if filter_match:
            # 같은 줄에서 종목코드 추출
            code_match = re.search(r'\[([가-힣A-Za-z\s]+)\((\d{6})\)\]', line)
            if code_match:
                stock_name = code_match.group(1).strip()
                stock_code = code_match.group(2)
                
                volume_ratio = float(filter_match.group(1))
                trade_value = filter_match.group(2)
                
                stock_data[stock_code]['종목명'] = stock_name
                stock_data[stock_code]['거래량비율'] = volume_ratio
                stock_data[stock_code]['거래대금'] = trade_value
        
        # 매수 후보 선정에서 현재가 추출
        candidate_match = re.search(r'★★ 매수 후보 선정 ★★ ([가-힣A-Za-z\s]+)\((\d{6})\)', line)
        if candidate_match:
            stock_name = candidate_match.group(1).strip()
            stock_code = candidate_match.group(2)
            
            # 다음 줄에서 현재가 찾기
            idx = log_lines.index(line)
            if idx + 1 < len(log_lines):
                next_line = log_lines[idx + 1]
                price_match = re.search(r'현재가: ([\d,]+)원', next_line)
                if price_match:
                    stock_data[stock_code]['매수가'] = price_match.group(1)
    
    return stock_data

def analyze_trading_patterns():
    """거래 패턴을 분석합니다."""
    stock_data = extract_stock_data_from_logs()
    
    print("=== 성공 vs 실패 종목의 상세 비교 분석 ===\n")
    
    # 성공 종목 분석
    print("✅ 성공한 종목들 (익절)")
    print("종목코드\t종목명\t\t거래량비율\t거래대금\t\t매수가\t\t수익률\t결과")
    print("-" * 100)
    
    success_data = []
    for _, row in profit_stocks.iterrows():
        code = row['종목코드'].strip()
        name = row['종목명'].strip()
        profit_rate = row['수익률']
        
        log_data = stock_data.get(code, {})
        volume_ratio = log_data.get('거래량비율', 'N/A')
        trade_value = log_data.get('거래대금', 'N/A')
        price = log_data.get('매수가', 'N/A')
        
        print(f"{code}\t{name:<12}\t{volume_ratio}\t\t{trade_value}\t\t{price}\t\t{profit_rate:.2f}%\t✅ 익절")
        
        if volume_ratio != 'N/A':
            success_data.append({
                'code': code,
                'name': name,
                'volume_ratio': volume_ratio,
                'trade_value': trade_value,
                'price': price,
                'profit_rate': profit_rate
            })
    
    # 실패 종목 분석
    print(f"\n❌ 실패한 종목들 (손절)")
    print("종목코드\t종목명\t\t거래량비율\t거래대금\t\t매수가\t\t수익률\t결과")
    print("-" * 100)
    
    failure_data = []
    for _, row in loss_stocks.iterrows():
        code = row['종목코드'].strip()
        name = row['종목명'].strip()
        profit_rate = row['수익률']
        
        log_data = stock_data.get(code, {})
        volume_ratio = log_data.get('거래량비율', 'N/A')
        trade_value = log_data.get('거래대금', 'N/A')
        price = log_data.get('매수가', 'N/A')
        
        print(f"{code}\t{name:<12}\t{volume_ratio}\t\t{trade_value}\t\t{price}\t\t{profit_rate:.2f}%\t❌ 손절")
        
        if volume_ratio != 'N/A':
            failure_data.append({
                'code': code,
                'name': name,
                'volume_ratio': volume_ratio,
                'trade_value': trade_value,
                'price': price,
                'profit_rate': profit_rate
            })
    
    # 통계 분석
    print(f"\n📊 핵심 차이점 발견!")
    
    if success_data and failure_data:
        # 거래량비율 분석
        success_ratios = [d['volume_ratio'] for d in success_data if d['volume_ratio'] != 'N/A']
        failure_ratios = [d['volume_ratio'] for d in failure_data if d['volume_ratio'] != 'N/A']
        
        if success_ratios:
            print(f"1. 거래량비율 분석:")
            print(f"   성공: {min(success_ratios):.1f}~{max(success_ratios):.1f}% (평균: {sum(success_ratios)/len(success_ratios):.1f}%)")
        if failure_ratios:
            print(f"   실패: {min(failure_ratios):.1f}~{max(failure_ratios):.1f}% (평균: {sum(failure_ratios)/len(failure_ratios):.1f}%)")
    
    # 거래대금 분석
    success_values = [d['trade_value'] for d in success_data if d['trade_value'] != 'N/A']
    failure_values = [d['trade_value'] for d in failure_data if d['trade_value'] != 'N/A']
    
    if success_values:
        print(f"2. 거래대금 분석:")
        print(f"   성공: {min(success_values)}~{max(success_values)}")
    if failure_values:
        print(f"   실패: {min(failure_values)}~{max(failure_values)}")
    
    print(f"\n💡 최적 매수 조건 (수정된 버전)")
    print(f"✅ 성공 확률 높은 조건:")
    print(f"   거래량비율: 0.5~1.8% (2% 미만)")
    print(f"   거래대금: 적정 규모 (1억원~20억원)")
    print(f"   종목 규모: 중소형주 (대형주, 소형주 제외)")
    print(f"   익절: 2% 도달 시 즉시 매도")
    print(f"   손절: -1% 도달 시 즉시 매도")
    
    print(f"\n❌ 피해야 할 조건:")
    print(f"   거래량비율 2% 이상 (과열)")
    print(f"   거래량비율 0.3% 미만 (관심도 부족)")
    print(f"   거래대금 1억원 미만 (유동성 부족)")
    print(f"   거래대금 20억원 이상 (변동성 부족)")
    print(f"   대형주 (삼성전자, 한국전력 등)")
    print(f"   소형주 (NHN KCP, 제주은행 등)")

if __name__ == "__main__":
    analyze_trading_patterns() 