"""
Simple Naver News Crawler
간단한 네이버 뉴스 크롤러 - 1년치 데이터 수집용
"""

import time
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict, Any
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleNaverCrawler:
    """간단한 네이버 뉴스 크롤러"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_news_by_date(self, date: str, category: str = "economy") -> List[Dict[str, Any]]:
        """
        특정 날짜의 뉴스를 수집
        
        Args:
            date: YYYY-MM-DD 형식의 날짜
            category: 뉴스 카테고리 (economy, stock, company)
        
        Returns:
            뉴스 데이터 리스트
        """
        news_list = []
        
        # 네이버 뉴스 URL 구성
        if category == "economy":
            base_url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=101"
        elif category == "stock":
            base_url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=102"
        else:
            base_url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=103"
        
        # 날짜 파라미터 추가
        url = f"{base_url}&date={date.replace('-', '')}"
        
        try:
            logger.info(f"날짜 {date} 뉴스 수집 중...")
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 항목 찾기
            news_items = soup.find_all('dt', class_='photo')
            if not news_items:
                news_items = soup.find_all('dt')  # 대안 검색
            
            for item in news_items:
                link_tag = item.find('a')
                if not link_tag:
                    continue
                
                href = link_tag.get('href', '')
                title = link_tag.get_text(strip=True)
                
                if not href or not title:
                    continue
                
                # 상대 URL을 절대 URL로 변환
                if href.startswith('/'):
                    full_url = "https://news.naver.com" + href
                else:
                    full_url = href
                
                # 뉴스 상세 정보 수집
                news_detail = self.get_news_detail(full_url)
                
                news_data = {
                    'date': date,
                    'title': title,
                    'url': full_url,
                    'category': category,
                    'content': news_detail.get('content', ''),
                    'summary': news_detail.get('summary', ''),
                    'source': news_detail.get('source', ''),
                    'crawl_time': datetime.now().isoformat()
                }
                
                news_list.append(news_data)
                time.sleep(0.5)  # 서버 부하 방지
            
            logger.info(f"날짜 {date}: {len(news_list)}개 뉴스 수집 완료")
            
        except Exception as e:
            logger.error(f"날짜 {date} 뉴스 수집 실패: {e}")
        
        return news_list
    
    def get_news_detail(self, url: str) -> Dict[str, str]:
        """뉴스 상세 정보 수집"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목
            title_tag = soup.select_one('h2#title_area span')
            title = title_tag.get_text(strip=True) if title_tag else ''
            
            # 본문
            content_tag = soup.select_one('article#dic_area')
            content = ''
            if content_tag:
                # 불필요한 요소 제거
                for unwanted in content_tag.select('script, style, .reporter_area, .copyright'):
                    unwanted.decompose()
                content = content_tag.get_text(separator='\n', strip=True)
            
            # 요약
            summary_tag = soup.select_one('.summary')
            summary = summary_tag.get_text(strip=True) if summary_tag else ''
            
            # 출처
            source_tag = soup.select_one('.press_logo img, .press_logo a')
            source = ''
            if source_tag:
                source = source_tag.get('alt', '') or source_tag.get_text(strip=True)
            
            return {
                'content': content,
                'summary': summary,
                'source': source
            }
            
        except Exception as e:
            logger.error(f"뉴스 상세 정보 수집 실패 {url}: {e}")
            return {'content': '', 'summary': '', 'source': ''}
    
    def crawl_date_range(self, start_date: str, end_date: str, category: str = "economy") -> List[Dict[str, Any]]:
        """
        날짜 범위의 뉴스를 수집
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            category: 뉴스 카테고리
        
        Returns:
            전체 뉴스 데이터 리스트
        """
        all_news = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"날짜 범위 {start_date} ~ {end_date} 뉴스 수집 시작")
        
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_news = self.get_news_by_date(date_str, category)
            all_news.extend(daily_news)
            
            current_date += timedelta(days=1)
            time.sleep(1)  # 서버 부하 방지
        
        logger.info(f"전체 {len(all_news)}개 뉴스 수집 완료")
        return all_news
    
    def save_to_csv(self, news_list: List[Dict[str, Any]], filename: str):
        """뉴스 데이터를 CSV 파일로 저장"""
        try:
            df = pd.DataFrame(news_list)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"뉴스 데이터 저장 완료: {filename}")
        except Exception as e:
            logger.error(f"CSV 저장 실패: {e}")
    
    def save_to_json(self, news_list: List[Dict[str, Any]], filename: str):
        """뉴스 데이터를 JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2)
            logger.info(f"뉴스 데이터 저장 완료: {filename}")
        except Exception as e:
            logger.error(f"JSON 저장 실패: {e}")

def main():
    """메인 실행 함수"""
    crawler = SimpleNaverCrawler()
    
    # 1년 전부터 오늘까지의 날짜 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    logger.info(f"1년치 뉴스 수집 시작: {start_str} ~ {end_str}")
    
    # 경제 뉴스 수집
    economy_news = crawler.crawl_date_range(start_str, end_str, "economy")
    
    # 주식 뉴스 수집
    stock_news = crawler.crawl_date_range(start_str, end_str, "stock")
    
    # 기업 뉴스 수집
    company_news = crawler.crawl_date_range(start_str, end_str, "company")
    
    # 모든 뉴스 합치기
    all_news = economy_news + stock_news + company_news
    
    # 결과 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # CSV 저장
    csv_filename = f"naver_news_1year_{timestamp}.csv"
    crawler.save_to_csv(all_news, csv_filename)
    
    # JSON 저장
    json_filename = f"naver_news_1year_{timestamp}.json"
    crawler.save_to_json(all_news, json_filename)
    
    logger.info(f"수집 완료: 총 {len(all_news)}개 뉴스")
    logger.info(f"저장된 파일: {csv_filename}, {json_filename}")

if __name__ == "__main__":
    main() 