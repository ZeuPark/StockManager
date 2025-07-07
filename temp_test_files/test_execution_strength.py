#!/usr/bin/env python3
"""
체결강도 API 테스트
키움 API의 체결강도 조회 기능을 테스트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from utils.token_manager import TokenManager
from analysis.volume_scanner import VolumeScanner
import requests
import json

async def test_execution_strength_api():
    """체결강도 API 직접 테스트"""
    print("=== 체결강도 API 직접 테스트 ===")
    
    # 설정 로드
    settings = Settings()
    token_manager = TokenManager(settings)
    
    try:
        # 토큰 가져오기
        token = await token_manager.get_valid_token()
        if not token:
            print("❌ 토큰을 가져올 수 없습니다.")
            return
        
        print(f"✅ 토큰 획득: {token[:20]}...")
        
        # API 호출
        if settings.ENVIRONMENT == "simulation":
            host = "https://mockapi.kiwoom.com"
        else:
            host = "https://api.kiwoom.com"
        
        endpoint = "/api/dostk/mrkcond"
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'api-id': 'ka10046',
        }
        
        # 테스트 종목들
        test_stocks = [
            "005930",  # 삼성전자
            "000660",  # SK하이닉스
            "035420",  # NAVER
        ]
        
        for stock_code in test_stocks:
            print(f"\n🔍 {stock_code} 체결강도 조회 중...")
            
            data = {
                'stk_cd': stock_code,
            }
            
            print(f"🌐 API 호출: {url}")
            print(f"📋 요청 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            response = requests.post(url, headers=headers, json=data)
            
            print(f"📊 응답 상태: {response.status_code}")
            print(f"📋 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API 호출 성공!")
                print(f"📋 응답 데이터:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 체결강도 데이터 확인
                if "return_code" in result and result["return_code"] == 0:
                    print(f"✅ 체결강도 조회 성공: {stock_code}")
                else:
                    print(f"❌ 체결강도 조회 실패: {result.get('return_msg', 'Unknown error')}")
            else:
                print(f"❌ API 호출 실패: {response.status_code}")
                print(f"📋 에러 응답: {response.text}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

async def test_volume_scanner_with_execution_strength():
    """Volume Scanner와 함께 체결강도 테스트"""
    print("\n=== Volume Scanner 체결강도 테스트 ===")
    
    # 설정 로드
    settings = Settings()
    token_manager = TokenManager(settings)
    
    # 스캐너 초기화
    scanner = VolumeScanner(settings, token_manager)
    
    print(f"환경: {settings.ENVIRONMENT}")
    print(f"최소 체결강도: {scanner.min_execution_strength}")
    print()
    
    try:
        # 개별 종목 체결강도 테스트
        test_stocks = ["005930", "000660", "035420"]
        
        for stock_code in test_stocks:
            print(f"🔍 {stock_code} 체결강도 조회...")
            strength = await scanner.get_execution_strength(stock_code)
            print(f"   체결강도: {strength:.1f}%")
            print(f"   조건 만족: {'예' if strength >= scanner.min_execution_strength else '아니오'}")
            print()
        
        # 전체 스캔 테스트 (상위 5개만)
        print("📊 전체 스캔 테스트 (상위 5개 종목)...")
        
        # 거래량 순위 조회 (상위 5개만)
        volume_data = await scanner.get_volume_ranking()
        if volume_data:
            test_data = volume_data[:5]  # 상위 5개만
            
            for item in test_data:
                stock_code = item.get("stk_cd", "")
                stock_name = item.get("stk_nm", "")
                
                print(f"\n🔍 {stock_name}({stock_code}) 체결강도 확인...")
                strength = await scanner.get_execution_strength(stock_code)
                print(f"   체결강도: {strength:.1f}%")
                print(f"   조건 만족: {'예' if strength >= scanner.min_execution_strength else '아니오'}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_execution_strength_api())
    asyncio.run(test_volume_scanner_with_execution_strength()) 