#!/usr/bin/env python3
"""
자동매매 로직 테스트 스크립트
현재 시스템과 분리되어 독립적으로 실행됩니다.
"""

import sys
import os
import time
import json
import asyncio
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from analysis.volume_scanner import VolumeScanner
from analysis.momentum_analyzer import StockData
from orders.order_manager import OrderManager
from orders.signal_processor import SignalProcessor
from utils.logger import get_logger
from utils.token_manager import TokenManager

async def test_trading_logic():
    """자동매매 로직 테스트"""
    
    print("=" * 60)
    print("🧪 자동매매 로직 테스트 시작")
    print("=" * 60)
    
    # 로거 설정
    logger = get_logger("trading_test")
    
    try:
        # 설정 로드
        settings = Settings()
        logger.info("설정 로드 완료")
        
        # 토큰 매니저 초기화
        token_manager = TokenManager(settings)
        logger.info("토큰 매니저 초기화 완료")
        
        # API 클라이언트 초기화
        api_client = KiwoomClient(settings)
        logger.info("API 클라이언트 초기화 완료")
        
        # 거래량 스캐너 초기화 (token_manager 전달)
        volume_scanner = VolumeScanner(settings, token_manager)
        logger.info("거래량 스캐너 초기화 완료")
        
        # 주문 매니저 초기화
        order_manager = OrderManager(settings, api_client)
        logger.info("주문 매니저 초기화 완료")
        
        # 신호 프로세서 초기화
        signal_processor = SignalProcessor(settings)
        logger.info("신호 프로세서 초기화 완료")
        
        print("\n📊 현재 필터 조건:")
        print(f"   • 거래량 돌파: 오늘 ≥ 전일")
        print(f"   • 등락률: ≥ {settings.VOLUME_SCANNING['min_price_change'] * 100}%")
        print(f"   • 거래대금: ≥ {settings.VOLUME_SCANNING['min_trade_value']:,}원")
        print(f"   • 체결강도: ≥ {settings.VOLUME_SCANNING['min_execution_strength'] * 100}%")
        
        print("\n🔄 테스트 시나리오:")
        print("   1. 거래량 돌파 종목 스캔")
        print("   2. 필터 조건 적용")
        print("   3. 후보 종목 선정")
        print("   4. 매수 신호 생성 (시뮬레이션)")
        print("   5. 주문 실행 (시뮬레이션)")
        
        # 테스트 실행
        test_count = 0
        max_tests = 5  # 최대 5회 테스트
        
        while test_count < max_tests:
            test_count += 1
            print(f"\n{'='*50}")
            print(f"📈 테스트 #{test_count} 실행 중...")
            print(f"{'='*50}")
            
            # 1. 거래량 돌파 종목 스캔 (비동기)
            logger.info(f"테스트 #{test_count}: 거래량 스캔 시작")
            breakout_stocks = await volume_scanner.scan_volume_candidates()
            
            if not breakout_stocks:
                print("   ❌ 거래량 돌파 종목 없음")
                await asyncio.sleep(3)
                continue
            
            print(f"   ✅ 거래량 돌파 종목 {len(breakout_stocks)}개 발견")
            
            # 2. 필터 적용 및 후보 선정
            candidates = []
            for stock in breakout_stocks:
                stock_code = stock.stock_code
                stock_name = stock.stock_name
                
                # 2차 필터 적용 (VolumeCandidate 객체의 속성 사용)
                if (stock.price_change >= settings.VOLUME_SCANNING['min_price_change'] * 100 and
                    stock.trade_value >= settings.VOLUME_SCANNING['min_trade_value'] and
                    stock.execution_strength >= settings.VOLUME_SCANNING['min_execution_strength']):
                    candidates.append(stock)
                    print(f"   🎯 후보 선정: {stock_name}({stock_code})")
                else:
                    # 탈락 이유 분석
                    change_rate = stock.price_change
                    trading_value = stock.trade_value
                    execution_strength = stock.execution_strength
                    
                    reasons = []
                    if change_rate < settings.VOLUME_SCANNING['min_price_change'] * 100:
                        reasons.append(f"등락률 {change_rate:.2f}%")
                    if trading_value < settings.VOLUME_SCANNING['min_trade_value']:
                        reasons.append(f"거래대금 {trading_value:,}원")
                    if execution_strength < settings.VOLUME_SCANNING['min_execution_strength']:
                        reasons.append(f"체결강도 {execution_strength:.1f}%")
                    
                    print(f"   ❌ 탈락: {stock_name}({stock_code}) - {', '.join(reasons)}")
            
            # 3. 후보 종목이 있으면 매수 신호 생성
            if candidates:
                print(f"\n   🚀 {len(candidates)}개 후보 종목에 대해 매수 신호 생성")
                
                for candidate in candidates:
                    stock_code = candidate.stock_code
                    stock_name = candidate.stock_name
                    current_price = candidate.current_price
                    
                    # 매수 신호 생성 (시뮬레이션)
                    signal = {
                        'type': 'buy',
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'price': current_price,
                        'quantity': 1,  # 테스트용 1주
                        'timestamp': datetime.now(),
                        'reason': '거래량 돌파 + 필터 조건 만족'
                    }
                    
                    print(f"      📋 매수 신호: {stock_name}({stock_code}) @ {current_price:,}원")
                    
                    # 4. 주문 실행 (시뮬레이션)
                    try:
                        # StockData 객체 생성
                        stock_data = StockData(
                            code=stock_code,
                            current_price=current_price,
                            open_price=current_price,
                            high_price=current_price,
                            low_price=current_price,
                            volume=1,
                            execution_strength=1.0,
                            prev_close=current_price,
                            timestamp=datetime.now()
                        )
                        
                        # 실제 주문 API 호출 (테스트용)
                        order_result = await order_manager.execute_buy_order(stock_data, confidence=1.0)
                        
                        if order_result:
                            print(f"      ✅ 주문 성공: {stock_name}")
                            logger.info(f"테스트 주문 성공: {stock_code}")
                        else:
                            print(f"      ❌ 주문 실패: {stock_name}")
                            logger.warning(f"테스트 주문 실패: {stock_code}")
                            
                    except Exception as e:
                        print(f"      ⚠️ 주문 오류: {stock_name} - {str(e)}")
                        logger.error(f"테스트 주문 오류: {stock_code} - {str(e)}")
                
                print(f"\n   🎉 테스트 #{test_count} 완료 - {len(candidates)}개 종목 매수 신호 생성")
                break  # 성공한 테스트가 있으면 종료
                
            else:
                print(f"   📊 후보 종목 없음 - 조건을 만족하는 종목이 없습니다")
            
            await asyncio.sleep(3)  # 3초 대기
        
        if test_count >= max_tests:
            print(f"\n⚠️ 최대 테스트 횟수({max_tests})에 도달했습니다.")
            print("   현재 시장 상황에서 조건을 만족하는 종목이 없는 것 같습니다.")
        
        print("\n" + "=" * 60)
        print("✅ 자동매매 로직 테스트 완료")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        print(f"\n❌ 테스트 오류: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_trading_logic()) 