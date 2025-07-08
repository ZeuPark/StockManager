#!/usr/bin/env python3
"""
Configuration Settings for Stock Manager
Kiwoom REST API integration settings and trading strategy parameters
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import logger with relative path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback import
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils"))
    from logger import get_logger


class Settings:
    """Central configuration management for Stock Manager"""
    
    def __init__(self, config_path: str = "config/keys.json"):
        self.config_path = Path(config_path)
        self.logger = get_logger("settings")
        
        # Load secrets
        self.secrets = self._load_secrets()
        
        # Environment settings
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "simulation")  # simulation/production
        
        # Kiwoom REST API settings
        self.KIWOOM_API = {
            "simulation": {
                "host": "https://mockapi.kiwoom.com",  # 모의투자 API
                "appkey": self.secrets.get("simulation", {}).get("appkey"),
                "secretkey": self.secrets.get("simulation", {}).get("secretkey"),
                "token": self.secrets.get("simulation", {}).get("token")
            },
            "production": {
                "host": "https://api.kiwoom.com",  # 실제투자 API
                "appkey": self.secrets.get("production", {}).get("appkey"),
                "secretkey": self.secrets.get("production", {}).get("secretkey"),
                "token": self.secrets.get("production", {}).get("token")
            }
        }
        
        # API Host for current environment
        self.API_HOST = self.KIWOOM_API[self.ENVIRONMENT]["host"]
        
        # API endpoints (실제 Kiwoom API 엔드포인트)
        self.API_ENDPOINTS = {
            "token": "/oauth2/token",
            "account_info": "/api/dostk/acnt",           # 계좌 정보 조회
            "stock_price": "/api/dostk/stkinfo",         # 주식 현재가 조회
            "order": "/api/dostk/ordr",                  # 주식 주문
            "order_status": "/api/dostk/ordr",           # 주문 상태 조회
            "execution": "/api/dostk/exec",              # 체결 정보 조회
            "daily_chart": "/api/dostk/chart",           # 일봉 차트 조회
            "minute_chart": "/api/dostk/chart",          # 분봉 차트 조회
            "market_data": "/api/dostk/stkinfo",         # 시장 데이터
            "real_time": "/api/dostk/stkinfo",           # 실시간 데이터
            "volume_ranking": "/api/dostk/rkinfo",       # 거래량 급증 종목 조회
            "volume_chart": "/api/dostk/chart",          # 거래량 차트 조회
            "execution_strength": "/api/dostk/mrkcond"   # 체결강도 조회
        }
        
        # API IDs for different endpoints (실제 키움 API ID)
        self.API_IDS = {
            "account_info": "kt00018",  # 계좌 평가 잔고 내역
            "order_buy": "kt10000",     # 주식 매수 주문
            "order_sell": "kt10001",    # 주식 매도 주문
            "execution_strength": "ka10007",  # 시세표 성정보
            "stock_price": "ka10007",   # 현재가 조회
            "volume_ranking": "ka10023", # 거래량 급증 종목
            "daily_chart": "ka10081"    # 일봉 차트
        }
        
        # TR IDs for different environments (모의투자 vs 실제거래)
        self.TR_IDS = {
            "simulation": {
                "account_info": "kt00018",  # 모의투자 계좌 조회
                "order": "kt10000",  # 모의투자 주식 주문
                "order_status": "kt10000",  # 모의투자 주문 조회
                "execution": "kt10000",  # 모의투자 체결 조회
                "balance": "kt00018",  # 모의투자 잔고 조회
                "volume_ranking": "ka10023",  # 거래량 급증 종목 조회
                "daily_chart": "ka10081"      # 일봉 차트 조회
            },
            "production": {
                "account_info": "kt00018",  # 실제거래 계좌 조회
                "order": "kt10000",  # 실제거래 주식 주문
                "order_status": "kt10000",  # 실제거래 주문 조회
                "execution": "kt10000",  # 실제거래 체결 조회
                "balance": "kt00018",  # 실제거래 잔고 조회
                "volume_ranking": "ka10023",  # 거래량 급증 종목 조회
                "daily_chart": "ka10081"      # 일봉 차트 조회
            }
        }
        
        # Trading strategy parameters
        self.TRADING_STRATEGY = {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "ma_short": 5,
            "ma_long": 20,
            "volume_ratio_threshold": 2.0,  # 거래량 급증 기준
            "price_change_threshold": 0.02,  # 가격 변동 기준 (2%)
            "momentum_period": 10
        }
        
        # Real-time trading conditions (실제 거래 조건)
        self.MOMENTUM_CONDITIONS = {
            "volume_requirement": {
                "enabled": True,
                "threshold": 1.0,  # 오늘 누적 거래량 ≥ 전일 총 거래량
                "description": "거래량 필수 조건"
            },
            "execution_strength": {
                "enabled": True,
                "threshold": 1.1,  # 체결강도 ≥ 110%
                "description": "매수세 우위 조건"
            },
            "price_change": {
                "enabled": True,
                "threshold": 0.02,  # 등락률 ≥ +2%
                "description": "가격 상승 조건"
            },
            "trade_value": {
                "enabled": True,
                "threshold": 100_000_000,  # 1분 거래대금 ≥ 1억원
                "description": "유동성 조건"
            },
            "opening_price_rise": {
                "enabled": True,
                "description": "시가 대비 상승 조건"
            },
            "price_movement": {
                "enabled": True,
                "min_tick_change": 1,  # 최소 호가 단위 이상 변동
                "description": "시세 변동 조건"
            }
        }
        
        # Volume scanning conditions (최적화된 거래 조건 - 분석 결과 기반)
        self.VOLUME_SCANNING = {
            "enabled": True,
            "scan_interval": 30,  # 스캔 간격 (30초)
            "min_volume_ratio": 0.2,  # 거래량비율 하한선: 0.2% (기존 1.0%에서 완화)
            "max_volume_ratio": 1.9,  # 거래량비율 상한선: 1.9% (기존 2.0%에서 조정)
            "min_trade_value": 180_000_000,  # 최소 거래대금: 1.8억원 (기존 1억원에서 상향)
            "max_trade_value": 8_100_000_000,  # 최대 거래대금: 81억원 (새로 추가)
            "min_price_change": 0.01,  # 등락률: 1% 이상 (기존 2%에서 완화)
            "min_execution_strength": 1.1,  # 체결강도: 110% 이상 (유지)
            "max_candidates": 3,  # 최대 후보 종목 수: 3개 (기존 5개에서 축소)
            "auto_trade_enabled": True,  # 자동매매 활성화
            "max_hold_time": 3600,  # 최대 보유 시간 (1시간)
            "optimal_volume_ratio_range": [0.5, 1.8],  # 최적 거래량비율 범위
            "optimal_trade_value_range": [1_000_000_000, 20_000_000_000],  # 최적 거래대금 범위 (10억~200억)
            "max_stock_price": 50000,  # 최대 주가: 5만원 미만 (새로 추가)
            "min_stock_price": 1000    # 최소 주가: 1천원 이상 (새로 추가)
        }
        
        # Sell parameters (매도 설정) - 패턴 분석 기반 최적화
        self.SELL_SETTINGS = {
            "enabled": True,  # 자동 매도 활성화
            "monitoring_interval": 10,  # 매도 모니터링 주기 (30초에서 10초로 단축 - 빠른 반응)
            "stop_loss_percent": -1.0,  # 손절 기준 (패턴 분석 결과 유지)
            "take_profit_percent": 2.5,  # 익절 기준 (2.0% → 2.5%로 상향 - 패턴 분석 기반)
            "sell_all_on_stop_loss": True,  # 손절 시 전량 매도
            "sell_all_on_take_profit": True,  # 익절 시 전량 매도
            "min_hold_time": 300,  # 최소 보유 시간 (5분)
            "enable_partial_sell": False,  # 부분 매도 활성화
            "partial_sell_ratio": 0.5  # 부분 매도 비율 (50%)
        }
        
        # WebSocket settings (연결 안정성 개선)
        self.WEBSOCKET = {
            "reconnect_interval": 10,  # 재연결 간격 (5초 → 10초로 증가)
            "heartbeat_interval": 30,  # 하트비트 간격 (초)
            "max_reconnect_attempts": 3,  # 최대 재연결 시도 횟수 (5회 → 3회로 감소)
            "connection_timeout": 30,  # 연결 타임아웃 (10초 → 30초로 증가)
            "message_timeout": 10  # 메시지 타임아웃 (5초 → 10초로 증가)
        }
        
        # WebSocket URLs (실제 키움 API 웹소켓 URL로 수정)
        if self.ENVIRONMENT == "simulation":
            self.KIWOOM_WEBSOCKET_URL = "wss://openapi.kiwoom.com:10000/websocket"  # 모의투자 웹소켓
        else:
            self.KIWOOM_WEBSOCKET_URL = "wss://openapi.kiwoom.com:10000/websocket"  # 실제투자 웹소켓
        
        # Risk management - 패턴 분석 기반 최적화 + 10종목 제한
        self.RISK_MANAGEMENT = {
            "max_position_size": 0.05,  # 전체 자산의 5% (10% → 5%)
            "position_size_ratio": 0.02,  # 계좌 잔고의 2% (5% → 2%)
            "max_daily_loss": 0.03,    # 일일 최대 손실 3% (5% → 3%)
            "stop_loss": 0.03,         # 개별 종목 손절 3% (패턴 분석 결과 유지)
            "take_profit": 0.10,       # 개별 종목 익절 10%
            "max_positions": 10,       # 최대 보유 종목 수 (정확히 10개로 제한)
            "strict_position_limit": True,  # 10종목 제한 엄격 적용
            "min_trade_amount": 100000,  # 최소 거래 금액 (10만원) - 패턴 분석 기반
            "max_trade_amount": 500000,  # 최대 거래 금액 (50만원) - 패턴 분석 기반 추가
            "min_position_size": 1,    # 최소 주문 수량
            "max_quantity_per_stock": 10,  # 종목당 최대 보유 수량 (10주) - 패턴 분석 기반 추가
            "max_per_stock": 1000000   # 주식별 최대 투자 금액 (100만원)
        }
        
        # Database settings
        self.DATABASE = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "stock_manager"),
            "username": os.getenv("DB_USER", "stock_user"),
            "password": os.getenv("DB_PASSWORD", "stock_password")
        }
        
        # Redis settings
        self.REDIS = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0"))
        }
        
        # System settings
        self.SYSTEM = {
            "main_loop_interval": 1,  # 메인 루프 간격 (초)
            "data_update_interval": 30,  # 데이터 업데이트 간격 (60초에서 30초로 단축)
            "log_level": "INFO",
            "max_retries": 3,
            "timeout": 30,
            "auto_execute_orders": False,  # 자동 주문 실행 여부
            "min_confidence": 0.7,  # 최소 신뢰도 (0.0 ~ 1.0)
            "signal_cooldown": 300,  # 신호 쿨다운 (초)
            "enable_notifications": True,  # 알림 활성화
            "save_signals_to_db": True  # 신호를 DB에 저장
        }
        
        # Market hours (KST)
        self.MARKET_HOURS = {
            "open": "09:00",
            "close": "15:30"
        }
        
        # Target stocks (관심 종목)
        self.TARGET_STOCKS = [
            "005930",  # 삼성전자
            "000660",  # SK하이닉스
            "035420",  # NAVER
            "051910",  # LG화학
            "006400",  # 삼성SDI
            "035720",  # 카카오
            "207940",  # 삼성바이오로직스
            "068270",  # 셀트리온
            "323410",  # 카카오뱅크
            "373220"   # LG에너지솔루션
        ]
        
        self.logger.info(f"Settings initialized for environment: {self.ENVIRONMENT}")
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from config file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Secrets file not found: {self.config_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading secrets: {e}")
            return {}
    
    def get_api_config(self, environment: Optional[str] = None) -> Dict[str, str]:
        """Get API configuration for specified environment"""
        env = environment or self.ENVIRONMENT
        return self.KIWOOM_API.get(env, {})
    
    def get_api_url(self, endpoint: str, environment: Optional[str] = None) -> str:
        """Get full API URL for endpoint"""
        env = environment or self.ENVIRONMENT
        host = self.KIWOOM_API[env]["host"]
        return host + self.API_ENDPOINTS.get(endpoint, endpoint)
    
    def get_headers(self, environment: Optional[str] = None, tr_type: str = "account_info") -> Dict[str, str]:
        """Get API headers with authentication and API ID"""
        env = environment or self.ENVIRONMENT
        api_config = self.get_api_config(env)
        
        # Get API ID for the specific request type
        api_id = self.API_IDS.get(tr_type, "")
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {api_config.get("token", "")}',
            'appkey': api_config.get("appkey", ""),
            'appsecret': api_config.get("secretkey", ""),
            'api-id': api_id,
        }
        
        return headers
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        from datetime import datetime, time
        import pytz
        
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        current_time = now.time()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        open_time = time(9, 0)
        close_time = time(15, 30)
        
        return open_time <= current_time <= close_time
    
    def update_token(self, token: str, environment: Optional[str] = None):
        """Update token in settings and save to file"""
        env = environment or self.ENVIRONMENT
        self.KIWOOM_API[env]["token"] = token
        
        # Update secrets file
        if env in self.secrets:
            self.secrets[env]["token"] = token
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.secrets, f, indent=2)
                self.logger.info(f"Token updated for {env} environment")
            except Exception as e:
                self.logger.error(f"Failed to save token: {e}")
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        try:
            # Check required API keys
            for env in ["simulation", "production"]:
                api_config = self.KIWOOM_API[env]
                if not api_config.get("appkey") or not api_config.get("secretkey"):
                    self.logger.warning(f"Missing API keys for {env} environment")
            
            # Check database connection
            if not all(self.DATABASE.values()):
                self.logger.warning("Database configuration incomplete")
            
            # Check trading parameters
            if self.TRADING_STRATEGY["rsi_period"] <= 0:
                self.logger.error("Invalid RSI period")
                return False
            
            if self.RISK_MANAGEMENT["max_position_size"] > 1.0:
                self.logger.error("Max position size cannot exceed 100%")
                return False
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False


# Global settings instance
_settings_instance = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


if __name__ == "__main__":
    # Test settings
    settings = Settings()
    
    print("=== Stock Manager Settings ===")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"API Host: {settings.get_api_config()['host']}")
    print(f"Target Stocks: {len(settings.TARGET_STOCKS)}")
    print(f"Market Open: {settings.is_market_open()}")
    
    # Validate configuration
    if settings.validate_config():
        print("Configuration validation: PASSED")
    else:
        print("Configuration validation: FAILED")
