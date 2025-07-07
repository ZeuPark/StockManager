#!/usr/bin/env python3
"""
API 응답 데이터 디버그
실제 키움 API 응답을 확인하여 데이터 구조를 파악
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from utils.token_manager import TokenManager
import requests
import json

async def debug_api_response():
    """API 응답 데이터 디버그"""
    print("=== API 응답 데이터 디버그 ===")
    
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
        
        endpoint = "/api/dostk/rkinfo"
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'api-id': 'ka10023',
        }
        
        data = {
            'mrkt_tp': '000',  # 전체 시장
            'sort_tp': '1',    # 거래량 순
            'tm_tp': '1',      # 1분 단위
            'trde_qty_tp': '10',  # 상위 10개만
            'tm': '',
            'stk_cnd': '20',   # 거래량 급증 조건
            'pric_tp': '0',    # 전체 가격대
            'stex_tp': '3',    # 코스피
        }
        
        print(f"🌐 API 호출: {url}")
        print(f"📋 요청 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📋 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 호출 성공!")
            print(f"📋 응답 데이터 구조:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 거래량 데이터 확인
            volume_data = result.get("trde_qty_sdnin", [])
            print(f"\n📈 거래량 데이터 개수: {len(volume_data)}")
            
            if volume_data:
                print(f"\n🔍 첫 번째 종목 데이터:")
                first_item = volume_data[0]
                print(json.dumps(first_item, indent=2, ensure_ascii=False))
                
                # 사용 가능한 필드들 확인
                print(f"\n📋 사용 가능한 필드들:")
                for key, value in first_item.items():
                    print(f"  - {key}: {value} (타입: {type(value).__name__})")
                
                # 체결강도 관련 필드 찾기
                print(f"\n🔍 체결강도 관련 필드:")
                strength_fields = [k for k in first_item.keys() if 'strength' in k.lower() or 'exec' in k.lower()]
                if strength_fields:
                    for field in strength_fields:
                        print(f"  - {field}: {first_item[field]}")
                else:
                    print("  - 체결강도 관련 필드를 찾을 수 없습니다.")
                    
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"📋 에러 응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_response()) 