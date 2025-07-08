#!/usr/bin/env python3
"""
Order Manager for Stock Manager
자동매매 주문 실행 및 관리
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from analysis.momentum_analyzer import StockData, ConditionResult
from analysis.volume_scanner import VolumeCandidate
from api.kiwoom_client import KiwoomClient
from config.settings import Settings
from database.database_manager import get_database_manager

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """주문 타입"""
    BUY = "매수"
    SELL = "매도"

class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "주문접수"
    PARTIAL_FILLED = "부분체결"
    FILLED = "전체체결"
    CANCELLED = "주문취소"
    REJECTED = "주문거부"

@dataclass
class Order:
    """주문 정보"""
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: float
    order_time: datetime
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: float = 0.0
    commission: float = 0.0
    tax: float = 0.0

@dataclass
class Position:
    """보유 포지션"""
    stock_code: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_update: datetime = None

class OrderManager:
    """자동매매 주문 관리자"""
    
    def __init__(self, settings: Settings, kiwoom_client: KiwoomClient):
        self.settings = settings
        self.kiwoom_client = kiwoom_client
        self.risk_management = settings.RISK_MANAGEMENT
        self.db_manager = get_database_manager()
        
        # 주문 및 포지션 관리
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        
        # 자동매매 설정
        self.auto_execute = settings.SYSTEM.get("auto_execute_orders", False)
        self.min_confidence = settings.SYSTEM.get("min_confidence", 0.7)
        
        # 거래량 스캐닝 자동매매 설정
        self.volume_auto_trade = settings.VOLUME_SCANNING.get("auto_trade_enabled", True)  # 기본값을 True로 변경
        self.volume_stop_loss = settings.VOLUME_SCANNING.get("stop_loss", 0.05)
        self.volume_take_profit = settings.VOLUME_SCANNING.get("take_profit", 0.15)
        self.volume_max_hold_time = settings.VOLUME_SCANNING.get("max_hold_time", 3600)
        
        # 거래량 스캐닝 포지션 관리
        self.volume_positions: Dict[str, Dict] = {}
        
        logger.info(f"OrderManager 초기화 완료 (자동매매: {self.auto_execute}, 거래량자동매매: {self.volume_auto_trade})")
    
    def calculate_order_quantity(self, stock_code: str, current_price: float) -> int:
        """주문 수량 계산 (리스크 관리) - 패턴 분석 기반 최적화"""
        try:
            # 계좌 잔고 조회
            balance = self.kiwoom_client.get_account_balance()
            available_cash = balance.get("available_cash", 0)
            
            # 최대 투자 금액 계산
            max_investment = min(
                available_cash * self.risk_management["position_size_ratio"],
                self.risk_management["max_per_stock"]
            )
            
            # 최소 거래 금액 체크 (패턴 분석 기반)
            if max_investment < self.risk_management["min_trade_amount"]:
                logger.warning(f"최소 거래 금액 부족: {max_investment:,}원 < {self.risk_management['min_trade_amount']:,}원")
                return 0
            
            # 최대 거래 금액 체크 (패턴 분석 기반)
            max_trade_amount = self.risk_management.get("max_trade_amount", float('inf'))
            if max_investment > max_trade_amount:
                max_investment = max_trade_amount
                logger.info(f"최대 거래 금액으로 제한: {max_investment:,}원")
            
            # 주문 수량 계산
            quantity = int(max_investment / current_price)
            
            # 최소 주문 수량 체크
            if quantity < self.risk_management["min_position_size"]:
                logger.warning(f"최소 주문 수량 부족: {quantity} < {self.risk_management['min_position_size']}")
                return 0
            
            # 최대 보유 수량 체크 (패턴 분석 기반)
            max_quantity = self.risk_management.get("max_quantity_per_stock", float('inf'))
            if quantity > max_quantity:
                quantity = max_quantity
                logger.info(f"최대 보유 수량으로 제한: {quantity}주")
            
            # 현재 보유 수량 체크
            current_position = self.positions.get(stock_code)
            if current_position and current_position.quantity > 0:
                total_quantity = current_position.quantity + quantity
                if total_quantity > max_quantity:
                    additional_quantity = max_quantity - current_position.quantity
                    if additional_quantity <= 0:
                        logger.warning(f"이미 최대 보유 수량 도달: {stock_code} ({current_position.quantity}주)")
                        return 0
                    quantity = additional_quantity
                    logger.info(f"추가 매수 수량 제한: {quantity}주")
            
            logger.info(f"주문 수량 계산: {stock_code} - {quantity}주 ({quantity * current_price:,}원)")
            return quantity
            
        except Exception as e:
            logger.error(f"주문 수량 계산 실패: {e}")
            return 0
    
    async def execute_buy_order(self, stock_data: StockData, confidence: float = 1.0) -> Optional[Order]:
        """
        매수 주문 실행 (모든 경로에서 10종목 제한 강제)
        """
        try:
            if not self.auto_execute:
                logger.info(f"자동매매 비활성화 - 매수 신호 무시: {stock_data.code}")
                return None
            if confidence < self.min_confidence:
                logger.info(f"신뢰도 부족 - 매수 신호 무시: {stock_data.code} (신뢰도: {confidence:.2f})")
                return None
            stock_code = stock_data.code
            current_price = stock_data.current_price
            quantity = self.calculate_order_quantity(stock_code, current_price)
            if quantity <= 0:
                return None
            # 10종목 제한 강제
            if not self.check_risk_limits(stock_code, OrderType.BUY, quantity, current_price):
                logger.warning(f"🚫 10종목 제한! 매수 차단: {stock_code}")
                return None
            # 매수 주문 실행
            logger.info(f"매수 주문 실행: {stock_code} - {quantity}주 @ {current_price:,}원")
            order_result = await self.kiwoom_client.place_order(
                stock_code=stock_code,
                order_type="매수",
                quantity=quantity,
                price=current_price
            )
            
            # 키움 API 주문 결과 판단 (return_code: 0이 성공)
            if order_result and order_result.get("return_code") == 0:
                # 주문 정보 저장
                order = Order(
                    order_id=order_result.get("ord_no", f"ORDER_{datetime.now().timestamp()}"),
                    stock_code=stock_code,
                    order_type=OrderType.BUY,
                    quantity=quantity,
                    price=current_price,
                    order_time=datetime.now()
                )
                
                # DB에 주문 내역 저장
                order_data = {
                    'order_id': order.order_id,
                    'order_type': 'BUY',
                    'quantity': quantity,
                    'price': current_price,
                    'status': 'PENDING',
                    'created_at': order.order_time
                }
                self.db_manager.save_order(stock_code, order_data)
                # === 거래 분석용 DB 저장 ===
                trade = {
                    'stock_code': stock_code,
                    'stock_name': getattr(stock_data, 'name', stock_code),
                    'buy_price': current_price,
                    'sell_price': None,
                    'quantity': quantity,
                    'buy_time': order.order_time,
                    'sell_time': None,
                    'profit_rate': None,
                    'profit_amount': None,
                    'result': None
                }
                trade_id = self.db_manager.save_trade(trade)
                # 매수 시점 조건 저장
                cond = {
                    'volume_ratio': getattr(stock_data, 'volume_ratio', None),
                    'trade_value': getattr(stock_data, 'trade_value', None),
                    'execution_strength': getattr(stock_data, 'execution_strength', None),
                    'price_change': getattr(stock_data, 'price_change', None),
                    'market_cap': getattr(stock_data, 'market_cap', None)
                }
                if trade_id > 0:
                    self.db_manager.save_trade_condition(trade_id, cond)
                # === END ===
                self.orders[stock_code] = order
                self.daily_trades += 1
                
                logger.info(f"✅ 매수 주문 성공: {stock_code} - 주문ID: {order.order_id}")
                return order
            else:
                logger.error(f"❌ 매수 주문 실패: {stock_code} - {order_result}")
                return None
                
        except Exception as e:
            logger.error(f"매수 주문 실행 실패: {e}")
            return None
    
    async def execute_sell_order(self, stock_code: str, quantity: int, price: float, reason: str = "익절") -> Optional[Order]:
        """매도 주문 실행"""
        try:
            if not self.auto_execute:
                logger.info(f"자동매매 비활성화 - 매도 신호 무시: {stock_code}")
                return None
            
            # 리스크 한도 체크
            if not self.check_risk_limits(stock_code, OrderType.SELL, quantity, price):
                return None
            
            # 주문 실행
            logger.info(f"매도 주문 실행: {stock_code} - {quantity}주 @ {price:,}원 ({reason})")
            
            # 키움 API 주문 실행
            order_result = await self.kiwoom_client.place_order(
                stock_code=stock_code,
                order_type="매도",
                quantity=quantity,
                price=price
            )
            
            if order_result and order_result.get("success"):
                # 주문 정보 저장
                order = Order(
                    order_id=order_result.get("order_id", f"ORDER_{datetime.now().timestamp()}"),
                    stock_code=stock_code,
                    order_type=OrderType.SELL,
                    quantity=quantity,
                    price=price,
                    order_time=datetime.now()
                )
                
                # DB에 주문 내역 저장
                order_data = {
                    'order_id': order.order_id,
                    'order_type': 'SELL',
                    'quantity': quantity,
                    'price': price,
                    'status': 'PENDING',
                    'created_at': order.order_time
                }
                self.db_manager.save_order(stock_code, order_data)
                # === 거래 분석용 DB 업데이트 ===
                # 가장 최근 매수 거래 찾기
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, buy_price, buy_time, quantity FROM trades WHERE stock_code=? AND sell_price IS NULL ORDER BY buy_time DESC LIMIT 1", (stock_code,))
                    row = cursor.fetchone()
                    if row:
                        trade_id = row[0]
                        buy_price = row[1]
                        buy_time = row[2]
                        buy_qty = row[3]
                        profit_rate = ((price - buy_price) / buy_price) * 100 if buy_price else None
                        profit_amount = (price - buy_price) * quantity if buy_price else None
                        result = "익절" if profit_rate and profit_rate > 0 else "손절"
                        cursor.execute("""
                            UPDATE trades SET sell_price=?, sell_time=?, profit_rate=?, profit_amount=?, result=? WHERE id=?
                        """, (price, datetime.now(), profit_rate, profit_amount, result, trade_id))
                        conn.commit()
                # === END ===
                self.orders[stock_code] = order
                self.daily_trades += 1
                
                logger.info(f"매도 주문 성공: {stock_code} - 주문ID: {order.order_id}")
                return order
            else:
                logger.error(f"매도 주문 실패: {stock_code} - {order_result}")
                return None
                
        except Exception as e:
            logger.error(f"매도 주문 실행 실패: {e}")
            return None
    
    async def handle_trading_signal(self, stock_data: StockData, results: Dict[str, ConditionResult]) -> Optional[Order]:
        """매매 신호 처리"""
        try:
            # 조건 만족 개수 계산
            satisfied_conditions = sum(1 for result in results.values() if result.is_satisfied)
            total_conditions = len([c for c in self.settings.MOMENTUM_CONDITIONS.values() if c["enabled"]])
            
            # 신뢰도 계산 (만족한 조건 비율)
            confidence = satisfied_conditions / total_conditions if total_conditions > 0 else 0
            
            logger.info(f"매매 신호 처리: {stock_data.code} - 신뢰도: {confidence:.2f} ({satisfied_conditions}/{total_conditions})")
            
            # 매수 주문 실행
            return await self.execute_buy_order(stock_data, confidence)
            
        except Exception as e:
            logger.error(f"매매 신호 처리 실패: {e}")
            return None
    
    def update_position(self, stock_code: str, quantity: int, price: float, order_type: OrderType):
        """포지션 업데이트"""
        try:
            if stock_code not in self.positions:
                self.positions[stock_code] = Position(
                    stock_code=stock_code,
                    quantity=0,
                    avg_price=0.0,
                    current_price=price
                )
            
            position = self.positions[stock_code]
            
            if order_type == OrderType.BUY:
                # 매수: 평균단가 계산
                total_cost = position.quantity * position.avg_price + quantity * price
                position.quantity += quantity
                position.avg_price = total_cost / position.quantity if position.quantity > 0 else 0
            else:
                # 매도: 수익/손실 계산
                if position.quantity >= quantity:
                    realized_pnl = (price - position.avg_price) * quantity
                    position.realized_pnl += realized_pnl
                    position.quantity -= quantity
                    
                    if position.quantity == 0:
                        position.avg_price = 0.0
                    
                    # 일일 손익 업데이트
                    self.daily_pnl += realized_pnl
                    logger.info(f"실현 손익: {stock_code} - {realized_pnl:,.0f}원")
            
            position.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
    
    def get_position_summary(self) -> Dict[str, Any]:
        """포지션 요약"""
        total_positions = len([p for p in self.positions.values() if p.quantity > 0])
        total_value = sum(p.quantity * p.current_price for p in self.positions.values() if p.quantity > 0)
        
        return {
            "total_positions": total_positions,
            "total_value": total_value,
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "positions": [
                {
                    "stock_code": p.stock_code,
                    "quantity": p.quantity,
                    "avg_price": p.avg_price,
                    "current_price": p.current_price,
                    "unrealized_pnl": p.unrealized_pnl,
                    "realized_pnl": p.realized_pnl
                }
                for p in self.positions.values() if p.quantity > 0
            ]
        }
    
    async def check_profit_loss(self, stock_data: StockData):
        """익절/손절 조건 체크"""
        try:
            stock_code = stock_data.code
            current_price = stock_data.current_price
            
            if stock_code not in self.positions or self.positions[stock_code].quantity <= 0:
                return
            
            position = self.positions[stock_code]
            position.current_price = current_price
            
            # 수익률 계산
            profit_ratio = (current_price - position.avg_price) / position.avg_price
            position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
            
            logger.debug(f"수익률 체크: {stock_code} - 수익률: {profit_ratio:.2%}, 현재가: {current_price:,}원, 평균단가: {position.avg_price:,}원")
            
            # 익절 조건 체크
            if profit_ratio >= self.risk_management["take_profit"]:
                logger.info(f"🎯 익절 조건 만족: {stock_code} - 수익률: {profit_ratio:.2%} >= {self.risk_management['take_profit']:.2%}")
                await self.execute_sell_order(
                    stock_code=stock_code,
                    quantity=position.quantity,
                    price=current_price,
                    reason="익절"
                )
                return
            
            # 손절 조건 체크
            if profit_ratio <= -self.risk_management["stop_loss"]:
                logger.info(f"🛑 손절 조건 만족: {stock_code} - 손실률: {profit_ratio:.2%} <= -{self.risk_management['stop_loss']:.2%}")
                await self.execute_sell_order(
                    stock_code=stock_code,
                    quantity=position.quantity,
                    price=current_price,
                    reason="손절"
                )
                return
            
            # 부분 익절 조건 (선택적)
            if profit_ratio >= self.risk_management["take_profit"] * 0.5:  # 익절 기준의 50%에서 부분 익절
                # 보유 수량의 50%만 매도
                sell_quantity = position.quantity // 2
                if sell_quantity > 0:
                    logger.info(f"📈 부분 익절 실행: {stock_code} - 수익률: {profit_ratio:.2%}, 매도수량: {sell_quantity}주")
                    await self.execute_sell_order(
                        stock_code=stock_code,
                        quantity=sell_quantity,
                        price=current_price,
                        reason="부분익절"
                    )
            
        except Exception as e:
            logger.error(f"익절/손절 체크 실패: {e}")
    
    async def update_all_positions(self, stock_data_dict: Dict[str, StockData]):
        """모든 포지션의 익절/손절 조건 체크"""
        try:
            for stock_code, stock_data in stock_data_dict.items():
                await self.check_profit_loss(stock_data)
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
    
    def get_profit_loss_summary(self) -> Dict[str, Any]:
        """익절/손절 현황 요약"""
        summary = {
            "total_positions": 0,
            "total_unrealized_pnl": 0.0,
            "total_realized_pnl": 0.0,
            "positions": []
        }
        
        for position in self.positions.values():
            if position.quantity > 0:
                summary["total_positions"] += 1
                summary["total_unrealized_pnl"] += position.unrealized_pnl
                summary["total_realized_pnl"] += position.realized_pnl
                
                profit_ratio = (position.current_price - position.avg_price) / position.avg_price if position.avg_price > 0 else 0
                
                summary["positions"].append({
                    "stock_code": position.stock_code,
                    "quantity": position.quantity,
                    "avg_price": position.avg_price,
                    "current_price": position.current_price,
                    "profit_ratio": profit_ratio,
                    "unrealized_pnl": position.unrealized_pnl,
                    "realized_pnl": position.realized_pnl,
                    "take_profit_target": position.avg_price * (1 + self.risk_management["take_profit"]),
                    "stop_loss_target": position.avg_price * (1 - self.risk_management["stop_loss"])
                })
        
        return summary
    
    def handle_volume_candidate(self, candidate: VolumeCandidate) -> Optional[Order]:
        """
        거래량 급증 후보 종목 처리 (10종목 제한 강제)
        """
        try:
            if not self.volume_auto_trade:
                logger.info(f"거래량 자동매매 비활성화 - 후보 무시: {candidate.stock_code}")
                return None
            stock_code = candidate.stock_code
            current_price = candidate.current_price
            current_positions = len([p for p in self.positions.values() if p.quantity > 0])
            volume_positions = len(self.volume_positions)
            total_positions = current_positions + volume_positions
            logger.info(f"🔍 포지션 상태 체크 - {stock_code}: 일반:{current_positions}개, 거래량:{volume_positions}개, 총:{total_positions}개")
            if stock_code in self.volume_positions:
                logger.info(f"이미 거래량 포지션 보유 중: {stock_code}")
                return None
            quantity = self.calculate_order_quantity(stock_code, current_price)
            if quantity <= 0:
                logger.info(f"주문 수량 부족: {stock_code} - {quantity}")
                return None
            # 10종목 제한 강제
            if not self.check_risk_limits(stock_code, OrderType.BUY, quantity, current_price):
                logger.warning(f"🚫 10종목 제한! 매수 차단: {stock_code}")
                return None
            logger.info(f"✅ 리스크 한도 체크 통과: {stock_code} - 매수 진행")
            # 매수 주문 실행 (한 번 더 10종목 제한 강제)
            if not self.check_risk_limits(stock_code, OrderType.BUY, quantity, current_price):
                logger.warning(f"🚫 10종목 제한! 매수 차단(최종): {stock_code}")
                return None
            
            order_result = self.kiwoom_client.place_order(
                stock_code=stock_code,
                order_type="매수",
                quantity=quantity,
                price=current_price
            )
            
            # 키움 API 주문 결과 판단 (return_code: 0이 성공)
            if order_result and order_result.get("return_code") == 0:
                # 주문 정보 저장
                order = Order(
                    order_id=order_result.get("ord_no", f"VOL_ORDER_{datetime.now().timestamp()}"),
                    stock_code=stock_code,
                    order_type=OrderType.BUY,
                    quantity=quantity,
                    price=current_price,
                    order_time=datetime.now()
                )
                
                # DB에 주문 내역 저장
                order_data = {
                    'order_id': order.order_id,
                    'order_type': 'BUY',
                    'quantity': quantity,
                    'price': current_price,
                    'status': 'PENDING',
                    'created_at': order.order_time
                }
                self.db_manager.save_order(stock_code, order_data)
                
                self.orders[stock_code] = order
                self.daily_trades += 1
                
                # 거래량 포지션 정보 저장
                self.volume_positions[stock_code] = {
                    'buy_price': current_price,
                    'quantity': quantity,
                    'buy_time': datetime.now(),
                    'candidate_info': {
                        'volume_ratio': candidate.volume_ratio,
                        'score': candidate.score,
                        'is_breakout': candidate.is_breakout,
                        'ma_trend': candidate.ma_trend
                    }
                }
                
                logger.info(f"✅ 거래량 급증 매수 주문 성공: {stock_code} - 주문ID: {order.order_id}")
                return order
            else:
                logger.error(f"❌ 거래량 급증 매수 주문 실패: {stock_code} - {order_result}")
                return None
        except Exception as e:
            logger.error(f"거래량 후보 처리 실패: {e}")
            return None
    
    async def check_volume_position_profit_loss(self, stock_data: StockData):
        """거래량 포지션 손익 체크"""
        try:
            stock_code = stock_data.code
            current_price = stock_data.current_price
            
            if stock_code not in self.volume_positions:
                return
            
            position = self.volume_positions[stock_code]
            buy_price = position['buy_price']
            buy_time = position['buy_time']
            
            # 수익률 계산
            profit_rate = (current_price - buy_price) / buy_price
            
            # 보유 시간 계산
            hold_time = (datetime.now() - buy_time).total_seconds()
            
            # 손절 체크
            if profit_rate <= -self.volume_stop_loss:
                await self._close_volume_position(stock_code, current_price, "손절")
                return
            
            # 익절 체크
            if profit_rate >= self.volume_take_profit:
                await self._close_volume_position(stock_code, current_price, "익절")
                return
            
            # 최대 보유 시간 체크
            if hold_time >= self.volume_max_hold_time:
                await self._close_volume_position(stock_code, current_price, "시간초과")
                return
                
        except Exception as e:
            logger.error(f"거래량 포지션 손익 체크 실패: {e}")
    
    async def _close_volume_position(self, stock_code: str, sell_price: float, reason: str):
        """거래량 포지션 종료"""
        try:
            position = self.volume_positions[stock_code]
            quantity = position['quantity']
            
            logger.info(f"거래량 포지션 종료: {stock_code} - {reason}")
            logger.info(f"  매수가: {position['buy_price']:,}원, 매도가: {sell_price:,}원")
            
            # 매도 주문 실행
            order_result = await self.kiwoom_client.place_order(
                stock_code=stock_code,
                order_type="매도",
                quantity=quantity,
                price=sell_price
            )
            
            if order_result and order_result.get("success"):
                # 수익률 계산
                buy_price = position['buy_price']
                profit_rate = (sell_price - buy_price) / buy_price * 100
                
                # DB에 매도 주문 내역 저장
                order_data = {
                    'order_id': f"VOL_SELL_{datetime.now().timestamp()}",
                    'order_type': 'SELL',
                    'quantity': quantity,
                    'price': sell_price,
                    'status': 'PENDING',
                    'created_at': datetime.now()
                }
                self.db_manager.save_order(stock_code, order_data)
                
                logger.info(f"거래량 포지션 매도 성공: {stock_code} - 수익률: {profit_rate:.2f}%")
                
                # 포지션 제거
                del self.volume_positions[stock_code]
                
                # 일일 손익 업데이트
                self.daily_pnl += profit_rate
                
            else:
                logger.error(f"거래량 포지션 매도 실패: {stock_code}")
                
        except Exception as e:
            logger.error(f"거래량 포지션 종료 실패: {e}")
    
    def get_volume_positions_summary(self) -> Dict[str, Any]:
        """거래량 포지션 요약 반환"""
        return {
            "total_volume_positions": len(self.volume_positions),
            "volume_positions": [
                {
                    "stock_code": stock_code,
                    "buy_price": pos['buy_price'],
                    "quantity": pos['quantity'],
                    "buy_time": pos['buy_time'].isoformat(),
                    "candidate_info": pos['candidate_info']
                }
                for stock_code, pos in self.volume_positions.items()
            ]
        }
    
    def get_current_holdings(self) -> set:
        """현재 보유(매수) 종목 코드 집합 반환 (일반 포지션 + 거래량 포지션)"""
        regular_holdings = set([code for code, pos in self.positions.items() if pos.quantity > 0])
        volume_holdings = set(self.volume_positions.keys())
        return regular_holdings.union(volume_holdings)
    
    def get_position_count(self) -> int:
        """현재 보유 종목 수 반환 (일반 포지션 + 거래량 포지션)"""
        current_positions = len([p for p in self.positions.values() if p.quantity > 0])
        volume_positions = len(self.volume_positions)
        return current_positions + volume_positions
    
    def can_buy_new_stock(self) -> bool:
        """새 종목 매수 가능 여부 확인 (10종목 제한)"""
        current_count = self.get_position_count()
        max_positions = self.risk_management["max_positions"]
        return current_count < max_positions
    
    def get_position_limit_status(self) -> dict:
        """10종목 제한 상태 정보 반환"""
        current_count = self.get_position_count()
        current_positions = len([p for p in self.positions.values() if p.quantity > 0])
        volume_positions = len(self.volume_positions)
        max_positions = self.risk_management["max_positions"]
        
        return {
            "current_total": current_count,
            "current_positions": current_positions,
            "volume_positions": volume_positions,
            "max_positions": max_positions,
            "remaining_slots": max_positions - current_count,
            "can_buy_new": current_count < max_positions
        }

    def check_risk_limits(self, stock_code: str, order_type: OrderType, quantity: int, price: float) -> bool:
        """리스크 한도 체크 - 10종목 엄격 제한 + 주가 제한"""
        try:
            # 최대 보유 종목 수 체크 (10종목 엄격 제한)
            if order_type == OrderType.BUY:
                # 일반 포지션 + 거래량 포지션 모두 포함하여 체크
                current_positions = len([p for p in self.positions.values() if p.quantity > 0])
                volume_positions = len(self.volume_positions)
                total_positions = current_positions + volume_positions
                
                max_positions = self.risk_management["max_positions"]
                strict_limit = self.risk_management.get("strict_position_limit", False)
                
                logger.info(f"[리스크체크] 일반:{current_positions}, 거래량:{volume_positions}, 총:{total_positions} (최대:{max_positions})")
                
                # 현재 종목이 이미 보유 중인지 확인 (일반 포지션 + 거래량 포지션 모두 체크)
                current_position = self.positions.get(stock_code)
                volume_position = self.volume_positions.get(stock_code)
                is_new_stock = (not current_position or current_position.quantity == 0) and not volume_position
                
                if is_new_stock and total_positions >= max_positions:
                    logger.warning(f"🚫 10종목 제한 도달! 매수 불가: {stock_code} (현재 보유: {total_positions}개 - 일반:{current_positions}개, 거래량:{volume_positions}개)")
                    return False
                elif not is_new_stock and total_positions > max_positions:
                    logger.warning(f"🚫 10종목 초과! 매수 불가: {stock_code} (현재 보유: {total_positions}개 - 일반:{current_positions}개, 거래량:{volume_positions}개)")
                    return False
                
                if strict_limit and total_positions >= max_positions:
                    logger.info(f"📊 10종목 제한으로 인한 매수 제한: {stock_code} (현재 보유: {total_positions}개 - 일반:{current_positions}개, 거래량:{volume_positions}개)")
                    return False
                
                # 🚨 주가 제한 체크 (새로 추가)
                max_stock_price = getattr(self.settings, 'VOLUME_SCANNING', {}).get('max_stock_price', 50000)
                min_stock_price = getattr(self.settings, 'VOLUME_SCANNING', {}).get('min_stock_price', 1000)
                
                if price > max_stock_price:
                    logger.warning(f"🚫 주가 상한선 초과! 매수 불가: {stock_code} (현재가: {price:,}원, 상한선: {max_stock_price:,}원)")
                    return False
                
                if price < min_stock_price:
                    logger.warning(f"🚫 주가 하한선 미달! 매수 불가: {stock_code} (현재가: {price:,}원, 하한선: {min_stock_price:,}원)")
                    return False
            
            # 일일 손실 한도 체크
            if self.daily_pnl < -self.risk_management["max_daily_loss"]:
                logger.warning(f"일일 손실 한도 초과: {self.daily_pnl:.2f}% < -{self.risk_management['max_daily_loss']:.2f}%")
                return False
            
            # 동일 종목 중복 주문 체크
            if stock_code in self.orders:
                pending_order = self.orders[stock_code]
                if pending_order.status in [OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED]:
                    logger.warning(f"동일 종목 주문 대기 중: {stock_code}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"리스크 한도 체크 실패: {e}")
            return False
