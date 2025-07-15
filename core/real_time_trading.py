"""
# 스윙 트레이딩 체크리스트

## 매수 전 확인사항

### 1. 시장 국면 ✅
- [ ] 코스피 지수가 20일선 위에 있는가?
- [ ] 전반적인 시장 분위기가 긍정적인가?

### 2. 추세 확인 ✅
- [ ] 5일선 > 20일선 > 60일선 정배열인가?
- [ ] 주가가 상승 추세에 있는가?
- [ ] 눌림목에서 반등하는가? (20일선 3% 이내)

### 3. 거래량 확인 ✅
- [ ] 평균 대비 거래량이 120% 이상인가?
- [ ] 장대양봉이 거래량과 함께 나왔는가?
- [ ] 거래량이 지속적으로 증가하는가?

### 4. 기술적 지표 ✅
- [ ] 20일선 위로 돌파했는가?
- [ ] RSI가 과매도에서 반등하는가?
- [ ] MACD가 상승 신호를 보이는가?

### 5. 기본적 재료 ✅
- [ ] 기업 실적이 개선되고 있는가?
- [ ] 긍정적인 뉴스나 재료가 있는가?
- [ ] 섹터 전망이 좋은가?

## 매수 실행

### 포지션 사이징
- [ ] 종목당 투자 금액: 200만원
- [ ] 최대 보유 종목: 3개
- [ ] 총 투자 비중: 60% 이하

### 매수 시점
- [ ] 눌림목에서 반등 시작 시
- [ ] 거래량 동반 돌파 시
- [ ] 장대양봉 출현 시

## 매도 조건

### 손절 (-8%)
- [ ] 매수 근거가 훼손되었는가?
- [ ] -8% 손절선에 도달했는가?
- [ ] 중요 지지선을 이탈했는가?

### 익절 (+20%)
- [ ] 목표 수익률 +20%에 도달했는가?
- [ ] 의미 있는 저항선에 도달했는가?
- [ ] 상승 추세가 약화되었는가?

### 트레일링 스탑 (-10%)
- [ ] 고점 대비 -10% 하락했는가?
- [ ] 수익이 있는 상태에서 추세 이탈했는가?

### 보유 기간 초과 (14일)
- [ ] 14일이 지났는가?
- [ ] 목표 수익률에 도달하지 못했는가?

## 일일 점검사항

### 포트폴리오 관리
- [ ] 보유 종목들의 수익률 확인
- [ ] 손절/익절 조건 체크
- [ ] 새로운 매수 기회 스캔

### 리스크 관리
- [ ] 전체 포트폴리오 수익률 확인
- [ ] 개별 종목 리스크 평가
- [ ] 시장 상황 재평가

## 주간 점검사항

### 성과 분석
- [ ] 주간 수익률 계산
- [ ] 승률 및 손익비 확인
- [ ] 전략별 성과 분석

### 전략 조정
- [ ] 시장 상황에 따른 전략 수정
- [ ] 매수/매도 조건 조정
- [ ] 포지션 사이징 재검토

## 월간 점검사항

### 종합 성과
- [ ] 월간 수익률 및 MDD 계산
- [ ] 샤프 비율 등 위험조정수익률 확인
- [ ] 벤치마크 대비 성과 비교

### 전략 개선
- [ ] 성공/실패 케이스 분석
- [ ] 전략 파라미터 최적화
- [ ] 새로운 전략 요소 추가 검토

## 주의사항

### 금지사항
- [ ] 감정적 매매 금지
- [ ] 손절 미루기 금지
- [ ] 익절 미루기 금지
- [ ] 과도한 레버리지 금지

### 필수 원칙
- [ ] 기계적 실행 원칙
- [ ] 리스크 관리 우선
- [ ] 분산 투자 원칙
- [ ] 장기적 관점 유지
"""
"""
# 스윙 트레이딩 전략 가이드

## 개요
단타의 한계를 극복하고 더 안정적인 수익을 추구하는 스윙 트레이딩 전략으로 전환했습니다.

## 핵심 변경사항

### 1. 보유 기간 확장
- **기존**: 2시간 (단타)
- **변경**: 14일 (스윙 트레이딩)
- **이유**: 추세 추종을 통한 안정적인 수익 추구

### 2. 손절/익절 기준 조정
- **손절**: -2% → -8% (더 큰 변동성 허용)
- **익절**: +5% → +20% (더 큰 수익 목표)
- **트레일링 스탑**: -3% → -10% (추세 추종 강화)

### 3. 포지션 사이징
- **종목당 투자 금액**: 100만원 → 200만원
- **최대 보유 종목**: 2개 → 3개

## 전략 구성

### 전략1: EDA 기반 거래량 급증 전략
- **목적**: 시초가 갭과 거래량 급증을 통한 단기 모멘텀 포착
- **조건**:
  - 시초가 갭 0.25% 이상
  - 9시 거래량 40,000주 이상
  - 20일선 아래에서 시작

### 전략2: 추세 추종 전략 (스윙 트레이딩 핵심)
- **목적**: 정배열과 눌림목을 통한 추세 추종
- **조건**:
  - 정배열 확인 (5일선 > 20일선 > 60일선)
  - 20일선 3% 이내 눌림목
  - 거래량 120% 이상 증가

### 전략3: 돌파 전략
- **목적**: 장대양봉과 거래량 급증을 통한 돌파 포착
- **조건**:
  - 전일 대비 3% 이상 상승
  - 거래량 200% 이상 급증
  - 20일선 위로 돌파

## 리스크 관리

### 1. 손절 원칙
- **매수 근거 훼손**: 설정한 조건이 깨지면 즉시 손절
- **가격 기준**: -8% 손절로 큰 변동성 허용
- **지지선 이탈**: 중요 지지선 하향 이탈 시 손절

### 2. 익절 원칙
- **목표 수익률**: +20% 목표로 큰 수익 추구
- **저항선 도달**: 의미 있는 저항선 도달 시 익절
- **추세 이탈**: 상승 추세 약화 신호 시 익절
- **분할 매도**: 목표가 도달 시 2-3회 분할 매도

### 3. 포지션 관리
- **최대 보유 기간**: 14일로 제한
- **트레일링 스탑**: 고점 대비 -10%로 수익 보호
- **일일 손실 제한**: 없음 (스윙 트레이딩 특성상)

## 백테스트 설정

### 기간 설정
- **시작일**: 2024-01-01
- **종료일**: 2024-12-31
- **테스트 종목**: 100개

### 성과 지표
- **총 수익률**: 목표 20% 이상
- **승률**: 목표 60% 이상
- **최대 낙폭**: 15% 이하
- **샤프 비율**: 1.0 이상

## 실행 방법

```bash
python core/backtest.py
```

## 주의사항

1. **시장 국면 필터**: 코스피 20일선 위에서만 매매
2. **거래량 확인**: 모든 전략에서 거래량 조건 필수
3. **기계적 실행**: 감정 배제하고 설정된 조건에 따라 실행
4. **분산 투자**: 최대 3개 종목으로 리스크 분산

## 성공 요인

1. **추세 추종**: 상승 추세에 올라타는 것이 핵심
2. **거래량 확인**: 의미 있는 거래량 동반 필수
3. **기계적 실행**: 감정적 판단 배제
4. **리스크 관리**: 명확한 손절/익절 원칙

## 향후 개선 방향

1. **섹터 분석**: 유망 섹터 선별 로직 추가
2. **재료 분석**: 기업 실적, 뉴스 등 기본적 분석 추가
3. **옵션 활용**: 헤지 전략으로 리스크 관리 강화
4. **AI 모델**: 머신러닝을 통한 신호 정확도 향상 
"""
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 1. 데이터 구조 정의
# ============================================================================
class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class StockData:
    """실시간 주식 데이터"""
    code: str
    name: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    volume_ratio: float
    price_change: float
    price_change_pct: float
    timestamp: datetime

