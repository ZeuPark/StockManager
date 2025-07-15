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
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os
import shutil
import platform
import requests
import zipfile
from .config import NEWS_SOURCES
import random
from datetime import timedelta

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
            # ChromeDriver 경로 설정
            driver_path = self._setup_chromedriver()
            
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--ignore-ssl-errors")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            logger.info(f"ChromeDriver 경로: {driver_path}")
            
            # 드라이버 파일 존재 확인
            if not os.path.exists(driver_path):
                raise FileNotFoundError(f"ChromeDriver 파일을 찾을 수 없습니다: {driver_path}")
            
            self.driver = webdriver.Chrome(
                service=Service(driver_path), 
                options=options
            )
            logger.info("셀레니움 드라이버 초기화 완료")
        except Exception as e:
            logger.error(f"드라이버 초기화 실패: {e}")
            raise
    
    def _setup_chromedriver(self):
        """ChromeDriver 설정"""
        try:
            # 현재 Chrome 버전 확인 (간단한 방법)
            chrome_version = "138.0.7204.94"  # 최신 안정 버전
            
            # 64비트 드라이버 다운로드 URL
            driver_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/win64/chromedriver-win64.zip"
            
            # 로컬 드라이버 경로
            driver_dir = os.path.join(os.path.expanduser("~"), ".chromedriver")
            driver_path = os.path.join(driver_dir, "chromedriver.exe")
            
            # 드라이버가 없으면 다운로드
            if not os.path.exists(driver_path):
                logger.info("ChromeDriver 다운로드 중...")
                self._download_chromedriver(driver_url, driver_dir)
            
            return driver_path
            
        except Exception as e:
            logger.error(f"ChromeDriver 설정 실패: {e}")
            raise
    
    def _download_chromedriver(self, url, driver_dir):
        """ChromeDriver 다운로드"""
        try:
            # 디렉토리 생성
            os.makedirs(driver_dir, exist_ok=True)
            
            # ZIP 파일 다운로드
            zip_path = os.path.join(driver_dir, "chromedriver.zip")
            response = requests.get(url)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # ZIP 파일 압축 해제
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(driver_dir)
            
            # ZIP 파일 삭제
            os.remove(zip_path)
            
            # 실제 chromedriver.exe 파일 찾기
            chromedriver_exe = None
            for root, dirs, files in os.walk(driver_dir):
                for file in files:
                    if file == 'chromedriver.exe':
                        chromedriver_exe = os.path.join(root, file)
                        break
                if chromedriver_exe:
                    break
            
            if chromedriver_exe:
                # 최상위 디렉토리로 이동
                final_path = os.path.join(driver_dir, "chromedriver.exe")
                if chromedriver_exe != final_path:
                    shutil.move(chromedriver_exe, final_path)
                logger.info(f"ChromeDriver 설치 완료: {final_path}")
            else:
                raise FileNotFoundError("chromedriver.exe 파일을 찾을 수 없습니다")
            
        except Exception as e:
            logger.error(f"ChromeDriver 다운로드 실패: {e}")
            raise
    
    def extract_detail_text(self, url: str) -> str:
        """뉴스 본문 추출"""
        try:
            self.driver.get(url)
            time.sleep(0.5)  # 페이지 로딩 대기
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 네이버 뉴스 본문 선택자들
            content_selectors = [
                'article#dic_area',
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
                logger.info(f"페이지 {page} 처리 중...")
                current_url = base_url.format(page)
                self.driver.get(current_url)
                time.sleep(3)  # 페이지 로딩 시간 증가
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 디버깅: 페이지 제목 확인
                page_title = soup.find('title')
                if page_title:
                    logger.info(f"페이지 제목: {page_title.get_text()}")
                
                # 더 포괄적인 뉴스 링크 추출 방법
                news_items = []
                
                # 방법 1: 모든 뉴스 링크 찾기
                all_links = soup.find_all('a', href=True)
                news_links = []
                
                for link in all_links:
                    href = link.get('href', '')
                    # 네이버 뉴스 링크 필터링
                    if ('news.naver.com' in href and 
                        ('/main/read.naver?' in href or '/article/' in href) and
                        len(link.get_text(strip=True)) > 10):  # 제목이 있는 링크만
                        news_links.append(link)
                
                logger.info(f"발견된 뉴스 링크: {len(news_links)}개")
                
                if not news_links:
                    logger.info("뉴스 링크를 찾을 수 없음. 종료.")
                    break
                
                # 중복 제거 및 유효한 뉴스만 필터링
                unique_news = []
                for link in news_links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    # 상대 URL을 절대 URL로 변환
                    if href.startswith('/'):
                        full_url = "https://news.naver.com" + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # 중복 제거 및 유효성 검사
                    if (full_url not in seen_urls and 
                        title and 
                        len(title) > 10 and
                        not any(skip in title.lower() for skip in ['광고', 'ad', 'sponsored'])):
                        
                        unique_news.append({
                            'title': title,
                            'url': full_url,
                            'link_element': link
                        })
                        seen_urls.add(full_url)
                
                logger.info(f"유효한 뉴스: {len(unique_news)}개")
                
                if not unique_news:
                    logger.info("유효한 뉴스가 없음. 종료.")
                    break
                
                # 뉴스 본문 추출 (처음 5개만 테스트)
                page_results = []
                for i, news in enumerate(unique_news[:5]):  # 처음 5개만 처리
                    try:
                        logger.info(f"뉴스 {i+1}/{min(5, len(unique_news))} 처리: {news['title'][:50]}...")
                        
                        # 본문 추출
                        content = self.extract_detail_text(news['url'])
                        
                        if content and len(content) > 50:  # 본문이 충분히 긴 경우만
                            page_results.append({
                                "title": news['title'],
                                "url": news['url'],
                                "content": content,
                                "category": category,
                                "source": "naver",
                                "timestamp": datetime.now().isoformat()
                            })
                            logger.info(f"뉴스 저장 완료: {len(content)}자")
                        else:
                            logger.warning(f"본문이 너무 짧음: {len(content) if content else 0}자")
                    
                    except Exception as e:
                        logger.error(f"뉴스 처리 실패: {e}")
                        continue
                
                # 페이지별 결과 저장
                if page_results:
                    filename = f"naver_news_{category}_page{page}.csv"
                    pd.DataFrame(page_results).to_csv(filename, index=False, encoding="utf-8-sig")
                    logger.info(f"페이지별 저장: {filename} (총 {len(page_results)}개)")
                
                results.extend(page_results)
                
                # 첫 페이지에서만 테스트
                if page == 1:
                    logger.info("첫 페이지 테스트 완료. 종료.")
                    break
                
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

def collect_naver_stock_by_date_range(start_date, end_date, save_dir='news_trading/naver_stock_news'):
    """
    네이버 증권 뉴스에서 start_date~end_date까지 날짜별로 본문까지 크롤링하여
    save_dir에 naver_stock_YYYY-MM-DD.csv로 저장
    """
    from news_trading.naver_crawler import NaverNewsCrawler
    os.makedirs(save_dir, exist_ok=True)
    crawler = NaverNewsCrawler(headless=True)
    try:
        cur_date = start_date
        while cur_date <= end_date:
            date_str = cur_date.strftime('%Y-%m-%d')
            print(f"[{date_str}] 뉴스 크롤링 시작...")
            # 네이버 증권 뉴스 목록 크롤링 (카테고리: stock, 날짜별)
            news_list = crawler.crawl_stock_news_by_date(date=cur_date)
            if not news_list:
                print(f"[{date_str}] 뉴스 없음.")
                cur_date += timedelta(days=1)
                time.sleep(random.uniform(1, 3))
                continue
            # 본문 추출 및 DataFrame 저장
            df = pd.DataFrame(news_list)
            filename = os.path.join(save_dir, f"naver_stock_{date_str}.csv")
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"[{date_str}] {len(df)}개 저장 완료: {filename}")
            cur_date += timedelta(days=1)
            time.sleep(random.uniform(1, 3))
    finally:
        crawler.close()

