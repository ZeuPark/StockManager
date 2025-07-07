#!/usr/bin/env python3
"""
Volume Trading Example
거래량 급증 종목 자동매매 사용 예제
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.volume_scanner import VolumeScanner, VolumeCandidate
from config.settings import Settings
from utils.token_manager import TokenManager
from utils.logger import get_logger

logger = get_logger("volume_example")

async def volume_scanning_example():
    """거래량 스캐닝 예제"""
    logger.info("거래량 스캐닝 예제 시작")
    
    # 설정 및 스캐너 초기화
    settings = Settings()
    token_manager = TokenManager(settings)
    scanner = VolumeScanner(settings, token_manager)
    
    # 스캐너 설정
    scanner.auto_trade_enabled = False  # 예제에서는 자동매매 비활성화
    scanner.scan_interval = 10  # 10초마다 스캔
    scanner.min_volume_ratio = 1.5  # 150% 이상
    scanner.min_trade_value = 30_000_000  # 3천만원 이상
    scanner.min_score = 3  # 최소 3점
    
    logger.info("거래량 스캐너 설정:")
    logger.info(f"  - 스캔 간격: {scanner.scan_interval}초")
    logger.info(f"  - 최소 거래량 비율: {scanner.min_volume_ratio:.1f}%")
    logger.info(f"  - 최소 거래대금: {scanner.min_trade_value:,}원")
    logger.info(f"  - 최소 점수: {scanner.min_score}점")
    logger.info(f"  - 자동매매: {'활성화' if scanner.auto_trade_enabled else '비활성화'}")
    
    try:
        # 3회 스캔 실행
        for i in range(3):
            logger.info(f"\n=== {i+1}번째 스캔 시작 ===")
            
            # 거래량 후보 스캔
            candidates = await scanner.scan_volume_candidates()
            
            if candidates:
                logger.info(f"발견된 후보 종목: {len(candidates)}개")
                for candidate in candidates:
                    logger.info(f"  {candidate.stock_name}({candidate.stock_code})")
                    logger.info(f"    현재가: {candidate.current_price:,}원")
                    logger.info(f"    거래량비율: {candidate.volume_ratio:.1f}%")
                    logger.info(f"    거래대금: {candidate.trade_value:,}원")
                    logger.info(f"    종합점수: {candidate.score}점")
                    logger.info(f"    고점돌파: {'예' if candidate.is_breakout else '아니오'}")
                    logger.info(f"    추세: {candidate.ma_trend}")
            else:
                logger.info("조건을 만족하는 후보 종목이 없습니다.")
            
            # 후보 종목 요약 출력
            summary = scanner.get_candidates_summary()
            logger.info(f"누적 후보 종목: {len(summary)}개")
            
            # 자동매매 상태 출력
            status = scanner.get_auto_trade_status()
            logger.info(f"자동매매 상태: {status}")
            
            if i < 2:  # 마지막 스캔이 아니면 대기
                logger.info(f"{scanner.scan_interval}초 후 다음 스캔...")
                await asyncio.sleep(scanner.scan_interval)
        
        logger.info("\n=== 스캔 완료 ===")
        
    except Exception as e:
        logger.error(f"스캐닝 중 오류 발생: {e}")

async def manual_candidate_example():
    """수동 후보 종목 처리 예제"""
    logger.info("\n수동 후보 종목 처리 예제")
    
    # 설정 및 스캐너 초기화
    settings = Settings()
    token_manager = TokenManager(settings)
    scanner = VolumeScanner(settings, token_manager)
    
    # 자동매매 활성화
    scanner.auto_trade_enabled = True
    
    # 수동으로 후보 종목 생성
    candidate = VolumeCandidate(
        stock_code="005930",
        stock_name="삼성전자",
        current_price=70000,
        volume_ratio=2.5,
        price_change=3.2,
        trade_value=100000000,
        score=7,
        timestamp=datetime.now(),
        is_breakout=True,
        ma_trend="상승추세"
    )
    
    logger.info(f"수동 후보 종목 생성: {candidate.stock_name}({candidate.stock_code})")
    
    # 자동매매 등록
    result = scanner.add_auto_trade(candidate.stock_code, candidate.current_price, candidate.stock_name)
    if result:
        logger.info("자동매매 등록 성공")
    else:
        logger.error("자동매매 등록 실패")
    
    # 자동매매 상태 확인
    status = scanner.get_auto_trade_status()
    logger.info(f"자동매매 상태: {status}")
    
    # 자동매매 제거 (시뮬레이션)
    scanner.remove_auto_trade(candidate.stock_code, 75000, "익절")
    logger.info("자동매매 제거 완료")

def configuration_example():
    """설정 예제"""
    logger.info("\n설정 예제")
    
    settings = Settings()
    
    # 거래량 스캐닝 설정 확인
    volume_config = settings.VOLUME_SCANNING
    logger.info("거래량 스캐닝 설정:")
    logger.info(f"  - 활성화: {volume_config.get('enabled')}")
    logger.info(f"  - 스캔 간격: {volume_config.get('scan_interval')}초")
    logger.info(f"  - 최소 거래량 비율: {volume_config.get('min_volume_ratio')}%")
    logger.info(f"  - 최소 거래대금: {volume_config.get('min_trade_value'):,}원")
    logger.info(f"  - 최소 점수: {volume_config.get('min_score')}점")
    logger.info(f"  - 자동매매: {volume_config.get('auto_trade_enabled')}")
    logger.info(f"  - 손절: {volume_config.get('stop_loss')*100}%")
    logger.info(f"  - 익절: {volume_config.get('take_profit')*100}%")
    logger.info(f"  - 최대 보유시간: {volume_config.get('max_hold_time')}초")

async def main():
    """메인 함수"""
    logger.info("거래량 스캐닝 예제 시작")
    logger.info("=" * 50)
    
    try:
        # 설정 예제
        configuration_example()
        
        # 수동 후보 종목 처리 예제
        await manual_candidate_example()
        
        # 실제 스캐닝 예제 (API 연결 필요)
        # await volume_scanning_example()
        
        logger.info("\n예제 완료")
        
    except Exception as e:
        logger.error(f"예제 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 