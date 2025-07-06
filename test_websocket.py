#!/usr/bin/env python3
"""
웹소켓 클라이언트 테스트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from utils.token_manager import TokenManager
from api.websocket_client import WebSocketClient

async def on_connect():
    print("✅ 웹소켓 연결됨")

async def on_disconnect():
    print("❌ 웹소켓 연결 해제됨")

async def on_trading_signal(stock_data, results):
    print(f"📈 트레이딩 신호 감지: {stock_data.code}")
    print(f"   현재가: {stock_data.current_price}")
    print(f"   결과: {results}")

async def on_error(error):
    print(f"❌ 에러 발생: {error}")

async def main():
    print("🔗 웹소켓 클라이언트 테스트 시작...")
    
    # 설정 및 토큰 매니저 초기화
    settings = Settings()
    token_manager = TokenManager(settings)
    
    # 웹소켓 클라이언트 생성
    ws_client = WebSocketClient(settings, token_manager)
    
    # 콜백 설정
    ws_client.set_callbacks(
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        on_trading_signal=on_trading_signal,
        on_error=on_error
    )
    
    # 테스트할 주식 코드들
    test_stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    try:
        print(f"📊 테스트 주식: {test_stocks}")
        
        # 웹소켓 클라이언트 실행
        await ws_client.run(test_stocks)
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
    finally:
        await ws_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 