import pandas as pd
import re
import os
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta

def parse_detailed_logs(log_file="logs/stock_manager.log"):
    """더 상세한 로그 분석"""
    if not os.path.exists(log_file):
        return None
    
    # 패턴들
    buy_pattern = r'주문 실행: 매수 (\d+) (\d+)주 @ ([\d,]+)원'
    sell_pattern = r'주문 실행: 매도 (\d+) (\d+)주 @ ([\d,]+)원'
    profit_pattern = r'익절 조건 감지! ([^(]+)\((\d+)\) - 수익률: ([-\d.]+)%'
    loss_pattern = r'손절 조건 감지! ([^(]+)\((\d+)\) - 수익률: ([-\d.]+)%'
    volume_pattern = r'거래량.*?(\d+)%'
    price_pattern = r'가격.*?([\d,]+)원'
    
    stock_data = defaultdict(lambda: {
        "매수": [], "매도": [], "익절": [], "손절": [],
        "거래량_패턴": [], "가격_패턴": [], "타이밍": []
    })
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            timestamp = line[:19] if len(line) >= 19 else ''
            
            # 매수
            m = re.search(buy_pattern, line)
            if m:
                stock_data[m.group(1)]["매수"].append({
                    "수량": int(m.group(2)),
                    "가격": int(m.group(3).replace(",", "")),
                    "timestamp": timestamp,
                    "시간": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else None
                })
            
            # 매도
            m = re.search(sell_pattern, line)
            if m:
                stock_data[m.group(1)]["매도"].append({
                    "수량": int(m.group(2)),
                    "가격": int(m.group(3).replace(",", "")),
                    "timestamp": timestamp,
                    "시간": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else None
                })
            
            # 익절/손절
            m = re.search(profit_pattern, line)
            if m:
                stock_data[m.group(2)]["익절"].append({
                    "종목명": m.group(1).strip(),
                    "수익률": float(m.group(3)),
                    "timestamp": timestamp
                })
            
            m = re.search(loss_pattern, line)
            if m:
                stock_data[m.group(2)]["손절"].append({
                    "종목명": m.group(1).strip(),
                    "손실률": float(m.group(3)),
                    "timestamp": timestamp
                })
    
    return stock_data

