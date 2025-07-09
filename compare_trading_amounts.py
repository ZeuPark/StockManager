import re
from datetime import datetime

def compare_trading_amounts():
    print("실제 거래 내역과 로그의 거래대금을 자세히 비교 분석합니다...")
    
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
    
    # 실제 거래대금 계산
    for trade in actual_trades:
        trade["actual_amount"] = trade["buy_price"] * trade["buy_qty"]
    
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
    
    print(f"=== 실제 거래 내역 vs 로그 거래대금 비교 ===")
    print(f"실제 거래 종목 수: {len(actual_trades)}개")
    print(f"로그 거래대금 기록 종목 수: {len(log_amounts)}개")
    
    # 실제 거래 종목들의 거래대금과 로그 거래대금 비교
    print(f"\n=== 종목별 거래대금 비교 ===")
    matched_count = 0
    
    for trade in actual_trades:
        code = trade["code"]
        actual_amount = trade["actual_amount"]
        actual_profit = trade["profit"]
        actual_profit_rate = trade["profit_rate"]
        
        print(f"\n{code}({trade['name']}):")
        print(f"  실제 거래대금: {actual_amount:,}원")
        print(f"  실제 손익: {actual_profit:+,}원 ({actual_profit_rate:+.2f}%)")
        
        if code in log_amounts:
            log_amounts_list = log_amounts[code]
            avg_log_amount = sum(log_amounts_list) / len(log_amounts_list)
            print(f"  로그 거래대금: {avg_log_amount:,.0f}원 (평균, {len(log_amounts_list)}회 기록)")
            print(f"  로그 거래대금 범위: {min(log_amounts_list):,}원 ~ {max(log_amounts_list):,}원")
            
            # 거래대금 차이 분석
            amount_diff = abs(actual_amount - avg_log_amount)
            amount_diff_rate = amount_diff / avg_log_amount * 100
            print(f"  거래대금 차이: {amount_diff:,}원 ({amount_diff_rate:.1f}%)")
            
            if amount_diff_rate < 10:  # 10% 이내 차이
                print(f"  → 거래대금 일치도: 높음")
                matched_count += 1
            elif amount_diff_rate < 50:
                print(f"  → 거래대금 일치도: 보통")
            else:
                print(f"  → 거래대금 일치도: 낮음")
        else:
            print(f"  로그 거래대금: 기록 없음")
    
    print(f"\n=== 거래대금 일치도 분석 ===")
    print(f"거래대금 일치 종목: {matched_count}/{len(actual_trades)} = {matched_count/len(actual_trades)*100:.1f}%")
    
    # 손익별 거래대금 분석
    print(f"\n=== 손익별 거래대금 분석 ===")
    
    profit_trades = [t for t in actual_trades if t["profit"] > 0]
    loss_trades = [t for t in actual_trades if t["profit"] < 0]
    
    if profit_trades:
        profit_amounts = [t["actual_amount"] for t in profit_trades]
        print(f"수익 거래 ({len(profit_trades)}개):")
        print(f"  평균 거래대금: {sum(profit_amounts)/len(profit_amounts):,.0f}원")
        print(f"  거래대금 범위: {min(profit_amounts):,}원 ~ {max(profit_amounts):,}원")
        print(f"  수익 종목들:")
        for trade in profit_trades:
            print(f"    {trade['code']}: {trade['actual_amount']:,}원 → {trade['profit']:+,}원")
    
    if loss_trades:
        loss_amounts = [t["actual_amount"] for t in loss_trades]
        print(f"손실 거래 ({len(loss_trades)}개):")
        print(f"  평균 거래대금: {sum(loss_amounts)/len(loss_amounts):,.0f}원")
        print(f"  거래대금 범위: {min(loss_amounts):,}원 ~ {max(loss_amounts):,}원")
        print(f"  손실 종목들:")
        for trade in loss_trades:
            print(f"    {trade['code']}: {trade['actual_amount']:,}원 → {trade['profit']:+,}원")
    
    # 거래대금 구간별 손익 분석
    print(f"\n=== 거래대금 구간별 손익 분석 ===")
    
    amount_ranges = [
        (0, 100000, "10만원 미만"),
        (100000, 200000, "10-20만원"),
        (200000, 300000, "20-30만원"),
        (300000, 500000, "30-50만원"),
        (500000, float('inf'), "50만원 이상")
    ]
    
    for min_amount, max_amount, range_name in amount_ranges:
        if max_amount == float('inf'):
            trades_in_range = [t for t in actual_trades if t["actual_amount"] >= min_amount]
        else:
            trades_in_range = [t for t in actual_trades if min_amount <= t["actual_amount"] < max_amount]
        
        if trades_in_range:
            total_profit = sum(t["profit"] for t in trades_in_range)
            avg_profit_rate = sum(t["profit_rate"] for t in trades_in_range) / len(trades_in_range)
            print(f"{range_name} ({len(trades_in_range)}개): {total_profit:+,}원 (평균 {avg_profit_rate:+.2f}%)")

if __name__ == "__main__":
    compare_trading_amounts() 