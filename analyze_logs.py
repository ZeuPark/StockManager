import re
from datetime import datetime

def analyze_trading_logs():
    with open('logs/stock_manager.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 2025-07-09 09시 로그 필터링
    target_lines = []
    for line in lines:
        if '2025-07-09 09:' in line and ('거래량 급증' in line or '매수' in line or '매도' in line or '거래량비율' in line or '거래대금' in line):
            target_lines.append(line.strip())
    
    print(f"총 {len(target_lines)}개의 관련 로그 발견")
    
    # 실제 거래 내역 (사용자가 제공한 데이터)
    actual_trades = [
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "004990", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "004990", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "010140", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "010140", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "004990", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "004990", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "028050", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "028050", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "010140", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "010140", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "450080", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "450080", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "004990", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "004990", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "010140", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "010140", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "032820", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200},
        {"code": "450080", "action": "매수", "price": 12350, "quantity": 8, "amount": 98800, "fee": 0, "profit": -200},
        {"code": "450080", "action": "매도", "price": 12325, "quantity": 8, "amount": 98600, "fee": 0, "profit": -200}
    ]
    
    # 거래량 급증 감지 로그 분석
    volume_breakout = []
    for line in target_lines:
        if '거래량 급증 자동매매 조건' in line:
            volume_breakout.append(line)
    
    print(f"\n=== 거래량 급증 감지 분석 ===")
    print(f"거래량 급증 감지: {len(volume_breakout)}개")
    
    # 실제 거래된 종목들
    traded_stocks = set()
    for trade in actual_trades:
        traded_stocks.add(trade["code"])
    
    print(f"실제 거래된 종목: {sorted(traded_stocks)}")
    
    # 거래량 급증 감지된 종목들 추출
    detected_stocks = set()
    for log in volume_breakout:
        # 로그에서 종목코드 추출
        match = re.search(r'(\d{6}):', log)
        if match:
            detected_stocks.add(match.group(1))
    
    print(f"거래량 급증 감지된 종목: {sorted(detected_stocks)}")
    
    # 매칭 분석
    matched_stocks = traded_stocks.intersection(detected_stocks)
    print(f"매칭된 종목: {sorted(matched_stocks)}")
    print(f"매칭률: {len(matched_stocks)}/{len(traded_stocks)} = {len(matched_stocks)/len(traded_stocks)*100:.1f}%")
    
    # 손익 분석
    print(f"\n=== 손익 분석 ===")
    total_profit = sum(trade["profit"] for trade in actual_trades)
    total_amount = sum(trade["amount"] for trade in actual_trades)
    
    print(f"총 손익: {total_profit:,}원")
    print(f"총 거래대금: {total_amount:,}원")
    print(f"수익률: {total_profit/total_amount*100:.2f}%")
    
    # 종목별 손익 분석
    stock_profits = {}
    for trade in actual_trades:
        code = trade["code"]
        if code not in stock_profits:
            stock_profits[code] = {"profit": 0, "trades": 0}
        stock_profits[code]["profit"] += trade["profit"]
        stock_profits[code]["trades"] += 1
    
    print(f"\n=== 종목별 손익 ===")
    for code, data in sorted(stock_profits.items()):
        avg_profit = data["profit"] / data["trades"]
        print(f"{code}: {data['profit']:,}원 (평균 {avg_profit:,.0f}원/거래, {data['trades']}회 거래)")
    
    # 공통점 분석
    print(f"\n=== 공통점 분석 ===")
    
    # 거래대금 분석
    amounts = [trade["amount"] for trade in actual_trades]
    avg_amount = sum(amounts) / len(amounts)
    print(f"평균 거래대금: {avg_amount:,.0f}원")
    print(f"거래대금 범위: {min(amounts):,}원 ~ {max(amounts):,}원")
    
    # 손실 거래와 수익 거래 분리
    loss_trades = [t for t in actual_trades if t["profit"] < 0]
    profit_trades = [t for t in actual_trades if t["profit"] > 0]
    
    print(f"\n손실 거래: {len(loss_trades)}개")
    if loss_trades:
        loss_amounts = [t["amount"] for t in loss_trades]
        print(f"손실 거래 평균 거래대금: {sum(loss_amounts)/len(loss_amounts):,.0f}원")
    
    print(f"수익 거래: {len(profit_trades)}개")
    if profit_trades:
        profit_amounts = [t["amount"] for t in profit_trades]
        print(f"수익 거래 평균 거래대금: {sum(profit_amounts)/len(profit_amounts):,.0f}원")

if __name__ == "__main__":
    analyze_trading_logs() 