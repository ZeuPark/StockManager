#!/usr/bin/env python3
"""
API Caller for Stock Manager
Handles API calls to Kiwoom REST API with proper authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import logger with relative path
try:
    from utils.logger import get_logger
    from utils.token_manager import TokenManager
except ImportError:
    # Fallback import
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
    from logger import get_logger
    from token_manager import TokenManager


class APICaller:
    """Handles API calls to Kiwoom REST API"""
    
    def __init__(self, settings):
        self.settings = settings
        self.token_manager = TokenManager(settings)
        self.logger = get_logger("api_caller")
        
        # Get current environment config
        self.env_config = self.settings.get_api_config()
        self.base_url = self.env_config.get("host", "")
        
    def _get_headers(self, include_token: bool = True) -> Dict[str, str]:
        """Get headers for API request"""
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json'
        }
        
        if include_token:
            token = self.env_config.get("token")
            if token:
                headers['Authorization'] = f'Bearer {token}'
            else:
                self.logger.warning("No token available for API call")
                
        return headers
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, retry_count: int = 0) -> Optional[Dict]:
        """Make HTTP request to API"""
        url = self.base_url + endpoint
        
        try:
            headers = self._get_headers()
            
            self.logger.debug(f"Making {method} request to: {url}")
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            self.logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401 and retry_count < 2:
                # Token might be expired, try to refresh
                self.logger.info("Token expired, attempting to refresh...")
                if self.token_manager.refresh_token(self.settings.ENVIRONMENT):
                    # Retry with new token
                    return self._make_request(method, endpoint, params, data, retry_count + 1)
                else:
                    self.logger.error("Failed to refresh token")
                    return None
            else:
                self.logger.error(f"API request failed: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Network error during API request: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        endpoint = self.settings.API_ENDPOINTS["account_info"]
        params = {
            "CANO": "00000000",  # 계좌번호 (실제 사용시 수정 필요)
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "AFHR_FLPR_YN": "N",  # 시간외단일가여부
            "OFL_YN": "",  # 오프라인여부
            "INQR_DVSN": "02",  # 조회구분
            "UNPR_DVSN": "01",  # 단가구분
            "FUND_STTL_ICLD_YN": "N",  # 펀드결제분포함여부
            "FNCG_AMT_AUTO_RDPT_YN": "N",  # 융자금액자동상환여부
            "PRCS_DVSN": "01",  # 처리구분
            "CTX_AREA_FK100": "",  # 연속조회검색조건
            "CTX_AREA_NK100": ""  # 연속조회키
        }
        
        return self._make_request("GET", endpoint, params=params)
    
    def get_stock_price(self, stock_code: str) -> Optional[Dict]:
        """Get current stock price"""
        endpoint = self.settings.API_ENDPOINTS["stock_price"]
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드
            "FID_COND_SCR_DIV_CODE": "20171",  # 종목분류코드
            "FID_INPUT_ISCD": stock_code,  # 종목코드
            "FID_INPUT_PRICE_1": "",  # 가격1
            "FID_INPUT_PRICE_2": "",  # 가격2
            "FID_VOL_CNT": "",  # 거래량
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드
            "FID_COND_SCR_DIV_CODE": "20171"  # 종목분류코드
        }
        
        return self._make_request("GET", endpoint, params=params)
    
    def place_order(self, stock_code: str, order_type: str, quantity: int, 
                   price: int = 0) -> Optional[Dict]:
        """Place stock order"""
        endpoint = self.settings.API_ENDPOINTS["order"]
        
        # Order type mapping
        order_type_map = {
            "buy": "01",      # 매수
            "sell": "02",     # 매도
            "buy_cancel": "03",  # 매수취소
            "sell_cancel": "04"  # 매도취소
        }
        
        data = {
            "CANO": "00000000",  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "OVRS_EXCG_CD": "KRX",  # 해외거래소코드
            "PDNO": stock_code,  # 종목코드
            "ORD_DVSN": "00",  # 주문구분
            "ORD_QTY": str(quantity),  # 주문수량
            "OVRS_ORD_UNPR": str(price),  # 해외주문단가
            "CTAC_TLNO": "",  # 연락전화번호
            "MGCO_APTM_ODNO": "",  # 모사신청번호
            "ORD_SVR_DVSN_CD": "0",  # 주문서버구분코드
            "ORD_DVSN_CD": order_type_map.get(order_type, "01")  # 주문구분코드
        }
        
        return self._make_request("POST", endpoint, data=data)
    
    def get_order_status(self, order_no: str = "") -> Optional[Dict]:
        """Get order status"""
        endpoint = self.settings.API_ENDPOINTS["order_status"]
        params = {
            "CANO": "00000000",  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
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
        
        return self._make_request("GET", endpoint, params=params)
    
    def get_execution_info(self) -> Optional[Dict]:
        """Get execution information"""
        endpoint = self.settings.API_ENDPOINTS["execution"]
        params = {
            "CANO": "00000000",  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "CTX_AREA_FK100": "",  # 연속조회검색조건
            "CTX_AREA_NK100": "",  # 연속조회키
            "INQR_DVSN": "01",  # 조회구분
            "PDNO": "",  # 종목코드
            "ORD_DT": datetime.now().strftime("%Y%m%d"),  # 주문일자
            "SLL_BUY_DVSN_CD": "00",  # 매도매수구분코드
            "OVRS_EXCG_CD": "KRX",  # 해외거래소코드
            "SORT_SQN": "DS",  # 정렬순서
            "CTX_AREA_FK200": ""  # 연속조회검색조건2
        }
        
        return self._make_request("GET", endpoint, params=params)
    
    def get_daily_chart(self, stock_code: str, start_date: str = None, 
                       end_date: str = None) -> Optional[Dict]:
        """Get daily chart data"""
        endpoint = self.settings.API_ENDPOINTS["daily_chart"]
        
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
            "FID_VOL_CNT": "",  # 거래량
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드
            "FID_COND_SCR_DIV_CODE": "20171"  # 종목분류코드
        }
        
        return self._make_request("GET", endpoint, params=params)
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try to get account info as a connection test
            result = self.get_account_info()
            if result:
                self.logger.info("API connection test successful")
                return True
            else:
                self.logger.error("API connection test failed")
                return False
        except Exception as e:
            self.logger.error(f"API connection test error: {e}")
            return False


def main():
    """Test function"""
    from config.settings import Settings
    
    settings = Settings()
    api_caller = APICaller(settings)
    
    # Test connection
    if api_caller.test_connection():
        print("API connection successful!")
        
        # Test getting stock price
        result = api_caller.get_stock_price("005930")  # 삼성전자
        if result:
            print("Stock price API call successful!")
        else:
            print("Stock price API call failed!")
    else:
        print("API connection failed!")


if __name__ == "__main__":
    main()
