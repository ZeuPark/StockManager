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
import sqlite3
import pandas as pd
from prometheus_client import start_http_server

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from utils.token_manager import TokenManager
from api.kiwoom_client import KiwoomClient
from api.websocket_client import WebSocketClient
from orders.order_manager import OrderManager
from analysis.volume_scanner import VolumeScanner
from analysis.momentum_analyzer import MomentumAnalyzer
from analysis.strategy2_analyzer import Strategy2Analyzer  # 전략 2 분석기 추가
from monitor.sell_monitor import SellMonitor
from utils.logger import get_logger
from monitor.prometheus_metrics import set_holdings_count

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
        self.volume_scanner = VolumeScanner(self.settings, self.token_manager)
        self.momentum_analyzer = MomentumAnalyzer(self.settings)
        self.strategy2_analyzer = Strategy2Analyzer(self.settings, self.token_manager)  # 전략 2 분석기 추가
        self.sell_monitor = SellMonitor(self.settings, self.kiwoom_client)
        
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
            self.volume_scanner.set_order_manager(self.order_manager)
            self.momentum_analyzer.set_order_manager(self.order_manager)
            self.strategy2_analyzer.set_order_manager(self.order_manager)
            
            # 전략 2 분석기에 Volume Scanner 연결 (데이터 공유)
            self.strategy2_analyzer.set_volume_scanner(self.volume_scanner)
            
            # 거래량 스캐닝 설정
            if self.settings.VOLUME_SCANNING.get("enabled", False):
                self.volume_scanner.auto_trade_enabled = self.settings.VOLUME_SCANNING.get("auto_trade_enabled", False)
                self.volume_scanner.scan_interval = self.settings.VOLUME_SCANNING.get("scan_interval", 120)  # 120초로 증가
                self.volume_scanner.min_volume_ratio = self.settings.VOLUME_SCANNING.get("min_volume_ratio", 2.0)
                self.volume_scanner.min_trade_value = self.settings.VOLUME_SCANNING.get("min_trade_value", 50_000_000)
                self.volume_scanner.min_score = self.settings.VOLUME_SCANNING.get("min_score", 5)
                logger.info("거래량 스캐닝 활성화")
            
            # 전략 2 분석기 설정
            if self.settings.VOLUME_SCANNING.get("strategy2_enabled", False):
                self.strategy2_analyzer.auto_trade_enabled = self.settings.VOLUME_SCANNING.get("auto_trade_enabled", False)
                self.strategy2_analyzer.scan_interval = self.settings.VOLUME_SCANNING.get("scan_interval", 30)
                logger.info("전략 2 분석기 활성화")
            
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
        # 재연결 시도 (선택적)
        if self.is_running:
            logger.info("웹소켓 재연결 시도 중...")
            try:
                await asyncio.sleep(5)  # 5초 대기 후 재연결
                await self.websocket_client.reconnect()
            except Exception as e:
                logger.error(f"웹소켓 재연결 실패: {e}")
    
    async def on_error(self, error):
        """에러 콜백 (연결 안정성 개선)"""
        error_str = str(error).lower()
        
        # 연결 관련 에러는 심각하지 않음 - 시스템 계속 실행
        if any(keyword in error_str for keyword in ["연결", "timeout", "websocket", "token", "인증"]):
            logger.warning(f"연결 관련 에러 (시스템 계속 실행): {error}")
            return
        
        # 심각한 에러인 경우
        logger.error(f"심각한 시스템 에러: {error}")
        # 필요시 시스템 종료 고려
        # await self.stop()
    
    async def handle_trading_event(self, stock_data, results):
        """신호 발생 시 주문→DB저장→실시간 분석/출력까지 한 번에 처리"""
        logger.info(f"[핵심핸들러] 신호 발생: {stock_data.code}")
        order = None
        if self.order_manager:
            try:
                order = await self.order_manager.handle_trading_signal(stock_data, results)
                if order:
                    logger.info(f"[핵심핸들러] 주문 성공: {stock_data.code}")
                else:
                    logger.info(f"[핵심핸들러] 주문 실패/조건 불만족: {stock_data.code}")
            except Exception as e:
                logger.error(f"[핵심핸들러] 주문 오류: {e}")
        # 주문 후 DB에 자동 저장됨 (order_manager에서)
        # 실시간 분석/상태 출력
        await self.print_realtime_status()
        return order

    async def print_realtime_status(self):
        """실시간 상태/분석 결과 출력 (TOP3 수익률, 보유 종목 등)"""
        try:
            # DB에서 완료된 거래 조회 (TOP3 수익률)
            conn = sqlite3.connect('database/stock_manager.db')
            query = '''
            SELECT t.stock_code, t.stock_name, t.buy_price, t.sell_price, t.profit_rate, t.result,
                   c.volume_ratio, c.trade_value
            FROM trades t
            LEFT JOIN trade_conditions c ON t.id = c.trade_id
            WHERE t.sell_price IS NOT NULL
            ORDER BY t.profit_rate DESC
            LIMIT 3
            '''
            df = pd.read_sql_query(query, conn)
            print("\n=== [실시간 TOP3 수익률 종목] ===")
            if not df.empty:
                for _, row in df.iterrows():
                    print(f"{row['stock_code']} {row['stock_name']}: {row['profit_rate']:.2f}% (거래량: {row['volume_ratio']}%, 거래대금: {row['trade_value']})")
            else:
                print("(아직 거래 없음)")
            conn.close()
            
            # 실제 계좌에서 보유 종목 조회
            if self.kiwoom_client:
                try:
                    account_info = self.kiwoom_client.get_account_info()
                    if account_info and 'acnt_evlt_remn_indv_tot' in account_info:
                        holdings = []
                        for stock in account_info['acnt_evlt_remn_indv_tot']:
                            stock_code = stock.get('stk_cd', '')
                            if stock_code and stock_code.startswith('A'):
                                actual_code = stock_code[1:]  # A 제거
                                stock_name = stock.get('stk_nm', '')
                                quantity = int(stock.get('rmnd_qty', '0'))
                                current_price = int(stock.get('cur_prc', '0'))
                                profit_rate = float(stock.get('prft_rt', '0')) / 100
                                purchase_price = int(stock.get('pur_pric', '0'))
                                
                                if quantity > 0:  # 실제 보유 수량이 있는 종목만
                                    holdings.append({
                                        'code': actual_code,
                                        'name': stock_name,
                                        'quantity': quantity,
                                        'current_price': current_price,
                                        'purchase_price': purchase_price,
                                        'profit_rate': profit_rate
                                    })
                        
                        print("\n=== [보유 중인 종목] ===")
                        if holdings:
                            for holding in holdings:
                                profit_color = "🔴" if holding['profit_rate'] < 0 else "🟢"
                                print(f"{profit_color} {holding['code']} {holding['name']}: {holding['quantity']}주 @ {holding['current_price']:,}원 (수익률: {holding['profit_rate']*100:.2f}%)")
                        else:
                            print("(보유 중인 종목 없음)")
                    else:
                        print("\n=== [보유 중인 종목] ===")
                        print("(계좌 정보 조회 실패)")
                except Exception as e:
                    print(f"\n=== [보유 중인 종목] ===")
                    print(f"(계좌 조회 오류: {e})")
            else:
                print("\n=== [보유 중인 종목] ===")
                print("(키움 클라이언트 없음)")
                
        except Exception as e:
            print(f"[실시간 상태 출력 오류] {e}")

    async def periodic_status_printer(self, interval_sec=60):
        """주기적으로 실시간 상태/분석 결과 출력"""
        while self.is_running:
            await self.print_realtime_status()
            await asyncio.sleep(interval_sec)

    async def on_trading_signal(self, stock_data, results):
        """매매 신호 콜백 (핵심핸들러로 위임)"""
        await self.handle_trading_event(stock_data, results)
    
    async def start(self):
        """시스템 시작 (웹소켓 연결 실패 시에도 계속 실행)"""
        try:
            await self.initialize()
            self.is_running = True
            self.start_time = datetime.now()
            logger.info("트레이딩 시스템 시작")
            
            tasks = []
            
            # 거래량 스캐닝 태스크 (웹소켓과 독립적으로 실행)
            if self.settings.VOLUME_SCANNING.get("enabled", False):
                volume_task = asyncio.create_task(self.volume_scanner.start_scanning())
                tasks.append(volume_task)
                logger.info("거래량 스캐닝 태스크 시작")
            
            # 전략 2 분석기 스캐닝 태스크 (웹소켓과 독립적으로 실행)
            if self.settings.VOLUME_SCANNING.get("strategy2_enabled", False):
                strategy2_task = asyncio.create_task(self.strategy2_analyzer.start_scanning())
                tasks.append(strategy2_task)
                logger.info("전략 2 분석기 스캐닝 태스크 시작")
            
            # 매도 모니터링 태스크 (웹소켓과 독립적으로 실행)
            if self.settings.SELL_SETTINGS.get("enabled", False):
                sell_monitor_task = asyncio.create_task(self.sell_monitor.start_monitoring())
                tasks.append(sell_monitor_task)
                logger.info("매도 모니터링 태스크 시작")
            
            # 주기적 상태 출력 태스크
            status_task = asyncio.create_task(self.periodic_status_printer(interval_sec=60))
            tasks.append(status_task)
            logger.info("상태 출력 태스크 시작")
            
            # 웹소켓 태스크 제거 (API 기반 스캐닝으로 대체)
            # try:
            #     websocket_task = asyncio.create_task(self.websocket_client.run(self.settings.TARGET_STOCKS))
            #     tasks.append(websocket_task)
            #     logger.info("웹소켓 태스크 시작")
            # except Exception as e:
            #     logger.warning(f"웹소켓 태스크 시작 실패 (다른 기능은 계속 실행): {e}")
            logger.info("웹소켓 태스크 제거됨 (API 기반 스캐닝으로 대체)")
            
            # 모든 태스크 실행 (하나라도 실패해도 다른 태스크는 계속)
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                logger.warning("실행할 태스크가 없습니다")
                
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """시스템 종료"""
        if self.is_running:
            self.is_running = False
            
            # 웹소켓 연결 해제 (제거됨)
            # if self.websocket_client:
            #     await self.websocket_client.disconnect()
            
            # 최종 포지션 요약 출력
            if self.order_manager:
                summary = self.order_manager.get_position_summary()
                set_holdings_count(summary['total_positions'])
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
            "websocket_status": "제거됨 (API 기반 스캐닝으로 대체)",
            "position_summary": self.order_manager.get_position_summary() if self.order_manager else None,
            "volume_scanner_status": self.volume_scanner.get_auto_trade_status() if self.volume_scanner else None,
            "volume_positions": self.order_manager.get_volume_positions_summary() if self.order_manager else None,
            "volume_candidates": self.volume_scanner.get_candidates_summary() if self.volume_scanner else None,
            "strategy2_analyzer_status": self.strategy2_analyzer.get_auto_trade_status() if self.strategy2_analyzer else None,
            "strategy2_candidates": self.strategy2_analyzer.get_candidates_summary() if self.strategy2_analyzer else None
        }

async def main():
    """메인 함수"""
    trading_system = TradingSystem()
    
    try:
        start_http_server(8000)
        await trading_system.start()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {e}")
    finally:
        await trading_system.stop()

if __name__ == "__main__":
    asyncio.run(main())
