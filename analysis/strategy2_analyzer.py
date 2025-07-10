#!/usr/bin/env python3
"""
Strategy 2 Analyzer - 전략 2 최종 버전 분석기
핵심 조건과 추가 확인 조건을 분리한 '폭풍 전야의 저점 상승' 포착 전략
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import requests

from utils.logger import get_logger
from config.settings import Settings
from utils.token_manager import TokenManager
from database.database_manager import get_database_manager

logger = get_logger("strategy2_analyzer")

@dataclass
class Strategy2Candidate:
    """전략 2 후보 종목"""
    stock_code: str
    stock_name: str
    current_price: int
    price_change: float  # 등락률
    volume_ratio: float  # 거래량비율
    market_amount: int   # 시장거래대금
    ma_short: float      # 단기 이동평균선
    ma_long: float       # 장기 이동평균선
    core_conditions_met: bool  # 핵심 조건 만족 여부
    additional_conditions_met: bool  # 추가 조건 만족 여부
    final_signal: bool   # 최종 매수 신호
    confidence_score: float  # 신뢰도 점수
    timestamp: datetime
    strategy_type: str = "순추세_조용한상승"

class Strategy2Analyzer:
    """전략 2 최종 버전 분석 클래스"""
    
    def __init__(self, settings: Settings, token_manager: TokenManager):
        self.settings = settings
        self.token_manager = token_manager
        self.candidates: List[Strategy2Candidate] = []
        self.processed_stocks: set = set()
        
        # 전략 2 설정
        strategy2_config = settings.VOLUME_SCANNING.get("strategy2_core_conditions", {})
        self.core_conditions = {
            "price_change_min": strategy2_config.get("price_change_range", [0.5, 3.0])[0],
            "price_change_max": strategy2_config.get("price_change_range", [0.5, 3.0])[1],
            "volume_ratio_max": strategy2_config.get("volume_ratio_max", 120.0)
        }
        
        additional_config = settings.VOLUME_SCANNING.get("strategy2_additional_conditions", {})
        self.additional_conditions = {
            "min_market_amount": additional_config.get("min_market_amount", 150_000_000),
            "ma_trend_enabled": additional_config.get("ma_trend_enabled", True),
            "ma_short_period": additional_config.get("ma_short_period", 5),
            "ma_long_period": additional_config.get("ma_long_period", 20)
        }
        
        self.strategy_logic = settings.VOLUME_SCANNING.get("strategy2_logic", "AND_OR")
        self.enabled = settings.VOLUME_SCANNING.get("strategy2_enabled", True)
        
        # 데이터베이스 매니저
        self.db = get_database_manager()
        
        logger.info("전략 2 분석기 초기화 완료")
        logger.info(f"핵심 조건: 등락률 {self.core_conditions['price_change_min']}~{self.core_conditions['price_change_max']}%, 거래량비율 {self.core_conditions['volume_ratio_max']}% 미만")
        logger.info(f"추가 조건: 거래대금 {self.additional_conditions['min_market_amount']/100000000:.1f}억원 이상, 이동평균선 추세 확인")
    
    def check_core_conditions(self, price_change: float, volume_ratio: float) -> bool:
        """핵심 조건 확인 (반드시 충족해야 함)"""
        # 핵심 조건 1: 등락률 +0.5% ~ +3%
        price_condition = (self.core_conditions["price_change_min"] <= price_change <= self.core_conditions["price_change_max"])
        
        # 핵심 조건 2: 거래량비율 120% 미만
        volume_condition = volume_ratio < self.core_conditions["volume_ratio_max"]
        
        return price_condition and volume_condition
    
    def check_additional_conditions(self, market_amount: int, ma_short: float, ma_long: float) -> bool:
        """추가 확인 조건 확인 (최소 1개 이상 충족)"""
        conditions_met = 0
        
        # 추가 조건 1: 시장거래대금 1.5억원 이상
        if market_amount >= self.additional_conditions["min_market_amount"]:
            conditions_met += 1
        
        # 추가 조건 2: 이동평균선 배열 (5일선 > 20일선)
        if (self.additional_conditions["ma_trend_enabled"] and 
            ma_short > ma_long and ma_short > 0 and ma_long > 0):
            conditions_met += 1
        
        # 최소 1개 이상 충족하면 True
        return conditions_met >= 1
    
    async def get_moving_averages(self, stock_code: str) -> Tuple[float, float]:
        """이동평균선 계산"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                return 0.0, 0.0
            
            # 일봉 데이터 조회
            url = self.settings.get_api_url("daily_chart")
            headers = self.settings.get_headers(tr_type="daily_chart")
            
            data = {
                "stk_cd": stock_code,
                "base_dt": datetime.now().strftime("%Y%m%d"),
                "upd_stkpc_tp": "1",
                "req_cnt": 80,
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                return 0.0, 0.0
            
            result = response.json()
            daily_data = result.get('stk_dt_pole_chart_qry', [])
            
            if not daily_data or len(daily_data) < 30:
                return 0.0, 0.0
            
            # DataFrame 구성
            df = pd.DataFrame(daily_data)
            if 'dt' in df.columns:
                df = df.sort_values('dt').reset_index(drop=True)
            
            df['cur_prc'] = df['cur_prc'].astype(int).abs()
            
            # 이동평균선 계산
            ma_short = df['cur_prc'].rolling(window=self.additional_conditions["ma_short_period"]).mean().iloc[-1]
            ma_long = df['cur_prc'].rolling(window=self.additional_conditions["ma_long_period"]).mean().iloc[-1]
            
            return ma_short, ma_long
            
        except Exception as e:
            logger.error(f"이동평균선 계산 중 오류: {e} - {stock_code}")
            return 0.0, 0.0
    
    def calculate_confidence_score(self, price_change: float, volume_ratio: float, 
                                 market_amount: int, ma_short: float, ma_long: float) -> float:
        """신뢰도 점수 계산"""
        score = 0.0
        
        # 등락률 점수 (1.5% 근처일수록 높은 점수) - 구체적 수식 적용
        optimal_price_change = 1.5
        price_score = max(0.0, 1.0 - abs(price_change - optimal_price_change) / optimal_price_change)
        score += price_score * 0.3
        
        # 거래량비율 점수 (최적 구간 50%~100%에 높은 점수)
        if volume_ratio <= 50.0:
            volume_score = 0.3  # 너무 낮은 거래량은 낮은 점수
        elif 50.0 < volume_ratio <= 100.0:
            volume_score = 1.0  # 최적 구간
        else:
            volume_score = max(0.0, 1.0 - (volume_ratio - 100.0) / 20.0)  # 100% 초과시 점수 감소
        score += volume_score * 0.3
        
        # 거래대금 점수 (목표 거래대금 대비 비례 점수)
        target_trade_value = 10_000_000_000  # 목표 거래대금: 100억원
        amount_score = min(1.0, market_amount / target_trade_value)
        score += amount_score * 0.2
        
        # 이동평균선 점수 (이격도 기반 구체적 계산)
        if ma_short > ma_long and ma_short > 0 and ma_long > 0:
            ma_ratio = ma_short / ma_long  # 이격도
            if ma_ratio >= 1.03:  # 3% 이상 이격
                ma_score = 1.0
            elif ma_ratio >= 1.02:  # 2~3% 이격
                ma_score = 0.8
            elif ma_ratio >= 1.01:  # 1~2% 이격
                ma_score = 0.6
            else:  # 1% 미만 이격
                ma_score = 0.3
            score += ma_score * 0.2
        
        return score
    
    async def analyze_stock(self, stock_data: Dict) -> Optional[Strategy2Candidate]:
        """개별 종목 분석"""
        try:
            stock_code = stock_data.get("stk_cd", "").replace("_AL", "")
            stock_name = stock_data.get("stk_nm", "")
            current_price = abs(int(stock_data.get("cur_prc", 0)))
            price_change = float(stock_data.get("flu_rt", 0))
            
            # 거래량비율 계산
            volume_ratio = float(stock_data.get("sdnin_rt", "0").replace("+", "").replace("%", ""))
            
            # 거래대금 계산
            prev_qty = int(stock_data.get("prev_trde_qty", 0))
            now_qty = int(stock_data.get("now_trde_qty", 0))
            one_min_qty = now_qty - prev_qty
            market_amount = one_min_qty * current_price
            
            # 이동평균선 계산
            ma_short, ma_long = await self.get_moving_averages(stock_code)
            
            # 핵심 조건 확인
            core_conditions_met = self.check_core_conditions(price_change, volume_ratio)
            
            # 추가 조건 확인
            additional_conditions_met = self.check_additional_conditions(market_amount, ma_short, ma_long)
            
            # 최종 매수 신호 결정
            final_signal = False
            if self.strategy_logic == "AND_OR":
                final_signal = core_conditions_met and additional_conditions_met
            else:
                final_signal = core_conditions_met and additional_conditions_met
            
            # 신뢰도 점수 계산
            confidence_score = self.calculate_confidence_score(
                price_change, volume_ratio, market_amount, ma_short, ma_long
            )
            
            candidate = Strategy2Candidate(
                stock_code=stock_code,
                stock_name=stock_name,
                current_price=current_price,
                price_change=price_change,
                volume_ratio=volume_ratio,
                market_amount=market_amount,
                ma_short=ma_short,
                ma_long=ma_long,
                core_conditions_met=core_conditions_met,
                additional_conditions_met=additional_conditions_met,
                final_signal=final_signal,
                confidence_score=confidence_score,
                timestamp=datetime.now()
            )
            
            return candidate
            
        except Exception as e:
            logger.error(f"종목 분석 중 오류: {e} - {stock_data.get('stk_cd', '')}")
            return None
    
    def set_order_manager(self, order_manager):
        """주문 매니저 설정"""
        self.order_manager = order_manager
        logger.info("주문 매니저가 전략 2 분석기에 연결되었습니다.")

    async def scan_strategy2_candidates(self) -> List[Strategy2Candidate]:
        """전략 2 후보 종목 스캔"""
        if not self.enabled:
            logger.info("전략 2가 비활성화되어 있습니다.")
            return []
        
        try:
            logger.info("전략 2 후보 종목 스캔 시작...")
            
            # 기존 volume_scanner의 데이터 활용 (중복 API 호출 방지)
            if hasattr(self, 'volume_scanner') and self.volume_scanner:
                # volume_scanner에서 이미 스캔된 데이터 활용
                volume_data = await self.volume_scanner.get_volume_ranking()
            else:
                # 독립적으로 거래량 순위 조회
                volume_data = await self.get_volume_ranking()
            
            if not volume_data:
                logger.warning("거래량 데이터를 가져올 수 없습니다.")
                return []
            
            candidates = []
            
            for item in volume_data:
                try:
                    candidate = await self.analyze_stock(item)
                    if candidate and candidate.final_signal:
                        candidates.append(candidate)
                        
                        logger.info(f"🎯 전략 2 매수 신호 발생! {candidate.stock_name}({candidate.stock_code})")
                        logger.info(f"   현재가: {candidate.current_price:,}원")
                        logger.info(f"   등락률: {candidate.price_change:+.2f}%")
                        logger.info(f"   거래량비율: {candidate.volume_ratio:.1f}%")
                        logger.info(f"   거래대금: {candidate.market_amount/100000000:.1f}억원")
                        logger.info(f"   이동평균선: {candidate.ma_short:.0f} > {candidate.ma_long:.0f}")
                        logger.info(f"   신뢰도: {candidate.confidence_score:.2f}")
                        logger.info(f"   핵심조건: {'만족' if candidate.core_conditions_met else '불만족'}")
                        logger.info(f"   추가조건: {'만족' if candidate.additional_conditions_met else '불만족'}")
                        
                        # 주문 매니저를 통한 자동매매 실행
                        if hasattr(self, 'order_manager') and self.order_manager:
                            try:
                                order = self.order_manager.handle_strategy2_candidate(candidate)
                                if order:
                                    logger.info(f"전략 2 자동매매 실행: {candidate.stock_code}")
                                else:
                                    logger.info(f"전략 2 자동매매 조건 불만족: {candidate.stock_code}")
                            except Exception as e:
                                logger.error(f"전략 2 후보 처리 실패: {e}")
                        
                        # 데이터베이스에 후보 저장
                        candidate_data = {
                            'candidate_time': datetime.now(),
                            'strategy_type': 'strategy2',
                            'current_price': candidate.current_price,
                            'price_change': candidate.price_change,
                            'volume_ratio': candidate.volume_ratio,
                            'market_amount': candidate.market_amount,
                            'ma_short': candidate.ma_short,
                            'ma_long': candidate.ma_long,
                            'confidence_score': candidate.confidence_score,
                            'core_conditions_met': candidate.core_conditions_met,
                            'additional_conditions_met': candidate.additional_conditions_met,
                            'status': 'ACTIVE'
                        }
                        self.db.save_auto_trading_candidate(candidate.stock_code, candidate_data)
                        
                except Exception as e:
                    logger.error(f"종목 처리 중 오류: {e}")
                    continue
            
            # 후보 목록 업데이트
            self.candidates = candidates
            
            logger.info(f"전략 2 스캔 완료: {len(candidates)}개 후보 종목 발견")
            return candidates
            
        except Exception as e:
            logger.error(f"전략 2 스캔 실패: {e}")
            return []
    
    async def get_volume_ranking(self) -> List[Dict]:
        """거래량 순위 조회 (기존 volume_scanner의 로직 활용)"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                return []
            
            url = self.settings.get_api_url("volume_ranking")
            headers = self.settings.get_headers(tr_type="volume_ranking")
            
            data = {
                "stk_cd": "",
                "base_dt": datetime.now().strftime("%Y%m%d"),
                "upd_stkpc_tp": "1",
                "req_cnt": 100,
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                return []
            
            result = response.json()
            return result.get('stk_vol_rank_qry', [])
            
        except Exception as e:
            logger.error(f"거래량 순위 조회 실패: {e}")
            return []
    
    def get_candidates_summary(self) -> List[Dict]:
        """후보 종목 요약 반환"""
        return [
            {
                'stock_code': c.stock_code,
                'stock_name': c.stock_name,
                'current_price': c.current_price,
                'price_change': c.price_change,
                'volume_ratio': c.volume_ratio,
                'market_amount': c.market_amount,
                'confidence_score': c.confidence_score,
                'final_signal': c.final_signal,
                'timestamp': c.timestamp.isoformat()
            }
            for c in self.candidates
        ]

    def get_auto_trade_status(self) -> Dict[str, Any]:
        """자동매매 상태 반환"""
        return {
            'enabled': self.enabled,
            'active_candidates': len(self.candidates),
            'processed_stocks': len(self.processed_stocks),
            'strategy_type': 'strategy2_quiet_rise',
            'core_conditions': self.core_conditions,
            'additional_conditions': self.additional_conditions,
            'strategy_logic': self.strategy_logic
        }
    
    async def start_scanning(self):
        """지속적인 스캐닝 시작"""
        logger.info("전략 2 스캐닝 시작...")
        
        scan_interval = self.settings.VOLUME_SCANNING.get("scan_interval", 30)
        
        while True:
            try:
                # 전략 2 후보 스캔
                candidates = await self.scan_strategy2_candidates()
                
                # 스캔 간격 대기
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"전략 2 스캐닝 중 오류: {e}")
                await asyncio.sleep(scan_interval) 

    def set_volume_scanner(self, volume_scanner):
        """Volume Scanner 설정 (데이터 공유용)"""
        self.volume_scanner = volume_scanner
        logger.info("Volume Scanner가 전략 2 분석기에 연결되었습니다.") 