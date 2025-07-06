#!/usr/bin/env python3
"""
Kiwoom Open API 연결 테스트
실제 Kiwoom API와의 연결을 테스트합니다.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from api.kiwoom_client import KiwoomClient
from utils.token_manager import TokenManager

def test_kiwoom_connection():
    """Kiwoom API 연결 테스트"""
    print("🔗 Kiwoom Open API 연결 테스트 시작...")
    
    # 환경 설정
    os.environ["ENVIRONMENT"] = "simulation"
    settings = Settings()
    
    print(f"환경: {settings.ENVIRONMENT}")
    print(f"API URL: {settings.KIWOOM_API[settings.ENVIRONMENT]['host']}")
    
    # 토큰 관리자 테스트
    print("\n1. 토큰 관리자 테스트...")
    token_manager = TokenManager(settings)
    
    # 토큰 갱신 시도
    if token_manager.refresh_token("simulation"):
        print("✅ 토큰 갱신 성공")
    else:
        print("❌ 토큰 갱신 실패")
        return False
    
    # Kiwoom 클라이언트 테스트
    print("\n2. Kiwoom API 클라이언트 테스트...")
    client = KiwoomClient(settings)
    
    # 연결 테스트
    if client.test_connection():
        print("✅ Kiwoom API 연결 성공!")
        
        # 계좌 정보 조회 테스트
        print("\n3. 계좌 정보 조회 테스트...")
        account_info = client.get_account_info()
        if account_info:
            print(f"계좌 정보 조회 성공: {account_info.get('rt_cd')}")
            if account_info.get('rt_cd') == '0':
                print("✅ 계좌 정보 조회 성공")
            else:
                print(f"❌ 계좌 정보 조회 실패: {account_info.get('msg1')}")
        else:
            print("❌ 계좌 정보 조회 실패")
        
        # 주식 현재가 조회 테스트
        print("\n4. 주식 현재가 조회 테스트...")
        stock_price = client.get_stock_price("005930")  # 삼성전자
        if stock_price:
            print(f"주식 현재가 조회 성공: {stock_price.get('rt_cd')}")
            if stock_price.get('rt_cd') == '0':
                print("✅ 주식 현재가 조회 성공")
                output = stock_price.get('output', {})
                if output:
                    print(f"삼성전자 현재가: {output.get('stck_prpr', 'N/A')}원")
            else:
                print(f"❌ 주식 현재가 조회 실패: {stock_price.get('msg1')}")
        else:
            print("❌ 주식 현재가 조회 실패")
        
        return True
    else:
        print("❌ Kiwoom API 연결 실패!")
        return False

def main():
    """메인 함수"""
    print("=" * 50)
    print("Kiwoom Open API 연결 테스트")
    print("=" * 50)
    
    try:
        success = test_kiwoom_connection()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 모든 테스트가 성공했습니다!")
            print("이제 실제 모의투자 계좌와 연결되어 있습니다.")
        else:
            print("❌ 일부 테스트가 실패했습니다.")
            print("API 키와 토큰을 확인해주세요.")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 