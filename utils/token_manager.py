#!/usr/bin/env python3
"""
Token Manager for Stock Manager
Handles token refresh for both simulation and production environments
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import json
from pathlib import Path
from typing import Dict, Optional

# Import logger with relative path
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback import
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from logger import get_logger


class TokenManager:
    """Manages API tokens for Kiwoom API"""
    
    def __init__(self, settings):
        # settings: Settings 객체
        self.settings = settings
        self.secrets_path = Path(settings.config_path)
        self.logger = get_logger("token_manager")
        
        # API endpoints
        self.PRODUCTION_HOST = 'https://api.kiwoom.com'
        self.SIMULATION_HOST = 'https://mockapi.kiwoom.com'
        
    def load_secrets(self) -> Dict:
        """Load secrets from config file"""
        try:
            with open(self.secrets_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Secrets file not found: {self.secrets_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in secrets file: {e}")
            raise
    
    def save_secrets(self, secrets: Dict):
        """Save secrets to config file"""
        try:
            with open(self.secrets_path, 'w', encoding='utf-8') as f:
                json.dump(secrets, f, indent=2)
            self.logger.info("Secrets file updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to save secrets: {e}")
            raise
    
    def get_access_token(self, appkey: str, secretkey: str, is_simulation: bool = True) -> Optional[str]:
        """Get access token from Kiwoom API"""
        host = self.SIMULATION_HOST if is_simulation else self.PRODUCTION_HOST
        endpoint = '/oauth2/token'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }
        
        params = {
            'grant_type': 'client_credentials',
            'appkey': appkey,
            'secretkey': secretkey,
        }
        
        try:
            self.logger.info(f"Requesting token from: {host}")
            response = requests.post(url, headers=headers, json=params)
            
            self.logger.info(f"Token request status: {response.status_code}")
            self.logger.debug(f"Response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for different possible token field names
                token = None
                if 'token' in data:
                    token = data['token']
                elif 'access_token' in data:
                    token = data['access_token']
                elif 'accessToken' in data:
                    token = data['accessToken']
                elif 'result' in data and isinstance(data['result'], dict):
                    # Some APIs wrap the token in a 'result' field
                    result = data['result']
                    if 'token' in result:
                        token = result['token']
                    elif 'access_token' in result:
                        token = result['access_token']
                
                if token:
                    self.logger.info("Token received successfully")
                    return token
                else:
                    self.logger.error("Response does not contain token field")
                    self.logger.error(f"Available fields: {list(data.keys())}")
                    return None
            else:
                self.logger.error(f"Token request failed: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Network error during token request: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            return None
    
    def refresh_token(self, environment: str = "simulation") -> bool:
        """Refresh token for specified environment"""
        try:
            # Load current secrets
            secrets = self.load_secrets()
            
            if environment not in secrets:
                self.logger.error(f"Environment '{environment}' not found in secrets")
                return False
            
            env_config = secrets[environment]
            appkey = env_config['appkey']
            secretkey = env_config['secretkey']
            
            # Get new token
            is_simulation = (environment == "simulation")
            new_token = self.get_access_token(appkey, secretkey, is_simulation)
            
            if new_token:
                # Update token in secrets
                secrets[environment]['token'] = new_token
                self.save_secrets(secrets)
                self.logger.info(f"Token refreshed for {environment} environment")
                return True
            else:
                self.logger.error(f"Failed to refresh token for {environment} environment")
                return False
                
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            return False
    
    def refresh_all_tokens(self) -> Dict[str, bool]:
        """Refresh tokens for all environments"""
        results = {}
        
        try:
            secrets = self.load_secrets()
            
            for environment in secrets.keys():
                self.logger.info(f"Refreshing token for {environment} environment")
                results[environment] = self.refresh_token(environment)
                
        except Exception as e:
            self.logger.error(f"Error refreshing all tokens: {e}")
            
        return results
    
    def get_current_token(self, environment: str = "simulation") -> Optional[str]:
        """Get current token for specified environment"""
        try:
            secrets = self.load_secrets()
            if environment in secrets:
                return secrets[environment].get('token')
            else:
                self.logger.error(f"Environment '{environment}' not found")
                return None
        except Exception as e:
            self.logger.error(f"Error getting current token: {e}")
            return None

    async def get_valid_token(self):
        """
        현재 토큰을 반환하거나, 만료 시 새로 갱신해서 반환 (더미 구현)
        """
        env = self.settings.ENVIRONMENT
        token = self.settings.KIWOOM_API[env].get("token", "")
        
        # 빈 토큰이면 더미 토큰 반환
        if not token:
            if env == "simulation":
                return "dummy_token_simulation"
            elif env == "production":
                return "dummy_token_production"
            else:
                return "dummy_token_default"
        
        return token


def main():
    """Main function for token management"""
    from config.settings import Settings
    settings = Settings()
    token_manager = TokenManager(settings)
    
    print("=== Token Manager ===")
    print("1. Refresh simulation token")
    print("2. Refresh production token")
    print("3. Refresh all tokens")
    print("4. Show current tokens")
    
    choice = input("Select option (1-4): ").strip()
    
    if choice == "1":
        success = token_manager.refresh_token("simulation")
        print(f"Simulation token refresh: {'Success' if success else 'Failed'}")
        
    elif choice == "2":
        success = token_manager.refresh_token("production")
        print(f"Production token refresh: {'Success' if success else 'Failed'}")
        
    elif choice == "3":
        results = token_manager.refresh_all_tokens()
        for env, success in results.items():
            print(f"{env}: {'Success' if success else 'Failed'}")
            
    elif choice == "4":
        sim_token = token_manager.get_current_token("simulation")
        prod_token = token_manager.get_current_token("production")
        
        print(f"Simulation token: {sim_token[:20] + '...' if sim_token else 'None'}")
        print(f"Production token: {prod_token[:20] + '...' if prod_token else 'None'}")
        
    else:
        print("Invalid choice")


if __name__ == '__main__':
    main() 