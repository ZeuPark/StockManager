import pandas as pd
import numpy as np

def analyze_trade_amount_ranges(csv_file="trading_data_utf8.csv"):
    """거래대금 범위별 수익률 분석"""
    
    # CSV 데이터 읽기
    df = pd.read_csv(csv_file, encoding='utf-8')
    df['종목코드'] = df['종목코드'].str.strip("'")
    df['평가손익'] = df['평가손익'].str.replace(',', '').astype(float)
    df['수익률'] = df['수익률'].str.rstrip('%').astype(float)
    df['매 입 가'] = df['매 입 가'].str.replace(',', '').astype(float)
    df['보유수량'] = df['보유수량'].astype(int)
    
    # 거래대금 계산
    df['거래대금'] = df['매 입 가'] * df['보유수량']
    
    print("📊 거래대금 범위별 수익률 분석")
    print("=" * 60)
    
    # 거래대금 범위별 분석
    ranges = [
        (0, 50000, "5만원 미만"),
        (50000, 100000, "5~10만원"),
        (100000, 150000, "10~15만원"),
        (150000, 200000, "15~20만원"),
        (200000, 300000, "20~30만원"),
        (300000, 500000, "30~50만원"),
        (500000, 1000000, "50~100만원"),
        (1000000, float('inf'), "100만원 이상")
    ]
    
    results = []
    
    for min_amount, max_amount, label in ranges:
        if max_amount == float('inf'):
            mask = df['거래대금'] >= min_amount
        else:
            mask = (df['거래대금'] >= min_amount) & (df['거래대금'] < max_amount)
        
        range_df = df[mask]
        
        if len(range_df) > 0:
            avg_profit_rate = range_df['수익률'].mean()
            profit_count = len(range_df[range_df['평가손익'] > 0])
            loss_count = len(range_df[range_df['평가손익'] < 0])
            total_count = len(range_df)
            profit_ratio = profit_count / total_count if total_count > 0 else 0
            
            results.append({
                '범위': label,
                '종목수': total_count,
                '평균수익률': avg_profit_rate,
                '수익종목': profit_count,
                '손실종목': loss_count,
                '수익비율': profit_ratio,
                '평균거래대금': range_df['거래대금'].mean()
            })
            
            print(f"\n💰 {label}")
            print(f"  종목 수: {total_count}개")
            print(f"  평균 수익률: {avg_profit_rate:.2f}%")
            print(f"  수익 종목: {profit_count}개 ({profit_ratio:.1%})")
            print(f"  손실 종목: {loss_count}개")
            print(f"  평균 거래대금: {range_df['거래대금'].mean():,.0f}원")
    
    # 결과를 DataFrame으로 변환
    results_df = pd.DataFrame(results)
    
    print(f"\n🎯 최적 거래대금 범위 분석")
    print("-" * 40)
    
    # 수익률 기준 상위 3개
    top_profit = results_df.nlargest(3, '평균수익률')
    print(f"📈 수익률 기준 상위 3개:")
    for _, row in top_profit.iterrows():
        print(f"  {row['범위']}: {row['평균수익률']:.2f}% (종목수: {row['종목수']}개)")
    
    # 수익 비율 기준 상위 3개
    top_ratio = results_df.nlargest(3, '수익비율')
    print(f"\n📊 수익 비율 기준 상위 3개:")
    for _, row in top_ratio.iterrows():
        print(f"  {row['범위']}: {row['수익비율']:.1%} (평균수익률: {row['평균수익률']:.2f}%)")
    
    # 종목 수가 충분한 범위 중 최적 선택
    sufficient_data = results_df[results_df['종목수'] >= 2]  # 2개 이상 종목이 있는 범위
    
    if len(sufficient_data) > 0:
        best_range = sufficient_data.loc[sufficient_data['평균수익률'].idxmax()]
        print(f"\n🏆 최적 거래대금 범위 추천:")
        print(f"  범위: {best_range['범위']}")
        print(f"  평균 수익률: {best_range['평균수익률']:.2f}%")
        print(f"  수익 비율: {best_range['수익비율']:.1%}")
        print(f"  종목 수: {best_range['종목수']}개")
        print(f"  평균 거래대금: {best_range['평균거래대금']:,.0f}원")
    
    # 상세 데이터 출력
    print(f"\n📋 상세 데이터:")
    for _, row in results_df.iterrows():
        print(f"  {row['범위']:12} | 수익률: {row['평균수익률']:6.2f}% | 수익비율: {row['수익비율']:5.1%} | 종목수: {row['종목수']:2d}개")
    
    return results_df

if __name__ == "__main__":
    analyze_trade_amount_ranges() 