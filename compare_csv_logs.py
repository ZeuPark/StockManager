import pandas as pd
import re
from datetime import datetime, timedelta
import os

def parse_trading_logs(log_file="logs/stock_manager.log"):
    """로그에서 거래 데이터 추출"""
    
    if not os.path.exists(log_file):
        print(f"❌ 로그 파일을 찾을 수 없습니다: {log_file}")
        return None
    
    print(f"📖 로그 파일 분석 중: {log_file}")
    
    trading_data = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 거래 관련 패턴들 (실제 로그 패턴에 맞춤)
        buy_pattern = r'주문 실행: 매수 (\d+) (\d+)주 @ ([\d,]+)원'
        sell_pattern = r'주문 실행: 매도 (\d+) (\d+)주 @ ([\d,]+)원'
        profit_pattern = r'익절 조건 감지! ([^(]+)\((\d+)\) - 수익률: ([-\d.]+)%'
        loss_pattern = r'손절 조건 감지! ([^(]+)\((\d+)\) - 수익률: ([-\d.]+)%'
        
        for line in lines:
            # 매수 신호
            buy_match = re.search(buy_pattern, line)
            if buy_match:
                trading_data.append({
                    'type': '매수',
                    '종목코드': buy_match.group(1),
                    '수량': int(buy_match.group(2)),
                    '가격': int(buy_match.group(3).replace(',', '')),
                    'timestamp': line[:19] if len(line) >= 19 else ''
                })
            
            # 매도 신호
            sell_match = re.search(sell_pattern, line)
            if sell_match:
                trading_data.append({
                    'type': '매도',
                    '종목코드': sell_match.group(1),
                    '수량': int(sell_match.group(2)),
                    '가격': int(sell_match.group(3).replace(',', '')),
                    'timestamp': line[:19] if len(line) >= 19 else ''
                })
            
            # 익절
            profit_match = re.search(profit_pattern, line)
            if profit_match:
                trading_data.append({
                    'type': '익절',
                    '종목명': profit_match.group(1).strip(),
                    '종목코드': profit_match.group(2),
                    '수익률': float(profit_match.group(3)),
                    'timestamp': line[:19] if len(line) >= 19 else ''
                })
            
            # 손절
            loss_match = re.search(loss_pattern, line)
            if loss_match:
                trading_data.append({
                    'type': '손절',
                    '종목명': loss_match.group(1).strip(),
                    '종목코드': loss_match.group(2),
                    '손실률': float(loss_match.group(3)),
                    'timestamp': line[:19] if len(line) >= 19 else ''
                })
        
        print(f"✅ 로그에서 {len(trading_data)}개의 거래 데이터 추출")
        return trading_data
        
    except Exception as e:
        print(f"❌ 로그 파싱 오류: {e}")
        return None