def collect_naver_stock_all_by_paging(max_pages=2000, save_dir='news_trading/naver_stock_news'):
    """
    네이버 증권 뉴스(page=1~max_pages)를 최신→과거 순으로 크롤링하며,
    각 뉴스의 날짜별로 news_trading/naver_stock_news/naver_stock_YYYY-MM-DD.csv로 저장
    이미 저장된 날짜는 건너뜀. 본문까지 저장. 각 페이지마다 1~3초 딜레이.
    """
    from news_trading.naver_crawler import NaverNewsCrawler
    os.makedirs(save_dir, exist_ok=True)
    crawler = NaverNewsCrawler(headless=True)
    seen_urls = set()
    date_news = {}
    try:
        for page in range(1, max_pages+1):
            print(f"[page {page}] 크롤링 중...")
            news_list = crawler.crawl_naver_news(
                base_url="https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=259&page={}",
                max_pages=1, category="stock")
            if not news_list:
                print(f"[page {page}] 뉴스 없음. 종료.")
                break
            for news in news_list:
                url = news.get('url')
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                # 날짜 파싱
                ts = news.get('timestamp')
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts)
                    except Exception:
                        continue
                date_str = ts.strftime('%Y-%m-%d') if ts else None
                if not date_str:
                    continue
                if date_str not in date_news:
                    date_news[date_str] = []
                date_news[date_str].append(news)
            # 날짜별로 저장
            for date_str, news_list in date_news.items():
                filename = os.path.join(save_dir, f"naver_stock_{date_str}.csv")
                if os.path.exists(filename):
                    continue  # 이미 저장된 날짜는 건너뜀
                if news_list:
                    df = pd.DataFrame(news_list)
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f"[{date_str}] {len(df)}개 저장 완료: {filename}")
            time.sleep(random.uniform(1, 3))
    finally:
        crawler.close()

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
        print(f"총 {len(all_news)}개 저장 완료: naver_news_all.csv")
        
    finally:
        crawler.close()

if __name__ == "__main__":
    main() 