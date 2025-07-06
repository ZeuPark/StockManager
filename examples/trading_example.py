#!/usr/bin/env python3
"""
Trading System Example
트레이딩 시스템 사용 예제
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import TradingSystem
from config.settings import Settings
from analysis.momentum_analyzer import StockData
from datetime import datetime

async def example_trading_signal_handler(signal):
    """매매 신호 처리 예제"""
    print(f"🚀 매매 신호 발생!")
    print(f"   종목: {signal.stock_code}")
    print(f"   타입: {signal.signal_type}")
    print(f"   가격: {signal.price:,}원")
    print(f"   수량: {signal.quantity}주")
    print(f"   신뢰도: {signal.confidence:.3f}")
    print(f"   시간: {signal.timestamp}")
    print()

async def example_order_handler(signal, order_result):
    """주문 실행 처리 예제"""
    print(f"📋 주문 실행됨!")
    print(f"   종목: {signal.stock_code}")
    print(f"   수량: {signal.quantity}주")
    print(f"   가격: {signal.price:,}원")
    print()

async def example_websocket_connect():
    """웹소켓 연결 처리 예제"""
    print("🔗 웹소켓 연결됨")
    print()

async def example_websocket_disconnect():
    """웹소켓 연결 해제 처리 예제"""
    print("❌ 웹소켓 연결 해제됨")
    print()

async def example_error_handler(error):
    """에러 처리 예제"""
    print(f"⚠️  에러 발생: {error}")
    print()

async def run_simulation_example():
    """시뮬레이션 모드 예제"""
    print("=== 시뮬레이션 모드 예제 ===")
    
    # 트레이딩 시스템 생성
    trading_system = TradingSystem(mode="simulation")
    
    # 콜백 함수 설정
    trading_system.signal_processor.set_callbacks(
        on_signal=example_trading_signal_handler,
        on_order=example_order_handler,
        on_error=example_error_handler
    )
    
    trading_system.websocket_client.set_callbacks(
        on_connect=example_websocket_connect,
        on_disconnect=example_websocket_disconnect,
        on_error=example_error_handler
    )
    
    # 테스트용 주식 코드들
    test_stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    try:
        # 시스템 초기화
        await trading_system.initialize()
        print("✅ 시스템 초기화 완료")
        
        # 시스템 상태 확인
        status = trading_system.get_status()
        print(f"📊 시스템 상태: {status['is_running']}")
        print(f"🎯 모니터링 종목: {status['settings']['target_stocks']}")
        print()
        
        # 설정 정보 출력
        settings = trading_system.settings
        print("=== 현재 설정 ===")
        print(f"거래량 급증 기준: {settings.MOMENTUM_CONDITIONS['volume_spike']['threshold']}")
        print(f"체결강도 기준: {settings.MOMENTUM_CONDITIONS['execution_strength']['threshold']}")
        print(f"가격 돌파 틱: {settings.MOMENTUM_CONDITIONS['price_breakout']['breakout_ticks']}")
        print(f"최소 신뢰도: {settings.SYSTEM['min_confidence']}")
        print(f"자동 주문: {settings.SYSTEM['auto_execute_orders']}")
        print()
        
        # 테스트 데이터로 신호 생성 시뮬레이션
        print("=== 신호 생성 테스트 ===")
        test_data = StockData(
            code="005930",
            current_price=75000,
            volume=1000000,
            execution_strength=2.0,
            high_price=75500,
            low_price=74500,
            open_price=74800,
            prev_close=74700,
            timestamp=datetime.now()
        )
        
        # 모멘텀 분석
        is_signal, results = trading_system.momentum_analyzer.is_trading_signal(test_data)
        
        print(f"신호 발생 여부: {is_signal}")
        for condition_name, result in results.items():
            print(f"  {result.description}: {result.is_satisfied} (값: {result.current_value:.3f})")
        print()
        
        # 신호 처리
        if is_signal:
            await trading_system.signal_processor.process_trading_signal(test_data, results)
        
        print("✅ 시뮬레이션 완료")
        
    except Exception as e:
        print(f"❌ 시뮬레이션 실패: {e}")

async def run_production_example():
    """실제 거래 모드 예제"""
    print("=== 실제 거래 모드 예제 ===")
    print("⚠️  실제 거래 모드는 실제 주문이 발생할 수 있습니다!")
    print()
    
    # 사용자 확인
    confirm = input("실제 거래 모드로 실행하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("실제 거래 모드 실행을 취소했습니다.")
        return
    
    # 트레이딩 시스템 생성 (production 모드로 제대로 설정)
    trading_system = TradingSystem(mode="production")
    # 환경을 production으로 강제 설정
    trading_system.settings.ENVIRONMENT = "production"
    
    # 콜백 함수 설정
    trading_system.signal_processor.set_callbacks(
        on_signal=example_trading_signal_handler,
        on_order=example_order_handler,
        on_error=example_error_handler
    )
    
    trading_system.websocket_client.set_callbacks(
        on_connect=example_websocket_connect,
        on_disconnect=example_websocket_disconnect,
        on_error=example_error_handler
    )
    
    try:
        # 시스템 실행 (실제 웹소켓 연결)
        print("🔄 실제 거래 시스템 시작...")
        await trading_system.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 실제 거래 시스템 실패: {e}")

def show_settings_example():
    """설정 변경 예제"""
    print("=== 설정 변경 예제 ===")
    
    # 설정 인스턴스 생성
    settings = Settings("simulation")
    
    print("현재 모멘텀 조건:")
    for condition_name, condition in settings.MOMENTUM_CONDITIONS.items():
        print(f"  {condition['description']}: {condition['enabled']}")
        for key, value in condition.items():
            if key != "description" and key != "enabled":
                print(f"    {key}: {value}")
    
    print("\n설정 변경 방법:")
    print("1. config/settings.py 파일에서 직접 수정")
    print("2. 코드에서 동적으로 변경:")
    print("   settings.MOMENTUM_CONDITIONS['volume_spike']['threshold'] = 1.5")
    print("   settings.SYSTEM['auto_execute_orders'] = True")
    print()

async def main():
    """메인 함수"""
    print("🎯 Stock Manager Trading System Example")
    print("=" * 50)
    
    while True:
        print("\n실행할 예제를 선택하세요:")
        print("1. 시뮬레이션 모드 예제")
        print("2. 실제 거래 모드 예제")
        print("3. 설정 변경 예제")
        print("4. 종료")
        
        choice = input("\n선택 (1-4): ")
        
        if choice == "1":
            await run_simulation_example()
        elif choice == "2":
            await run_production_example()
        elif choice == "3":
            show_settings_example()
        elif choice == "4":
            print("👋 예제를 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    asyncio.run(main()) 