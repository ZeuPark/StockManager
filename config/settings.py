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
    
    def __init__(self, config_path: str = "config/secrets.json"):
        self.config_path = Path(config_path)
        self.logger = get_logger("settings")
        
        # Load secrets
        self.secrets = self._load_secrets()
        
        # Environment settings
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "simulation")  # simulation/production
        
        # Kiwoom REST API settings
        self.KIWOOM_API = {
            "simulation": {
                "host": "https://mockapi.kiwoom.com",
                "appkey": self.secrets.get("simulation", {}).get("appkey"),
                "secretkey": self.secrets.get("simulation", {}).get("secretkey"),
                "token": self.secrets.get("simulation", {}).get("token")
            },
            "production": {
                "host": "https://api.kiwoom.com",
                "appkey": self.secrets.get("production", {}).get("appkey"),
                "secretkey": self.secrets.get("production", {}).get("secretkey"),
                "token": self.secrets.get("production", {}).get("token")
            }
        }
        
        # API endpoints
        self.API_ENDPOINTS = {
            "token": "/oauth2/token",
            "account_info": "/uapi/domestic-stock/v1/trading/inquire-balance",
            "stock_price": "/uapi/domestic-stock/v1/quotations/inquire-price",
            "order": "/uapi/domestic-stock/v1/trading/order-cash",
            "order_status": "/uapi/domestic-stock/v1/trading/inquire-order",
            "execution": "/uapi/domestic-stock/v1/trading/inquire-execution",
            "daily_chart": "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            "minute_chart": "/uapi/domestic-stock/v1/quotations/inquire-time-series",
            "market_data": "/uapi/domestic-stock/v1/quotations/inquire-price"
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
        
        # Risk management
        self.RISK_MANAGEMENT = {
            "max_position_size": 0.1,  # 전체 자산의 10%
            "max_daily_loss": 0.05,    # 일일 최대 손실 5%
            "stop_loss": 0.05,         # 개별 종목 손절 5%
            "take_profit": 0.15,       # 개별 종목 익절 15%
            "max_positions": 5,        # 최대 보유 종목 수
            "min_trade_amount": 100000  # 최소 거래 금액 (10만원)
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
            "data_update_interval": 60,  # 데이터 업데이트 간격 (초)
            "log_level": "INFO",
            "max_retries": 3,
            "timeout": 30
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
    
    def get_headers(self, environment: Optional[str] = None) -> Dict[str, str]:
        """Get API headers with authentication"""
        env = environment or self.ENVIRONMENT
        api_config = self.get_api_config(env)
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {api_config.get("token", "")}',
            'appkey': api_config.get("appkey", ""),
            'appsecret': api_config.get("secretkey", ""),
            'tr_id': '',  # Will be set per request
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