def analyze_csv_data(csv_file="trading_data_utf8.csv"):
    """CSV 데이터 분석"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_file}")
        return None
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # 데이터 정리
        df['종목코드'] = df['종목코드'].str.strip("'")
        df['평가손익'] = df['평가손익'].str.replace(',', '').astype(float)
        df['수익률'] = df['수익률'].str.rstrip('%').astype(float)
        df['현재가'] = df['현재가'].str.replace(',', '').astype(int)
        df['보유수량'] = df['보유수량'].astype(int)
        
        return df
        
    except Exception as e:
        print(f"❌ CSV 읽기 오류: {e}")
        return None

def compare_analysis():
    """CSV와 로그 데이터 비교 분석"""
    
    print("🔍 CSV와 로그 데이터 비교 분석 시작")
    print("=" * 50)
    
    # CSV 데이터 분석
    print("\n📊 CSV 데이터 분석:")
    csv_df = analyze_csv_data()
    if csv_df is None:
        return
    
    print(f"  총 보유 종목: {len(csv_df)}개")
    print(f"  수익 종목: {len(csv_df[csv_df['평가손익'] > 0])}개")
    print(f"  손실 종목: {len(csv_df[csv_df['평가손익'] < 0])}개")
    print(f"  순손익: {csv_df['평가손익'].sum():,.0f}원")
    print(f"  평균 수익률: {csv_df['수익률'].mean():.2f}%")
    
    # 로그 데이터 분석
    print("\n📋 로그 데이터 분석:")
    log_data = parse_trading_logs()
    if log_data is None:
        return
    
    log_df = pd.DataFrame(log_data)
    
    if len(log_df) > 0:
        # 거래 타입별 분석
        trade_types = log_df['type'].value_counts()
        print(f"  총 거래 신호: {len(log_df)}개")
        for trade_type, count in trade_types.items():
            print(f"  {trade_type}: {count}개")
        
        # 익절/손절 분석
        profit_trades = log_df[log_df['type'] == '익절']
        loss_trades = log_df[log_df['type'] == '손절']
        
        if len(profit_trades) > 0:
            print(f"\n  🏆 익절 거래: {len(profit_trades)}개")
            avg_profit = profit_trades['수익률'].mean()
            print(f"    평균 익절률: {avg_profit:.2f}%")
            
            # 상위 익절 종목
            top_profit = profit_trades.nlargest(3, '수익률')
            print("    상위 익절 종목:")
            for _, row in top_profit.iterrows():
                print(f"      {row['종목명']}: {row['수익률']:.2f}%")
        
        if len(loss_trades) > 0:
            print(f"\n  📉 손절 거래: {len(loss_trades)}개")
            avg_loss = loss_trades['손실률'].mean()
            print(f"    평균 손실률: {avg_loss:.2f}%")
            
            # 하위 손절 종목
            bottom_loss = loss_trades.nsmallest(3, '손실률')
            print("    하위 손절 종목:")
            for _, row in bottom_loss.iterrows():
                print(f"      {row['종목명']}: {row['손실률']:.2f}%")
    
    # CSV와 로그 비교
    print("\n🔄 CSV와 로그 비교 분석:")
    
    # CSV에서 수익률이 높은 종목들
    csv_profit_stocks = csv_df[csv_df['수익률'] > 0].nlargest(5, '수익률')
    csv_loss_stocks = csv_df[csv_df['수익률'] < 0].nsmallest(5, '수익률')
    
    print(f"\n  📈 CSV 상위 수익 종목:")
    for _, row in csv_profit_stocks.iterrows():
        print(f"    {row['종목명']}: {row['수익률']:.2f}% ({row['평가손익']:,.0f}원)")
    
    print(f"\n  📉 CSV 하위 손실 종목:")
    for _, row in csv_loss_stocks.iterrows():
        print(f"    {row['종목명']}: {row['수익률']:.2f}% ({row['평가손익']:,.0f}원)")
    
    # 손절 기준과 실제 손실 비교
    print(f"\n  🛑 손절 기준 분석:")
    print(f"    현재 손절 기준: -1.0%")
    print(f"    CSV 최대 손실: {csv_df['수익률'].min():.2f}%")
    print(f"    손절 기준 대비: {abs(csv_df['수익률'].min()) - 1.0:.2f}% 여유")
    
    # 거래 빈도 분석
    if len(log_df) > 0:
        print(f"\n  📊 거래 빈도 분석:")
        today_trades = log_df[log_df['timestamp'].str.contains('2025-07-08', na=False)]
        print(f"    오늘 거래 신호: {len(today_trades)}개")
        
        if len(today_trades) > 0:
            today_types = today_trades['type'].value_counts()
            for trade_type, count in today_types.items():
                print(f"    오늘 {trade_type}: {count}개")
    
    # 종합 평가
    print(f"\n🎯 종합 평가:")
    
    # 수익성 평가
    total_profit = csv_df['평가손익'].sum()
    if total_profit > 0:
        print(f"  ✅ 수익성: 양호 (순손익: {total_profit:,.0f}원)")
    else:
        print(f"  ❌ 수익성: 개선 필요 (순손익: {total_profit:,.0f}원)")
    
    # 손절 효율성 평가
    max_loss = csv_df['수익률'].min()
    if max_loss > -1.0:
        print(f"  ✅ 손절 효율성: 양호 (최대 손실: {max_loss:.2f}%)")
    else:
        print(f"  ⚠️ 손절 효율성: 개선 필요 (최대 손실: {max_loss:.2f}%)")
    
    # 거래 안정성 평가
    profit_ratio = len(csv_df[csv_df['평가손익'] > 0]) / len(csv_df)
    if profit_ratio > 0.5:
        print(f"  ✅ 거래 안정성: 양호 (수익 종목 비율: {profit_ratio:.1%})")
    else:
        print(f"  ⚠️ 거래 안정성: 개선 필요 (수익 종목 비율: {profit_ratio:.1%})")

if __name__ == "__main__":
    compare_analysis() 