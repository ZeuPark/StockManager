import pandas as pd
import os

def read_korean_csv(file_path):
    """한글 CSV 파일을 올바르게 읽어서 UTF-8로 저장"""
    
    # 파일 존재 확인
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return None
    
    try:
        # cp949 인코딩으로 읽기 (한국어 Windows 기본 인코딩)
        print(f"📖 CSV 파일 읽는 중: {file_path}")
        df = pd.read_csv(file_path, encoding='cp949')
        
        print(f"✅ 파일 읽기 성공!")
        print(f"📊 데이터 형태: {df.shape}")
        print(f"📋 컬럼명: {list(df.columns)}")
        
        # UTF-8로 저장
        output_file = "trading_data_utf8.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 UTF-8로 저장 완료: {output_file}")
        
        # 데이터 미리보기
        print("\n📈 데이터 미리보기:")
        print(df.head())
        
        return df
        
    except UnicodeDecodeError:
        print("❌ cp949 인코딩으로 읽기 실패, 다른 인코딩 시도...")
        try:
            # 다른 인코딩 시도
            df = pd.read_csv(file_path, encoding='euc-kr')
            print("✅ euc-kr 인코딩으로 읽기 성공!")
            
            output_file = "trading_data_utf8.csv"
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"💾 UTF-8로 저장 완료: {output_file}")
            
            print("\n📈 데이터 미리보기:")
            print(df.head())
            
            return df
            
        except Exception as e:
            print(f"❌ 모든 인코딩 시도 실패: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        return None

if __name__ == "__main__":
    # CSV 파일 읽기
    csv_file = "2025-07-08 오후 매매.csv"
    df = read_korean_csv(csv_file)
    
    if df is not None:
        print(f"\n🎯 총 {len(df)}개의 거래 데이터가 있습니다.")
        
        # 수익/손실 분석
        if '수익금' in df.columns:
            profit_stocks = df[df['수익금'] > 0]
            loss_stocks = df[df['수익금'] < 0]
            
            print(f"\n📈 수익 종목: {len(profit_stocks)}개")
            print(f"📉 손실 종목: {len(loss_stocks)}개")
            
            if len(profit_stocks) > 0:
                print("\n🏆 상위 수익 종목:")
                top_profit = profit_stocks.nlargest(5, '수익금')
                for _, row in top_profit.iterrows():
                    print(f"  {row.get('종목명', 'N/A')}: {row.get('수익금', 0):,}원 ({row.get('수익률', 0):.2f}%)")
        
        # 거래량 분석
        if '거래량' in df.columns:
            total_volume = df['거래량'].sum()
            avg_volume = df['거래량'].mean()
            print(f"\n📊 거래량 분석:")
            print(f"  총 거래량: {total_volume:,}주")
            print(f"  평균 거래량: {avg_volume:.0f}주") 