import re
from datetime import datetime

def analyze_specific_log_section():
    print("로그 파일에서 34938~35187라인 구간을 추출하고 분석합니다...")
    
    with open('logs/stock_manager.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 34938~35187라인 추출
    start_line = 34938
    end_line = 35187
    target_lines = lines[start_line-1:end_line]  # 0-based indexing
    
    print(f"추출된 라인 수: {len(target_lines)}")
    
    # 분석할 패턴들
    patterns = {
        '거래량 급증': [],
        '매수 신호': [],
        '매도 신호': [],
        '매수 체결': [],
        '매도 체결': [],
        '손익': [],
        '거래대금': [],
        '거래량비율': [],
        '수익률': [],
        '손실': [],
        '이익': []
    }
    
    # 패턴별로 로그 분류
    for i, line in enumerate(target_lines, start_line):
        line = line.strip()
        
        # 2025-07-09 09시 로그만 필터링
        if '2025-07-09 09:' not in line:
            continue
            
        for pattern_name in patterns.keys():
            if pattern_name in line:
                patterns[pattern_name].append((i, line))
    
    # 결과 출력
    print(f"\n=== 2025-07-09 09시 로그 분석 결과 ===")
    
    for pattern_name, matched_lines in patterns.items():
        print(f"\n{pattern_name}: {len(matched_lines)}개")
        for line_num, line in matched_lines[:10]:  # 최대 10개까지만 출력
            print(f"  라인 {line_num}: {line}")
        if len(matched_lines) > 10:
            print(f"  ... (총 {len(matched_lines)}개 중 10개만 표시)")
    
    # 거래량 급증 감지된 종목들 추출
    print(f"\n=== 거래량 급증 감지 종목 분석 ===")
    volume_breakout_stocks = set()
    for line_num, line in patterns['거래량 급증']:
        # 종목코드 추출 (6자리 숫자)
        match = re.search(r'(\d{6}):', line)
        if match:
            volume_breakout_stocks.add(match.group(1))
    
    print(f"거래량 급증 감지된 종목: {sorted(volume_breakout_stocks)}")
    
    # 매수/매도 신호 종목들 추출
    buy_signal_stocks = set()
    sell_signal_stocks = set()
    
    for line_num, line in patterns['매수 신호']:
        match = re.search(r'(\d{6})', line)
        if match:
            buy_signal_stocks.add(match.group(1))
    
    for line_num, line in patterns['매도 신호']:
        match = re.search(r'(\d{6})', line)
        if match:
            sell_signal_stocks.add(match.group(1))
    
    print(f"매수 신호 종목: {sorted(buy_signal_stocks)}")
    print(f"매도 신호 종목: {sorted(sell_signal_stocks)}")
    
    # 손익 관련 로그 분석
    print(f"\n=== 손익 관련 로그 분석 ===")
    profit_logs = []
    loss_logs = []
    
    for line_num, line in patterns['손익'] + patterns['수익률'] + patterns['손실'] + patterns['이익']:
        if any(keyword in line for keyword in ['수익', '이익', '플러스', '+']):
            profit_logs.append((line_num, line))
        elif any(keyword in line for keyword in ['손실', '손해', '마이너스', '-']):
            loss_logs.append((line_num, line))
    
    print(f"수익 관련 로그: {len(profit_logs)}개")
    for line_num, line in profit_logs[:5]:
        print(f"  라인 {line_num}: {line}")
    
    print(f"손실 관련 로그: {len(loss_logs)}개")
    for line_num, line in loss_logs[:5]:
        print(f"  라인 {line_num}: {line}")
    
    # 거래대금 분석
    print(f"\n=== 거래대금 분석 ===")
    amount_logs = patterns['거래대금']
    print(f"거래대금 관련 로그: {len(amount_logs)}개")
    for line_num, line in amount_logs[:10]:
        print(f"  라인 {line_num}: {line}")

if __name__ == "__main__":
    analyze_specific_log_section() 