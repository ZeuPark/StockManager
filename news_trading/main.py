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
from news_trading.config import PERFORMANCE_CONFIG

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
        self.is_running = False
        
        logger.info("뉴스 거래 시스템 초기화 완료")
    
    async def start(self):
        """시스템 시작"""
        self.is_running = True
        logger.info("뉴스 거래 시스템 시작")
        
        try:
            while self.is_running:
                await self._run_trading_cycle()
                await asyncio.sleep(PERFORMANCE_CONFIG['crawl_interval'])
        except KeyboardInterrupt:
            logger.info("사용자에 의해 시스템 중단")
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
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'is_running': self.is_running,
            'active_signals': len(self.signal_manager.get_active_signals()),
            'crawl_interval': PERFORMANCE_CONFIG['crawl_interval'],
            'last_update': datetime.now().isoformat()
        }

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
        print("4. 종료")
        
        while True:
            try:
                choice = input("\n선택하세요 (1-4): ").strip()
                
                if choice == '1':
                    await self._start_system()
                elif choice == '2':
                    await self._show_status()
                elif choice == '3':
                    await self._test_analysis()
                elif choice == '4':
                    print("시스템을 종료합니다.")
                    break
                else:
                    print("잘못된 선택입니다.")
                    
            except KeyboardInterrupt:
                print("\n시스템을 종료합니다.")
                break
            except Exception as e:
                print(f"오류: {e}")
    
    async def _start_system(self):
        """시스템 시작"""
        print("뉴스 거래 시스템을 시작합니다...")
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

async def main():
    """메인 함수"""
    cli = NewsTradingCLI()
    await cli.run()

if __name__ == "__main__":
    # logs 디렉토리 생성
    os.makedirs('logs', exist_ok=True)
    
    # 비동기 실행
    asyncio.run(main()) 