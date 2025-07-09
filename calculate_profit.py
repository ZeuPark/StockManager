def calculate_actual_profit():
    print("실제 거래 내역의 손익을 정확히 계산합니다...")
    
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
    
    print("=== 개별 거래 손익 계산 ===")
    total_profit = 0
    total_buy_amount = 0
    total_sell_amount = 0
    
    for i, trade in enumerate(actual_trades, 1):
        buy_amount = trade["buy_price"] * trade["buy_qty"]
        sell_amount = trade["sell_price"] * trade["sell_qty"]
        calculated_profit = sell_amount - buy_amount
        
        total_buy_amount += buy_amount
        total_sell_amount += sell_amount
        total_profit += calculated_profit
        
        print(f"{i:2d}. {trade['code']}({trade['name']}): "
              f"매수 {buy_amount:,}원 → 매도 {sell_amount:,}원 = "
              f"{calculated_profit:+,}원 ({trade['profit_rate']:+.2f}%)")
    
    print(f"\n=== 총계 ===")
    print(f"총 매입금액: {total_buy_amount:,}원")
    print(f"총 매도금액: {total_sell_amount:,}원")
    print(f"총 손익: {total_profit:+,}원")
    print(f"전체 수익률: {total_profit/total_buy_amount*100:+.2f}%")
    
    # 수익/손실 거래 분리
    profit_trades = [t for t in actual_trades if t["profit"] > 0]
    loss_trades = [t for t in actual_trades if t["profit"] < 0]
    
    print(f"\n=== 수익/손실 분석 ===")
    print(f"수익 거래: {len(profit_trades)}개")
    print(f"손실 거래: {len(loss_trades)}개")
    
    if profit_trades:
        total_profit_amount = sum(t["profit"] for t in profit_trades)
        print(f"총 수익: +{total_profit_amount:,}원")
    
    if loss_trades:
        total_loss_amount = sum(t["profit"] for t in loss_trades)
        print(f"총 손실: {total_loss_amount:,}원")
    
    print(f"순손익: {total_profit:+,}원")

if __name__ == "__main__":
    calculate_actual_profit() 