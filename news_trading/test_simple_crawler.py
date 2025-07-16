"""
Simple Naver Crawler Test
간단한 네이버 크롤러 테스트 스크립트
"""

import sys
import os
from datetime import datetime, timedelta

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_naver_crawler import SimpleNaverCrawler

def test_crawler():
    """크롤러 테스트"""
    print("=== 간단한 네이버 크롤러 테스트 ===")
    
    try:
        # 크롤러 초기화
        print("1. 크롤러 초기화...")
        crawler = SimpleNaverCrawler()
        print("✓ 크롤러 초기화 완료")
        
        # 테스트 날짜 (최근 3일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"2. 테스트 기간: {start_str} ~ {end_str}")
        
        # 경제 뉴스 테스트
        print("3. 경제 뉴스 수집 테스트...")
        economy_news = crawler.crawl_date_range(start_str, end_str, "economy")
        print(f"✓ 경제 뉴스 {len(economy_news)}개 수집 완료")
        
        if economy_news:
            # 첫 번째 뉴스 정보 출력
            first_news = economy_news[0]
            print(f"\n첫 번째 뉴스:")
            print(f"  제목: {first_news['title'][:50]}...")
            print(f"  날짜: {first_news['date']}")
            print(f"  출처: {first_news['source']}")
            print(f"  URL: {first_news['url']}")
        
        # 파일 저장 테스트
        print("\n4. 파일 저장 테스트...")
        test_filename = "test_news_data.csv"
        crawler.save_to_csv(economy_news, test_filename)
        print(f"✓ 테스트 파일 저장 완료: {test_filename}")
        
        # 파일 크기 확인
        if os.path.exists(test_filename):
            file_size = os.path.getsize(test_filename) / 1024  # KB
            print(f"  파일 크기: {file_size:.1f} KB")
        
        print("\n=== 테스트 완료 ===")
        print("모든 테스트가 성공적으로 완료되었습니다!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False

def test_backtest():
    """백테스트 테스트"""
    print("\n=== 백테스트 테스트 ===")
    
    try:
        from simple_backtest import SimpleNewsBacktest
        
        # 테스트 데이터 파일 확인
        test_file = "test_news_data.csv"
        if not os.path.exists(test_file):
            print(f"❌ 테스트 파일이 없습니다: {test_file}")
            print("먼저 크롤러 테스트를 실행하세요.")
            return False
        
        print("1. 백테스트 초기화...")
        backtest = SimpleNewsBacktest(test_file)
        print("✓ 백테스트 초기화 완료")
        
        print("2. 백테스트 실행...")
        results = backtest.simulate_trading()
        print(f"✓ 백테스트 완료: {len(results)}일간")
        
        print("3. 성과 지표 계산...")
        metrics = backtest.calculate_metrics()
        print("✓ 성과 지표 계산 완료")
        
        print("\n=== 백테스트 결과 ===")
        for key, value in metrics.items():
            print(f"{key}: {value}")
        
        print("\n=== 백테스트 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"\n❌ 백테스트 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("간단한 네이버 뉴스 크롤러 & 백테스트 테스트")
    print("=" * 50)
    
    # 크롤러 테스트
    crawler_success = test_crawler()
    
    if crawler_success:
        # 백테스트 테스트
        backtest_success = test_backtest()
        
        if backtest_success:
            print("\n🎉 모든 테스트가 성공했습니다!")
            print("\n이제 실제 사용을 시작할 수 있습니다:")
            print("1. python run_simple_crawler.py")
            print("2. python simple_backtest.py")
        else:
            print("\n⚠️ 백테스트 테스트에 실패했습니다.")
    else:
        print("\n⚠️ 크롤러 테스트에 실패했습니다.")

if __name__ == "__main__":
    main() 