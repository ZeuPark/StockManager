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
        
        # 주문 매니저 (선택적)
        self.order_manager = None
        
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
    
    def set_order_manager(self, order_manager):
        """주문 매니저 설정"""
        self.order_manager = order_manager
        logger.info("주문 매니저가 웹소켓 클라이언트에 연결되었습니다.")
    
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
            try:
                self.websocket = await asyncio.wait_for(
                    websockets.connect(ws_url),
                    timeout=self.websocket_config["connection_timeout"]
                )
            except asyncio.TimeoutError:
                raise Exception(f"웹소켓 연결 타임아웃 ({self.websocket_config['connection_timeout']}초)")
            except websockets.exceptions.InvalidURI:
                raise Exception(f"잘못된 웹소켓 URL: {ws_url}")
            except websockets.exceptions.ConnectionClosed:
                raise Exception("웹소켓 연결이 서버에 의해 거부되었습니다")
            except Exception as e:
                raise Exception(f"웹소켓 연결 실패: {e}")
            
            self.is_connected = True
            self.reconnect_attempts = 0
            self.last_heartbeat = time.time()
            
            logger.info("웹소켓 연결 성공")
            
            # 키움 API 로그인 메시지 전송
            try:
                login_message = {
                    'trnm': 'LOGIN',
                    'token': token
                }
                await self.websocket.send(json.dumps(login_message))
                logger.info("로그인 메시지 전송 완료")
            except Exception as e:
                logger.error(f"로그인 메시지 전송 실패: {e}")
                await self.disconnect()
                raise
            
            # 연결 콜백 호출
            if self.on_connect_callback:
                await self.on_connect_callback()
                
        except Exception as e:
            logger.error(f"웹소켓 연결 실패: {e}")
            self.is_connected = False
            if self.on_error_callback:
                await self.on_error_callback(e)
            raise
    
    async def disconnect(self):
        """웹소켓 연결 해제"""
        if self.websocket:
            self.is_connected = False
            
            await self.websocket.close()
            self.websocket = None
            
            logger.info("웹소켓 연결 해제")
            
            # 연결 해제 콜백 호출
            if self.on_disconnect_callback:
                await self.on_disconnect_callback()
    
    async def register_stock(self, stock_code: str):
        """주식 등록 (키움 API 형식)"""
        if not self.is_connected or not self.websocket:
            logger.warning(f"웹소켓이 연결되지 않아 주식 등록을 건너뜁니다: {stock_code}")
            return
        
        # 이미 등록된 종목인지 확인
        if stock_code in self.registered_stocks:
            logger.debug(f"이미 등록된 종목: {stock_code}")
            return
        
        try:
            # 키움 API 실시간 등록 메시지 형식
            register_msg = {
                "trnm": "REG",
                "grp_no": "1",
                "refresh": "1",
                "data": [{
                    "item": [stock_code],
                    "type": ["00"],  # 실시간 시세
                }]
            }
            
            await self.websocket.send(json.dumps(register_msg))
            self.registered_stocks.append(stock_code)
            
            logger.info(f"주식 등록: {stock_code}")
            
            # 등록 후 대기 시간 증가 (API 제한 방지)
            await asyncio.sleep(0.5)  # 1초 → 0.5초로 조정
            
        except Exception as e:
            logger.error(f"주식 등록 실패 ({stock_code}): {e}")
            # 연결 상태 재확인
            if not self.websocket or self.websocket.closed:
                self.is_connected = False
                logger.warning("웹소켓 연결이 끊어졌습니다.")
    
    async def unregister_stock(self, stock_code: str):
        """주식 등록 해제"""
        if not self.is_connected or not self.websocket:
            return
        
        try:
            # 키움 API 실시간 해제 메시지 형식
            unregister_msg = {
                "trnm": "REG",
                "grp_no": "1",
                "refresh": "1",
                "data": [{
                    "item": [stock_code],
                    "type": [""],  # 빈 타입으로 해제
                }]
            }
            
            await self.websocket.send(json.dumps(unregister_msg))
            
            if stock_code in self.registered_stocks:
                self.registered_stocks.remove(stock_code)
            
            logger.info(f"주식 등록 해제: {stock_code}")
        except Exception as e:
            logger.error(f"주식 등록 해제 실패 ({stock_code}): {e}")
            if not self.websocket or self.websocket.closed:
                self.is_connected = False
    
    async def _handle_stock_data(self, data: Dict[str, Any]):
        """주식 데이터 처리 (키움 API 형식)"""
        try:
            # 키움 API 실시간 데이터 형식에 맞춰 파싱
            stock_code = data.get("종목코드") or data.get("stock_code")
            if not stock_code:
                logger.warning(f"종목코드가 없는 데이터: {data}")
                return
            
            # 실시간 데이터 파싱 (키움 API 형식)
            current_price = float(data.get("현재가", 0))
            volume = int(data.get("거래량", 0))
            execution_strength = float(data.get("체결강도", 0))
            high_price = float(data.get("고가", current_price))
            low_price = float(data.get("저가", current_price))
            open_price = float(data.get("시가", current_price))
            prev_close = float(data.get("전일종가", current_price))
            
            # 추가 실시간 데이터
            bid_price = float(data.get("매수호가", 0))
            ask_price = float(data.get("매도호가", 0))
            bid_volume = int(data.get("매수호가수량", 0))
            ask_volume = int(data.get("매도호가수량", 0))
            
            # StockData 객체 생성
            stock_data = StockData(
                code=stock_code,
                current_price=current_price,
                volume=volume,
                execution_strength=execution_strength,
                high_price=high_price,
                low_price=low_price,
                open_price=open_price,
                prev_close=prev_close,
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
            )
            
            # 실시간 데이터 로깅 (디버그 레벨)
            logger.debug(f"실시간 데이터 수신: {stock_code} - 현재가: {current_price:,}원, 거래량: {volume:,}, 체결강도: {execution_strength:.2f}")
            
            # 익절/손절 조건 체크 (보유 종목인 경우)
            if self.order_manager:
                await self.order_manager.check_profit_loss(stock_data)
                # 거래량 포지션 손익 체크
                await self.order_manager.check_volume_position_profit_loss(stock_data)
            
            # 모멘텀 분석
            is_signal, results = self.momentum_analyzer.is_trading_signal(stock_data)
            
            if is_signal:
                logger.info(f"🚨 매매 신호 감지: {stock_code}")
                logger.info(f"   현재가: {current_price:,}원")
                logger.info(f"   거래량: {volume:,}")
                logger.info(f"   체결강도: {execution_strength:.2f}")
                
                # 조건별 상세 정보 로깅
                for condition_name, result in results.items():
                    if result.is_satisfied:
                        logger.info(f"   ✅ {result.description}: {result.current_value:.3f} >= {result.threshold}")
                
                # 주문 매니저를 통한 자동 주문 실행
                if self.order_manager:
                    try:
                        order = await self.order_manager.handle_trading_signal(stock_data, results)
                        if order:
                            logger.info(f"💰 자동 주문 실행 완료: {stock_code} - {order.order_type.value} {order.quantity}주")
                        else:
                            logger.info(f"⚠️ 자동 주문 실행 실패 또는 조건 불만족: {stock_code}")
                    except Exception as e:
                        logger.error(f"자동 주문 실행 중 오류: {e}")
                
                # 트레이딩 신호 콜백 호출
                if self.on_trading_signal_callback:
                    await self.on_trading_signal_callback(stock_data, results)
            
            # 조건 요약 로깅 (주기적으로)
            if stock_code in self.registered_stocks and len(self.registered_stocks) % 10 == 0:  # 10개 종목마다
                summary = self.momentum_analyzer.get_condition_summary(stock_code)
                if summary:
                    logger.debug(f"조건 분석 요약 - {stock_code}: {summary}")
            
        except Exception as e:
            logger.error(f"주식 데이터 처리 실패: {e}")
            logger.error(f"원본 데이터: {data}")
    
    async def _handle_message(self, message: str):
        """메시지 처리 (키움 API 형식)"""
        try:
            data = json.loads(message)
            trnm = data.get("trnm", "unknown")
            
            # 키움 API 메시지 타입별 핸들러 호출
            if trnm in self.message_handlers:
                await self.message_handlers[trnm](data)
            elif trnm == "LOGIN":
                if data.get("return_code") == 0:
                    logger.info("로그인 성공")
                else:
                    logger.error(f"로그인 실패: {data.get('return_msg')}")
                    await self.disconnect()
            elif trnm == "PING":
                # PING에 대한 PONG 응답
                await self.websocket.send(json.dumps(data))
                logger.debug("PING-PONG 응답")
            elif trnm == "REG":
                if data.get("return_code") == 0:
                    logger.info("실시간 등록 성공")
                else:
                    logger.error(f"실시간 등록 실패: {data.get('return_msg')}")
            elif trnm == "STOCK_DATA" or trnm == "체결" or trnm == "호가":
                # 실시간 주식 데이터 처리
                await self._handle_stock_data(data)
            elif trnm == "HEARTBEAT":
                logger.debug("하트비트 수신")
            elif trnm == "ERROR":
                logger.error(f"서버 에러: {data.get('message', 'Unknown error')}")
            else:
                # 알 수 없는 메시지 타입이지만 실시간 데이터일 가능성
                if any(key in data for key in ["종목코드", "stock_code", "현재가", "current_price"]):
                    logger.debug(f"실시간 데이터로 추정되는 메시지: {trnm}")
                    await self._handle_stock_data(data)
                else:
                    logger.warning(f"알 수 없는 메시지 타입: {trnm}")
                    logger.debug(f"메시지 내용: {data}")
                
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
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"웹소켓 클라이언트 실행 시도 {retry_count + 1}/{max_retries}")
                
                await self.connect()
                
                # 로그인 응답을 기다린 후 주식 등록
                login_success = await self._wait_for_login_response()
                if not login_success:
                    logger.error("로그인 실패")
                    break
                
                # 주식 등록 (API 제한 방지를 위해 간격 조정)
                if stock_codes:
                    logger.info(f"총 {len(stock_codes)}개 종목 등록 시작")
                    for i, stock_code in enumerate(stock_codes):
                        await self.register_stock(stock_code)
                        
                        # 5개 종목마다 추가 대기 (API 제한 방지)
                        if (i + 1) % 5 == 0:
                            logger.info(f"등록 진행률: {i + 1}/{len(stock_codes)} - 2초 대기")
                            await asyncio.sleep(2)  # 5초 → 2초로 조정
                        else:
                            # 개별 종목 등록 후 1초 대기
                            await asyncio.sleep(1)  # 2초 → 1초로 조정
                    
                    logger.info("모든 종목 등록 완료")
                
                # 메시지 수신 시작
                await self.listen()
                
                # 정상적으로 종료된 경우 루프 탈출
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"웹소켓 클라이언트 실행 실패 (시도 {retry_count}/{max_retries}): {e}")
                
                if self.on_error_callback:
                    await self.on_error_callback(e)
                
                if retry_count < max_retries:
                    wait_time = retry_count * 10  # 점진적으로 대기 시간 증가 (5초 → 10초)
                    logger.info(f"{wait_time}초 후 재시도합니다...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("최대 재시도 횟수 초과. 웹소켓 클라이언트를 종료합니다.")
                    break
            finally:
                await self.disconnect()
    
    async def _wait_for_login_response(self, timeout: int = 10) -> bool:
        """로그인 응답을 기다림"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                if not self.websocket:
                    return False
                
                try:
                    # 타임아웃을 짧게 설정하여 응답 대기
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=1.0
                    )
                    
                    data = json.loads(message)
                    trnm = data.get("trnm")
                    
                    if trnm == "LOGIN":
                        if data.get("return_code") == 0:
                            logger.info("로그인 성공 확인")
                            return True
                        else:
                            logger.error(f"로그인 실패: {data.get('return_msg')}")
                            return False
                    elif trnm == "PING":
                        # PING에 대한 PONG 응답
                        await self.websocket.send(json.dumps(data))
                        logger.debug("PING-PONG 응답")
                    else:
                        logger.debug(f"로그인 대기 중 다른 메시지 수신: {trnm}")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"로그인 응답 대기 중 오류: {e}")
                    return False
            
            logger.error("로그인 응답 타임아웃")
            return False
            
        except Exception as e:
            logger.error(f"로그인 응답 대기 실패: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        return {
            "is_connected": self.is_connected,
            "reconnect_attempts": self.reconnect_attempts,
            "registered_stocks": self.registered_stocks.copy(),
            "last_heartbeat": self.last_heartbeat,
            "websocket_config": self.websocket_config
        } 