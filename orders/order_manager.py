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
from api.kiwoom_client import KiwoomClient
from config.settings import Settings

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
        
        # 주문 및 포지션 관리
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        
        # 자동매매 설정
        self.auto_execute = settings.SYSTEM.get("auto_execute_orders", False)
        self.min_confidence = settings.SYSTEM.get("min_confidence", 0.7)
        
        logger.info(f"OrderManager 초기화 완료 (자동매매: {self.auto_execute})")
    
    def calculate_order_quantity(self, stock_code: str, current_price: float) -> int:
        """주문 수량 계산 (리스크 관리)"""
        try:
            # 계좌 잔고 조회
            balance = self.kiwoom_client.get_account_balance()
            available_cash = balance.get("available_cash", 0)
            
            # 최대 투자 금액 계산
            max_investment = min(
                available_cash * self.risk_management["position_size_ratio"],
                self.risk_management["max_per_stock"]
            )
            
            # 최소 거래 금액 체크
            if max_investment < self.risk_management["min_trade_amount"]:
                logger.warning(f"최소 거래 금액 부족: {max_investment:,}원 < {self.risk_management['min_trade_amount']:,}원")
                return 0
            
            # 주문 수량 계산
            quantity = int(max_investment / current_price)
            
            # 최소 주문 수량 체크
            if quantity < self.risk_management["min_position_size"]:
                logger.warning(f"최소 주문 수량 부족: {quantity} < {self.risk_management['min_position_size']}")
                return 0
            
            logger.info(f"주문 수량 계산: {stock_code} - {quantity}주 ({quantity * current_price:,}원)")
            return quantity
            
        except Exception as e:
            logger.error(f"주문 수량 계산 실패: {e}")
            return 0
    
    def check_risk_limits(self, stock_code: str, order_type: OrderType, quantity: int, price: float) -> bool:
        """리스크 한도 체크"""
        try:
            # 최대 보유 종목 수 체크
            if order_type == OrderType.BUY:
                current_positions = len([p for p in self.positions.values() if p.quantity > 0])
                if current_positions >= self.risk_management["max_positions"]:
                    logger.warning(f"최대 보유 종목 수 초과: {current_positions} >= {self.risk_management['max_positions']}")
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
    
    async def execute_buy_order(self, stock_data: StockData, confidence: float = 1.0) -> Optional[Order]:
        """매수 주문 실행"""
        try:
            if not self.auto_execute:
                logger.info(f"자동매매 비활성화 - 매수 신호 무시: {stock_data.code}")
                return None
            
            if confidence < self.min_confidence:
                logger.info(f"신뢰도 부족 - 매수 신호 무시: {stock_data.code} (신뢰도: {confidence:.2f})")
                return None
            
            stock_code = stock_data.code
            current_price = stock_data.current_price
            
            # 주문 수량 계산
            quantity = self.calculate_order_quantity(stock_code, current_price)
            if quantity <= 0:
                return None
            
            # 리스크 한도 체크
            if not self.check_risk_limits(stock_code, OrderType.BUY, quantity, current_price):
                return None
            
            # 주문 실행
            logger.info(f"매수 주문 실행: {stock_code} - {quantity}주 @ {current_price:,}원")
            
            # 키움 API 주문 실행
            order_result = await self.kiwoom_client.place_order(
                stock_code=stock_code,
                order_type="매수",
                quantity=quantity,
                price=current_price
            )
            
            if order_result and order_result.get("success"):
                # 주문 정보 저장
                order = Order(
                    order_id=order_result.get("order_id", f"ORDER_{datetime.now().timestamp()}"),
                    stock_code=stock_code,
                    order_type=OrderType.BUY,
                    quantity=quantity,
                    price=current_price,
                    order_time=datetime.now()
                )
                
                self.orders[stock_code] = order
                self.daily_trades += 1
                
                logger.info(f"매수 주문 성공: {stock_code} - 주문ID: {order.order_id}")
                return order
            else:
                logger.error(f"매수 주문 실패: {stock_code} - {order_result}")
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