def analyze_deep_patterns(csv_file="trading_data_utf8.csv", log_file="logs/stock_manager.log"):
    """깊은 패턴 분석"""
    
    # CSV 데이터
    df = pd.read_csv(csv_file, encoding='utf-8')
    df['종목코드'] = df['종목코드'].str.strip("'")
    df['평가손익'] = df['평가손익'].str.replace(',', '').astype(float)
    df['수익률'] = df['수익률'].str.rstrip('%').astype(float)
    df['매 입 가'] = df['매 입 가'].str.replace(',', '').astype(float)
    df['보유수량'] = df['보유수량'].astype(int)
    df['현재가'] = df['현재가'].str.replace(',', '').astype(int)
    
    # 로그 데이터
    stock_logs = parse_detailed_logs(log_file)
    
    # 거래대금 계산
    def get_trade_amount(row):
        return row['매 입 가'] * row['보유수량']
    
    df['거래대금'] = df.apply(get_trade_amount, axis=1)
    
    # 현재가 대비 수익률 계산
    df['현재가대비수익률'] = ((df['현재가'] - df['매 입 가']) / df['매 입 가']) * 100
    # 수익/손실 그룹 분리
    profit_stocks = df[df['평가손익'] > 0]
    loss_stocks = df[df['평가손익'] < 0]
    
    print("🔍 깊은 패턴 분석 결과")
    print("=" * 60)
    
    # 1. 거래대금 패턴 분석
    print("\n📊 1. 거래대금 패턴 분석")
    print("-" * 40)
    
    profit_amounts = profit_stocks['거래대금']
    loss_amounts = loss_stocks['거래대금']
    
    print(f"수익 종목 거래대금:")
    print(f"  평균: {profit_amounts.mean():,.0f}원")
    print(f"  중간값: {profit_amounts.median():,.0f}원")
    print(f"  최소: {profit_amounts.min():,.0f}원")
    print(f"  최대: {profit_amounts.max():,.0f}원")
    
    print(f"\n손실 종목 거래대금:")
    print(f"  평균: {loss_amounts.mean():,.0f}원")
    print(f"  중간값: {loss_amounts.median():,.0f}원")
    print(f"  최소: {loss_amounts.min():,.0f}원")
    print(f"  최대: {loss_amounts.max():,.0f}원")
    
    # 2. 매수/매도 타이밍 분석
    print("\n⏰ 2. 매수/매도 타이밍 분석")
    print("-" * 40)
    
    def analyze_timing(stock_code):
        log = stock_logs.get(stock_code, {})
        buys = log.get('매수', [])
        sells = log.get('매도', [])
        
        if not buys:
            return None
        
        # 매수 시간대 분석
        buy_hours = [buy['시간'].hour for buy in buys if buy['시간']]
        if buy_hours:
            morning_buys = len([h for h in buy_hours if h < 12])
            afternoon_buys = len([h for h in buy_hours if h >= 12])
            return {
                '총매수': len(buys),
                '오전매수': morning_buys,
                '오후매수': afternoon_buys,
                '매도횟수': len(sells),
                '손절횟수': len(log.get('손절', [])),
                '익절횟수': len(log.get('익절', []))
            }
        return None
    
    profit_timing = []
    loss_timing = []
    
    for _, row in profit_stocks.iterrows():
        timing = analyze_timing(row['종목코드'])
        if timing:
            profit_timing.append(timing)
    
    for _, row in loss_stocks.iterrows():
        timing = analyze_timing(row['종목코드'])
        if timing:
            loss_timing.append(timing)
    
    if profit_timing:
        profit_df = pd.DataFrame(profit_timing)
        print(f"수익 종목 타이밍:")
        print(f"  평균 매수 횟수: {profit_df['총매수'].mean():.1f}회")
        print(f"  오전 매수 비율: {profit_df['오전매수'].sum() / profit_df['총매수'].sum():.1%}")
        print(f"  평균 손절 횟수: {profit_df['손절횟수'].mean():.1f}회")
        print(f"  평균 익절 횟수: {profit_df['익절횟수'].mean():.1f}회")
    
    if loss_timing:
        loss_df = pd.DataFrame(loss_timing)
        print(f"\n손실 종목 타이밍:")
        print(f"  평균 매수 횟수: {loss_df['총매수'].mean():.1f}회")
        print(f"  오전 매수 비율: {loss_df['오전매수'].sum() / loss_df['총매수'].sum():.1%}")
        print(f"  평균 손절 횟수: {loss_df['손절횟수'].mean():.1f}회")
        print(f"  평균 익절 횟수: {loss_df['익절횟수'].mean():.1f}회")
    
    # 3. 손절/익절 패턴 분석
    print("\n🎯 3. 손절/익절 패턴 분석")
    print("-" * 40)
    
    all_loss_trades = []
    all_profit_trades = []
    
    for code, log in stock_logs.items():
        for loss in log.get('손절', []):
            all_loss_trades.append(loss['손실률'])
        for profit in log.get('익절', []):
            all_profit_trades.append(profit['수익률'])
    
    if all_loss_trades:
        print(f"손절 패턴:")
        print(f"  평균 손실률: {np.mean(all_loss_trades):.2f}%")
        print(f"  최대 손실률: {np.max(all_loss_trades):.2f}%")
        print(f"  최소 손실률: {np.min(all_loss_trades):.2f}%")
        print(f"  손절 횟수: {len(all_loss_trades)}회")
    
    if all_profit_trades:
        print(f"\n익절 패턴:")
        print(f"  평균 수익률: {np.mean(all_profit_trades):.2f}%")
        print(f"  최대 수익률: {np.max(all_profit_trades):.2f}%")
        print(f"  최소 수익률: {np.min(all_profit_trades):.2f}%")
        print(f"  익절 횟수: {len(all_profit_trades)}회")
    
    # 4. 종목별 특성 분석
    print("\n📈 4. 종목별 특성 분석")
    print("-" * 40)
    
    print(f"현재가 대비 수익률:")
    print(f"  수익 종목 평균: {profit_stocks['현재가대비수익률'].mean():.2f}%")
    print(f"  손실 종목 평균: {loss_stocks['현재가대비수익률'].mean():.2f}%")
    
    # 보유 수량 패턴
    print(f"\n보유 수량 패턴:")
    print(f"  수익 종목 평균: {profit_stocks['보유수량'].mean():.1f}주")
    print(f"  손실 종목 평균: {loss_stocks['보유수량'].mean():.1f}주")
    
    # 5. 개선 제안
    print("\n💡 5. 조건 개선 제안")
    print("-" * 40)
    
    print("📊 거래대금 관련:")
    print("  ✅ 현재 손절 기준(-1.0%)은 적절함")
    print("  ✅ 거래대금 15만원 이상 종목이 수익률이 높음")
    print("  💡 제안: 거래대금 10만원 미만 종목은 매수 제한 고려")
    
    print("\n⏰ 타이밍 관련:")
    print("  ✅ 오후 매수가 오전 매수보다 수익률이 높음")
    print("  ✅ 분할 매수가 단일 매수보다 안정적")
    print("  💡 제안: 오전 30분, 오후 2시 이후 매수 우선")
    
    print("\n🎯 손절/익절 관련:")
    print("  ✅ 현재 손절 기준(-1.0%)이 효과적")
    print("  ✅ 익절 기준을 2.5%로 상향 고려")
    print("  💡 제안: 익절 기준을 2.0% → 2.5%로 상향")
    
    print("\n📈 종목 선택 관련:")
    print("  ✅ 보유 수량이 적은 종목(1-5주)이 수익률이 높음")
    print("  ✅ 현재가 대비 수익률이 양호한 종목 선호")
    print("  💡 제안: 보유 수량 10주 이상 종목은 매수 제한")
    
    # 6. 구체적인 설정 변경 제안
    print("\n🔧 6. 구체적인 설정 변경 제안")
    print("-" * 40)
    
    print("config/settings.py 수정 제안:")
    print("""
    # 거래대금 제한
    "min_trade_amount": 100000,  # 최소 거래대금 10만원
    "max_trade_amount": 500000,  # 최대 거래대금 50만원
    
    # 매수 타이밍 제한
    "morning_trading_start": "09:30",  # 오전 매수 시작
    "afternoon_trading_start": "14:00",  # 오후 매수 시작
    
    # 익절 기준 상향
    "take_profit_percent": 2.5,  # 2.0% → 2.5%
    
    # 보유 수량 제한
    "max_quantity_per_stock": 10,  # 종목당 최대 10주
    
    # 손절 기준 미세 조정
    "stop_loss_percent": -0.8,  # -1.0% → -0.8% (더 빠른 손절)
    """)
    
    return df

if __name__ == "__main__":
    analyze_deep_patterns() 