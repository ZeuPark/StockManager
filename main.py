#!/usr/bin/env python3
"""
Stock Manager - Main Application
자동매매 시스템 메인 애플리케이션
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from utils.token_manager import TokenManager
from api.kiwoom_client import KiwoomClient
from api.websocket_client import WebSocketClient
from orders.order_manager import OrderManager
from utils.logger import get_logger

# 로거 설정
logger = get_logger("main")

class TradingSystem:
    """자동매매 시스템 메인 클래스"""
    
    def __init__(self):
        self.settings = Settings()
        self.token_manager = TokenManager(self.settings)
        self.kiwoom_client = KiwoomClient(self.settings)
        self.order_manager = OrderManager(self.settings, self.kiwoom_client)
        self.websocket_client = WebSocketClient(self.settings, self.token_manager)
        
        # 시스템 상태
        self.is_running = False
        self.start_time = None
        
        logger.info(f"트레이딩 시스템 초기화 시작 (모드: {self.settings.ENVIRONMENT})")
    
    async def initialize(self):
        """시스템 초기화"""
        try:
            # 토큰 갱신
            logger.info("토큰 갱신 중...")
            token_refresh_success = self.token_manager.refresh_token(self.settings.ENVIRONMENT)
            if not token_refresh_success:
                logger.warning("토큰 갱신 실패, 기존 토큰 사용")
            logger.info("토큰 갱신 완료")
            
            # 계좌 정보 조회
            logger.info("계좌 정보 조회 중...")
            try:
                account_info = self.kiwoom_client.get_account_info()
                logger.info(f"계좌 정보 조회 성공: {account_info}")
            except Exception as e:
                logger.warning(f"계좌 정보 조회 실패, 기본값 사용: {e}")
            
            # 웹소켓 클라이언트 설정
            self.websocket_client.set_callbacks(
                on_connect=self.on_websocket_connect,
                on_disconnect=self.on_websocket_disconnect,
                on_trading_signal=self.on_trading_signal,
                on_error=self.on_error
            )
            
            # 주문 매니저 연결
            self.websocket_client.set_order_manager(self.order_manager)
            
            logger.info("시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            raise
    
    async def on_websocket_connect(self):
        """웹소켓 연결 콜백"""
        logger.info("웹소켓 연결됨")
    
    async def on_websocket_disconnect(self):
        """웹소켓 연결 해제 콜백"""
        logger.info("웹소켓 연결 해제됨")
    
    async def on_trading_signal(self, stock_data, results):
        """매매 신호 콜백"""
        logger.info(f"매매 신호 수신: {stock_data.code}")
        
        # 주문 매니저를 통한 자동 주문 실행
        if self.order_manager:
            try:
                order = await self.order_manager.handle_trading_signal(stock_data, results)
                if order:
                    logger.info(f"자동 주문 실행 완료: {stock_data.code}")
                else:
                    logger.info(f"자동 주문 실행 실패 또는 조건 불만족: {stock_data.code}")
            except Exception as e:
                logger.error(f"자동 주문 실행 중 오류: {e}")
    
    async def on_error(self, error):
        """에러 콜백"""
        logger.error(f"시스템 에러: {error}")
    
    async def start(self):
        """시스템 시작"""
        try:
            await self.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("트레이딩 시스템 시작")
            
            # 웹소켓 클라이언트 실행
            await self.websocket_client.run(self.settings.TARGET_STOCKS)
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """시스템 종료"""
        if self.is_running:
            self.is_running = False
            
            # 웹소켓 연결 해제
            if self.websocket_client:
                await self.websocket_client.disconnect()
            
            # 최종 포지션 요약 출력
            if self.order_manager:
                summary = self.order_manager.get_position_summary()
                logger.info("=== 최종 포지션 요약 ===")
                logger.info(f"총 보유 종목: {summary['total_positions']}개")
                logger.info(f"총 보유 가치: {summary['total_value']:,.0f}원")
                logger.info(f"일일 실현 손익: {summary['daily_pnl']:,.0f}원")
                logger.info(f"일일 거래 횟수: {summary['daily_trades']}회")
                
                if summary['positions']:
                    logger.info("보유 종목 상세:")
                    for pos in summary['positions']:
                        logger.info(f"  {pos['stock_code']}: {pos['quantity']}주 @ {pos['avg_price']:,.0f}원")
            
            logger.info("트레이딩 시스템 종료")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time,
            "environment": self.settings.ENVIRONMENT,
            "websocket_status": self.websocket_client.get_status() if self.websocket_client else None,
            "position_summary": self.order_manager.get_position_summary() if self.order_manager else None
        }

async def main():
    """메인 함수"""
    trading_system = TradingSystem()
    
    try:
        await trading_system.start()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {e}")
    finally:
        await trading_system.stop()

if __name__ == "__main__":
    asyncio.run(main())
