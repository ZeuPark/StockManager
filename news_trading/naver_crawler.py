"""
Naver News Crawler
셀레니움 기반 네이버 뉴스 크롤러
"""

import time
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from .config import NEWS_SOURCES

logger = logging.getLogger(__name__)

class NaverNewsCrawler:
    """네이버 뉴스 크롤러"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """셀레니움 드라이버 설정"""
        try:
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=options
            )
            logger.info("셀레니움 드라이버 초기화 완료")
        except Exception as e:
            logger.error(f"드라이버 초기화 실패: {e}")
            raise
    
    def extract_detail_text(self, url: str) -> str:
        """뉴스 본문 추출"""
        try:
            self.driver.get(url)
            time.sleep(0.5)  # 페이지 로딩 대기
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 네이버 뉴스 본문 선택자들
            content_selectors = [
                'div#articleBodyContents',
                'div#articleBody',
                'div.article_body',
                'div.article_body_wrp',
                'div#content',
                'div.article_content'
            ]
            
            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break
            
            if content:
                # 불필요한 요소 제거
                for unwanted in content.select('script, style, .reporter_area, .copyright'):
                    unwanted.decompose()
                
                return content.get_text(separator='\n', strip=True)
            else:
                logger.warning(f"본문을 찾을 수 없음: {url}")
                return ''
                
        except Exception as e:
            logger.error(f"본문 추출 실패 {url}: {e}")
            return ''
    
    def crawl_naver_news(self, base_url: str, max_pages: int = 10, 
                        category: str = "economy") -> List[Dict[str, Any]]:
        """네이버 뉴스 크롤링"""
        results = []
        seen_urls = set()
        page = 1
        
        logger.info(f"네이버 뉴스 크롤링 시작: {base_url}")
        
        while page <= max_pages:
            try:
                logger.info(f"📄 페이지 {page} 처리 중...")
                current_url = base_url.format(page)
                self.driver.get(current_url)
                time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 네이버 뉴스 목록 선택자들
                news_selectors = [
                    'ul.list_news > li',
                    'div.news_area > div.news_wrap',
                    'div.news_area > a',
                    'ul.content_list > li'
                ]
                
                items = []
                for selector in news_selectors:
                    items = soup.select(selector)
                    if items:
                        break
                
                if not items:
                    logger.info("✅ 더 이상 항목 없음. 종료.")
                    break
                
                page_results = []
                for item in tqdm(items, desc=f"Page {page}"):
                    try:
                        # 제목과 링크 추출
                        title_tag = item.select_one('a') or item.select_one('strong.title') or item.select_one('.news_tit')
                        if not title_tag:
                            continue
                        
                        href = title_tag.get('href', '')
                        if not href:
                            continue
                        
                        # 상대 URL을 절대 URL로 변환
                        if href.startswith('/'):
                            full_url = "https://news.naver.com" + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        title = title_tag.get_text(strip=True)
                        
                        if full_url in seen_urls:
                            continue
                        
                        # 본문 추출
                        content = self.extract_detail_text(full_url)
                        
                        if content:  # 본문이 있는 경우만 저장
                            page_results.append({
                                "title": title,
                                "url": full_url,
                                "content": content,
                                "category": category,
                                "source": "naver",
                                "timestamp": datetime.now().isoformat()
                            })
                            seen_urls.add(full_url)
                    
                    except Exception as e:
                        logger.error(f"❌ 항목 처리 실패: {e}")
                        continue
                
                # 페이지별 결과 저장
                if page_results:
                    filename = f"naver_news_{category}_page{page}.csv"
                    pd.DataFrame(page_results).to_csv(filename, index=False, encoding="utf-8-sig")
                    logger.info(f"💾 페이지별 저장: {filename} (총 {len(page_results)}개)")
                
                results.extend(page_results)
                page += 1
                
            except Exception as e:
                logger.error(f"페이지 {page} 처리 실패: {e}")
                page += 1
                continue
        
        return results
    
    def crawl_economy_news(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """경제 뉴스 크롤링"""
        base_url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258&page={}"
        return self.crawl_naver_news(base_url, max_pages, "economy")
    
    def crawl_stock_news(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """주식 뉴스 크롤링"""
        base_url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=259&page={}"
        return self.crawl_naver_news(base_url, max_pages, "stock")
    
    def crawl_company_news(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """기업 뉴스 크롤링"""
        base_url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=260&page={}"
        return self.crawl_naver_news(base_url, max_pages, "company")
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("셀레니움 드라이버 종료")

# 사용 예시
def main():
    crawler = NaverNewsCrawler(headless=True)
    
    try:
        # 경제 뉴스 크롤링
        print("경제 뉴스 크롤링 시작...")
        economy_news = crawler.crawl_economy_news(max_pages=3)
        print(f"경제 뉴스: {len(economy_news)}개")
        
        # 주식 뉴스 크롤링
        print("주식 뉴스 크롤링 시작...")
        stock_news = crawler.crawl_stock_news(max_pages=3)
        print(f"주식 뉴스: {len(stock_news)}개")
        
        # 전체 결과 저장
        all_news = economy_news + stock_news
        df = pd.DataFrame(all_news)
        df.to_csv("naver_news_all.csv", index=False, encoding="utf-8-sig")
        print(f"✅ 총 {len(all_news)}개 저장 완료: naver_news_all.csv")
        
    finally:
        crawler.close()

if __name__ == "__main__":
    main() 