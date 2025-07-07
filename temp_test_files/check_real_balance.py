#!/usr/bin/env python3
"""
실제 계좌 잔고 API 호출 결과 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.kiwoom_client import KiwoomClient
from config.settings import Settings
import json

def main():
    print("=" * 60)
    print("🏦 실제 계좌 잔고 API 호출 결과 확인")
    print("=" * 60)
    
    # 설정 초기화
    settings = Settings()
    print(f"📋 환경: {settings.ENVIRONMENT}")
    print(f"🌐 API: {settings.get_api_config(settings.ENVIRONMENT).get('base_url', 'N/A')}")
    
    # KiwoomClient 초기화
    client = KiwoomClient(settings)
    
    print("\n💰 계좌 정보 API 호출 중...")
    print("-" * 40)
    
    # 실제 API 호출
    result = client.get_account_info()
    
    print(f"📡 API 응답 상태: {result is not None}")
    
    if result:
        print("✅ API 호출 성공!")
        print("📄 전체 응답 내용:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 실제 잔고 추출 시도
        if isinstance(result, dict):
            print("\n🔍 잔고 정보 분석:")
            
            # 가능한 잔고 필드들 확인
            balance_fields = [
                'available_cash', 'cash', 'balance', 'account_balance',
                'available_amount', 'total_cash', 'cash_balance',
                'acnt_bal', 'avl_cash', 'cash_avl'
            ]
            
            for field in balance_fields:
                if field in result:
                    print(f"  💰 {field}: {result[field]}")
            
            # 중첩된 구조 확인
            if 'data' in result:
                print(f"  📊 data 필드: {result['data']}")
            if 'output' in result:
                print(f"  📊 output 필드: {result['output']}")
            if 'response' in result:
                print(f"  📊 response 필드: {result['response']}")
                
        else:
            print(f"❓ 예상치 못한 응답 타입: {type(result)}")
            print(f"   내용: {result}")
    else:
        print("❌ API 호출 실패")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 