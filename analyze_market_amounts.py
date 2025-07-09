import re
from datetime import datetime

def analyze_market_amounts():
    print("시장 전체 거래대금 기준으로 수익/손실 거래를 비교 분석합니다...")
    
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
    
    # 로그에서 거래대금 정보 추출
    with open('logs/trading.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 2025-07-09 09시 로그 필터링
    target_lines = []
    for line in lines:
        if '2025-07-09 09:' in line and '거래대금' in line:
            target_lines.append(line.strip())
    
    # 로그에서 거래대금 정보 파싱
    log_amounts = {}
    for line in target_lines:
        # 종목코드와 거래대금 추출
        code_match = re.search(r'\[([^(]+)\((\d{6})\)\]', line)
        amount_match = re.search(r'거래대금:\s*([\d,]+)원', line)
        
        if code_match and amount_match:
            code = code_match.group(2)
            amount_str = amount_match.group(1).replace(',', '')
            amount = int(amount_str)
            
            if code not in log_amounts:
                log_amounts[code] = []
            log_amounts[code].append(amount)
    
    print(f"=== 시장 전체 거래대금 기준 수익/손실 분석 ===")
    
    # 수익/손실 거래 분리
    profit_trades = [t for t in actual_trades if t["profit"] > 0]
    loss_trades = [t for t in actual_trades if t["profit"] < 0]
    
    print(f"수익 거래: {len(profit_trades)}개")
    print(f"손실 거래: {len(loss_trades)}개")
    
    # 수익 거래의 시장 거래대금 분석
    print(f"\n=== 수익 거래의 시장 거래대금 분석 ===")
    profit_market_amounts = []
    
    for trade in profit_trades:
        code = trade["code"]
        if code in log_amounts:
            avg_market_amount = sum(log_amounts[code]) / len(log_amounts[code])
            profit_market_amounts.append(avg_market_amount)
            print(f"{code}({trade['name']}):")
            print(f"  개인 손익: {trade['profit']:+,}원 ({trade['profit_rate']:+.2f}%)")
            print(f"  시장 거래대금: {avg_market_amount:,.0f}원")
            print(f"  시장 거래대금 범위: {min(log_amounts[code]):,}원 ~ {max(log_amounts[code]):,}원")
        else:
            print(f"{code}({trade['name']}): 시장 거래대금 기록 없음")
    
    if profit_market_amounts:
        print(f"\n수익 거래 시장 거래대금 통계:")
        print(f"  평균: {sum(profit_market_amounts)/len(profit_market_amounts):,.0f}원")
        print(f"  최소: {min(profit_market_amounts):,.0f}원")
        print(f"  최대: {max(profit_market_amounts):,.0f}원")
    
    # 손실 거래의 시장 거래대금 분석
    print(f"\n=== 손실 거래의 시장 거래대금 분석 ===")
    loss_market_amounts = []
    
    for trade in loss_trades:
        code = trade["code"]
        if code in log_amounts:
            avg_market_amount = sum(log_amounts[code]) / len(log_amounts[code])
            loss_market_amounts.append(avg_market_amount)
            print(f"{code}({trade['name']}):")
            print(f"  개인 손익: {trade['profit']:+,}원 ({trade['profit_rate']:+.2f}%)")
            print(f"  시장 거래대금: {avg_market_amount:,.0f}원")
            print(f"  시장 거래대금 범위: {min(log_amounts[code]):,}원 ~ {max(log_amounts[code]):,}원")
        else:
            print(f"{code}({trade['name']}): 시장 거래대금 기록 없음")
    
    if loss_market_amounts:
        print(f"\n손실 거래 시장 거래대금 통계:")
        print(f"  평균: {sum(loss_market_amounts)/len(loss_market_amounts):,.0f}원")
        print(f"  최소: {min(loss_market_amounts):,.0f}원")
        print(f"  최대: {max(loss_market_amounts):,.0f}원")
    
    # 시장 거래대금 구간별 분석
    print(f"\n=== 시장 거래대금 구간별 수익/손실 분석 ===")
    
    # 수익 거래 구간별 분석
    if profit_market_amounts:
        profit_ranges = {
            "1억원 미만": [a for a in profit_market_amounts if a < 100000000],
            "1-5억원": [a for a in profit_market_amounts if 100000000 <= a < 500000000],
            "5-10억원": [a for a in profit_market_amounts if 500000000 <= a < 1000000000],
            "10억원 이상": [a for a in profit_market_amounts if a >= 1000000000]
        }
        
        print("수익 거래 시장 거래대금 구간별 분포:")
        for range_name, amounts in profit_ranges.items():
            if amounts:
                print(f"  {range_name}: {len(amounts)}개 (평균 {sum(amounts)/len(amounts):,.0f}원)")
    
    # 손실 거래 구간별 분석
    if loss_market_amounts:
        loss_ranges = {
            "1억원 미만": [a for a in loss_market_amounts if a < 100000000],
            "1-5억원": [a for a in loss_market_amounts if 100000000 <= a < 500000000],
            "5-10억원": [a for a in loss_market_amounts if 500000000 <= a < 1000000000],
            "10억원 이상": [a for a in loss_market_amounts if a >= 1000000000]
        }
        
        print("손실 거래 시장 거래대금 구간별 분포:")
        for range_name, amounts in loss_ranges.items():
            if amounts:
                print(f"  {range_name}: {len(amounts)}개 (평균 {sum(amounts)/len(amounts):,.0f}원)")
    
    # 시장 거래대금과 수익률의 상관관계 분석
    print(f"\n=== 시장 거래대금과 수익률 상관관계 분석 ===")
    
    all_trades_with_market_amount = []
    for trade in actual_trades:
        code = trade["code"]
        if code in log_amounts:
            avg_market_amount = sum(log_amounts[code]) / len(log_amounts[code])
            all_trades_with_market_amount.append({
                "code": code,
                "name": trade["name"],
                "profit_rate": trade["profit_rate"],
                "market_amount": avg_market_amount
            })
    
    if all_trades_with_market_amount:
        # 시장 거래대금 순으로 정렬
        sorted_trades = sorted(all_trades_with_market_amount, key=lambda x: x["market_amount"])
        
        print("시장 거래대금 순으로 정렬된 수익률:")
        for trade in sorted_trades:
            print(f"  {trade['code']}({trade['name']}): {trade['market_amount']:,.0f}원 → {trade['profit_rate']:+.2f}%")
        
        # 상위/하위 거래대금 종목 분석
        top_5 = sorted_trades[-5:]  # 상위 5개
        bottom_5 = sorted_trades[:5]  # 하위 5개
        
        print(f"\n시장 거래대금 상위 5개 종목:")
        for trade in top_5:
            print(f"  {trade['code']}({trade['name']}): {trade['market_amount']:,.0f}원 → {trade['profit_rate']:+.2f}%")
        
        print(f"\n시장 거래대금 하위 5개 종목:")
        for trade in bottom_5:
            print(f"  {trade['code']}({trade['name']}): {trade['market_amount']:,.0f}원 → {trade['profit_rate']:+.2f}%")

if __name__ == "__main__":
    analyze_market_amounts() 