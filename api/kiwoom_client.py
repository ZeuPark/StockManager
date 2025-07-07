#!/usr/bin/env python3
"""
Kiwoom API Client for Stock Manager
실제 Kiwoom Open API와 통신하는 클라이언트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    from utils.logger import get_logger
    from utils.token_manager import TokenManager
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
    from logger import get_logger
    from token_manager import TokenManager


class KiwoomClient:
    """실제 Kiwoom Open API 클라이언트"""
    
    def __init__(self, settings):
        self.settings = settings
        self.token_manager = TokenManager(settings)
        self.logger = get_logger("kiwoom_client")
        
        # API 설정
        self.env_config = self.settings.get_api_config()
        self.base_url = self.env_config.get("host")  # 환경에 따른 API URL
        self.appkey = self.env_config.get("appkey")
        self.secretkey = self.env_config.get("secretkey")
        
        # 실제 키움증권 API 엔드포인트
        self.api_endpoints = {
            "account_info": "/api/dostk/acnt",           # 계좌 정보 조회
            "stock_price": "/api/dostk/stkinfo",         # 주식 현재가 조회
            "order": "/api/dostk/ordr",                  # 주식 주문
            "order_status": "/api/dostk/ordr",           # 주문 상태 조회
            "execution": "/api/dostk/exec",              # 체결 정보 조회
            "daily_chart": "/api/dostk/chart",           # 일봉 차트 조회
            "minute_chart": "/api/dostk/chart",          # 분봉 차트 조회
            "volume_ranking": "/api/dostk/rkinfo",       # 거래량 급증 종목 조회
            "execution_strength": "/api/dostk/mrkcond"   # 체결강도 조회
        }
        
        # 세션 관리
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json',
            'appkey': self.appkey,
            'appsecret': self.secretkey
        })
        
        self.logger.info(f"KiwoomClient initialized for {self.settings.ENVIRONMENT}")
    
    def _get_headers(self, include_token: bool = True, tr_type: str = "account_info", api_id: str = None) -> Dict[str, str]:
        """API 요청 헤더 생성 (TR ID 포함)"""
        headers = self.settings.get_headers(tr_type=tr_type)
        headers['Accept'] = 'application/json'
        
        # API ID 추가 (주문 API용)
        if api_id:
            headers['api-id'] = api_id
        
        if not include_token:
            headers.pop('authorization', None)
            
        return headers
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, retry_count: int = 0, tr_type: str = "account_info", api_id: str = None) -> Optional[Dict]:
        """API 요청 실행"""
        url = self.base_url + endpoint
        
        try:
            headers = self._get_headers(tr_type=tr_type, api_id=api_id)
            
            self.logger.debug(f"API 요청: {method} {url}")
            self.logger.debug(f"TR ID: {headers.get('tr_id', 'N/A')}")
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            else:
                self.logger.error(f"지원하지 않는 HTTP 메서드: {method}")
                return None
            
            self.logger.debug(f"응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"API 응답: {result}")
                return result
            elif response.status_code == 429 and retry_count < 3:
                # API 호출 제한, 지수 백오프로 재시도
                wait_time = (2 ** retry_count) * 10  # 10초, 20초, 40초
                self.logger.warning(f"API 호출 제한 (429). {wait_time}초 후 재시도... (시도 {retry_count + 1}/3)")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, data, retry_count + 1, tr_type)
            elif response.status_code == 401 and retry_count < 2:
                # 토큰 만료, 갱신 시도
                self.logger.info("토큰이 만료되었습니다. 토큰을 갱신합니다...")
                if self.token_manager.refresh_token(self.settings.ENVIRONMENT):
                    # 새 토큰으로 재시도
                    return self._make_request(method, endpoint, params, data, retry_count + 1, tr_type)
                else:
                    self.logger.error("토큰 갱신에 실패했습니다.")
                    return None
            else:
                self.logger.error(f"API 요청 실패: {response.status_code}")
                self.logger.error(f"응답 내용: {response.text}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"네트워크 오류: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"잘못된 JSON 응답: {e}")
            return None
    
    def get_account_info(self, account_no: str = None) -> Optional[Dict]:
        """계좌 정보 조회"""
        endpoint = self.api_endpoints["account_info"]
        
        # 실제 키움증권 API 파라미터 (kt00018)
        data = {
            "qry_tp": "1",  # 조회구분
            "dmst_stex_tp": "KRX"  # 국내거래소구분
        }
        
        return self._make_request("POST", endpoint, data=data, tr_type="account_info")
    
    def get_stock_price(self, stock_code: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        endpoint = self.api_endpoints["execution_strength"]
        
        data = {
            "stk_cd": stock_code  # 종목코드
        }
        
        return self._make_request("POST", endpoint, data=data, tr_type="stock_price")
    
    def place_order(self, stock_code: str, order_type: str, quantity: int, 
                   price: int = 0, account_no: str = None) -> Optional[Dict]:
        """주식 주문"""
        endpoint = self.api_endpoints["order"]
        
        # 계좌번호가 없으면 설정에서 가져오기
        if not account_no:
            account_no = self.settings.secrets.get(self.settings.ENVIRONMENT, {}).get("account_no", "00000000")
        
        # 주문구분 매핑
        order_type_map = {
            "매수": "01",      # 매수
            "매도": "02",     # 매도
            "buy": "01",      # 매수
            "sell": "02",     # 매도
            "buy_cancel": "03",  # 매수취소
            "sell_cancel": "04"  # 매도취소
        }
        
        # 환경에 따른 주문 방식 결정
        # 모의투자: 시장가 주문, 실제거래: 지정가 주문
        if self.settings.ENVIRONMENT == "simulation":
            # 모의투자에서는 시장가 주문
            trde_tp = "3"  # 시장가
            ord_uv = ""    # 시장가 주문시 단가 빈값
            self.logger.info(f"모의투자 환경: 시장가 주문으로 실행")
        else:
            # 실제거래에서는 지정가 주문
            trde_tp = "1"  # 지정가
            ord_uv = str(price) if price > 0 else ""  # 지정가 주문시 단가 설정
            self.logger.info(f"실제거래 환경: 지정가 주문으로 실행")
        
        # 실제 키움증권 API 주문 파라미터
        data = {
            "dmst_stex_tp": "KRX",  # 국내거래소구분
            "stk_cd": stock_code,  # 종목코드
            "ord_qty": str(quantity),  # 주문수량
            "ord_uv": ord_uv,  # 주문단가
            "trde_tp": trde_tp,  # 거래구분 (3: 시장가, 1: 지정가)
            "cond_uv": ""  # 조건단가
        }
        
        # API ID 설정 (매수/매도 구분)
        tr_type = "order_buy" if order_type in ["buy", "매수"] else "order_sell"
        
        order_method = "시장가" if trde_tp == "3" else "지정가"
        self.logger.info(f"주문 실행: {order_type} {stock_code} {quantity}주 @ {price}원 ({order_method})")
        return self._make_request("POST", endpoint, data=data, tr_type=tr_type)
    
    def get_order_status(self, order_no: str = "", account_no: str = None) -> Optional[Dict]:
        """주문 상태 조회"""
        endpoint = "/uapi/domestic-stock/v1/trading/inquire-order"
        
        # 계좌번호가 없으면 설정에서 가져오기
        if not account_no:
            account_no = self.settings.secrets.get(self.settings.ENVIRONMENT, {}).get("account_no", "00000000")
        
        params = {
            "CANO": account_no[:8],  # 계좌번호
            "ACNT_PRDT_CD": account_no[8:] if len(account_no) > 8 else "01",  # 계좌상품코드
            "CTX_AREA_FK100": "",  # 연속조회검색조건
            "CTX_AREA_NK100": "",  # 연속조회키
            "INQR_DVSN": "01",  # 조회구분
            "PDNO": "",  # 종목코드
            "ORD_DT": datetime.now().strftime("%Y%m%d"),  # 주문일자
            "SLL_BUY_DVSN_CD": "00",  # 매도매수구분코드
            "OVRS_EXCG_CD": "KRX",  # 해외거래소코드
            "SORT_SQN": "DS",  # 정렬순서
            "ORD_PRC": "",  # 주문가격
            "ORD_QTY": "",  # 주문수량
            "CTX_AREA_FK200": ""  # 연속조회검색조건2
        }
        
        if order_no:
            params["MGCO_APTM_ODNO"] = order_no  # 모사신청번호
        
        return self._make_request("GET", endpoint, params=params, tr_type="order_status")
    
    def get_daily_chart(self, stock_code: str, start_date: str = None, 
                       end_date: str = None) -> Optional[Dict]:
        """일봉 차트 데이터 조회"""
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드
            "FID_COND_SCR_DIV_CODE": "20171",  # 종목분류코드
            "FID_INPUT_ISCD": stock_code,  # 종목코드
            "FID_INPUT_DATE_1": start_date,  # 시작일자
            "FID_INPUT_DATE_2": end_date,  # 종료일자
            "FID_VOL_CNT": "100",  # 거래량
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드
            "FID_COND_SCR_DIV_CODE": "20171"  # 종목분류코드
        }
        
        return self._make_request("GET", endpoint, params=params)
    
    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            # 간단한 계좌 정보 조회로 연결 테스트
            result = self.get_account_info()
            if result and result.get("rt_cd") == "0":
                self.logger.info("Kiwoom API 연결 성공!")
                return True
            else:
                self.logger.error(f"API 연결 실패: {result}")
                return False
        except Exception as e:
            self.logger.error(f"연결 테스트 중 오류: {e}")
            return False
    
    def get_account_balance(self, account_no: str = None) -> dict:
        """
        계좌 잔고(가용 현금 등) 조회
        """
        try:
            info = self.get_account_info(account_no)
            if not info:
                self.logger.warning("계좌 잔고 조회 실패: get_account_info 결과 없음 - 기본값 사용")
                return {"available_cash": 10000000}  # 기본값 1000만원

            # Kiwoom API 응답 구조에 따라 파싱 (예시)
            try:
                # 실제 응답 구조에 맞게 수정 필요
                output = info.get("output", {})
                available_cash = 0
                if isinstance(output, dict):
                    available_cash = int(output.get("dnca_tot_amt", 10000000))  # 예: 가용현금 필드명
                elif isinstance(output, list) and output:
                    available_cash = int(output[0].get("dnca_tot_amt", 10000000))
                else:
                    available_cash = 10000000  # 기본값
                return {"available_cash": available_cash}
            except Exception as e:
                self.logger.warning(f"계좌 잔고 파싱 실패: {e} - 기본값 사용")
                return {"available_cash": 10000000}  # 기본값 1000만원
        except Exception as e:
            self.logger.warning(f"계좌 잔고 조회 중 오류: {e} - 기본값 사용")
            return {"available_cash": 10000000}  # 기본값 1000만원


def main():
    """테스트 함수"""
    from config.settings import Settings
    
    settings = Settings()
    client = KiwoomClient(settings)
    
    # 연결 테스트
    if client.test_connection():
        print("✅ Kiwoom API 연결 성공!")
        
        # 계좌 정보 조회
        account_info = client.get_account_info()
        if account_info:
            print(f"계좌 정보: {account_info}")
        
        # 삼성전자 현재가 조회
        stock_price = client.get_stock_price("005930")
        if stock_price:
            print(f"삼성전자 현재가: {stock_price}")
    else:
        print("❌ Kiwoom API 연결 실패!")


if __name__ == "__main__":
    main() 