#!/usr/bin/env python3
"""
간단한 모의투자 계좌 정보 확인
"""

import sys
import os
import json

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient

def simple_account_check():
    """간단한 계좌 정보 확인"""
    
    print("=" * 50)
    print("🏦 모의투자 계좌 정보 (간단 버전)")
    print("=" * 50)
    
    try:
        # 설정 로드
        settings = Settings()
        print(f"📋 환경: {settings.ENVIRONMENT}")
        print(f"🌐 API: {settings.API_HOST}")
        
        # API 클라이언트 초기화
        api_client = KiwoomClient(settings)
        
        # 계좌 잔고 조회
        print("\n💰 계좌 잔고 조회 중...")
        balance = api_client.get_account_balance()
        
        if balance:
            print("✅ 잔고 정보:")
            print(json.dumps(balance, indent=2, ensure_ascii=False))
        else:
            print("❌ 잔고 조회 실패")
            
        # 연결 테스트
        print("\n🔗 API 연결 테스트 중...")
        if api_client.test_connection():
            print("✅ API 연결 성공")
        else:
            print("❌ API 연결 실패")
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        
    print("\n" + "=" * 50)

if __name__ == "__main__":
    simple_account_check() 