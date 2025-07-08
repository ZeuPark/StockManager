import pandas as pd
import numpy as np

def analyze_trading_data(csv_file="trading_data_utf8.csv"):
    """거래 데이터 분석"""
    
    try:
        # UTF-8로 저장된 파일 읽기
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"📊 거래 데이터 분석 시작")
        print(f"📈 총 {len(df)}개 종목의 거래 데이터")
        
        # 데이터 정리
        df['종목코드'] = df['종목코드'].str.strip("'")  # 따옴표 제거
        df['평가손익'] = df['평가손익'].str.replace(',', '').astype(float)  # 쉼표 제거 후 숫자로 변환
        df['수익률'] = df['수익률'].str.rstrip('%').astype(float)  # % 제거 후 숫자로 변환
        
        # 수익/손실 분석
        profit_stocks = df[df['평가손익'] > 0]
        loss_stocks = df[df['평가손익'] < 0]
        break_even_stocks = df[df['평가손익'] == 0]
        
        print(f"\n🎯 수익/손실 현황:")
        print(f"  📈 수익 종목: {len(profit_stocks)}개")
        print(f"  📉 손실 종목: {len(loss_stocks)}개")
        print(f"  ➖ 손익분기: {len(break_even_stocks)}개")
        
        # 총 손익 계산
        total_profit = profit_stocks['평가손익'].sum()
        total_loss = loss_stocks['평가손익'].sum()
        net_profit = total_profit + total_loss
        
        print(f"\n💰 손익 분석:")
        print(f"  총 수익: {total_profit:,.0f}원")
        print(f"  총 손실: {total_loss:,.0f}원")
        print(f"  순손익: {net_profit:,.0f}원")
        
        # 상위 수익 종목
        if len(profit_stocks) > 0:
            print(f"\n🏆 상위 수익 종목 (TOP 5):")
            top_profit = profit_stocks.nlargest(5, '평가손익')
            for _, row in top_profit.iterrows():
                print(f"  {row['종목명']} ({row['종목코드']}): {row['평가손익']:,.0f}원 ({row['수익률']:.2f}%)")
        
        # 하위 손실 종목
        if len(loss_stocks) > 0:
            print(f"\n📉 하위 손실 종목 (BOTTOM 5):")
            bottom_loss = loss_stocks.nsmallest(5, '평가손익')
            for _, row in bottom_loss.iterrows():
                print(f"  {row['종목명']} ({row['종목코드']}): {row['평가손익']:,.0f}원 ({row['수익률']:.2f}%)")
        
        # 수익률 분석
        print(f"\n📊 수익률 분석:")
        print(f"  평균 수익률: {df['수익률'].mean():.2f}%")
        print(f"  최고 수익률: {df['수익률'].max():.2f}%")
        print(f"  최저 수익률: {df['수익률'].min():.2f}%")
        print(f"  수익률 표준편차: {df['수익률'].std():.2f}%")
        
        # 보유 비중 분석
        if '보유비중' in df.columns:
            df['보유비중'] = df['보유비중'].str.rstrip('%').astype(float)
            print(f"\n📈 보유 비중 분석:")
            print(f"  평균 보유비중: {df['보유비중'].mean():.2f}%")
            print(f"  최대 보유비중: {df['보유비중'].max():.2f}%")
            print(f"  최소 보유비중: {df['보유비중'].min():.2f}%")
        
        # 거래량 분석
        if '보유수량' in df.columns:
            df['보유수량'] = df['보유수량'].astype(int)
            total_quantity = df['보유수량'].sum()
            print(f"\n📦 보유 수량 분석:")
            print(f"  총 보유 수량: {total_quantity:,}주")
            print(f"  평균 보유 수량: {df['보유수량'].mean():.0f}주")
            print(f"  최대 보유 수량: {df['보유수량'].max():,}주")
        
        # 현재가 분석
        if '현재가' in df.columns:
            df['현재가'] = df['현재가'].str.replace(',', '').astype(int)
            print(f"\n💵 현재가 분석:")
            print(f"  평균 현재가: {df['현재가'].mean():,.0f}원")
            print(f"  최고 현재가: {df['현재가'].max():,.0f}원")
            print(f"  최저 현재가: {df['현재가'].min():,.0f}원")
        
        # 수익률 구간별 분석
        print(f"\n📊 수익률 구간별 분석:")
        profit_ranges = [
            (-float('inf'), -5, "5% 이상 손실"),
            (-5, -2, "2~5% 손실"),
            (-2, 0, "0~2% 손실"),
            (0, 2, "0~2% 수익"),
            (2, 5, "2~5% 수익"),
            (5, float('inf'), "5% 이상 수익")
        ]
        
        for min_rate, max_rate, label in profit_ranges:
            if max_rate == float('inf'):
                count = len(df[df['수익률'] >= min_rate])
            else:
                count = len(df[(df['수익률'] >= min_rate) & (df['수익률'] < max_rate)])
            print(f"  {label}: {count}개 종목")
        
        return df
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    df = analyze_trading_data()
    
    if df is not None:
        print(f"\n✅ 분석 완료!")
        print(f"💡 분석 결과가 위에 표시되었습니다.") 