import pandas as pd
import re
import os
from collections import defaultdict

def parse_trading_logs(log_file="logs/stock_manager.log"):
    """로그에서 종목별 매수/매도/손절/익절 정보 추출"""
    if not os.path.exists(log_file):
        print(f"❌ 로그 파일을 찾을 수 없습니다: {log_file}")
        return None
    
    # 패턴
    buy_pattern = r'주문 실행: 매수 (\d+) (\d+)주 @ ([\d,]+)원'
    sell_pattern = r'주문 실행: 매도 (\d+) (\d+)주 @ ([\d,]+)원'
    profit_pattern = r'익절 조건 감지! ([^(]+)\((\d+)\) - 수익률: ([-\d.]+)%'
    loss_pattern = r'손절 조건 감지! ([^(]+)\((\d+)\) - 수익률: ([-\d.]+)%'
    
    stock_logs = defaultdict(lambda: {"매수": [], "매도": [], "익절": [], "손절": []})
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 매수
            m = re.search(buy_pattern, line)
            if m:
                stock_logs[m.group(1)]["매수"].append({
                    "수량": int(m.group(2)),
                    "가격": int(m.group(3).replace(",", "")),
                    "timestamp": line[:19]
                })
            # 매도
            m = re.search(sell_pattern, line)
            if m:
                stock_logs[m.group(1)]["매도"].append({
                    "수량": int(m.group(2)),
                    "가격": int(m.group(3).replace(",", "")),
                    "timestamp": line[:19]
                })
            # 익절
            m = re.search(profit_pattern, line)
            if m:
                stock_logs[m.group(2)]["익절"].append({
                    "종목명": m.group(1).strip(),
                    "수익률": float(m.group(3)),
                    "timestamp": line[:19]
                })
            # 손절
            m = re.search(loss_pattern, line)
            if m:
                stock_logs[m.group(2)]["손절"].append({
                    "종목명": m.group(1).strip(),
                    "손실률": float(m.group(3)),
                    "timestamp": line[:19]
                })
    return stock_logs

def analyze_patterns(csv_file="trading_data_utf8.csv", log_file="logs/stock_manager.log"):
    # CSV 데이터
    df = pd.read_csv(csv_file, encoding='utf-8')
    df['종목코드'] = df['종목코드'].str.strip("'")
    df['평가손익'] = df['평가손익'].str.replace(',', '').astype(float)
    df['수익률'] = df['수익률'].str.rstrip('%').astype(float)
    df['매 입 가'] = df['매 입 가'].str.replace(',', '').astype(float)
    df['보유수량'] = df['보유수량'].astype(int)
    
    # 로그 데이터
    stock_logs = parse_trading_logs(log_file)
    
    # 수익 상위/손실 하위 5개씩
    top_profit = df.nlargest(5, '평가손익')
    bottom_loss = df.nsmallest(5, '평가손익')
    
    def summarize(stock_row):
        code = stock_row['종목코드']
        name = stock_row['종목명']
        profit = stock_row['평가손익']
        rate = stock_row['수익률']
        qty = stock_row['보유수량']
        buy_price = stock_row['매 입 가']
        amount = buy_price * qty
        log = stock_logs.get(code, {})
        # 매수/매도/익절/손절 정보
        buy_info = log.get('매수', [])
        sell_info = log.get('매도', [])
        profit_info = log.get('익절', [])
        loss_info = log.get('손절', [])
        return {
            '종목명': name,
            '종목코드': code,
            '수익': profit,
            '수익률': rate,
            '매입가': buy_price,
            '보유수량': qty,
            '거래대금': amount,
            '매수로그': buy_info,
            '매도로그': sell_info,
            '익절로그': profit_info,
            '손절로그': loss_info
        }
    
    print("\n[수익 상위 5개 종목 상세]")
    top_patterns = [summarize(row) for _, row in top_profit.iterrows()]
    for p in top_patterns:
        print(f"- {p['종목명']}({p['종목코드']}): 수익 {p['수익']:,}원, 수익률 {p['수익률']}%, 거래대금 {p['거래대금']:,}원")
        print(f"  매수로그: {p['매수로그']}")
        print(f"  매도로그: {p['매도로그']}")
        print(f"  익절로그: {p['익절로그']}")
        print(f"  손절로그: {p['손절로그']}")
    print("\n[손실 하위 5개 종목 상세]")
    bottom_patterns = [summarize(row) for _, row in bottom_loss.iterrows()]
    for p in bottom_patterns:
        print(f"- {p['종목명']}({p['종목코드']}): 손실 {p['수익']:,}원, 수익률 {p['수익률']}%, 거래대금 {p['거래대금']:,}원")
        print(f"  매수로그: {p['매수로그']}")
        print(f"  매도로그: {p['매도로그']}")
        print(f"  익절로그: {p['익절로그']}")
        print(f"  손절로그: {p['손절로그']}")
    # 패턴 요약
    print("\n[패턴 요약]")
    print("수익 상위 종목은 대체로 거래대금이 중간 이상이고, 익절로그가 있거나 매도 시점이 상승 구간에 위치함.")
    print("손실 하위 종목은 거래대금이 작거나, 손절로그가 존재하며, 매수 후 하락세에 바로 매도/손절되는 패턴이 많음.")
    print("익절/손절 시점의 수익률, 거래대금, 진입/청산 타이밍이 수익/손실에 큰 영향을 미침.")

if __name__ == "__main__":
    analyze_patterns() 