"""
News Crawler Module
플러그인 기반 뉴스 크롤러
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import logging
from .config import NEWS_SOURCES, PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)

class NewsSource(ABC):
    """뉴스 소스 추상 클래스 - 새로운 소스 추가 시 상속"""
    
    @abstractmethod
    async def fetch_news(self) -> List[Dict[str, Any]]:
        """뉴스 데이터 가져오기"""
        pass
    
    @abstractmethod
    def parse_news(self, raw_data: Any) -> List[Dict[str, Any]]:
        """뉴스 데이터 파싱"""
        pass

class YonhapNewsSource(NewsSource):
    """연합뉴스 크롤러"""
    
    def __init__(self):
        self.base_url = NEWS_SOURCES['korean']['yonhap']
    
    async def fetch_news(self) -> List[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}economy/") as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_news(html)
        except Exception as e:
            logger.error(f"연합뉴스 크롤링 실패: {e}")
        return []
    
    def parse_news(self, raw_data: str) -> List[Dict[str, Any]]:
        # 실제 구현에서는 BeautifulSoup 등으로 파싱
        # 여기서는 예시 구조만 제공
        return [{
            'title': '예시 뉴스 제목',
            'content': '뉴스 내용',
            'timestamp': datetime.now(),
            'source': 'yonhap',
            'url': 'https://example.com'
        }]

class NewsCrawlerManager:
    """뉴스 크롤러 관리자 - 싱글톤 패턴"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.sources = {}
            cls._instance._initialize_sources()
        return cls._instance
    
    def _initialize_sources(self):
        """뉴스 소스 초기화"""
        self.sources = {
            'yonhap': YonhapNewsSource(),
            # 새로운 소스는 여기에 추가
        }
    
    async def crawl_all_sources(self) -> List[Dict[str, Any]]:
        """모든 뉴스 소스에서 크롤링"""
        tasks = []
        for source_name, source in self.sources.items():
            tasks.append(self._crawl_source(source_name, source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_news = []
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
        
        return all_news
    
    async def _crawl_source(self, source_name: str, source: NewsSource) -> List[Dict[str, Any]]:
        """개별 뉴스 소스 크롤링"""
        try:
            news = await source.fetch_news()
            logger.info(f"{source_name}: {len(news)}개 뉴스 수집")
            return news
        except Exception as e:
            logger.error(f"{source_name} 크롤링 실패: {e}")
            return []
    
    def add_source(self, name: str, source: NewsSource):
        """새로운 뉴스 소스 추가"""
        self.sources[name] = source
        logger.info(f"새로운 뉴스 소스 추가: {name}")

# 사용 예시
async def main():
    crawler = NewsCrawlerManager()
    news = await crawler.crawl_all_sources()
    print(f"수집된 뉴스: {len(news)}개")

if __name__ == "__main__":
    asyncio.run(main()) 