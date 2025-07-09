import re
from datetime import datetime

def analyze_stock_info():
    print("각 종목의 매수 시점에서 알 수 있는 정보들을 분석합니다...")
    
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
    
    # 로그에서 각 종목의 정보 추출
    with open('logs/trading.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 2025-07-09 09시 로그 필터링
    target_lines = []
    for line in lines:
        if '2025-07-09 09:' in line:
            target_lines.append(line.strip())
    
    # 각 종목별 정보 수집
    stock_info = {}
    
    for trade in actual_trades:
        code = trade["code"]
        stock_info[code] = {
            "name": trade["name"],
            "buy_price": trade["buy_price"],
            "buy_qty": trade["buy_qty"],
            "profit": trade["profit"],
            "profit_rate": trade["profit_rate"],
            "market_amounts": [],
            "volume_ratios": [],
            "breakout_info": [],
            "buy_signals": [],
            "sell_signals": [],
            "price_changes": [],
            "volume_breakouts": []
        }
    
    # 로그에서 각 종목의 정보 파싱
    for line in target_lines:
        for code in stock_info.keys():
            if code in line:
                # 거래대금 정보
                amount_match = re.search(r'거래대금:\s*([\d,]+)원', line)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '')
                    stock_info[code]["market_amounts"].append(int(amount_str))
                
                # 거래량비율 정보
                volume_match = re.search(r'거래량비율:\s*([\d.]+)%', line)
                if volume_match:
                    volume_ratio = float(volume_match.group(1))
                    stock_info[code]["volume_ratios"].append(volume_ratio)
                
                # 돌파 정보
                if 'BREAKOUT' in line or 'RE-BREAKOUT' in line:
                    stock_info[code]["breakout_info"].append(line)
                
                # 매수 신호
                if '매수 후보 선정' in line or '주문 실행: 매수' in line:
                    stock_info[code]["buy_signals"].append(line)
                
                # 매도 신호
                if '매도 주문 실행' in line or '주문 실행: 매도' in line:
                    stock_info[code]["sell_signals"].append(line)
                
                # 등락률 정보
                change_match = re.search(r'등락률:\s*([+-]?[\d.]+)%', line)
                if change_match:
                    price_change = float(change_match.group(1))
                    stock_info[code]["price_changes"].append(price_change)
                
                # 거래량 돌파 정보
                if '거래량 돌파' in line or '전일 거래량 돌파' in line:
                    stock_info[code]["volume_breakouts"].append(line)
    
    print(f"=== 각 종목의 매수 시점 정보 분석 ===")
    
    # 수익/손실 거래 분리
    profit_trades = [t for t in actual_trades if t["profit"] > 0]
    loss_trades = [t for t in actual_trades if t["profit"] < 0]
    
    print(f"수익 거래: {len(profit_trades)}개")
    print(f"손실 거래: {len(loss_trades)}개")
    
    # 수익 거래 종목들의 매수 시점 정보
    print(f"\n=== 수익 거래 종목들의 매수 시점 정보 ===")
    for trade in profit_trades:
        code = trade["code"]
        info = stock_info[code]
        
        print(f"\n{code}({info['name']}):")
        print(f"  매수가: {info['buy_price']:,}원")
        print(f"  매수수량: {info['buy_qty']}주")
        print(f"  최종 손익: {info['profit']:+,}원 ({info['profit_rate']:+.2f}%)")
        
        # 시장 거래대금
        if info["market_amounts"]:
            avg_market_amount = sum(info["market_amounts"]) / len(info["market_amounts"])
            print(f"  시장 거래대금: {avg_market_amount:,.0f}원 (평균)")
            print(f"  시장 거래대금 범위: {min(info['market_amounts']):,}원 ~ {max(info['market_amounts']):,}원")
        
        # 거래량비율
        if info["volume_ratios"]:
            avg_volume_ratio = sum(info["volume_ratios"]) / len(info["volume_ratios"])
            print(f"  거래량비율: {avg_volume_ratio:.1f}% (평균)")
            print(f"  거래량비율 범위: {min(info['volume_ratios']):.1f}% ~ {max(info['volume_ratios']):.1f}%")
        
        # 돌파 정보
        if info["breakout_info"]:
            print(f"  돌파 감지: {len(info['breakout_info'])}회")
            for breakout in info["breakout_info"][:2]:  # 최대 2개만 표시
                print(f"    - {breakout}")
        
        # 매수 신호
        if info["buy_signals"]:
            print(f"  매수 신호: {len(info['buy_signals'])}회")
        
        # 등락률
        if info["price_changes"]:
            avg_price_change = sum(info["price_changes"]) / len(info["price_changes"])
            print(f"  등락률: {avg_price_change:+.2f}% (평균)")
            print(f"  등락률 범위: {min(info['price_changes']):+.2f}% ~ {max(info['price_changes']):+.2f}%")
    
    # 손실 거래 종목들의 매수 시점 정보
    print(f"\n=== 손실 거래 종목들의 매수 시점 정보 ===")
    for trade in loss_trades:
        code = trade["code"]
        info = stock_info[code]
        
        print(f"\n{code}({info['name']}):")
        print(f"  매수가: {info['buy_price']:,}원")
        print(f"  매수수량: {info['buy_qty']}주")
        print(f"  최종 손익: {info['profit']:+,}원 ({info['profit_rate']:+.2f}%)")
        
        # 시장 거래대금
        if info["market_amounts"]:
            avg_market_amount = sum(info["market_amounts"]) / len(info["market_amounts"])
            print(f"  시장 거래대금: {avg_market_amount:,.0f}원 (평균)")
            print(f"  시장 거래대금 범위: {min(info['market_amounts']):,}원 ~ {max(info['market_amounts']):,}원")
        
        # 거래량비율
        if info["volume_ratios"]:
            avg_volume_ratio = sum(info["volume_ratios"]) / len(info["volume_ratios"])
            print(f"  거래량비율: {avg_volume_ratio:.1f}% (평균)")
            print(f"  거래량비율 범위: {min(info['volume_ratios']):.1f}% ~ {max(info['volume_ratios']):.1f}%")
        
        # 돌파 정보
        if info["breakout_info"]:
            print(f"  돌파 감지: {len(info['breakout_info'])}회")
            for breakout in info["breakout_info"][:2]:  # 최대 2개만 표시
                print(f"    - {breakout}")
        
        # 매수 신호
        if info["buy_signals"]:
            print(f"  매수 신호: {len(info['buy_signals'])}회")
        
        # 등락률
        if info["price_changes"]:
            avg_price_change = sum(info["price_changes"]) / len(info["price_changes"])
            print(f"  등락률: {avg_price_change:+.2f}% (평균)")
            print(f"  등락률 범위: {min(info['price_changes']):+.2f}% ~ {max(info['price_changes']):+.2f}%")
    
    # 공통점 분석
    print(f"\n=== 수익/손실 거래의 매수 시점 공통점 분석 ===")
    
    # 수익 거래의 평균 정보
    profit_market_amounts = []
    profit_volume_ratios = []
    profit_price_changes = []
    
    for trade in profit_trades:
        code = trade["code"]
        info = stock_info[code]
        
        if info["market_amounts"]:
            profit_market_amounts.append(sum(info["market_amounts"]) / len(info["market_amounts"]))
        if info["volume_ratios"]:
            profit_volume_ratios.append(sum(info["volume_ratios"]) / len(info["volume_ratios"]))
        if info["price_changes"]:
            profit_price_changes.append(sum(info["price_changes"]) / len(info["price_changes"]))
    
    # 손실 거래의 평균 정보
    loss_market_amounts = []
    loss_volume_ratios = []
    loss_price_changes = []
    
    for trade in loss_trades:
        code = trade["code"]
        info = stock_info[code]
        
        if info["market_amounts"]:
            loss_market_amounts.append(sum(info["market_amounts"]) / len(info["market_amounts"]))
        if info["volume_ratios"]:
            loss_volume_ratios.append(sum(info["volume_ratios"]) / len(info["volume_ratios"]))
        if info["price_changes"]:
            loss_price_changes.append(sum(info["price_changes"]) / len(info["price_changes"]))
    
    print(f"수익 거래 매수 시점 평균 정보:")
    if profit_market_amounts:
        print(f"  평균 시장 거래대금: {sum(profit_market_amounts)/len(profit_market_amounts):,.0f}원")
    if profit_volume_ratios:
        print(f"  평균 거래량비율: {sum(profit_volume_ratios)/len(profit_volume_ratios):.1f}%")
    if profit_price_changes:
        print(f"  평균 등락률: {sum(profit_price_changes)/len(profit_price_changes):+.2f}%")
    
    print(f"\n손실 거래 매수 시점 평균 정보:")
    if loss_market_amounts:
        print(f"  평균 시장 거래대금: {sum(loss_market_amounts)/len(loss_market_amounts):,.0f}원")
    if loss_volume_ratios:
        print(f"  평균 거래량비율: {sum(loss_volume_ratios)/len(loss_volume_ratios):.1f}%")
    if loss_price_changes:
        print(f"  평균 등락률: {sum(loss_price_changes)/len(loss_price_changes):+.2f}%")

if __name__ == "__main__":
    analyze_stock_info() 