@dataclass
class Order:
    """주문 정보"""
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: float
    status: OrderStatus
    timestamp: datetime
    filled_price: Optional[float] = None
    filled_quantity: int = 0

# ============================================================================
# 2. 실시간 데이터 수집기
# ============================================================================
class RealTimeDataCollector:
    """실시간 데이터 수집 및 처리"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8080"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.stock_data_cache = {}  # {stock_code: StockData}
        self.data_history = {}  # {stock_code: [StockData]}
        self.max_history_size = 1000
        
    async def connect(self):
        """WebSocket 연결"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            logger.info(f"WebSocket 연결 성공: {self.websocket_url}")
            return True
        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {e}")
            return False
    
    async def subscribe_stocks(self, stock_codes: List[str]):
        """주식 구독"""
        if not self.websocket:
            logger.error("WebSocket이 연결되지 않았습니다.")
            return False
        
        subscribe_message = {
            "type": "subscribe",
            "stocks": stock_codes
        }
        
        try:
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"주식 구독 요청: {stock_codes}")
            return True
        except Exception as e:
            logger.error(f"구독 요청 실패: {e}")
            return False
    
    async def process_message(self, message: str):
        """실시간 메시지 처리"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "stock_data":
                stock_data = self._parse_stock_data(data)
                if stock_data:
                    self._update_cache(stock_data)
                    await self._process_strategy_signals(stock_data)
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
    
    def _parse_stock_data(self, data: Dict) -> Optional[StockData]:
        """주식 데이터 파싱"""
        try:
            return StockData(
                code=data.get("code"),
                name=data.get("name", ""),
                current_price=float(data.get("price", 0)),
                open_price=float(data.get("open", 0)),
                high_price=float(data.get("high", 0)),
                low_price=float(data.get("low", 0)),
                volume=int(data.get("volume", 0)),
                volume_ratio=float(data.get("volume_ratio", 0)),
                price_change=float(data.get("price_change", 0)),
                price_change_pct=float(data.get("price_change_pct", 0)),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
            )
        except Exception as e:
            logger.error(f"데이터 파싱 실패: {e}")
            return None
    
    def _update_cache(self, stock_data: StockData):
        """캐시 업데이트"""
        self.stock_data_cache[stock_data.code] = stock_data
        
        # 히스토리 업데이트
        if stock_data.code not in self.data_history:
            self.data_history[stock_data.code] = []
        
        self.data_history[stock_data.code].append(stock_data)
        
        # 히스토리 크기 제한
        if len(self.data_history[stock_data.code]) > self.max_history_size:
            self.data_history[stock_data.code].pop(0)
    
    async def _process_strategy_signals(self, stock_data: StockData):
        """전략 신호 처리"""
        # 여기서 백테스트의 전략 함수들을 실시간으로 적용
        signals = await self._check_strategies(stock_data)
        
        if signals:
            logger.info(f"매매 신호 감지: {stock_data.code} - {signals}")
            # 주문 매니저에 신호 전달
            if hasattr(self, 'order_manager'):
                await self.order_manager.process_signals(stock_data, signals)
    
    async def _check_strategies(self, stock_data: StockData) -> List[Dict]:
        """전략 체크 (백테스트 로직 적용)"""
        signals = []
        
        # 최근 데이터로 DataFrame 생성
        if stock_data.code in self.data_history:
            recent_data = self.data_history[stock_data.code][-20:]  # 최근 20개 데이터
            
            # DataFrame으로 변환
            df_data = []
            for data in recent_data:
                df_data.append({
                    'datetime': data.timestamp,
                    'open': data.open_price,
                    'high': data.high_price,
                    'low': data.low_price,
                    'close': data.current_price,
                    'volume': data.volume,
                    'volume_ratio': data.volume_ratio
                })
            
            if len(df_data) >= 20:
                df = pd.DataFrame(df_data)
                
                # 이동평균 계산
                df['ma5'] = df['close'].rolling(window=5).mean()
                df['ma20'] = df['close'].rolling(window=20).mean()
                
                # 전략 체크 (백테스트 로직 재사용)
                from backtest import check_strategy_1, check_strategy_2
                
                strategy1_score = check_strategy_1(df)
                strategy2_score = check_strategy_2(df)
                
                if strategy1_score is not None:
                    signals.append({
                        'strategy': 'Strategy1',
                        'score': strategy1_score,
                        'action': 'BUY'
                    })
                
                if strategy2_score is not None:
                    signals.append({
                        'strategy': 'Strategy2',
                        'score': strategy2_score,
                        'action': 'BUY'
                    })
        
        return signals
    
    async def start_listening(self):
        """실시간 데이터 수신 시작"""
        if not self.websocket:
            logger.error("WebSocket이 연결되지 않았습니다.")
            return
        
        try:
            async for message in self.websocket:
                await self.process_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결이 종료되었습니다.")
        except Exception as e:
            logger.error(f"데이터 수신 중 오류: {e}")

# ============================================================================
# 3. 주문 실행 매니저
# ============================================================================
class OrderManager:
    """주문 실행 및 관리"""
    
    def __init__(self, api_client=None):
        self.api_client = api_client
        self.orders = {}  # {order_id: Order}
        self.positions = {}  # {stock_code: {'quantity': int, 'avg_price': float}}
        self.cash = 10000000  # 초기 자본
        self.max_positions = 2
        self.position_size = 1000000
        
    async def process_signals(self, stock_data: StockData, signals: List[Dict]):
        """매매 신호 처리"""
        for signal in signals:
            if signal['action'] == 'BUY':
                await self._process_buy_signal(stock_data, signal)
            elif signal['action'] == 'SELL':
                await self._process_sell_signal(stock_data, signal)
    
    async def _process_buy_signal(self, stock_data: StockData, signal: Dict):
        """매수 신호 처리"""
        # 포지션 한도 체크
        if len(self.positions) >= self.max_positions:
            logger.info(f"포지션 한도 초과: {stock_data.code}")
            return
        
        # 이미 보유 중인지 체크
        if stock_data.code in self.positions:
            logger.info(f"이미 보유 중: {stock_data.code}")
            return
        
        # 주문 수량 계산
        quantity = int(self.position_size / stock_data.current_price)
        
        if quantity > 0:
            # 주문 실행
            order = await self._place_order(
                stock_code=stock_data.code,
                order_type=OrderType.BUY,
                quantity=quantity,
                price=stock_data.current_price
            )
            
            if order:
                logger.info(f"매수 주문 실행: {stock_data.code} {quantity}주 @ {stock_data.current_price}")
    
    async def _process_sell_signal(self, stock_data: StockData, signal: Dict):
        """매도 신호 처리"""
        if stock_data.code not in self.positions:
            return
        
        position = self.positions[stock_data.code]
        quantity = position['quantity']
        
        if quantity > 0:
            # 주문 실행
            order = await self._place_order(
                stock_code=stock_data.code,
                order_type=OrderType.SELL,
                quantity=quantity,
                price=stock_data.current_price
            )
            
            if order:
                logger.info(f"매도 주문 실행: {stock_data.code} {quantity}주 @ {stock_data.current_price}")
    
    async def _place_order(self, stock_code: str, order_type: OrderType, 
                          quantity: int, price: float) -> Optional[Order]:
        """주문 실행"""
        order_id = f"ORDER_{int(time.time() * 1000)}"
        
        order = Order(
            order_id=order_id,
            stock_code=stock_code,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING,
            timestamp=datetime.now()
        )
        
        # 실제 API 호출 (시뮬레이션)
        if self.api_client:
            success = await self.api_client.place_order(order)
            if success:
                order.status = OrderStatus.FILLED
                order.filled_price = price
                order.filled_quantity = quantity
                
                # 포지션 업데이트
                self._update_position(order)
                
                self.orders[order_id] = order
                return order
        else:
            # 시뮬레이션 모드
            order.status = OrderStatus.FILLED
            order.filled_price = price
            order.filled_quantity = quantity
            
            self._update_position(order)
            self.orders[order_id] = order
            return order
        
        return None
    
    def _update_position(self, order: Order):
        """포지션 업데이트"""
        if order.order_type == OrderType.BUY:
            if order.stock_code not in self.positions:
                self.positions[order.stock_code] = {
                    'quantity': 0,
                    'avg_price': 0
                }
            
            position = self.positions[order.stock_code]
            total_cost = position['quantity'] * position['avg_price'] + order.filled_quantity * order.filled_price
            total_quantity = position['quantity'] + order.filled_quantity
            
            if total_quantity > 0:
                position['avg_price'] = total_cost / total_quantity
                position['quantity'] = total_quantity
            
            self.cash -= order.filled_quantity * order.filled_price
        
        elif order.order_type == OrderType.SELL:
            if order.stock_code in self.positions:
                position = self.positions[order.stock_code]
                position['quantity'] -= order.filled_quantity
                
                if position['quantity'] <= 0:
                    del self.positions[order.stock_code]
                
                self.cash += order.filled_quantity * order.filled_price
    
    def get_portfolio_summary(self) -> Dict:
        """포트폴리오 요약"""
        total_value = self.cash
        positions_summary = {}
        
        for stock_code, position in self.positions.items():
            # 현재가 조회 (실제로는 실시간 데이터에서 가져와야 함)
            current_price = 0  # 실제 구현에서는 실시간 가격 사용
            position_value = position['quantity'] * current_price
            total_value += position_value
            
            positions_summary[stock_code] = {
                'quantity': position['quantity'],
                'avg_price': position['avg_price'],
                'current_price': current_price,
                'market_value': position_value,
                'unrealized_pnl': position_value - (position['quantity'] * position['avg_price'])
            }
        
        return {
            'cash': self.cash,
            'total_value': total_value,
            'positions': positions_summary,
            'total_positions': len(self.positions)
        }

# ============================================================================
# 4. 리스크 관리자
# ============================================================================
class RiskManager:
    """리스크 관리"""
    
    def __init__(self):
        self.max_daily_loss = -2.0  # 일일 최대 손실 비율
        self.max_position_size = 0.1  # 단일 포지션 최대 비율
        self.max_portfolio_risk = 0.05  # 포트폴리오 최대 리스크
        
    def check_position_risk(self, order: Order, portfolio_value: float) -> bool:
        """포지션 리스크 체크"""
        position_value = order.quantity * order.price
        position_ratio = position_value / portfolio_value
        
        return position_ratio <= self.max_position_size
    
    def check_daily_loss_limit(self, daily_pnl: float, initial_capital: float) -> bool:
        """일일 손실 한도 체크"""
        daily_loss_pct = daily_pnl / initial_capital * 100
        return daily_loss_pct >= self.max_daily_loss
    
    def calculate_position_size(self, stock_price: float, confidence: float, 
                              portfolio_value: float) -> int:
        """동적 포지션 사이징"""
        base_size = portfolio_value * self.max_position_size
        adjusted_size = base_size * confidence
        
        return int(adjusted_size / stock_price)

# ============================================================================
# 5. 실시간 거래 시스템
# ============================================================================
class RealTimeTradingSystem:
    """실시간 거래 시스템 메인 클래스"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8080"):
        self.data_collector = RealTimeDataCollector(websocket_url)
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        
        # 연결 설정
        self.data_collector.order_manager = self.order_manager
        
        # 모니터링
        self.performance_monitor = None  # PerformanceMonitor 인스턴스
        
    async def start(self, stock_codes: List[str]):
        """시스템 시작"""
        logger.info("실시간 거래 시스템 시작")
        
        # WebSocket 연결
        if not await self.data_collector.connect():
            logger.error("시스템 시작 실패: WebSocket 연결 실패")
            return False
        
        # 주식 구독
        if not await self.data_collector.subscribe_stocks(stock_codes):
            logger.error("시스템 시작 실패: 주식 구독 실패")
            return False
        
        # 실시간 데이터 수신 시작
        await self.data_collector.start_listening()
    
    async def stop(self):
        """시스템 종료"""
        logger.info("실시간 거래 시스템 종료")
        if self.data_collector.websocket:
            await self.data_collector.websocket.close()
    
    def get_system_status(self) -> Dict:
        """시스템 상태 조회"""
        portfolio = self.order_manager.get_portfolio_summary()
        
        return {
            'system_status': 'RUNNING',
            'portfolio': portfolio,
            'connected_stocks': list(self.data_collector.stock_data_cache.keys()),
            'total_orders': len(self.order_manager.orders)
        }

