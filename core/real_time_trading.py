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