"""
Improved Naver News Crawler
네이버 뉴스 구조에 맞게 개선된 크롤러
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
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedNaverCrawler:
    """개선된 네이버 뉴스 크롤러"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_news_by_date(self, date: str, category: str = "stock") -> List[Dict[str, Any]]:
        """
        특정 날짜의 뉴스를 수집
        
        Args:
            date: YYYY-MM-DD 형식의 날짜
            category: 뉴스 카테고리 (economy, stock, company)
        
        Returns:
            뉴스 데이터 리스트
        """
        news_list = []
        
        # 네이버 뉴스 URL 구성 (증권 뉴스)
        if category == "stock":
            base_url = "https://news.naver.com/breakingnews/section/101/258"
        elif category == "economy":
            base_url = "https://news.naver.com/breakingnews/section/101/259"
        else:
            base_url = "https://news.naver.com/breakingnews/section/101/260"
        
        # 날짜 파라미터 추가 (YYYYMMDD 형식)
        date_param = date.replace('-', '')
        url = f"{base_url}?date={date_param}"
        
        try:
            logger.info(f"날짜 {date} {category} 뉴스 수집 중...")
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 링크 추출 (개선된 선택자)
            news_links = []
            
            # 방법 1: sa_text_title 클래스로 링크 찾기
            title_links = soup.find_all('a', class_='sa_text_title')
            for link in title_links:
                href = link.get('href', '')
                if href and 'n.news.naver.com' in href:
                    news_links.append({
                        'url': href,
                        'title': link.get_text(strip=True)
                    })
            
            # 방법 2: 일반적인 뉴스 링크 찾기
            if not news_links:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if ('n.news.naver.com' in href and 
                        '/mnews/article/' in href and
                        len(link.get_text(strip=True)) > 10):
                        news_links.append({
                            'url': href,
                            'title': link.get_text(strip=True)
                        })
            
            logger.info(f"발견된 뉴스 링크: {len(news_links)}개")
            
            # 중복 제거
            unique_links = []
            seen_urls = set()
            for link in news_links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            # 각 뉴스 상세 정보 수집
            for i, link_info in enumerate(unique_links[:20]):  # 최대 20개로 제한
                try:
                    news_detail = self.get_news_detail(link_info['url'])
                    if news_detail:
                        news_data = {
                            'date': date,
                            'title': link_info['title'],
                            'url': link_info['url'],
                            'category': category,
                            'content': news_detail.get('content', ''),
                            'summary': news_detail.get('summary', ''),
                            'source': news_detail.get('source', ''),
                            'crawl_time': datetime.now().isoformat()
                        }
                        news_list.append(news_data)
                    
                    time.sleep(0.5)  # 서버 부하 방지
                    
                except Exception as e:
                    logger.error(f"뉴스 상세 정보 수집 실패 {link_info['url']}: {e}")
                    continue
            
            logger.info(f"날짜 {date}: {len(news_list)}개 뉴스 수집 완료")
            
        except Exception as e:
            logger.error(f"날짜 {date} 뉴스 수집 실패: {e}")
        
        return news_list
    
    def get_news_detail(self, url: str) -> Dict[str, str]:
        """뉴스 상세 정보 수집 (개선된 버전)"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 추출 (개선된 선택자)
            title = ""
            title_tag = soup.select_one('h2#title_area span')
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                # 대안 선택자들
                title_selectors = [
                    'h2.media_end_head_headline span',
                    'h1.media_end_head_headline span',
                    '.media_end_head_headline span'
                ]
                for selector in title_selectors:
                    title_tag = soup.select_one(selector)
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        break
            
            # 본문 추출 (개선된 선택자)
            content = ""
            content_tag = soup.select_one('article#dic_area')
            if content_tag:
                # 불필요한 요소 제거
                for unwanted in content_tag.select('script, style, .reporter_area, .copyright, .end_photo_org'):
                    unwanted.decompose()
                content = content_tag.get_text(separator='\n', strip=True)
            else:
                # 대안 선택자들
                content_selectors = [
                    'article.go_trans',
                    '.article_content',
                    '.news_end',
                    '.article_body'
                ]
                for selector in content_selectors:
                    content_tag = soup.select_one(selector)
                    if content_tag:
                        for unwanted in content_tag.select('script, style'):
                            unwanted.decompose()
                        content = content_tag.get_text(separator='\n', strip=True)
                        break
            
            # 요약 추출
            summary = ""
            summary_tag = soup.select_one('.media_end_summary')
            if summary_tag:
                summary = summary_tag.get_text(strip=True)
            else:
                # 대안 선택자들
                summary_selectors = [
                    '.summary',
                    '.article_summary',
                    '.news_summary'
                ]
                for selector in summary_selectors:
                    summary_tag = soup.select_one(selector)
                    if summary_tag:
                        summary = summary_tag.get_text(strip=True)
                        break
            
            # 출처 추출
            source = ""
            source_selectors = [
                '.press_logo img',
                '.press_logo a',
                '.media_end_head_top_logo img',
                '.media_end_head_top_logo a'
            ]
            for selector in source_selectors:
                source_tag = soup.select_one(selector)
                if source_tag:
                    source = source_tag.get('alt', '') or source_tag.get_text(strip=True)
                    break
            
            return {
                'content': content,
                'summary': summary,
                'source': source
            }
            
        except Exception as e:
            logger.error(f"뉴스 상세 정보 수집 실패 {url}: {e}")
            return {'content': '', 'summary': '', 'source': ''}
    
    def crawl_date_range(self, start_date: str, end_date: str, category: str = "stock") -> List[Dict[str, Any]]:
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
    crawler = ImprovedNaverCrawler()
    
    # 어제 날짜 (2025-07-16)
    target_date = "2025-07-16"
    
    print(f"=== {target_date} 증권 뉴스 수집 시작 ===")
    
    try:
        # 증권 뉴스 수집
        news_list = crawler.get_news_by_date(target_date, "stock")
        
        if not news_list:
            print("수집된 뉴스가 없습니다.")
            return
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"improved_naver_stock_{target_date}_{timestamp}.csv"
        json_filename = f"improved_naver_stock_{target_date}_{timestamp}.json"
        
        crawler.save_to_csv(news_list, csv_filename)
        crawler.save_to_json(news_list, json_filename)
        
        print(f"\n=== 수집 완료 ===")
        print(f"수집된 뉴스: {len(news_list)}개")
        print(f"CSV 파일: {csv_filename}")
        print(f"JSON 파일: {json_filename}")
        
        # 간단한 통계
        if news_list:
            df = pd.DataFrame(news_list)
            print(f"\n=== 통계 ===")
            print(f"출처별 분포:")
            source_counts = df['source'].value_counts().head(5)
            for source, count in source_counts.items():
                print(f"  {source}: {count}개")
            
            # 첫 번째 뉴스 미리보기
            if len(news_list) > 0:
                first_news = news_list[0]
                print(f"\n=== 첫 번째 뉴스 미리보기 ===")
                print(f"제목: {first_news['title']}")
                print(f"출처: {first_news['source']}")
                print(f"URL: {first_news['url']}")
                print(f"본문 길이: {len(first_news['content'])}자")
        
    except Exception as e:
        print(f"수집 실패: {e}")
        logger.error(f"수집 실패: {e}")

if __name__ == "__main__":
    main() 