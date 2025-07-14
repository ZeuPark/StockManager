import requests
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 1. API 설정 및 인증
# ============================================================================
class APIConfig:
    """API 설정"""
    
    def __init__(self, api_key: str, secret_key: str, account_number: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.account_number = account_number
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.token_expires = None
    
    def get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.api_key,
            "appSecret": self.secret_key,
            "tr_id": "TTTC0802U"  # 주식 현금 매수 주문
        }
        return headers

class APIAuthenticator:
    """API 인증 관리"""
    
    def __init__(self, config: APIConfig):
        self.config = config
    
    async def authenticate(self) -> bool:
        """API 인증"""
        try:
            url = f"{self.config.base_url}/oauth2/tokenP"
            
            data = {
                "grant_type": "client_credentials",
                "appkey": self.config.api_key,
                "appsecret": self.config.secret_key
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.config.access_token = result.get("access_token")
                expires_in = result.get("expires_in", 86400)
                self.config.token_expires = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("API 인증 성공")
                return True
            else:
                logger.error(f"API 인증 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"API 인증 중 오류: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """토큰 유효성 검사"""
        if not self.config.access_token or not self.config.token_expires:
            return False
        
        return datetime.now() < self.config.token_expires

# ============================================================================
# 2. 주식 시세 조회
# ============================================================================
class StockQuoteAPI:
    """주식 시세 조회 API"""
    
    def __init__(self, config: APIConfig):
        self.config = config
    
    async def get_current_price(self, stock_code: str) -> Optional[float]:
        """현재가 조회"""
        try:
            if not self.config.is_token_valid():
                logger.warning("토큰이 만료되었습니다. 재인증이 필요합니다.")
                return None
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "FHKST01010100"  # 주식 현재가 시세 조회
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    output = result.get("output", {})
                    current_price = float(output.get("stck_prpr", 0))
                    return current_price
                else:
                    logger.error(f"시세 조회 실패: {result.get('msg1')}")
                    return None
            else:
                logger.error(f"시세 조회 HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"시세 조회 중 오류: {e}")
            return None
    
    async def get_daily_chart(self, stock_code: str, date: str) -> Optional[Dict]:
        """일별 차트 데이터 조회"""
        try:
            if not self.config.is_token_valid():
                return None
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
            
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_DATE_1": date,
                "FID_INPUT_DATE_2": date
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "FHKST01010400"  # 주식 일자별 시세 조회
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    return result.get("output", {})
                else:
                    logger.error(f"일별 차트 조회 실패: {result.get('msg1')}")
                    return None
            else:
                logger.error(f"일별 차트 조회 HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"일별 차트 조회 중 오류: {e}")
            return None

# ============================================================================
# 3. 주문 실행
# ============================================================================
class OrderAPI:
    """주문 실행 API"""
    
    def __init__(self, config: APIConfig):
        self.config = config
    
    async def place_buy_order(self, stock_code: str, quantity: int, price: float) -> bool:
        """매수 주문"""
        try:
            if not self.config.is_token_valid():
                logger.warning("토큰이 만료되었습니다. 재인증이 필요합니다.")
                return False
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            data = {
                "CANO": self.config.account_number,
                "ACNT_PRDT_CD": "01",
                "PDNO": stock_code,
                "ORD_DVSN": "00",  # 지정가
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(price),
                "CTAC_TLNO": "",
                "MGCO_APTM_ODNO": "",
                "ORD_APLC_ID": "",
                "ORD_APLC_NM": "",
                "ORD_APLC_ICLD_YN": "N"
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "TTTC0802U"  # 주식 현금 매수 주문
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    logger.info(f"매수 주문 성공: {stock_code} {quantity}주 @ {price}")
                    return True
                else:
                    logger.error(f"매수 주문 실패: {result.get('msg1')}")
                    return False
            else:
                logger.error(f"매수 주문 HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"매수 주문 중 오류: {e}")
            return False
    
    async def place_sell_order(self, stock_code: str, quantity: int, price: float) -> bool:
        """매도 주문"""
        try:
            if not self.config.is_token_valid():
                logger.warning("토큰이 만료되었습니다. 재인증이 필요합니다.")
                return False
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            data = {
                "CANO": self.config.account_number,
                "ACNT_PRDT_CD": "01",
                "PDNO": stock_code,
                "ORD_DVSN": "00",  # 지정가
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(price),
                "CTAC_TLNO": "",
                "MGCO_APTM_ODNO": "",
                "ORD_APLC_ID": "",
                "ORD_APLC_NM": "",
                "ORD_APLC_ICLD_YN": "N"
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "TTTC0801U"  # 주식 현금 매도 주문
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    logger.info(f"매도 주문 성공: {stock_code} {quantity}주 @ {price}")
                    return True
                else:
                    logger.error(f"매도 주문 실패: {result.get('msg1')}")
                    return False
            else:
                logger.error(f"매도 주문 HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"매도 주문 중 오류: {e}")
            return False
    
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            if not self.config.is_token_valid():
                return False
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            data = {
                "CANO": self.config.account_number,
                "ACNT_PRDT_CD": "01",
                "KRX_FWDG_ORD_ORGNO": "",
                "ORGN_ODNO": order_id,
                "ORD_DVSN": "02",  # 취소
                "ORD_QTY": "0",
                "ORD_UNPR": "0"
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "TTTC0803U"  # 주식 주문 취소
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    logger.info(f"주문 취소 성공: {order_id}")
                    return True
                else:
                    logger.error(f"주문 취소 실패: {result.get('msg1')}")
                    return False
            else:
                logger.error(f"주문 취소 HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"주문 취소 중 오류: {e}")
            return False

# ============================================================================
# 4. 계좌 정보 조회
# ============================================================================
class AccountAPI:
    """계좌 정보 조회 API"""
    
    def __init__(self, config: APIConfig):
        self.config = config
    
    async def get_account_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회"""
        try:
            if not self.config.is_token_valid():
                return None
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            params = {
                "CANO": self.config.account_number,
                "ACNT_PRDT_CD": "01",
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "TTTC8434R"  # 주식 잔고2 조회
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    return result.get("output1", {})
                else:
                    logger.error(f"잔고 조회 실패: {result.get('msg1')}")
                    return None
            else:
                logger.error(f"잔고 조회 HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"잔고 조회 중 오류: {e}")
            return None
    
    async def get_positions(self) -> List[Dict]:
        """보유 종목 조회"""
        try:
            if not self.config.is_token_valid():
                return []
            
            url = f"{self.config.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            params = {
                "CANO": self.config.account_number,
                "ACNT_PRDT_CD": "01",
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "01",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            headers = self.config.get_headers()
            headers["tr_id"] = "TTTC8434R"  # 주식 잔고2 조회
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("rt_cd") == "0":
                    output2 = result.get("output2", [])
                    positions = []
                    
                    for item in output2:
                        if float(item.get("hldg_qty", 0)) > 0:
                            positions.append({
                                "stock_code": item.get("pdno"),
                                "stock_name": item.get("prdt_name"),
                                "quantity": int(item.get("hldg_qty", 0)),
                                "avg_price": float(item.get("pchs_avg_pric", 0)),
                                "current_price": float(item.get("prcs", 0)),
                                "market_value": float(item.get("evlu_pamt", 0)),
                                "unrealized_pnl": float(item.get("evlu_pfls_amt", 0))
                            })
                    
                    return positions
                else:
                    logger.error(f"보유 종목 조회 실패: {result.get('msg1')}")
                    return []
            else:
                logger.error(f"보유 종목 조회 HTTP 오류: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"보유 종목 조회 중 오류: {e}")
            return []

# ============================================================================
# 5. 통합 API 클라이언트
# ============================================================================
class APIClient:
    """통합 API 클라이언트"""
    
    def __init__(self, api_key: str, secret_key: str, account_number: str):
        self.config = APIConfig(api_key, secret_key, account_number)
        self.authenticator = APIAuthenticator(self.config)
        self.quote_api = StockQuoteAPI(self.config)
        self.order_api = OrderAPI(self.config)
        self.account_api = AccountAPI(self.config)
    
    async def initialize(self) -> bool:
        """API 클라이언트 초기화"""
        return await self.authenticator.authenticate()
    
    async def place_order(self, order) -> bool:
        """주문 실행"""
        if order.order_type.value == "BUY":
            return await self.order_api.place_buy_order(
                order.stock_code, order.quantity, order.price
            )
        elif order.order_type.value == "SELL":
            return await self.order_api.place_sell_order(
                order.stock_code, order.quantity, order.price
            )
        else:
            logger.error(f"지원하지 않는 주문 타입: {order.order_type}")
            return False
    
    async def get_current_price(self, stock_code: str) -> Optional[float]:
        """현재가 조회"""
        return await self.quote_api.get_current_price(stock_code)
    
    async def get_account_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회"""
        return await self.account_api.get_account_balance()
    
    async def get_positions(self) -> List[Dict]:
        """보유 종목 조회"""
        return await self.account_api.get_positions()

# ============================================================================
# 6. 설정 파일 관리
# ============================================================================
class APIConfigManager:
    """API 설정 관리"""
    
    def __init__(self, config_file: str = "api_config.json"):
        self.config_file = config_file
    
    def load_config(self) -> Optional[Dict]:
        """설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"설정 파일이 없습니다: {self.config_file}")
            return None
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return None
    
    def save_config(self, config: Dict) -> bool:
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
            return False
    
    def create_sample_config(self) -> Dict:
        """샘플 설정 생성"""
        sample_config = {
            "api_key": "your_api_key_here",
            "secret_key": "your_secret_key_here",
            "account_number": "your_account_number_here",
            "base_url": "https://openapi.koreainvestment.com:9443",
            "simulation_mode": True
        }
        
        self.save_config(sample_config)
        return sample_config

# ============================================================================
# 7. 메인 실행
# ============================================================================
async def main():
    """API 클라이언트 테스트"""
    # 설정 관리자
    config_manager = APIConfigManager()
    config = config_manager.load_config()
    
    if not config:
        logger.info("샘플 설정 파일을 생성합니다.")
        config = config_manager.create_sample_config()
        logger.info("api_config.json 파일을 편집하여 실제 API 키를 입력하세요.")
        return
    
    # API 클라이언트 초기화
    api_client = APIClient(
        config["api_key"],
        config["secret_key"],
        config["account_number"]
    )
    
    # 인증
    if not await api_client.initialize():
        logger.error("API 인증 실패")
        return
    
    # 테스트
    logger.info("API 클라이언트 테스트 시작")
    
    # 현재가 조회 테스트
    current_price = await api_client.get_current_price("005930")  # 삼성전자
    if current_price:
        logger.info(f"삼성전자 현재가: {current_price:,}원")
    
    # 계좌 잔고 조회 테스트
    balance = await api_client.get_account_balance()
    if balance:
        logger.info(f"계좌 잔고: {balance}")
    
    # 보유 종목 조회 테스트
    positions = await api_client.get_positions()
    if positions:
        logger.info(f"보유 종목: {positions}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 