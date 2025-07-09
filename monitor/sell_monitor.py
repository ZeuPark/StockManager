#!/usr/bin/env python3
"""
매도 모니터링 모듈
보유 종목의 손절/익절 조건을 모니터링하고 자동 매도 실행
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from utils.logger import get_logger
from database.database_manager import get_database_manager


class SellMonitor:
    """매도 모니터링 클래스"""
    
    def __init__(self, settings: Settings, kiwoom_client: KiwoomClient):
        self.settings = settings
        self.kiwoom_client = kiwoom_client
        self.logger = get_logger(__name__)
        self.db_manager = get_database_manager()
        
        # 매도 설정
        self.sell_settings = settings.SELL_SETTINGS
        self.monitoring_interval = self.sell_settings["monitoring_interval"]
        self.stop_loss_percent = self.sell_settings["stop_loss_percent"]
        self.take_profit_percent = self.sell_settings["take_profit_percent"]
        
        # API 호출 제한을 위한 설정
        self.last_api_call = 0
        self.min_api_interval = 30  # 최소 30초 간격으로 API 호출
        
        # 보유 종목 정보
        self.holdings: Dict[str, Dict] = {}
        self.last_check_time = 0
        
        self.logger.info(f"매도 모니터링 초기화 완료 - 손절: {self.stop_loss_percent}%, 익절: {self.take_profit_percent}%")
    
    async def start_monitoring(self):
        """매도 모니터링 시작"""
        if not self.sell_settings["enabled"]:
            self.logger.info("매도 모니터링이 비활성화되어 있습니다.")
            return
        
        self.logger.info("매도 모니터링 시작...")
        
        while True:
            try:
                await self.check_holdings_for_sell()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"매도 모니터링 오류: {e}")
                await asyncio.sleep(5)
    
    async def check_holdings_for_sell(self):
        """보유 종목 매도 조건 확인"""
        try:
            # API 호출 제한 확인
            current_time = time.time()
            if current_time - self.last_api_call < self.min_api_interval:
                self.logger.debug("API 호출 제한으로 인한 대기 중...")
                return
            
            # 계좌 정보 조회
            account_info = self.kiwoom_client.get_account_info()
            if not account_info:
                self.logger.warning("계좌 정보 조회 실패")
                return
            
            # API 호출 시간 업데이트
            self.last_api_call = current_time
            
            # 보유 종목 정보 추출
            holdings = self._extract_holdings(account_info)
            if not holdings:
                self.logger.info("보유 종목이 없습니다.")
                return
            
            self.logger.info(f"보유 종목 {len(holdings)}개 모니터링 중...")
            
            # 각 보유 종목에 대해 매도 조건 확인
            for stock_code, holding in holdings.items():
                await self._check_single_stock(stock_code, holding)
                
        except Exception as e:
            self.logger.error(f"보유 종목 확인 중 오류: {e}")
    
    def _extract_holdings(self, account_info: Dict) -> Dict[str, Dict]:
        """계좌 정보에서 보유 종목 추출"""
        holdings = {}
        
        try:
            # acnt_evlt_remn_indv_tot 필드에서 보유 종목 정보 추출
            if "acnt_evlt_remn_indv_tot" in account_info:
                for stock in account_info["acnt_evlt_remn_indv_tot"]:
                    stock_code = stock.get("stk_cd", "")
                    if stock_code and stock_code.startswith("A"):  # A로 시작하는 종목코드
                        # A 제거하여 실제 종목코드 추출
                        actual_code = stock_code[1:]
                        
                        holdings[actual_code] = {
                            "stock_name": stock.get("stk_nm", ""),
                            "quantity": int(stock.get("rmnd_qty", "0")),
                            "purchase_price": int(stock.get("pur_pric", "0")),
                            "current_price": int(stock.get("cur_prc", "0")),
                            "profit_loss": int(stock.get("evltv_prft", "0")),
                            "profit_rate": float(stock.get("prft_rt", "0")) / 100,  # 퍼센트를 소수로 변환
                            "purchase_amount": int(stock.get("pur_amt", "0"))
                        }
            
            return holdings
            
        except Exception as e:
            self.logger.error(f"보유 종목 추출 중 오류: {e}")
            return {}
    
    async def _check_single_stock(self, stock_code: str, holding: Dict):
        """단일 종목 매도 조건 확인"""
        try:
            stock_name = holding["stock_name"]
            profit_rate = holding["profit_rate"]
            quantity = holding["quantity"]
            purchase_price = holding["purchase_price"]
            current_price = holding["current_price"]
            
            # 최소 보유 시간 확인
            if not self._check_min_hold_time(stock_code):
                return
            
            # 손절 조건 확인
            if profit_rate <= self.stop_loss_percent / 100:
                self.logger.warning(f"손절 조건 감지! {stock_name}({stock_code}) - 수익률: {profit_rate*100:.2f}%")
                await self._execute_sell_order(stock_code, stock_name, quantity, "손절")
                return
            
            # 익절 조건 확인
            if profit_rate >= self.take_profit_percent / 100:
                self.logger.info(f"익절 조건 감지! {stock_name}({stock_code}) - 수익률: {profit_rate*100:.2f}%")
                await self._execute_sell_order(stock_code, stock_name, quantity, "익절")
                return
            
            # 수익률 로그 (디버깅용)
            if abs(profit_rate) > 0.01:  # 1% 이상 손익이 있을 때만 로그
                self.logger.debug(f"{stock_name}({stock_code}) - 수익률: {profit_rate*100:.2f}%")
                
        except Exception as e:
            self.logger.error(f"종목 {stock_code} 확인 중 오류: {e}")
    
    def _check_min_hold_time(self, stock_code: str) -> bool:
        """최소 보유 시간 확인 (현재 비활성화)"""
        # min_hold_time = self.sell_settings.get("min_hold_time", 0)
        # 최소 보유 시간 기능이 주석 처리되어 있으므로 항상 True 반환
        return True
    
    async def _execute_sell_order(self, stock_code: str, stock_name: str, quantity: int, reason: str):
        """매도 주문 실행"""
        try:
            self.logger.info(f"매도 주문 실행: {stock_name}({stock_code}) {quantity}주 - 사유: {reason}")
            
            # 매도 주문 실행
            result = self.kiwoom_client.place_order(
                stock_code=stock_code,
                order_type="매도",
                quantity=quantity,
                price=0  # 시장가 매도
            )
            
            if result:
                # DB에 매도 주문 내역 저장
                order_data = {
                    'order_id': f"SELL_{datetime.now().timestamp()}",
                    'order_type': 'SELL',
                    'quantity': quantity,
                    'price': 0,  # 시장가 매도
                    'status': 'PENDING',
                    'created_at': datetime.now()
                }
                self.db_manager.save_order(stock_code, order_data)
                
                self.logger.info(f"매도 주문 성공: {stock_name}({stock_code}) - {reason}")
            else:
                self.logger.error(f"매도 주문 실패: {stock_name}({stock_code}) - {reason}")
                
        except Exception as e:
            self.logger.error(f"매도 주문 실행 중 오류: {e}")
    
    def update_holdings(self, new_holdings: Dict[str, Dict]):
        """보유 종목 정보 업데이트"""
        self.holdings = new_holdings
    
    def get_holdings_summary(self) -> Dict:
        """보유 종목 요약 정보"""
        if not self.holdings:
            return {"total_stocks": 0, "total_value": 0, "total_profit": 0}
        
        total_value = 0
        total_profit = 0
        
        for holding in self.holdings.values():
            total_value += holding.get("purchase_amount", 0)
            total_profit += holding.get("profit_loss", 0)
        
        return {
            "total_stocks": len(self.holdings),
            "total_value": total_value,
            "total_profit": total_profit,
            "holdings": self.holdings
        } 