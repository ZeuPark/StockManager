#!/usr/bin/env python3
"""
Volume Trading System - 거래량 급증 종목 자동매매
키움 API를 사용하여 거래량 급증 종목을 실시간으로 스크리닝하고 자동매매 실행
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
from orders.order_manager import OrderManager
from analysis.volume_scanner import VolumeScanner
from utils.logger import get_logger

# 로거 설정
logger = get_logger("volume_trading")

class VolumeTradingSystem:
    """거래량 급증 종목 자동매매 시스템"""
    
    def __init__(self):
        self.settings = Settings()
        self.token_manager = TokenManager(self.settings)
        self.kiwoom_client = KiwoomClient(self.settings)
        self.order_manager = OrderManager(self.settings, self.kiwoom_client)
        self.volume_scanner = VolumeScanner(self.settings, self.token_manager)
        
        # 시스템 상태
        self.is_running = False
        self.start_time = None
        
        logger.info(f"거래량 자동매매 시스템 초기화 시작 (모드: {self.settings.ENVIRONMENT})")
    
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
            
            # 거래량 스캐너 설정
            self.volume_scanner.set_order_manager(self.order_manager)
            self.volume_scanner.auto_trade_enabled = self.settings.VOLUME_SCANNING.get("auto_trade_enabled", True)
            self.volume_scanner.scan_interval = self.settings.VOLUME_SCANNING.get("scan_interval", 5)
            self.volume_scanner.min_volume_ratio = self.settings.VOLUME_SCANNING.get("min_volume_ratio", 2.0)
            self.volume_scanner.min_trade_value = self.settings.VOLUME_SCANNING.get("min_trade_value", 50_000_000)
            self.volume_scanner.min_score = self.settings.VOLUME_SCANNING.get("min_score", 5)
            
            logger.info("거래량 스캐닝 설정 완료")
            logger.info(f"  - 스캔 간격: {self.volume_scanner.scan_interval}초")
            logger.info(f"  - 최소 거래량 비율: {self.volume_scanner.min_volume_ratio:.1f}%")
            logger.info(f"  - 최소 거래대금: {self.volume_scanner.min_trade_value:,}원")
            logger.info(f"  - 최소 점수: {self.volume_scanner.min_score}점")
            logger.info(f"  - 자동매매: {'활성화' if self.volume_scanner.auto_trade_enabled else '비활성화'}")
            
            logger.info("시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            raise
    
    async def start(self):
        """시스템 시작"""
        try:
            await self.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("거래량 자동매매 시스템 시작")
            logger.info("=" * 50)
            logger.info("거래량 급증 종목 스캐닝 및 자동매매를 시작합니다.")
            logger.info("종료하려면 Ctrl+C를 누르세요.")
            logger.info("=" * 50)
            
            # 거래량 스캐닝 시작
            await self.volume_scanner.start_scanning()
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """시스템 종료"""
        if self.is_running:
            self.is_running = False
            
            # 최종 포지션 요약 출력
            if self.order_manager:
                summary = self.order_manager.get_position_summary()
                volume_summary = self.order_manager.get_volume_positions_summary()
                
                logger.info("=" * 50)
                logger.info("=== 최종 거래 요약 ===")
                logger.info(f"총 보유 종목: {summary['total_positions']}개")
                logger.info(f"총 보유 가치: {summary['total_value']:,.0f}원")
                logger.info(f"일일 실현 손익: {summary['daily_pnl']:,.0f}원")
                logger.info(f"일일 거래 횟수: {summary['daily_trades']}회")
                
                if summary['positions']:
                    logger.info("보유 종목 상세:")
                    for pos in summary['positions']:
                        logger.info(f"  {pos['stock_code']}: {pos['quantity']}주 @ {pos['avg_price']:,.0f}원")
                
                logger.info(f"거래량 포지션: {volume_summary['total_volume_positions']}개")
                if volume_summary['volume_positions']:
                    logger.info("거래량 포지션 상세:")
                    for pos in volume_summary['volume_positions']:
                        logger.info(f"  {pos['stock_code']}: {pos['quantity']}주 @ {pos['buy_price']:,.0f}원")
                        logger.info(f"    거래량비율: {pos['candidate_info']['volume_ratio']:.1f}%, 점수: {pos['candidate_info']['score']}점")
                
                logger.info("=" * 50)
            
            logger.info("거래량 자동매매 시스템 종료")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time,
            "environment": self.settings.ENVIRONMENT,
            "volume_scanner_status": self.volume_scanner.get_auto_trade_status() if self.volume_scanner else None,
            "volume_positions": self.order_manager.get_volume_positions_summary() if self.order_manager else None,
            "volume_candidates": self.volume_scanner.get_candidates_summary() if self.volume_scanner else None,
            "position_summary": self.order_manager.get_position_summary() if self.order_manager else None
        }

async def main():
    """메인 함수"""
    volume_trading_system = VolumeTradingSystem()
    
    try:
        await volume_trading_system.start()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {e}")
    finally:
        await volume_trading_system.stop()

if __name__ == "__main__":
    asyncio.run(main()) 