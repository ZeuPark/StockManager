import re
from datetime import datetime

def analyze_trading_logs():
    print("trading.log 파일에서 2025-07-09 09시 구간을 분석합니다...")
    
    with open('logs/trading.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 2025-07-09 09시 로그 필터링
    target_lines = []
    for line in lines:
        if '2025-07-09 09:' in line:
            target_lines.append(line.strip())
    
    print(f"총 {len(target_lines)}개의 09시 로그 발견")
    
    # 분석할 패턴들
    patterns = {
        '매수': [],
        '매도': [],
        '체결': [],
        '손익': [],
        '수익': [],
        '손실': [],
        '거래대금': [],
        '거래량': [],
        '돌파': [],
        'RE-BREAKOUT': [],
        'BREAKOUT': []
    }
    
    # 패턴별로 로그 분류
    for line in target_lines:
        for pattern_name in patterns.keys():
            if pattern_name in line:
                patterns[pattern_name].append(line)
    
    # 결과 출력
    print(f"\n=== 2025-07-09 09시 trading.log 분석 결과 ===")
    
    for pattern_name, matched_lines in patterns.items():
        print(f"\n{pattern_name}: {len(matched_lines)}개")
        for i, line in enumerate(matched_lines[:10]):  # 최대 10개까지만 출력
            print(f"  {i+1}. {line}")
        if len(matched_lines) > 10:
            print(f"  ... (총 {len(matched_lines)}개 중 10개만 표시)")
    
    # 매수/매도 신호 종목들 추출
    print(f"\n=== 매수/매도 신호 종목 분석 ===")
    buy_stocks = set()
    sell_stocks = set()
    
    for line in patterns['매수']:
        # 종목코드 추출 (6자리 숫자)
        match = re.search(r'(\d{6})', line)
        if match:
            buy_stocks.add(match.group(1))
    
    for line in patterns['매도']:
        match = re.search(r'(\d{6})', line)
        if match:
            sell_stocks.add(match.group(1))
    
    print(f"매수 신호 종목: {sorted(buy_stocks)}")
    print(f"매도 신호 종목: {sorted(sell_stocks)}")
    
    # 돌파 감지 종목들 추출
    print(f"\n=== 돌파 감지 종목 분석 ===")
    breakout_stocks = set()
    
    for line in patterns['돌파'] + patterns['RE-BREAKOUT'] + patterns['BREAKOUT']:
        # 종목코드 추출 (6자리 숫자)
        match = re.search(r'(\d{6})', line)
        if match:
            breakout_stocks.add(match.group(1))
    
    print(f"돌파 감지 종목: {sorted(breakout_stocks)}")
    
    # 손익 관련 로그 분석
    print(f"\n=== 손익 관련 로그 분석 ===")
    profit_logs = []
    loss_logs = []
    
    for line in patterns['손익'] + patterns['수익'] + patterns['손실']:
        if any(keyword in line for keyword in ['수익', '이익', '플러스', '+', '익절']):
            profit_logs.append(line)
        elif any(keyword in line for keyword in ['손실', '손해', '마이너스', '-', '손절']):
            loss_logs.append(line)
    
    print(f"수익 관련 로그: {len(profit_logs)}개")
    for i, line in enumerate(profit_logs[:5]):
        print(f"  {i+1}. {line}")
    
    print(f"손실 관련 로그: {len(loss_logs)}개")
    for i, line in enumerate(loss_logs[:5]):
        print(f"  {i+1}. {line}")
    
    # 거래대금 분석
    print(f"\n=== 거래대금 분석 ===")
    amount_logs = patterns['거래대금']
    print(f"거래대금 관련 로그: {len(amount_logs)}개")
    for i, line in enumerate(amount_logs[:10]):
        print(f"  {i+1}. {line}")
    
    # 시간대별 분석
    print(f"\n=== 시간대별 분석 ===")
    time_slots = {}
    for line in target_lines:
        # 시간 추출 (09:XX:XX)
        time_match = re.search(r'09:(\d{2}):', line)
        if time_match:
            minute = time_match.group(1)
            if minute not in time_slots:
                time_slots[minute] = []
            time_slots[minute].append(line)
    
    print("분별 로그 개수:")
    for minute in sorted(time_slots.keys()):
        print(f"  09:{minute}:XX - {len(time_slots[minute])}개")

if __name__ == "__main__":
    analyze_trading_logs() 