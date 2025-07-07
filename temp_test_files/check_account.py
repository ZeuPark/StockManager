#!/usr/bin/env python3
"""
모의투자 계좌 정보 확인 스크립트
"""

import sys
import os
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from utils.token_manager import TokenManager
from utils.logger import get_logger

def check_account_info():
    """모의투자 계좌 정보 확인"""
    
    print("=" * 60)
    print("🏦 모의투자 계좌 정보 확인")
    print("=" * 60)
    
    # 로거 설정
    logger = get_logger("account_check")
    
    try:
        # 설정 로드
        settings = Settings()
        logger.info("설정 로드 완료")
        
        # 환경 확인
        print(f"📋 현재 환경: {settings.ENVIRONMENT}")
        print(f"🌐 API 호스트: {settings.API_HOST}")
        
        # 토큰 매니저 초기화
        token_manager = TokenManager(settings)
        logger.info("토큰 매니저 초기화 완료")
        
        # API 클라이언트 초기화
        api_client = KiwoomClient(settings)
        logger.info("API 클라이언트 초기화 완료")
        
        print("\n" + "=" * 50)
        print("📊 계좌 정보 조회 중...")
        print("=" * 50)
        
        # 1. 계좌 정보 조회
        account_info = api_client.get_account_info()
        
        if account_info:
            print("✅ 계좌 정보 조회 성공!")
            print(json.dumps(account_info, indent=2, ensure_ascii=False))
        else:
            print("❌ 계좌 정보 조회 실패")
            
        print("\n" + "=" * 50)
        print("💰 잔고 정보 조회 중...")
        print("=" * 50)
        
        # 2. 잔고 정보 조회
        balance_info = api_client.get_account_balance()
        
        if balance_info:
            print("✅ 잔고 정보 조회 성공!")
            print(json.dumps(balance_info, indent=2, ensure_ascii=False))
        else:
            print("❌ 잔고 정보 조회 실패")
            
        print("\n" + "=" * 50)
        print("📈 보유 종목 조회 중...")
        print("=" * 50)
        
        # 3. 보유 종목 조회
        holdings = api_client.get_holdings()
        
        if holdings:
            print("✅ 보유 종목 조회 성공!")
            print(json.dumps(holdings, indent=2, ensure_ascii=False))
        else:
            print("❌ 보유 종목 조회 실패")
            
        print("\n" + "=" * 50)
        print("📋 주문 내역 조회 중...")
        print("=" * 50)
        
        # 4. 주문 내역 조회
        order_history = api_client.get_order_history()
        
        if order_history:
            print("✅ 주문 내역 조회 성공!")
            print(json.dumps(order_history, indent=2, ensure_ascii=False))
        else:
            print("❌ 주문 내역 조회 실패")
            
    except Exception as e:
        logger.error(f"계좌 정보 확인 중 오류 발생: {e}")
        print(f"❌ 오류 발생: {e}")
        
    print("\n" + "=" * 60)
    print("🏁 계좌 정보 확인 완료")
    print("=" * 60)

if __name__ == "__main__":
    check_account_info() 