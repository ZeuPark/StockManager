import logging
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

from analysis.momentum_analyzer import StockData, ConditionResult

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """매매 신호 데이터 클래스"""
    stock_code: str
    signal_type: str  # "buy", "sell"
    price: float
    quantity: int
    timestamp: datetime
    conditions: Dict[str, ConditionResult]
    confidence: float  # 0.0 ~ 1.0
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

class SignalProcessor:
    """매매 신호 처리 클래스"""
    
    def __init__(self, settings):
        self.settings = settings
        self.risk_config = settings.RISK_MANAGEMENT
        self.trading_config = settings.TRADING_STRATEGY
        
        # 콜백 함수들
        self.on_signal_callback: Optional[Callable] = None
        self.on_order_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        # 신호 히스토리
        self.signal_history: List[TradingSignal] = []
        self.max_history_size = 1000
        
        # 중복 신호 방지
        self.recent_signals: Dict[str, datetime] = {}
        self.signal_cooldown = 300  # 5분 쿨다운
        
    def set_callbacks(self,
                     on_signal: Optional[Callable] = None,
                     on_order: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """콜백 함수 설정"""
        self.on_signal_callback = on_signal
        self.on_order_callback = on_order
        self.on_error_callback = on_error
    
    def calculate_confidence(self, conditions: Dict[str, ConditionResult]) -> float:
        """신호 신뢰도 계산"""
        if not conditions:
            return 0.0
        
        # 각 조건의 만족 정도를 계산
        confidence_scores = []
        
        for condition_name, result in conditions.items():
            if not result.is_satisfied:
                continue
                
            # 조건별 신뢰도 계산
            if condition_name == "volume_spike":
                # 거래량이 기준보다 클수록 높은 신뢰도
                volume_confidence = min(result.current_value / result.threshold, 3.0) / 3.0
                confidence_scores.append(volume_confidence)
                
            elif condition_name == "execution_strength":
                # 체결강도가 높을수록 높은 신뢰도
                strength_confidence = min(result.current_value / result.threshold, 2.0) / 2.0
                confidence_scores.append(strength_confidence)
                
            elif condition_name == "price_breakout":
                # 돌파 후 상승률이 클수록 높은 신뢰도
                breakout_confidence = min(result.current_value / result.threshold, 2.0) / 2.0
                confidence_scores.append(breakout_confidence)
        
        if not confidence_scores:
            return 0.0
        
        # 평균 신뢰도 반환
        return sum(confidence_scores) / len(confidence_scores)
    
    def check_risk_limits(self, stock_data: StockData, signal_type: str) -> bool:
        """리스크 한도 체크"""
        try:
            # 최대 손실 한도 체크
            if hasattr(self, 'current_loss') and self.current_loss >= self.risk_config["max_daily_loss"]:
                logger.warning(f"일일 최대 손실 한도 도달: {self.current_loss}")
                return False
            
            # 최대 포지션 수 체크
            if hasattr(self, 'current_positions') and len(self.current_positions) >= self.risk_config["max_positions"]:
                logger.warning(f"최대 포지션 수 한도 도달: {len(self.current_positions)}")
                return False
            
            # 주식별 최대 투자 금액 체크
            max_investment = self.risk_config["max_per_stock"]
            if stock_data.current_price * self.calculate_position_size(stock_data) > max_investment:
                logger.warning(f"주식별 최대 투자 금액 초과: {stock_data.code}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"리스크 한도 체크 실패: {e}")
            return False
    
    def calculate_position_size(self, stock_data: StockData) -> int:
        """포지션 크기 계산"""
        try:
            # 계좌 잔고의 일정 비율로 계산
            account_balance = getattr(self, 'account_balance', 10000000)  # 기본값 1천만원
            position_ratio = self.risk_config["position_size_ratio"]
            
            # 주식 가격으로 나누어 수량 계산
            position_value = account_balance * position_ratio
            quantity = int(position_value / stock_data.current_price)
            
            # 최소/최대 수량 제한
            min_quantity = self.risk_config["min_position_size"]
            max_quantity = self.risk_config["max_position_size"]
            
            quantity = max(min_quantity, min(quantity, max_quantity))
            
            return quantity
            
        except Exception as e:
            logger.error(f"포지션 크기 계산 실패: {e}")
            return self.risk_config["min_position_size"]
    
    def is_duplicate_signal(self, stock_code: str) -> bool:
        """중복 신호 체크"""
        if stock_code not in self.recent_signals:
            return False
        
        last_signal_time = self.recent_signals[stock_code]
        time_diff = (datetime.now() - last_signal_time).total_seconds()
        
        return time_diff < self.signal_cooldown
    
    async def process_trading_signal(self, stock_data: StockData, conditions: Dict[str, ConditionResult]):
        """매매 신호 처리"""
        try:
            # 중복 신호 체크
            if self.is_duplicate_signal(stock_data.code):
                logger.info(f"중복 신호 무시: {stock_data.code}")
                return
            
            # 신뢰도 계산
            confidence = self.calculate_confidence(conditions)
            
            # 최소 신뢰도 체크
            min_confidence = self.trading_config.get("min_confidence", 0.7)
            if confidence < min_confidence:
                logger.info(f"신뢰도 부족: {stock_data.code} (신뢰도: {confidence:.3f})")
                return
            
            # 리스크 한도 체크
            if not self.check_risk_limits(stock_data, "buy"):
                logger.warning(f"리스크 한도 초과: {stock_data.code}")
                return
            
            # 매수 신호 생성
            quantity = self.calculate_position_size(stock_data)
            
            signal = TradingSignal(
                stock_code=stock_data.code,
                signal_type="buy",
                price=stock_data.current_price,
                quantity=quantity,
                timestamp=datetime.now(),
                conditions=conditions,
                confidence=confidence
            )
            
            # 신호 히스토리에 추가
            self.signal_history.append(signal)
            if len(self.signal_history) > self.max_history_size:
                self.signal_history.pop(0)
            
            # 중복 신호 방지를 위한 시간 기록
            self.recent_signals[stock_data.code] = datetime.now()
            
            logger.info(f"매매 신호 생성: {stock_data.code} - 신뢰도: {confidence:.3f}")
            
            # 신호 콜백 호출
            if self.on_signal_callback:
                await self.on_signal_callback(signal)
            
            # 자동 주문 실행 (설정에 따라)
            if self.settings.get("auto_execute_orders", False):
                await self.execute_order(signal)
                
        except Exception as e:
            logger.error(f"매매 신호 처리 실패: {e}")
            if self.on_error_callback:
                await self.on_error_callback(e)
    
    async def execute_order(self, signal: TradingSignal):
        """주문 실행"""
        try:
            logger.info(f"주문 실행: {signal.stock_code} - {signal.quantity}주 @ {signal.price}")
            
            # 여기에 실제 주문 API 호출 로직 추가
            # order_result = await self.order_api.place_order(signal)
            
            # 주문 콜백 호출
            if self.on_order_callback:
                await self.on_order_callback(signal, None)  # order_result 대신 None
                
        except Exception as e:
            logger.error(f"주문 실행 실패: {e}")
            if self.on_error_callback:
                await self.on_error_callback(e)
    
    def get_signal_summary(self) -> Dict[str, any]:
        """신호 요약 정보"""
        if not self.signal_history:
            return {}
        
        recent_signals = self.signal_history[-10:]  # 최근 10개 신호
        
        summary = {
            "total_signals": len(self.signal_history),
            "recent_signals": len(recent_signals),
            "average_confidence": sum(s.confidence for s in recent_signals) / len(recent_signals),
            "signal_types": {},
            "top_stocks": {}
        }
        
        # 신호 타입별 통계
        for signal in recent_signals:
            signal_type = signal.signal_type
            if signal_type not in summary["signal_types"]:
                summary["signal_types"][signal_type] = 0
            summary["signal_types"][signal_type] += 1
        
        # 상위 주식별 통계
        stock_counts = {}
        for signal in recent_signals:
            if signal.stock_code not in stock_counts:
                stock_counts[signal.stock_code] = 0
            stock_counts[signal.stock_code] += 1
        
        summary["top_stocks"] = dict(sorted(stock_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return summary
    
    def update_account_info(self, balance: float, positions: List[Dict]):
        """계좌 정보 업데이트"""
        self.account_balance = balance
        self.current_positions = positions
        
        # 현재 손실 계산 (간단한 예시)
        self.current_loss = 0.0  # 실제로는 포지션별 손익 계산 필요 