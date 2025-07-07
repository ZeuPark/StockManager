#!/usr/bin/env python3
"""
Account Monitor - 계좌 모니터링 모듈
실시간 계좌 잔고, 수익률, 포트폴리오 분석 기능
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from config.settings import Settings
from utils.token_manager import TokenManager
from utils.logger import get_logger
from database.database_manager import get_database_manager

logger = get_logger("account_monitor")


@dataclass
class AccountSummary:
    """계좌 요약 정보"""
    deposit: int  # 예수금
    total_evaluation: int  # 총평가금액
    total_profit_rate: float  # 총수익률
    total_purchase: int  # 총매입금액
    total_profit_loss: int  # 총손익
    estimated_assets: int  # 추정자산


@dataclass
class PortfolioItem:
    """포트폴리오 아이템"""
    stock_code: str
    stock_name: str
    current_price: int
    quantity: int
    purchase_price: int
    purchase_amount: int
    evaluation_amount: int
    profit_loss: int
    profit_rate: float
    orderable_quantity: int


@dataclass
class RiskMetrics:
    """리스크 지표"""
    max_loss_rate: float  # 최대 손실률
    portfolio_concentration: float  # 포트폴리오 집중도
    daily_var: float  # 일일 VaR (Value at Risk)
    sharpe_ratio: float  # 샤프 비율


class AccountMonitor:
    """계좌 모니터링 클래스"""
    
    def __init__(self, settings: Settings, token_manager: TokenManager):
        self.settings = settings
        self.token_manager = token_manager
        self.db = get_database_manager()
        
        # 모니터링 설정
        self.monitoring_interval = 30  # 30초마다 모니터링
        self.risk_thresholds = {
            'max_loss_rate': -10.0,  # 최대 손실률 -10%
            'concentration_limit': 30.0,  # 단일 종목 집중도 30%
            'daily_loss_limit': -5.0  # 일일 손실 한도 -5%
        }
        
        # 실시간 데이터 캐시
        self.last_account_summary: Optional[AccountSummary] = None
        self.last_portfolio: List[PortfolioItem] = []
        self.last_update_time: Optional[datetime] = None
        
        # 알림 상태
        self.alert_history: List[Dict] = []
        
        logger.info("계좌 모니터링 초기화 완료")
    
    async def get_account_summary(self) -> Optional[AccountSummary]:
        """계좌 요약 정보 조회"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                logger.error("유효한 토큰을 가져올 수 없습니다.")
                return None
            
            url = f"{self.settings.API_HOST}/api/dostk/acnt"
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'authorization': f'Bearer {token}',
                'api-id': 'kt00018',
                'cont-yn': 'N',
            }
            data = {
                'qry_tp': '1',
                'dmst_stex_tp': 'KRX',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        logger.error(f"계좌 요약 조회 실패: {response.status}")
                        return None
                    
                    result = await response.json()
                    if result.get('return_code') != 0:
                        logger.error(f"API 오류: {result.get('return_message', 'Unknown error')}")
                        return None
                    
                    # 데이터 파싱
                    summary = AccountSummary(
                        deposit=int(str(result.get('prsm_dpst_aset_amt', '0')).lstrip('0') or '0'),
                        total_evaluation=int(str(result.get('tot_evlt_amt', '0')).lstrip('0') or '0'),
                        total_profit_rate=float(str(result.get('tot_prft_rt', '0')).replace('+', '').lstrip('0') or '0'),
                        total_purchase=int(str(result.get('tot_pur_amt', '0')).lstrip('0') or '0'),
                        total_profit_loss=int(str(result.get('tot_evlt_pl', '0')).lstrip('0') or '0'),
                        estimated_assets=int(str(result.get('tot_evlt_amt', '0')).lstrip('0') or '0')
                    )
                    
                    # 데이터베이스에 저장
                    self._save_account_summary(summary)
                    
                    return summary
                    
        except Exception as e:
            logger.error(f"계좌 요약 조회 중 오류: {e}")
            return None
    
    async def get_portfolio(self) -> List[PortfolioItem]:
        """포트폴리오 조회"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                logger.error("유효한 토큰을 가져올 수 없습니다.")
                return []
            
            url = f"{self.settings.API_HOST}/api/dostk/acnt"
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'authorization': f'Bearer {token}',
                'api-id': 'kt00018',
                'cont-yn': 'N',
            }
            data = {
                'qry_tp': '1',
                'dmst_stex_tp': 'KRX',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        logger.error(f"포트폴리오 조회 실패: {response.status}")
                        return []
                    
                    result = await response.json()
                    if result.get('return_code') != 0:
                        logger.error(f"API 오류: {result.get('return_message', 'Unknown error')}")
                        return []
                    
                    portfolio_list = result.get('acnt_evlt_remn_indv_tot', [])
                    portfolio_items = []
                    
                    for item in portfolio_list:
                        portfolio_item = PortfolioItem(
                            stock_code=item.get('stk_cd', ''),
                            stock_name=item.get('stk_nm', ''),
                            current_price=int(str(item.get('cur_prc', '0')).lstrip('0') or '0'),
                            quantity=int(str(item.get('rmnd_qty', '0')).lstrip('0') or '0'),
                            purchase_price=int(str(item.get('pur_pric', '0')).lstrip('0') or '0'),
                            purchase_amount=int(str(item.get('pur_amt', '0')).lstrip('0') or '0'),
                            evaluation_amount=int(str(item.get('evlt_amt', '0')).lstrip('0') or '0'),
                            profit_loss=int(str(item.get('evltv_prft', '0')).lstrip('0') or '0'),
                            profit_rate=float(str(item.get('prft_rt', '0')).replace('+', '').lstrip('0') or '0'),
                            orderable_quantity=int(str(item.get('trde_able_qty', '0')).lstrip('0') or '0')
                        )
                        portfolio_items.append(portfolio_item)
                    
                    # 데이터베이스에 저장
                    self._save_portfolio(portfolio_items)
                    
                    return portfolio_items
                    
        except Exception as e:
            logger.error(f"포트폴리오 조회 중 오류: {e}")
            return []
    
    def calculate_risk_metrics(self, portfolio: List[PortfolioItem], summary: AccountSummary) -> RiskMetrics:
        """리스크 지표 계산"""
        try:
            if not portfolio:
                return RiskMetrics(0.0, 0.0, 0.0, 0.0)
            
            # 최대 손실률
            max_loss_rate = min([item.profit_rate for item in portfolio]) if portfolio else 0.0
            
            # 포트폴리오 집중도 (가장 큰 비중의 종목)
            total_evaluation = sum(item.evaluation_amount for item in portfolio)
            if total_evaluation > 0:
                max_concentration = max([item.evaluation_amount / total_evaluation * 100 for item in portfolio])
            else:
                max_concentration = 0.0
            
            # 일일 VaR (간단한 계산)
            daily_var = -5.0  # 기본값, 실제로는 과거 데이터 기반 계산 필요
            
            # 샤프 비율 (간단한 계산)
            if summary.total_profit_rate != 0:
                sharpe_ratio = summary.total_profit_rate / 10.0  # 간단한 계산
            else:
                sharpe_ratio = 0.0
            
            return RiskMetrics(
                max_loss_rate=max_loss_rate,
                portfolio_concentration=max_concentration,
                daily_var=daily_var,
                sharpe_ratio=sharpe_ratio
            )
            
        except Exception as e:
            logger.error(f"리스크 지표 계산 중 오류: {e}")
            return RiskMetrics(0.0, 0.0, 0.0, 0.0)
    
    def check_risk_alerts(self, portfolio: List[PortfolioItem], summary: AccountSummary, risk_metrics: RiskMetrics) -> List[Dict]:
        """리스크 알림 체크"""
        alerts = []
        
        try:
            # 손실률 알림
            if risk_metrics.max_loss_rate < self.risk_thresholds['max_loss_rate']:
                alerts.append({
                    'type': 'LOSS_RATE',
                    'level': 'HIGH',
                    'message': f"손실률 한도 초과: {risk_metrics.max_loss_rate:.2f}% (한도: {self.risk_thresholds['max_loss_rate']:.1f}%)",
                    'timestamp': datetime.now()
                })
            
            # 포트폴리오 집중도 알림
            if risk_metrics.portfolio_concentration > self.risk_thresholds['concentration_limit']:
                alerts.append({
                    'type': 'CONCENTRATION',
                    'level': 'MEDIUM',
                    'message': f"포트폴리오 집중도 높음: {risk_metrics.portfolio_concentration:.1f}% (한도: {self.risk_thresholds['concentration_limit']:.1f}%)",
                    'timestamp': datetime.now()
                })
            
            # 총 손실 알림
            if summary.total_profit_loss < 0 and summary.total_profit_rate < self.risk_thresholds['daily_loss_limit']:
                alerts.append({
                    'type': 'DAILY_LOSS',
                    'level': 'HIGH',
                    'message': f"일일 손실 한도 초과: {summary.total_profit_rate:.2f}% (한도: {self.risk_thresholds['daily_loss_limit']:.1f}%)",
                    'timestamp': datetime.now()
                })
            
            # 새로운 알림만 필터링
            new_alerts = []
            for alert in alerts:
                if not any(existing['type'] == alert['type'] and 
                          (datetime.now() - existing['timestamp']).seconds < 300  # 5분 내 중복 제거
                          for existing in self.alert_history):
                    new_alerts.append(alert)
                    self.alert_history.append(alert)
            
            return new_alerts
            
        except Exception as e:
            logger.error(f"리스크 알림 체크 중 오류: {e}")
            return []
    
    def _save_account_summary(self, summary: AccountSummary):
        """계좌 요약 정보를 데이터베이스에 저장"""
        try:
            # 성능 지표로 저장
            self.db.save_performance_metric(1, "account_deposit", summary.deposit)
            self.db.save_performance_metric(1, "account_total_evaluation", summary.total_evaluation)
            self.db.save_performance_metric(1, "account_total_profit_rate", summary.total_profit_rate)
            self.db.save_performance_metric(1, "account_total_profit_loss", summary.total_profit_loss)
            
            # 시스템 로그로 저장
            self.db.save_system_log(
                "INFO", 
                f"계좌 요약 업데이트 - 예수금: {summary.deposit:,}원, 총평가: {summary.total_evaluation:,}원, 수익률: {summary.total_profit_rate:.2f}%",
                "account_monitor"
            )
            
        except Exception as e:
            logger.error(f"계좌 요약 저장 중 오류: {e}")
    
    def _save_portfolio(self, portfolio: List[PortfolioItem]):
        """포트폴리오 정보를 데이터베이스에 저장"""
        try:
            for item in portfolio:
                # 주식 종목이 데이터베이스에 없으면 추가
                if not self.db.get_stock(item.stock_code):
                    self.db.add_stock(item.stock_code, item.stock_name, "KOSPI")
                
                # 실시간 거래 데이터로 저장
                market_data = {
                    'timestamp': datetime.now(),
                    'close_price': item.current_price,
                    'volume': item.quantity,
                    'trade_value': item.evaluation_amount,
                    'price_change': item.profit_rate
                }
                self.db.save_market_data(item.stock_code, market_data)
            
            # 시스템 로그로 저장
            self.db.save_system_log(
                "INFO", 
                f"포트폴리오 업데이트 - 보유 종목: {len(portfolio)}개",
                "account_monitor"
            )
            
        except Exception as e:
            logger.error(f"포트폴리오 저장 중 오류: {e}")
    
    async def start_monitoring(self):
        """계좌 모니터링 시작"""
        logger.info("계좌 모니터링 시작...")
        
        while True:
            try:
                # 계좌 요약 정보 조회
                summary = await self.get_account_summary()
                if summary:
                    self.last_account_summary = summary
                    logger.info(f"계좌 요약 - 예수금: {summary.deposit:,}원, 총평가: {summary.total_evaluation:,}원, 수익률: {summary.total_profit_rate:.2f}%")
                
                # 포트폴리오 조회
                portfolio = await self.get_portfolio()
                if portfolio:
                    self.last_portfolio = portfolio
                    logger.info(f"포트폴리오 - 보유 종목: {len(portfolio)}개")
                    
                    # 리스크 지표 계산
                    if summary:
                        risk_metrics = self.calculate_risk_metrics(portfolio, summary)
                        
                        # 리스크 알림 체크
                        alerts = self.check_risk_alerts(portfolio, summary, risk_metrics)
                        for alert in alerts:
                            logger.warning(f"[RISK ALERT] {alert['message']}")
                
                self.last_update_time = datetime.now()
                
                # 모니터링 간격 대기
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"계좌 모니터링 중 오류: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def get_account_status(self) -> Dict[str, Any]:
        """계좌 상태 정보 반환"""
        return {
            'summary': self.last_account_summary,
            'portfolio': self.last_portfolio,
            'last_update': self.last_update_time,
            'alert_count': len([a for a in self.alert_history if (datetime.now() - a['timestamp']).seconds < 3600]),  # 1시간 내 알림
            'monitoring_active': True
        }
    
    def get_portfolio_analysis(self) -> Dict[str, Any]:
        """포트폴리오 분석 결과 반환"""
        if not self.last_portfolio or not self.last_account_summary:
            return {}
        
        try:
            total_evaluation = sum(item.evaluation_amount for item in self.last_portfolio)
            total_profit_loss = sum(item.profit_loss for item in self.last_portfolio)
            
            # 종목별 비중 계산
            portfolio_weights = []
            for item in self.last_portfolio:
                weight = (item.evaluation_amount / total_evaluation * 100) if total_evaluation > 0 else 0
                portfolio_weights.append({
                    'stock_code': item.stock_code,
                    'stock_name': item.stock_name,
                    'weight': weight,
                    'profit_rate': item.profit_rate
                })
            
            # 수익률 순 정렬
            portfolio_weights.sort(key=lambda x: x['profit_rate'], reverse=True)
            
            return {
                'total_evaluation': total_evaluation,
                'total_profit_loss': total_profit_loss,
                'portfolio_weights': portfolio_weights,
                'top_performers': portfolio_weights[:3],  # 상위 3개
                'worst_performers': portfolio_weights[-3:],  # 하위 3개
                'risk_metrics': self.calculate_risk_metrics(self.last_portfolio, self.last_account_summary)
            }
            
        except Exception as e:
            logger.error(f"포트폴리오 분석 중 오류: {e}")
            return {}
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """최근 알림 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert['timestamp'] > cutoff_time]
    
    def update_risk_thresholds(self, thresholds: Dict[str, float]):
        """리스크 임계값 업데이트"""
        self.risk_thresholds.update(thresholds)
        logger.info(f"리스크 임계값 업데이트: {thresholds}")


# 전역 계좌 모니터 인스턴스
_account_monitor = None


def get_account_monitor(settings: Settings = None, token_manager: TokenManager = None) -> AccountMonitor:
    """전역 계좌 모니터 인스턴스 반환"""
    global _account_monitor
    if _account_monitor is None:
        if settings is None:
            settings = Settings()
        if token_manager is None:
            token_manager = TokenManager(settings)
        _account_monitor = AccountMonitor(settings, token_manager)
    return _account_monitor


def init_account_monitor(settings: Settings, token_manager: TokenManager) -> AccountMonitor:
    """계좌 모니터 초기화"""
    global _account_monitor
    _account_monitor = AccountMonitor(settings, token_manager)
    return _account_monitor
