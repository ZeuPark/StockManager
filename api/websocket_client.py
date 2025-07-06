import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import logging
import websockets
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import time
from dataclasses import dataclass

# Import with fallback
try:
    from analysis.momentum_analyzer import StockData, MomentumAnalyzer
except ImportError:
    # Fallback import
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "analysis"))
    from momentum_analyzer import StockData, MomentumAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class WebSocketMessage:
    """웹소켓 메시지 데이터 클래스"""
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    stock_code: Optional[str] = None

class WebSocketClient:
    """키움 웹소켓 클라이언트 클래스"""
    
    def __init__(self, settings, token_manager):
        self.settings = settings
        self.token_manager = token_manager
        self.websocket_config = settings.WEBSOCKET
        self.websocket = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.registered_stocks: List[str] = []
        self.message_handlers: Dict[str, Callable] = {}
        self.momentum_analyzer = MomentumAnalyzer(settings)
        
        # 콜백 함수들
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        self.on_trading_signal_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        # 하트비트 관련
        self.last_heartbeat = None
        self.heartbeat_task = None
        
    def set_callbacks(self, 
                     on_connect: Optional[Callable] = None,
                     on_disconnect: Optional[Callable] = None,
                     on_trading_signal: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """콜백 함수 설정"""
        self.on_connect_callback = on_connect
        self.on_disconnect_callback = on_disconnect
        self.on_trading_signal_callback = on_trading_signal
        self.on_error_callback = on_error
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """메시지 타입별 핸들러 등록"""
        self.message_handlers[message_type] = handler
    
    async def connect(self):
        """웹소켓 연결"""
        try:
            # 토큰 가져오기
            token = await self.token_manager.get_valid_token()
            if not token:
                raise Exception("유효한 토큰을 가져올 수 없습니다.")
            
            # 웹소켓 URL (키움 API 형식)
            ws_url = self.settings.KIWOOM_WEBSOCKET_URL
            
            logger.info(f"웹소켓 연결 시도: {ws_url}")
            
            # 웹소켓 연결
            self.websocket = await asyncio.wait_for(
                websockets.connect(ws_url),
                timeout=self.websocket_config["connection_timeout"]
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            self.last_heartbeat = time.time()
            
            logger.info("웹소켓 연결 성공")
            
            # 키움 API 로그인 메시지 전송
            login_message = {
                'trnm': 'LOGIN',
                'token': token
            }
            await self.websocket.send(json.dumps(login_message))
            logger.info("로그인 메시지 전송 완료")
            
            # 하트비트 시작
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 연결 콜백 호출
            if self.on_connect_callback:
                await self.on_connect_callback()
                
        except Exception as e:
            logger.error(f"웹소켓 연결 실패: {e}")
            if self.on_error_callback:
                await self.on_error_callback(e)
            raise
    
    async def disconnect(self):
        """웹소켓 연결 해제"""
        if self.websocket:
            self.is_connected = False
            
            # 하트비트 중지
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            await self.websocket.close()
            self.websocket = None
            
            logger.info("웹소켓 연결 해제")
            
            # 연결 해제 콜백 호출
            if self.on_disconnect_callback:
                await self.on_disconnect_callback()
    
    async def _heartbeat_loop(self):
        """하트비트 루프"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.websocket_config["heartbeat_interval"])
                
                if self.is_connected and self.websocket:
                    heartbeat_msg = {
                        "trnm": "HEARTBEAT",
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.websocket.send(json.dumps(heartbeat_msg))
                    self.last_heartbeat = time.time()
                    logger.debug("하트비트 전송")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"하트비트 전송 실패: {e}")
                break
    
    async def register_stock(self, stock_code: str):
        """주식 등록 (키움 API 형식)"""
        if not self.is_connected:
            raise Exception("웹소켓이 연결되지 않았습니다.")
        
        # 키움 API 주식 등록 메시지 형식
        register_msg = {
            "trnm": "STOCK_REGISTER",
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(register_msg))
        self.registered_stocks.append(stock_code)
        
        logger.info(f"주식 등록: {stock_code}")
    
    async def unregister_stock(self, stock_code: str):
        """주식 등록 해제"""
        if not self.is_connected:
            return
        
        unregister_msg = {
            "type": "unregister_stock",
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(unregister_msg))
        
        if stock_code in self.registered_stocks:
            self.registered_stocks.remove(stock_code)
        
        logger.info(f"주식 등록 해제: {stock_code}")
    
    async def _handle_stock_data(self, data: Dict[str, Any]):
        """주식 데이터 처리 (키움 API 형식)"""
        try:
            # 키움 API 주식 데이터 형식에 맞춰 StockData 객체 생성
            stock_data = StockData(
                code=data.get("종목코드") or data.get("stock_code"),
                current_price=float(data.get("현재가") or data.get("current_price", 0)),
                volume=int(data.get("거래량") or data.get("volume", 0)),
                execution_strength=float(data.get("체결강도") or data.get("execution_strength", 0)),
                high_price=float(data.get("고가") or data.get("high_price", 0)),
                low_price=float(data.get("저가") or data.get("low_price", 0)),
                open_price=float(data.get("시가") or data.get("open_price", 0)),
                prev_close=float(data.get("전일종가") or data.get("prev_close", 0)),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
            )
            
            # 모멘텀 분석
            is_signal, results = self.momentum_analyzer.is_trading_signal(stock_data)
            
            if is_signal and self.on_trading_signal_callback:
                await self.on_trading_signal_callback(stock_data, results)
            
            # 조건 요약 로깅 (디버그 레벨)
            summary = self.momentum_analyzer.get_condition_summary(stock_data.code)
            logger.debug(f"조건 분석 결과: {summary}")
            
        except Exception as e:
            logger.error(f"주식 데이터 처리 실패: {e}")
    
    async def _handle_message(self, message: str):
        """메시지 처리 (키움 API 형식)"""
        try:
            data = json.loads(message)
            trnm = data.get("trnm", "unknown")
            
            # 키움 API 메시지 타입별 핸들러 호출
            if trnm in self.message_handlers:
                await self.message_handlers[trnm](data)
            elif trnm == "STOCK_DATA":
                await self._handle_stock_data(data)
            elif trnm == "HEARTBEAT":
                logger.debug("하트비트 수신")
            elif trnm == "ERROR":
                logger.error(f"서버 에러: {data.get('message', 'Unknown error')}")
            elif trnm == "LOGIN_RESPONSE":
                logger.info("로그인 응답 수신")
            elif trnm == "LOGIN":
                logger.info("로그인 메시지 수신")
            else:
                logger.warning(f"알 수 없는 메시지 타입: {trnm}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
    
    async def listen(self):
        """메시지 수신 루프"""
        if not self.websocket:
            raise Exception("웹소켓이 연결되지 않았습니다.")
        
        try:
            async for message in self.websocket:
                await self._handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("웹소켓 연결이 종료되었습니다.")
            self.is_connected = False
        except Exception as e:
            logger.error(f"메시지 수신 중 오류: {e}")
            self.is_connected = False
        finally:
            # 연결 해제 콜백 호출
            if self.on_disconnect_callback:
                await self.on_disconnect_callback()
    
    async def reconnect(self):
        """재연결 시도"""
        if self.reconnect_attempts >= self.websocket_config["max_reconnect_attempts"]:
            logger.error("최대 재연결 시도 횟수 초과")
            return False
        
        self.reconnect_attempts += 1
        logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.websocket_config['max_reconnect_attempts']}")
        
        try:
            await self.disconnect()
            await asyncio.sleep(self.websocket_config["reconnect_interval"])
            await self.connect()
            
            # 등록된 주식들 재등록
            for stock_code in self.registered_stocks:
                await self.register_stock(stock_code)
            
            logger.info("재연결 성공")
            return True
            
        except Exception as e:
            logger.error(f"재연결 실패: {e}")
            return False
    
    async def run(self, stock_codes: List[str] = None):
        """웹소켓 클라이언트 실행"""
        try:
            await self.connect()
            
            # 주식 등록
            if stock_codes:
                for stock_code in stock_codes:
                    await self.register_stock(stock_code)
            
            # 메시지 수신 시작
            await self.listen()
            
        except Exception as e:
            logger.error(f"웹소켓 클라이언트 실행 실패: {e}")
            if self.on_error_callback:
                await self.on_error_callback(e)
        finally:
            await self.disconnect()
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        return {
            "is_connected": self.is_connected,
            "reconnect_attempts": self.reconnect_attempts,
            "registered_stocks": self.registered_stocks.copy(),
            "last_heartbeat": self.last_heartbeat,
            "websocket_config": self.websocket_config
        } 