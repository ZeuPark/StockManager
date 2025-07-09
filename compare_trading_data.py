import re
from datetime import datetime

def compare_trading_data():
    print("실제 거래 내역과 로그를 비교 분석합니다...")
    
    # 실제 거래 내역 (사용자가 제공한 데이터)
    actual_trades = [
        {"code": "234030", "name": "싸이닉솔루션", "buy_price": 10820, "buy_qty": 10, "sell_price": 11340, "sell_qty": 10, "profit": 4270, "profit_rate": 3.95},
        {"code": "037270", "name": "YG PLUS", "buy_price": 8850, "buy_qty": 10, "sell_price": 9270, "sell_qty": 10, "profit": 3441, "profit_rate": 3.89},
        {"code": "006800", "name": "미래에셋증권", "buy_price": 21350, "buy_qty": 9, "sell_price": 22300, "sell_qty": 9, "profit": 6879, "profit_rate": 3.58},
        {"code": "060250", "name": "NHN KCP", "buy_price": 14300, "buy_qty": 10, "sell_price": 14720, "sell_qty": 10, "profit": 2970, "profit_rate": 2.08},
        {"code": "088350", "name": "한화생명", "buy_price": 3755, "buy_qty": 10, "sell_price": 3780, "sell_qty": 10, "profit": -66, "profit_rate": -0.18},
        {"code": "028050", "name": "삼성E&A", "buy_price": 24850, "buy_qty": 8, "sell_price": 24900, "sell_qty": 8, "profit": -1278, "profit_rate": -0.64},
        {"code": "012800", "name": "대창", "buy_price": 1442, "buy_qty": 10, "sell_price": 1440, "sell_qty": 10, "profit": -141, "profit_rate": -0.98},
        {"code": "003540", "name": "대신증권", "buy_price": 30358, "buy_qty": 6, "sell_price": 30300, "sell_qty": 6, "profit": -1882, "profit_rate": -1.03},
        {"code": "001440", "name": "대한전선", "buy_price": 16035, "buy_qty": 20, "sell_price": 15950, "sell_qty": 20, "profit": -4407, "profit_rate": -1.37},
        {"code": "462860", "name": "더즌", "buy_price": 5370, "buy_qty": 10, "sell_price": 5330, "sell_qty": 10, "profit": -839, "profit_rate": -1.56},
        {"code": "003530", "name": "한화투자증권", "buy_price": 6890, "buy_qty": 10, "sell_price": 6835, "sell_qty": 10, "profit": -1122, "profit_rate": -1.63},
        {"code": "041190", "name": "우리기술투자", "buy_price": 9780, "buy_qty": 10, "sell_price": 9700, "sell_qty": 10, "profit": -1614, "profit_rate": -1.65},
        {"code": "001200", "name": "유진투자증권", "buy_price": 4050, "buy_qty": 10, "sell_price": 4015, "sell_qty": 10, "profit": -690, "profit_rate": -1.70},
        {"code": "032820", "name": "우리기술", "buy_price": 3895, "buy_qty": 10, "sell_price": 3860, "sell_qty": 10, "profit": -667, "profit_rate": -1.71},
        {"code": "199820", "name": "제일일렉트릭", "buy_price": 11540, "buy_qty": 10, "sell_price": 11440, "sell_qty": 10, "profit": -1971, "profit_rate": -1.71},
        {"code": "010140", "name": "삼성중공업", "buy_price": 17330, "buy_qty": 10, "sell_price": 17170, "sell_qty": 10, "profit": -3057, "profit_rate": -1.76},
        {"code": "103590", "name": "일진전기", "buy_price": 38200, "buy_qty": 5, "sell_price": 37850, "sell_qty": 5, "profit": -3353, "profit_rate": -1.76},
        {"code": "316140", "name": "우리금융지주", "buy_price": 25400, "buy_qty": 14, "sell_price": 25284, "sell_qty": 28, "profit": -6395, "profit_rate": -1.80},
        {"code": "450080", "name": "에코프로머티", "buy_price": 48813, "buy_qty": 4, "sell_price": 48338, "sell_qty": 4, "profit": -3539, "profit_rate": -1.81},
        {"code": "323410", "name": "카카오뱅크", "buy_price": 30100, "buy_qty": 6, "sell_price": 29800, "sell_qty": 6, "profit": -3318, "profit_rate": -1.84},
        {"code": "475430", "name": "키스트론", "buy_price": 6880, "buy_qty": 10, "sell_price": 6800, "sell_qty": 10, "profit": -1372, "profit_rate": -1.99},
        {"code": "294570", "name": "쿠콘", "buy_price": 36825, "buy_qty": 10, "sell_price": 36325, "sell_qty": 10, "profit": -8094, "profit_rate": -2.20},
        {"code": "006220", "name": "제주은행", "buy_price": 16420, "buy_qty": 10, "sell_price": 16192, "sell_qty": 10, "profit": -3652, "profit_rate": -2.22}
    ]
    
    # 로그에서 매매 신호 추출
    with open('logs/trading.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 2025-07-09 09시 로그 필터링
    target_lines = []
    for line in lines:
        if '2025-07-09 09:' in line:
            target_lines.append(line.strip())
    
    # 매수/매도 신호 추출
    buy_signals = []
    sell_signals = []
    
    for line in target_lines:
        if '매수 후보 선정' in line or '주문 실행: 매수' in line:
            buy_signals.append(line)
        elif '매도 주문 실행' in line or '주문 실행: 매도' in line:
            sell_signals.append(line)
    
    print(f"=== 실제 거래 내역 vs 로그 비교 분석 ===")
    print(f"실제 거래 종목 수: {len(actual_trades)}개")
    print(f"로그 매수 신호: {len(buy_signals)}개")
    print(f"로그 매도 신호: {len(sell_signals)}개")
    
    # 실제 거래 종목들
    actual_stocks = set(trade["code"] for trade in actual_trades)
    print(f"\n실제 거래된 종목: {sorted(actual_stocks)}")
    
    # 로그에서 매수 신호 종목 추출
    buy_stocks_from_log = set()
    for line in buy_signals:
        match = re.search(r'(\d{6})', line)
        if match:
            buy_stocks_from_log.add(match.group(1))
    
    # 로그에서 매도 신호 종목 추출
    sell_stocks_from_log = set()
    for line in sell_signals:
        match = re.search(r'(\d{6})', line)
        if match:
            sell_stocks_from_log.add(match.group(1))
    
    print(f"로그 매수 신호 종목: {sorted(buy_stocks_from_log)}")
    print(f"로그 매도 신호 종목: {sorted(sell_stocks_from_log)}")
    
    # 매칭 분석
    matched_buy = actual_stocks.intersection(buy_stocks_from_log)
    matched_sell = actual_stocks.intersection(sell_stocks_from_log)
    
    print(f"\n매수 신호 매칭: {len(matched_buy)}/{len(actual_stocks)} = {len(matched_buy)/len(actual_stocks)*100:.1f}%")
    print(f"매도 신호 매칭: {len(matched_sell)}/{len(actual_stocks)} = {len(matched_sell)/len(actual_stocks)*100:.1f}%")
    
    # 손익 분석
    print(f"\n=== 손익 분석 ===")
    total_profit = sum(trade["profit"] for trade in actual_trades)
    total_amount = sum(trade["buy_price"] * trade["buy_qty"] for trade in actual_trades)
    
    print(f"총 손익: {total_profit:,}원")
    print(f"총 매입금액: {total_amount:,}원")
    print(f"전체 수익률: {total_profit/total_amount*100:.2f}%")
    
    # 수익/손실 거래 분리
    profit_trades = [t for t in actual_trades if t["profit"] > 0]
    loss_trades = [t for t in actual_trades if t["profit"] < 0]
    
    print(f"\n수익 거래: {len(profit_trades)}개")
    print(f"손실 거래: {len(loss_trades)}개")
    
    if profit_trades:
        avg_profit = sum(t["profit"] for t in profit_trades) / len(profit_trades)
        print(f"평균 수익: {avg_profit:,.0f}원")
        print("수익 종목:")
        for trade in profit_trades:
            print(f"  {trade['code']}({trade['name']}): {trade['profit']:,}원 ({trade['profit_rate']:.2f}%)")
    
    if loss_trades:
        avg_loss = sum(t["profit"] for t in loss_trades) / len(loss_trades)
        print(f"평균 손실: {avg_loss:,.0f}원")
        print("손실 종목:")
        for trade in loss_trades:
            print(f"  {trade['code']}({trade['name']}): {trade['profit']:,}원 ({trade['profit_rate']:.2f}%)")
    
    # 거래대금별 분석
    print(f"\n=== 거래대금별 분석 ===")
    for trade in actual_trades:
        amount = trade["buy_price"] * trade["buy_qty"]
        print(f"{trade['code']}({trade['name']}): {amount:,}원 - {trade['profit_rate']:.2f}%")
    
    # 공통점 분석
    print(f"\n=== 공통점 분석 ===")
    
    # 수익 거래의 공통점
    if profit_trades:
        profit_amounts = [t["buy_price"] * t["buy_qty"] for t in profit_trades]
        print(f"수익 거래 평균 거래대금: {sum(profit_amounts)/len(profit_amounts):,.0f}원")
        print(f"수익 거래 거래대금 범위: {min(profit_amounts):,}원 ~ {max(profit_amounts):,}원")
    
    # 손실 거래의 공통점
    if loss_trades:
        loss_amounts = [t["buy_price"] * t["buy_qty"] for t in loss_trades]
        print(f"손실 거래 평균 거래대금: {sum(loss_amounts)/len(loss_amounts):,.0f}원")
        print(f"손실 거래 거래대금 범위: {min(loss_amounts):,}원 ~ {max(loss_amounts):,}원")

if __name__ == "__main__":
    compare_trading_data() 