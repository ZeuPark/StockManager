"""
Simple Naver News Crawler Runner
간단한 네이버 뉴스 크롤러 실행 스크립트
"""

import sys
import os
from datetime import datetime, timedelta
import argparse

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_naver_crawler import SimpleNaverCrawler

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='간단한 네이버 뉴스 크롤러')
    parser.add_argument('--start-date', type=str, help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--category', type=str, default='economy', 
                       choices=['economy', 'stock', 'company'], 
                       help='뉴스 카테고리')
    parser.add_argument('--output', type=str, help='출력 파일명 (확장자 제외)')
    
    args = parser.parse_args()
    
    # 날짜 설정
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        # 기본값: 1년 전부터 오늘까지
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
    
    # 출력 파일명 설정
    if args.output:
        output_base = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_base = f"naver_news_{args.category}_{timestamp}"
    
    print(f"=== 네이버 뉴스 크롤링 시작 ===")
    print(f"기간: {start_date} ~ {end_date}")
    print(f"카테고리: {args.category}")
    print(f"출력 파일: {output_base}")
    print()
    
    try:
        # 크롤러 초기화
        crawler = SimpleNaverCrawler()
        
        # 뉴스 수집
        print("뉴스 수집 중...")
        news_list = crawler.crawl_date_range(start_date, end_date, args.category)
        
        if not news_list:
            print("수집된 뉴스가 없습니다.")
            return
        
        # 결과 저장
        csv_filename = f"{output_base}.csv"
        json_filename = f"{output_base}.json"
        
        crawler.save_to_csv(news_list, csv_filename)
        crawler.save_to_json(news_list, json_filename)
        
        print(f"\n=== 크롤링 완료 ===")
        print(f"수집된 뉴스: {len(news_list)}개")
        print(f"CSV 파일: {csv_filename}")
        print(f"JSON 파일: {json_filename}")
        
        # 간단한 통계
        if news_list:
            df = pd.DataFrame(news_list)
            print(f"\n=== 통계 ===")
            print(f"날짜 범위: {df['date'].min()} ~ {df['date'].max()}")
            print(f"일평균 뉴스 수: {len(news_list) / len(df['date'].unique()):.1f}개")
            print(f"출처별 분포:")
            source_counts = df['source'].value_counts().head(5)
            for source, count in source_counts.items():
                print(f"  {source}: {count}개")
        
    except Exception as e:
        print(f"크롤링 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import pandas as pd
    exit(main()) 