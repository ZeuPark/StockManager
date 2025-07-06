#!/usr/bin/env python3
"""
실시간 거래 신호 테스트 스크립트
모멘텀 분석 및 매매 신호 생성 기능을 테스트합니다.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# 프로젝트 모듈 import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.settings import Settings
from analysis.momentum_analyzer import MomentumAnalyzer, StockData
from orders.signal_processor import SignalProcessor
from utils.logger import get_logger

logger = get_logger("test_trading_signals")

class TradingSignalTester:
    """거래 신호 테스트 클래스"""
    
    def __init__(self):
        self.settings = Settings()
        self.momentum_analyzer = MomentumAnalyzer(self.settings)
        self.signal_processor = SignalProcessor(self.settings)
        
        # 테스트용 계좌 정보 설정
        self.signal_processor.update_account_info(
            balance=10000000,  # 1천만원
            positions=[]
        )
        
        # 콜백 설정
        self.signal_processor.set_callbacks(
            on_signal=self._on_signal_generated,
            on_order=self._on_order_executed,
            on_error=self._on_signal_error
        )
        
        # 테스트 결과
        self.test_results = {
            "total_signals": 0,
            "buy_signals": 0,
            "high_confidence_signals": 0,
            "test_stocks": []
        }
    
    def _on_signal_generated(self, signal):
        """신호 생성 콜백"""
        self.test_results["total_signals"] += 1
        
        if signal.signal_type == "buy":
            self.test_results["buy_signals"] += 1
        
        if signal.confidence >= 0.8:
            self.test_results["high_confidence_signals"] += 1
        
        logger.info(f"🎯 신호 생성: {signal.stock_code}")
        logger.info(f"   타입: {signal.signal_type}")
        logger.info(f"   가격: {signal.price:,}원")
        logger.info(f"   수량: {signal.quantity}주")
        logger.info(f"   신뢰도: {signal.confidence:.3f}")
        logger.info(f"   조건: {[name for name, result in signal.conditions.items() if result.is_satisfied]}")
        logger.info("-" * 50)
    
    def _on_order_executed(self, signal, order_result):
        """주문 실행 콜백"""
        logger.info(f"📈 주문 실행: {signal.stock_code} - {signal.quantity}주")
    
    def _on_signal_error(self, error):
        """신호 에러 콜백"""
        logger.error(f"❌ 신호 에러: {error}")
    
    def generate_test_data(self, stock_code: str, base_price: float = 50000, iteration: int = 0) -> StockData:
        # 히스토리 쌓기용: high_price를 점진적으로 증가
        current_price = base_price + (iteration * 100)  # 100원씩 증가
        high_price = base_price * 1.01 + (iteration * 50)  # 점진적으로 증가하는 최고가
        return StockData(
            code=stock_code,
            current_price=current_price,
            volume=1000000,
            execution_strength=1.6,
            high_price=high_price,
            low_price=base_price * 0.99,
            open_price=base_price,
            prev_close=base_price,
            timestamp=datetime.now()
        )
    
    def generate_momentum_data(self, stock_code: str, base_price: float = 50000) -> StockData:
        # history에서 최고가를 가져와서 돌파 조건 만족
        recent_data = self.momentum_analyzer.get_recent_data(stock_code, 5)
        if recent_data:
            # 최근 데이터의 최고가 계산
            prev_high = max(data.high_price for data in recent_data)
            current_price = prev_high * 1.11  # 11% 돌파 (상승률 10% 이상)
        else:
            # history가 없으면 기본값 사용
            prev_high = base_price * 1.01
            current_price = prev_high * 1.11
        
        return StockData(
            code=stock_code,
            current_price=current_price,
            volume=2000000,
            execution_strength=2.0,
            high_price=current_price,
            low_price=current_price * 0.98,
            open_price=base_price,
            prev_close=base_price,
            timestamp=datetime.now()
        )
    
    async def test_normal_data(self, stock_codes: list, iterations: int = 10):
        """일반 데이터로 테스트"""
        logger.info("🔄 일반 데이터 테스트 시작...")
        
        for i in range(iterations):
            for stock_code in stock_codes:
                # 일반적인 데이터 생성
                stock_data = self.generate_test_data(stock_code)
                
                # 모멘텀 분석
                conditions = self.momentum_analyzer.analyze_all_conditions(stock_data)
                
                # 디버깅: 조건 결과 출력
                logger.debug(f"종목 {stock_code} 조건 분석:")
                for condition_name, result in conditions.items():
                    logger.debug(f"  {condition_name}: {result.is_satisfied} (값: {result.current_value:.3f}, 기준: {result.threshold})")
                
                # 매매 신호 처리
                await self.signal_processor.process_trading_signal(stock_data, conditions)
                
                # 잠시 대기
                await asyncio.sleep(0.1)
            
            logger.info(f"일반 데이터 테스트 진행률: {(i+1)/iterations*100:.1f}%")
    
    async def test_momentum_data(self, stock_codes: list, iterations: int = 5):
        """모멘텀 조건을 만족하는 데이터로 테스트"""
        logger.info("🚀 모멘텀 조건 테스트 시작...")
        
        for i in range(iterations):
            for stock_code in stock_codes:
                # 먼저 기본 데이터를 몇 번 넣어서 히스토리 쌓기
                for j in range(4):
                    base_data = self.generate_test_data(stock_code, iteration=j)
                    conditions = self.momentum_analyzer.analyze_all_conditions(base_data)
                    await self.signal_processor.process_trading_signal(base_data, conditions)
                    await asyncio.sleep(0.1)
                
                # 이제 모멘텀 조건을 만족하는 데이터 생성
                stock_data = self.generate_momentum_data(stock_code)
                
                # 디버깅: 생성된 데이터 정보 출력
                logger.info(f"생성된 모멘텀 데이터 - {stock_code}:")
                logger.info(f"  가격: {stock_data.current_price:,.0f}원")
                logger.info(f"  거래량: {stock_data.volume:,}주")
                logger.info(f"  체결강도: {stock_data.execution_strength:.3f}")
                
                # 모멘텀 분석
                conditions = self.momentum_analyzer.analyze_all_conditions(stock_data)
                
                # 디버깅: 조건 결과 출력
                logger.info(f"조건 분석 결과 - {stock_code}:")
                for condition_name, result in conditions.items():
                    status = "✅ 만족" if result.is_satisfied else "❌ 불만족"
                    logger.info(f"  {condition_name}: {status} (값: {result.current_value:.3f}, 기준: {result.threshold})")
                
                # 매매 신호 처리
                await self.signal_processor.process_trading_signal(stock_data, conditions)
                
                # 잠시 대기
                await asyncio.sleep(0.2)
            
            logger.info(f"모멘텀 조건 테스트 진행률: {(i+1)/iterations*100:.1f}%")
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        logger.info("=" * 60)
        logger.info("📊 테스트 결과 요약")
        logger.info("=" * 60)
        logger.info(f"총 신호 수: {self.test_results['total_signals']}")
        logger.info(f"매수 신호: {self.test_results['buy_signals']}")
        logger.info(f"고신뢰도 신호 (≥0.8): {self.test_results['high_confidence_signals']}")
        
        if self.test_results['total_signals'] > 0:
            success_rate = (self.test_results['buy_signals'] / self.test_results['total_signals']) * 100
            high_confidence_rate = (self.test_results['high_confidence_signals'] / self.test_results['total_signals']) * 100
            logger.info(f"매수 신호 비율: {success_rate:.1f}%")
            logger.info(f"고신뢰도 신호 비율: {high_confidence_rate:.1f}%")
        
        # 신호 히스토리 요약
        signal_summary = self.signal_processor.get_signal_summary()
        logger.info(f"신호 처리기 통계: {signal_summary}")
        
        logger.info("=" * 60)
    
    async def run_comprehensive_test(self):
        """종합 테스트 실행"""
        logger.info("🎯 실시간 거래 신호 테스트 시작")
        logger.info("=" * 60)
        
        # 테스트할 종목들
        test_stocks = ["005930", "000660", "035420", "051910", "006400"]
        
        try:
            # 1. 일반 데이터 테스트
            await self.test_normal_data(test_stocks, iterations=5)
            
            # 2. 모멘텀 조건 테스트
            await self.test_momentum_data(test_stocks, iterations=3)
            
            # 3. 결과 출력
            self.print_test_summary()
            
            logger.info("✅ 테스트 완료!")
            
        except Exception as e:
            logger.error(f"❌ 테스트 중 오류 발생: {e}")
            raise

async def main():
    """메인 함수"""
    tester = TradingSignalTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 