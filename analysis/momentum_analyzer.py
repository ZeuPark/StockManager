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
    
    def check_volume_spike(self, stock_data: StockData) -> ConditionResult:
        """거래량 급증 조건 체크"""
        condition = self.conditions["volume_spike"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="volume_spike",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 전일 거래량 데이터가 필요 (실제로는 API에서 가져와야 함)
        # 여기서는 임시로 현재 거래량을 기준으로 체크
        volume_ratio = stock_data.volume / max(stock_data.volume * 0.8, 1)  # 임시 계산
        
        is_satisfied = volume_ratio >= condition["threshold"]
        
        return ConditionResult(
            condition_name="volume_spike",
            is_satisfied=is_satisfied,
            current_value=volume_ratio,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_execution_strength(self, stock_data: StockData) -> ConditionResult:
        """체결강도 조건 체크"""
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
        
        # 최근 N틱의 체결강도 체크
        recent_data = self.get_recent_data(stock_data.code, condition["consecutive_ticks"])
        if len(recent_data) < condition["consecutive_ticks"]:
            return ConditionResult(
                condition_name="execution_strength",
                is_satisfied=False,
                current_value=stock_data.execution_strength,
                threshold=condition["threshold"],
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 연속 틱에서 체결강도 조건 만족 여부 체크
        consecutive_satisfied = all(
            data.execution_strength >= condition["threshold"] 
            for data in recent_data
        )
        
        return ConditionResult(
            condition_name="execution_strength",
            is_satisfied=consecutive_satisfied,
            current_value=stock_data.execution_strength,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_price_breakout(self, stock_data: StockData) -> ConditionResult:
        """가격 돌파 조건 체크"""
        condition = self.conditions["price_breakout"]
        print(f"[DEBUG] price_breakout 시작: enabled={condition['enabled']}, breakout_ticks={condition['breakout_ticks']}")
        
        if not condition["enabled"]:
            print("[DEBUG] price_breakout 비활성화됨")
            return ConditionResult(
                condition_name="price_breakout",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 최근 N틱의 최고가 체크
        recent_data = self.get_recent_data(stock_data.code, condition["breakout_ticks"])
        print(f"[DEBUG] price_breakout: recent_data 개수={len(recent_data)}, 필요={condition['breakout_ticks']}")
        
        if len(recent_data) < condition["breakout_ticks"] or len(recent_data) <= 1:
            print(f"[DEBUG] price_breakout: 데이터 부족으로 early return (len={len(recent_data)})")
            return ConditionResult(
                condition_name="price_breakout",
                is_satisfied=False,
                current_value=stock_data.current_price,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 최고가 계산 (최근 데이터가 2개 이상일 때만 max 사용)
        if len(recent_data) > 1:
            recent_high = max(data.high_price for data in recent_data[:-1])  # 현재 틱 제외
        else:
            recent_high = stock_data.high_price
        breakout_price = recent_high
        
        # 돌파 여부 체크
        is_breakout = stock_data.current_price > breakout_price
        
        if is_breakout:
            # 돌파 후 상승률 체크
            rise_ratio = (stock_data.current_price - breakout_price) / breakout_price
            is_satisfied = rise_ratio >= condition["rise_threshold"]
        else:
            is_satisfied = False
            rise_ratio = 0
        
        # 디버깅 로그 추가
        print(f"[DEBUG] price_breakout: current={stock_data.current_price}, breakout={breakout_price}, rise_ratio={rise_ratio}, threshold={condition['rise_threshold']}, is_satisfied={is_satisfied}")
        
        return ConditionResult(
            condition_name="price_breakout",
            is_satisfied=is_satisfied,
            current_value=rise_ratio if is_breakout else 0,
            threshold=condition["rise_threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_price_momentum(self, stock_data: StockData) -> ConditionResult:
        """가격 모멘텀 조건 체크"""
        condition = self.conditions["price_momentum"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="price_momentum",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 최근 N틱의 가격 변동률 체크
        recent_data = self.get_recent_data(stock_data.code, condition["consecutive_ticks"])
        if len(recent_data) < condition["consecutive_ticks"]:
            return ConditionResult(
                condition_name="price_momentum",
                is_satisfied=False,
                current_value=stock_data.current_price,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 연속 틱에서 가격 변동률 조건 만족 여부 체크
        price_change = stock_data.current_price - stock_data.prev_close
        price_change_ratio = price_change / stock_data.prev_close
        consecutive_satisfied = all(
            price_change_ratio >= condition["threshold"] 
            for data in recent_data
        )
        
        return ConditionResult(
            condition_name="price_momentum",
            is_satisfied=consecutive_satisfied,
            current_value=price_change_ratio,
            threshold=condition["threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def check_volume_price_confirmation(self, stock_data: StockData) -> ConditionResult:
        """거래량-가격 동반 상승 조건 체크"""
        condition = self.conditions["volume_price_confirmation"]
        if not condition["enabled"]:
            return ConditionResult(
                condition_name="volume_price_confirmation",
                is_satisfied=False,
                current_value=0,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 최근 N틱의 거래량과 가격 변동률 체크
        recent_data = self.get_recent_data(stock_data.code, condition["consecutive_ticks"])
        if len(recent_data) < condition["consecutive_ticks"]:
            return ConditionResult(
                condition_name="volume_price_confirmation",
                is_satisfied=False,
                current_value=stock_data.current_price,
                threshold=0,
                description=condition["description"],
                timestamp=stock_data.timestamp
            )
        
        # 연속 틱에서 거래량과 가격 변동률 조건 만족 여부 체크
        price_change = stock_data.current_price - stock_data.prev_close
        price_change_ratio = price_change / stock_data.prev_close
        volume_change = stock_data.volume - stock_data.prev_close
        volume_change_ratio = volume_change / stock_data.prev_close
        consecutive_satisfied = all(
            price_change_ratio >= condition["price_threshold"] and
            volume_change_ratio >= condition["volume_threshold"]
            for data in recent_data
        )
        
        return ConditionResult(
            condition_name="volume_price_confirmation",
            is_satisfied=consecutive_satisfied,
            current_value=price_change_ratio,
            threshold=condition["price_threshold"],
            description=condition["description"],
            timestamp=stock_data.timestamp
        )
    
    def analyze_all_conditions(self, stock_data: StockData) -> Dict[str, ConditionResult]:
        """모든 조건을 분석"""
        # 데이터 히스토리에 추가
        self.add_stock_data(stock_data)
        
        results = {
            "volume_spike": self.check_volume_spike(stock_data),
            "execution_strength": self.check_execution_strength(stock_data),
            "price_breakout": self.check_price_breakout(stock_data),
            "price_momentum": self.check_price_momentum(stock_data),
            "volume_price_confirmation": self.check_volume_price_confirmation(stock_data)
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