# ============================================================================
# 6. 시뮬레이션 WebSocket 서버 (테스트용)
# ============================================================================
class MockWebSocketServer:
    """테스트용 Mock WebSocket 서버"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.clients = set()
        self.stock_data = {
            "005930": {"price": 70000, "volume": 1000000},  # 삼성전자
            "000660": {"price": 50000, "volume": 500000},   # SK하이닉스
            "035420": {"price": 30000, "volume": 300000},   # NAVER
        }
    
    async def handle_client(self, websocket, path):
        """클라이언트 연결 처리"""
        self.clients.add(websocket)
        logger.info(f"클라이언트 연결: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data.get("type") == "subscribe":
                    # 구독 확인
                    response = {"type": "subscribed", "stocks": data.get("stocks", [])}
                    await websocket.send(json.dumps(response))
                    
                    # 실시간 데이터 전송 시작
                    asyncio.create_task(self._send_mock_data(websocket))
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"클라이언트 연결 해제: {websocket.remote_address}")
    
    async def _send_mock_data(self, websocket):
        """Mock 실시간 데이터 전송"""
        while True:
            try:
                for stock_code, data in self.stock_data.items():
                    # 가격 변동 시뮬레이션
                    price_change = np.random.normal(0, 0.001)  # 0.1% 변동
                    data["price"] *= (1 + price_change)
                    data["volume"] = int(data["volume"] * (1 + np.random.normal(0, 0.1)))
                    
                    message = {
                        "type": "stock_data",
                        "code": stock_code,
                        "price": data["price"],
                        "volume": data["volume"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(message))
                
                await asyncio.sleep(1)  # 1초 간격
                
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logger.error(f"Mock 데이터 전송 오류: {e}")
                break

# ============================================================================
# 7. 메인 실행
# ============================================================================
async def main():
    """메인 실행 함수"""
    # Mock 서버 시작
    server = MockWebSocketServer(8080)
    start_server = websockets.serve(server.handle_client, "localhost", 8080)
    
    # 실시간 거래 시스템 시작
    trading_system = RealTimeTradingSystem("ws://localhost:8080")
    
    # 테스트용 주식 코드
    test_stocks = ["005930", "000660", "035420"]
    
    try:
        # 서버 시작
        await start_server
        
        # 거래 시스템 시작
        await trading_system.start(test_stocks)
        
        # 시스템 상태 모니터링
        while True:
            status = trading_system.get_system_status()
            logger.info(f"시스템 상태: {status}")
            await asyncio.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("시스템 종료 요청")
        await trading_system.stop()

if __name__ == "__main__":
    asyncio.run(main()) 