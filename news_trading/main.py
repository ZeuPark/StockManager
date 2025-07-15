"""
News Trading System Main Orchestrator
모든 모듈을 통합하는 메인 시스템
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_trading.news_crawler import NewsCrawlerManager
from news_trading.sentiment_analyzer import SentimentAnalyzerManager
from news_trading.trading_signals import SignalManager
from news_trading.swing_news_collector import SwingNewsCollector
from news_trading.config import PERFORMANCE_CONFIG
from trading.swing_trade_simulator import simulate_trade
import pandas as pd

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/news_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NewsTradingSystem:
    """뉴스 기반 거래 시스템 메인 클래스"""
    
    def __init__(self):
        self.crawler_manager = NewsCrawlerManager()
        self.sentiment_analyzer = SentimentAnalyzerManager()
        self.signal_manager = SignalManager()
        self.swing_collector = SwingNewsCollector()
        self.is_running = False
        
        logger.info("뉴스 거래 시스템 초기화 완료")
    
    async def start(self):
        """시스템 시작"""
        self.is_running = True
        logger.info("뉴스 거래 시스템 시작")
        
        try:
            while self.is_running:
                await self._run_trading_cycle()
                if self.is_running:  # 중지 요청이 없을 때만 대기
                    await asyncio.sleep(PERFORMANCE_CONFIG['crawl_interval'])
        except KeyboardInterrupt:
            logger.info("사용자에 의해 시스템 중단")
        except asyncio.CancelledError:
            logger.info("시스템 작업 취소됨")
        except Exception as e:
            logger.error(f"시스템 오류: {e}")
        finally:
            await self.stop()
    
    async def _run_trading_cycle(self):
        """거래 사이클 실행"""
        try:
            # 1. 뉴스 크롤링
            logger.info("뉴스 크롤링 시작...")
            news_data = await self.crawler_manager.crawl_all_sources()
            logger.info(f"수집된 뉴스: {len(news_data)}개")
            
            if not news_data:
                logger.info("수집된 뉴스가 없습니다.")
                return
            
            # 2. 거래 신호 생성
            logger.info("거래 신호 생성 중...")
            signals = self.signal_manager.process_news(news_data)
            logger.info(f"생성된 신호: {len(signals)}개")
            
            # 3. 신호 출력
            for signal in signals:
                logger.info(f"거래 신호: {signal}")
                await self._execute_signal(signal)
            
            # 4. 활성 신호 상태 출력
            active_signals = self.signal_manager.get_active_signals()
            if active_signals:
                logger.info(f"활성 신호: {len(active_signals)}개")
                for signal in active_signals:
                    logger.info(f"  - {signal}")
            
        except Exception as e:
            logger.error(f"거래 사이클 오류: {e}")
    
    async def _execute_signal(self, signal):
        """거래 신호 실행 (실제 거래는 여기서 구현)"""
        # 실제 거래 실행 로직
        logger.info(f"신호 실행: {signal.stock_code} {signal.signal_type}")
        logger.info(f"  이유: {signal.reason}")
        logger.info(f"  목표가: {signal.target_price}")
        logger.info(f"  손절가: {signal.stop_loss}")
        logger.info(f"  익절가: {signal.take_profit}")
        
        # 여기에 실제 거래 API 호출 로직 추가
        # await self._place_order(signal)
    
    async def stop(self):
        """시스템 중지"""
        self.is_running = False
        logger.info("뉴스 거래 시스템 중지")
        
        # 드라이버 정리
        self.crawler_manager.close_all_drivers()
        self.swing_collector.close()
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'is_running': self.is_running,
            'active_signals': len(self.signal_manager.get_active_signals()),
            'crawl_interval': PERFORMANCE_CONFIG['crawl_interval'],
            'last_update': datetime.now().isoformat()
        }
    
    async def test_crawler(self):
        """크롤러 테스트"""
        logger.info("크롤러 테스트 시작...")
        try:
            news_data = await self.crawler_manager.crawl_all_sources()
            logger.info(f"테스트 결과: {len(news_data)}개 뉴스 수집")
            
            if news_data:
                logger.info("샘플 뉴스:")
                for i, news in enumerate(news_data[:3]):  # 처음 3개만 출력
                    logger.info(f"  {i+1}. {news.get('title', '제목 없음')}")
                    logger.info(f"     출처: {news.get('source', '알 수 없음')}")
                    logger.info(f"     내용 길이: {len(news.get('content', ''))}자")
            
            return news_data
            
        except Exception as e:
            logger.error(f"크롤러 테스트 실패: {e}")
            return []

class NewsTradingCLI:
    """명령행 인터페이스"""
    
    def __init__(self):
        self.system = NewsTradingSystem()
    
    async def run(self):
        """CLI 실행"""
        print("=== 뉴스 기반 거래 시스템 ===")
        print("1. 시스템 시작")
        print("2. 시스템 상태 조회")
        print("3. 테스트 뉴스 분석")
        print("4. 크롤러 테스트")
        print("5. 스윙 트레이딩 분석")
        print("6. 종료")
        print("7. 뉴스 기반 스윙 트레이딩 시뮬레이션 (수익/손실 자동 검증, 날짜 입력)")
        
        while True:
            try:
                choice = input("\n선택하세요 (1-7): ").strip()
                
                if choice == '1':
                    await self._start_system()
                elif choice == '2':
                    await self._show_status()
                elif choice == '3':
                    await self._test_analysis()
                elif choice == '4':
                    await self._test_crawler()
                elif choice == '5':
                    await self._swing_trading_analysis()
                elif choice == '6':
                    print("시스템을 종료합니다.")
                    await self.system.stop()
                    break
                elif choice == '7':
                    await self._swing_trading_simulation()
                else:
                    print("잘못된 선택입니다.")
                    
            except KeyboardInterrupt:
                print("\n시스템을 종료합니다.")
                await self.system.stop()
                break
            except Exception as e:
                print(f"오류: {e}")
    
    async def _start_system(self):
        """시스템 시작"""
        print("뉴스 거래 시스템을 시작합니다...")
        print("Ctrl+C로 중단할 수 있습니다.")
        await self.system.start()
    
    async def _show_status(self):
        """시스템 상태 표시"""
        status = self.system.get_system_status()
        print(f"시스템 상태: {'실행 중' if status['is_running'] else '중지됨'}")
        print(f"활성 신호: {status['active_signals']}개")
        print(f"크롤링 간격: {status['crawl_interval']}초")
        print(f"마지막 업데이트: {status['last_update']}")
    
    async def _test_analysis(self):
        """테스트 뉴스 분석"""
        print("테스트 뉴스 분석을 실행합니다...")
        
        test_news = [
            {
                'title': '삼성전자 실적호전으로 상승세 전망',
                'content': '삼성전자가 예상보다 좋은 실적을 발표하여 주가 상승이 기대됩니다.',
                'timestamp': datetime.now(),
                'source': 'test'
            },
            {
                'title': 'LG전자 신기술 개발 성공',
                'content': 'LG전자가 혁신적인 신기술을 개발하여 시장에서 주목받고 있습니다.',
                'timestamp': datetime.now(),
                'source': 'test'
            }
        ]
        
        signals = self.system.signal_manager.process_news(test_news)
        print(f"테스트 결과: {len(signals)}개의 신호 생성")
        
        for signal in signals:
            print(f"  - {signal}")
    
    async def _test_crawler(self):
        """크롤러 테스트"""
        print("크롤러 테스트를 실행합니다...")
        news_data = await self.system.test_crawler()
        
        if news_data:
            print(f"✅ 크롤러 테스트 성공: {len(news_data)}개 뉴스 수집")
            print("\n샘플 뉴스:")
            for i, news in enumerate(news_data[:3]):
                print(f"  {i+1}. {news.get('title', '제목 없음')}")
                print(f"     출처: {news.get('source', '알 수 없음')}")
                print(f"     카테고리: {news.get('category', '알 수 없음')}")
                print()
        else:
            print("❌ 크롤러 테스트 실패")
    
    async def _swing_trading_analysis(self):
        """스윙 트레이딩 분석"""
        print("스윙 트레이딩 분석을 시작합니다...")
        try:
            recommendations = self.system.swing_collector.get_swing_recommendations()
            
            print("\n=== 스윙 트레이딩 뉴스 분석 결과 ===")
            print(f"일간 뉴스: {recommendations['daily_news_count']}개")
            print(f"트리거 뉴스: {recommendations['trigger_news_count']}개")
            print("\n" + recommendations['recommendation'])
            
            # 상위 트리거 뉴스 출력
            if recommendations['top_triggers']:
                print("\n=== 상위 트리거 뉴스 ===")
                for i, news in enumerate(recommendations['top_triggers'][:5], 1):
                    print(f"{i}. {news['title']}")
                    print(f"   키워드: {news.get('matched_keywords', 'N/A')}")
                    print()
            
            # 감정 분석 요약
            sentiment_summary = recommendations.get('sentiment_summary', {})
            if not sentiment_summary.empty:
                print("=== 감정 분석 요약 ===")
                print(sentiment_summary)
            
            print("\n✅ 스윙 트레이딩 분석 완료")
            
        except Exception as e:
            logger.error(f"스윙 트레이딩 분석 실패: {e}")
            print(f"❌ 스윙 트레이딩 분석 실패: {e}")
