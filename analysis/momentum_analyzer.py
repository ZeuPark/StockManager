import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class StockData:
    """주식 데이터를 저장하는 클래스"""
    code: str
    current_price: float
    volume: int
    execution_strength: float
    high_price: float
    low_price: float
    open_price: float
    prev_close: float
    timestamp: datetime
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

@dataclass
class ConditionResult:
    """조건 체크 결과를 저장하는 클래스"""
    condition_name: str
    is_satisfied: bool
    current_value: float
    threshold: float
    description: str
    timestamp: datetime

class MomentumAnalyzer:
    """모멘텀 조건을 분석하는 클래스"""
    
    def __init__(self, settings):
        self.settings = settings
        self.conditions = settings.MOMENTUM_CONDITIONS
        self.stock_data_history: Dict[str, List[StockData]] = {}
        self.max_history_size = 100  # 최대 저장할 데이터 개수
        
    def add_stock_data(self, stock_data: StockData):
        """주식 데이터를 히스토리에 추가"""
        if stock_data.code not in self.stock_data_history:
            self.stock_data_history[stock_data.code] = []
        
        history = self.stock_data_history[stock_data.code]
        history.append(stock_data)
        
        # 최대 개수 제한
        if len(history) > self.max_history_size:
            history.pop(0)
    
    def get_recent_data(self, code: str, count: int = 10) -> List[StockData]:
        """최근 데이터 가져오기"""
        if code not in self.stock_data_history:
            return []
        return self.stock_data_history[code][-count:]
    
    def check_volume_requirement(self, stock_data: StockData) -> ConditionResult:
        """거래량 필수 조건 체크 (오늘 누적 거래량 ≥ 전일 총 거래량)"""
        condition = self.conditions["volume_requirement"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="volume_requirement",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 오늘 누적 거래량 vs 전일 총 거래량 비교
        # 실제로는 API에서 전일 거래량 데이터를 가져와야 함
        today_volume = stock_data.volume  # 현재 누적 거래량
        prev_day_volume = stock_data.prev_volume if hasattr(stock_data, 'prev_volume') else today_volume * 0.8
        
        volume_ratio = today_volume / max(prev_day_volume, 1)
        is_satisfied = volume_ratio >= condition["threshold"]
        
        return ConditionResult(
            condition_name="volume_requirement",
            is_satisfied=is_satisfied,
            current_value=volume_ratio,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_execution_strength(self, stock_data: StockData) -> ConditionResult:
        """체결강도 조건 체크 (≥ 150%)"""
        condition = self.conditions["execution_strength"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="execution_strength",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 체결강도 = 매수 체결량 / 매도 체결량 × 100
        execution_strength = stock_data.execution_strength
        is_satisfied = execution_strength >= condition["threshold"]
        
        return ConditionResult(
            condition_name="execution_strength",
            is_satisfied=is_satisfied,
            current_value=execution_strength,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_price_change(self, stock_data: StockData) -> ConditionResult:
        """등락률 조건 체크 (≥ +2%)"""
        condition = self.conditions["price_change"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="price_change",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 등락률 = (현재가 - 전일종가) / 전일종가 × 100
        price_change_ratio = (stock_data.current_price - stock_data.prev_close) / stock_data.prev_close
        is_satisfied = price_change_ratio >= condition["threshold"]
        
        return ConditionResult(
            condition_name="price_change",
            is_satisfied=is_satisfied,
            current_value=price_change_ratio,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_trade_value(self, stock_data: StockData) -> ConditionResult:
        """1분 거래대금 조건 체크 (≥ 1억원)"""
        condition = self.conditions["trade_value"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="trade_value",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 1분 거래대금 = 1분 거래량 × 현재가
        one_min_volume = stock_data.volume  # 실제로는 1분 거래량을 가져와야 함
        trade_value = one_min_volume * stock_data.current_price
        is_satisfied = trade_value >= condition["threshold"]
        
        return ConditionResult(
            condition_name="trade_value",
            is_satisfied=is_satisfied,
            current_value=trade_value,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_opening_price_rise(self, stock_data: StockData) -> ConditionResult:
        """시가 대비 상승 조건 체크"""
        condition = self.conditions["opening_price_rise"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="opening_price_rise",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 조건: 시가 > 전일종가 AND 현재가 > 시가
        opening_price = stock_data.open_price
        prev_close = stock_data.prev_close
        current_price = stock_data.current_price
        
        is_satisfied = (opening_price > prev_close) and (current_price > opening_price)
        
        return ConditionResult(
            condition_name="opening_price_rise",
            is_satisfied=is_satisfied,
            current_value=current_price - opening_price,
            threshold=0,
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_price_movement(self, stock_data: StockData) -> ConditionResult:
        """시세 변동 조건 체크 (최소 호가 단위 이상)"""
        condition = self.conditions["price_movement"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="price_movement",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 최근 데이터에서 가격 변동 확인
        recent_data = self.get_recent_data(stock_data.code, 2)
        if len(recent_data) < 2:
            return ConditionResult(
                condition_name="price_movement",
                is_satisfied=False,
                current_value=0,
                threshold=condition["min_tick_change"],
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 이전 가격과 현재 가격의 차이
        prev_price = recent_data[-2].current_price
        current_price = stock_data.current_price
        price_change = abs(current_price - prev_price)
        
        # 최소 호가 단위 (보통 1원 이상)
        min_tick_change = condition["min_tick_change"]
        is_satisfied = price_change >= min_tick_change
        
        return ConditionResult(
            condition_name="price_movement",
            is_satisfied=is_satisfied,
            current_value=price_change,
            threshold=min_tick_change,
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def analyze_all_conditions(self, stock_data: StockData) -> Dict[str, ConditionResult]:
        """모든 조건을 분석"""
        # 데이터 히스토리에 추가
        self.add_stock_data(stock_data)
        
        results = {
            "volume_requirement": self.check_volume_requirement(stock_data),
            "execution_strength": self.check_execution_strength(stock_data),
            "price_change": self.check_price_change(stock_data),
            "trade_value": self.check_trade_value(stock_data),
            "opening_price_rise": self.check_opening_price_rise(stock_data),
            "price_movement": self.check_price_movement(stock_data)
        }
        
        return results
    
    def is_trading_signal(self, stock_data: StockData) -> Tuple[bool, Dict[str, ConditionResult]]:
        """모든 조건이 만족되는지 체크하여 매매 신호 생성"""
        results = self.analyze_all_conditions(stock_data)
        
        # 모든 활성화된 조건이 만족되는지 체크
        all_satisfied = all(
            result.is_satisfied 
            for result in results.values() 
            if self.conditions[result.condition_name]["enabled"]
        )
        
        if all_satisfied:
            logger.info(f"매매 신호 발생: {stock_data.code} - 모든 조건 만족")
            for condition_name, result in results.items():
                if result.is_satisfied:
                    logger.info(f"  - {result.description}: {result.current_value:.3f} >= {result.threshold}")
        
        return all_satisfied, results
    
    def get_condition_summary(self, stock_code: str) -> Dict[str, any]:
        """조건 만족 현황 요약"""
        if stock_code not in self.stock_data_history:
            return {}
        
        latest_data = self.stock_data_history[stock_code][-1]
        results = self.analyze_all_conditions(latest_data)
        
        summary = {
            "stock_code": stock_code,
            "current_price": latest_data.current_price,
            "timestamp": latest_data.timestamp,
            "conditions": {}
        }
        
        for condition_name, result in results.items():
            summary["conditions"][condition_name] = {
                "satisfied": result.is_satisfied,
                "current_value": result.current_value,
                "threshold": result.threshold,
                "description": result.description
            }
        
        return summary 