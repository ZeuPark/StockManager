#!/usr/bin/env python3
"""
Stock Manager - Main Trading System
키움 API를 사용한 자동 주식 거래 시스템
"""

import asyncio
import logging
import signal
import sys
import os
from typing import List, Dict, Optional
from datetime import datetime

# 프로젝트 모듈 import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config.settings import Settings
    from utils.token_manager import TokenManager
    from api.websocket_client import WebSocketClient
    from orders.signal_processor import SignalProcessor
    from analysis.momentum_analyzer import MomentumAnalyzer
except ImportError as e:
    print(f"Import error: {e}")
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path)
    raise

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingSystem:
    """메인 트레이딩 시스템 클래스"""
    
    def __init__(self, mode: str = "simulation"):
        self.mode = mode
        # 환경 변수 설정
        os.environ["ENVIRONMENT"] = mode
        self.settings = Settings()
        self.token_manager = TokenManager(self.settings)
        self.websocket_client = WebSocketClient(self.settings, self.token_manager)
        self.signal_processor = SignalProcessor(self.settings)
        self.momentum_analyzer = MomentumAnalyzer(self.settings)
        
        # 시스템 상태
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # 콜백 설정
        self._setup_callbacks()
        
        # 시그널 핸들러 설정
        self._setup_signal_handlers()
    
    def _setup_callbacks(self):
        """콜백 함수 설정"""
        # 웹소켓 클라이언트 콜백
        self.websocket_client.set_callbacks(
            on_connect=self._on_websocket_connect,
            on_disconnect=self._on_websocket_disconnect,
            on_trading_signal=self._on_trading_signal,
            on_error=self._on_websocket_error
        )
        
        # 신호 처리기 콜백
        self.signal_processor.set_callbacks(
            on_signal=self._on_signal_generated,
            on_order=self._on_order_executed,
            on_error=self._on_signal_error
        )
    
    def _setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        def signal_handler(signum, frame):
            logger.info(f"시스템 종료 신호 수신: {signum}")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _on_websocket_connect(self):
        """웹소켓 연결 콜백"""
        logger.info("웹소켓 연결됨")
        
        # 초기 주식 등록 (한 번만 실행)
        if self.settings.TARGET_STOCKS and not hasattr(self, '_stocks_registered'):
            for stock_code in self.settings.TARGET_STOCKS:
                try:
                    await self.websocket_client.register_stock(stock_code)
                    logger.info(f"주식 등록: {stock_code}")
                except Exception as e:
                    logger.error(f"주식 등록 실패 {stock_code}: {e}")
                    break
            self._stocks_registered = True
    
    async def _on_websocket_disconnect(self):
        """웹소켓 연결 해제 콜백"""
        logger.warning("웹소켓 연결 해제됨")
        
        # 재연결 시도 (최대 3회)
        if self.is_running and not hasattr(self, '_reconnect_attempts'):
            self._reconnect_attempts = 0
        
        if self.is_running and self._reconnect_attempts < 3:
            self._reconnect_attempts += 1
            logger.info(f"재연결 시도 중... ({self._reconnect_attempts}/3)")
            await asyncio.sleep(5)
            try:
                await self.websocket_client.reconnect()
            except Exception as e:
                logger.error(f"재연결 실패: {e}")
        else:
            logger.error("최대 재연결 시도 횟수 초과. 시스템을 종료합니다.")
            self.shutdown_event.set()
    
    async def _on_trading_signal(self, stock_data, conditions):
        """매매 신호 콜백"""
        logger.info(f"매매 신호 수신: {stock_data.code}")
        
        # 신호 처리
        await self.signal_processor.process_trading_signal(stock_data, conditions)
    
    async def _on_websocket_error(self, error):
        """웹소켓 에러 콜백"""
        logger.error(f"웹소켓 에러: {error}")
    
    async def _on_signal_generated(self, signal):
        """신호 생성 콜백"""
        logger.info(f"신호 생성: {signal.stock_code} - {signal.signal_type} @ {signal.price}")
        
        # 신호 통계 출력
        summary = self.signal_processor.get_signal_summary()
        logger.info(f"신호 통계: {summary}")
    
    async def _on_order_executed(self, signal, order_result):
        """주문 실행 콜백"""
        logger.info(f"주문 실행됨: {signal.stock_code} - {signal.quantity}주")
    
    async def _on_signal_error(self, error):
        """신호 처리 에러 콜백"""
        logger.error(f"신호 처리 에러: {error}")
    
    async def initialize(self):
        """시스템 초기화"""
        try:
            logger.info(f"트레이딩 시스템 초기화 시작 (모드: {self.mode})")
            
            # 토큰 갱신
            self.token_manager.refresh_token()
            logger.info("토큰 갱신 완료")
            
            # 계좌 정보 초기화 (실제로는 API에서 가져와야 함)
            self.signal_processor.update_account_info(
                balance=10000000,  # 1천만원
                positions=[]
            )
            
            logger.info("시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            raise
    
    async def start(self, stock_codes: Optional[List[str]] = None):
        """시스템 시작"""
        try:
            await self.initialize()
            
            self.is_running = True
            logger.info("트레이딩 시스템 시작")
            
            # 웹소켓 클라이언트 실행
            await self.websocket_client.run(stock_codes or self.settings.TARGET_STOCKS)
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            raise
        finally:
            self.is_running = False
    
    async def stop(self):
        """시스템 종료"""
        logger.info("시스템 종료 시작")
        
        self.is_running = False
        self.shutdown_event.set()
        
        # 웹소켓 연결 해제
        await self.websocket_client.disconnect()
        
        logger.info("시스템 종료 완료")
    
    async def run(self, stock_codes: Optional[List[str]] = None):
        """시스템 실행 (종료 신호 대기 포함)"""
        try:
            # 시스템 시작
            start_task = asyncio.create_task(self.start(stock_codes))
            
            # 종료 신호 대기
            await self.shutdown_event.wait()
            
            # 시스템 종료
            await self.stop()
            
            # 시작 태스크 취소
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
                
        except Exception as e:
            logger.error(f"시스템 실행 중 오류: {e}")
            await self.stop()
    
    def get_status(self) -> Dict[str, any]:
        """시스템 상태 반환"""
        return {
            "mode": self.mode,
            "is_running": self.is_running,
            "websocket_status": self.websocket_client.get_status(),
            "signal_summary": self.signal_processor.get_signal_summary(),
            "settings": {
                "target_stocks": self.settings.TARGET_STOCKS,
                "momentum_conditions": self.settings.MOMENTUM_CONDITIONS,
                "risk_management": self.settings.RISK_MANAGEMENT
            }
        }

async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock Manager Trading System")
    parser.add_argument("--mode", choices=["simulation", "production"], 
                       default="simulation", help="실행 모드")
    parser.add_argument("--stocks", nargs="+", help="모니터링할 주식 코드들")
    
    args = parser.parse_args()
    
    # 트레이딩 시스템 생성
    trading_system = TradingSystem(mode=args.mode)
    
    try:
        # 시스템 실행
        await trading_system.run(args.stocks)
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시스템 실행 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 로그 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    
    # 메인 함수 실행
    asyncio.run(main())
