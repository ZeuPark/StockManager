import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def collect_kospi_data_yf(start_date, end_date):
    """
    yfinance를 사용해서 코스피 지수 데이터 수집
    """
    print(f"코스피 지수 데이터 수집 시작: {start_date} ~ {end_date}")
    
    try:
        # 코스피 지수 심볼: ^KS11
        kospi = yf.download('^KS11', start=start_date, end=end_date)
        
        if kospi.empty:
            print("데이터가 없습니다.")
            return pd.DataFrame()
        
        # 컬럼명 정리 (멀티인덱스 → 단일 컬럼명)
        kospi = kospi.reset_index()
        kospi.columns = [col[0] if isinstance(col, tuple) else col for col in kospi.columns]
        print(f"원본 컬럼: {list(kospi.columns)}")
        
        # 필요한 컬럼만 선택
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        available_columns = [col for col in required_columns if col in kospi.columns]
        kospi = kospi[available_columns]
        
        # 컬럼명 소문자로 통일
        kospi.columns = [c.lower() for c in kospi.columns]
        
        # 날짜 형식 변환
        kospi['date'] = pd.to_datetime(kospi['date'])
        
        # 거래일만 필터링 (주말 제거)
        kospi = kospi[kospi['date'].dt.weekday < 5]
        
        print(f"수집 완료: {len(kospi)}일의 데이터")
        return kospi
        
    except Exception as e:
        print(f"데이터 수집 실패: {e}")
        return pd.DataFrame()

def save_market_data(df, filename='market_data/KOSPI_daily.csv'):
    """
    시장 데이터를 CSV 파일로 저장
    """
    # 디렉토리 생성
    os.makedirs('market_data', exist_ok=True)
    
    # CSV 저장
    df.to_csv(filename, index=False)
    print(f"데이터 저장 완료: {filename}")

if __name__ == '__main__':
    # 수집 기간 (백테스트 기간과 동일)
    start_date = '2024-07-08'
    end_date = '2025-07-08'
    
    print("yfinance를 사용한 코스피 지수 데이터 수집")
    print("="*50)
    
    # 데이터 수집
    kospi_df = collect_kospi_data_yf(start_date, end_date)
    
    if not kospi_df.empty:
        # 데이터 저장
        save_market_data(kospi_df)
        
        # 샘플 데이터 출력
        print("\n수집된 데이터 샘플:")
        print(kospi_df.head())
        print(f"\n총 {len(kospi_df)}일의 데이터 수집 완료")
        
        # 데이터 통계
        print(f"\n데이터 통계:")
        print(f"시작일: {kospi_df['date'].min()}")
        print(f"종료일: {kospi_df['date'].max()}")
        print(f"평균 종가: {kospi_df['close'].mean():.2f}")
        print(f"최고가: {kospi_df['high'].max():.2f}")
        print(f"최저가: {kospi_df['low'].min():.2f}")
    else:
        print("데이터 수집에 실패했습니다.") 