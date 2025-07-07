#!/usr/bin/env python3
"""
Volume Scanner - 거래량 급증 종목 스크리닝
키움 API를 사용하여 거래량 급증 종목을 실시간으로 스크리닝하고 자동매매 후보를 선정
"""

import asyncio
import logging
import time
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import threading
import collections
import aiohttp

from utils.logger import get_logger
from config.settings import Settings
from utils.token_manager import TokenManager
from database.database_manager import get_database_manager

logger = get_logger("volume_scanner")

@dataclass
class VolumeCandidate:
    """거래량 급증 후보 종목"""
    stock_code: str
    stock_name: str
    current_price: int
    volume_ratio: float  # 거래량 비율
    price_change: float  # 가격 변동률
    trade_value: int     # 거래대금
    score: int          # 종합 점수
    timestamp: datetime
    is_breakout: bool   # 고점 돌파 여부
    ma_trend: str       # 이동평균 추세
    execution_strength: float = 0.0

class VolumeScanner:
    """거래량 급증 종목 스크리닝 클래스"""
    
    def __init__(self, settings, token_manager):
        self.settings = settings
        self.token_manager = token_manager
        self.candidates: List[VolumeCandidate] = []
        self.processed_stocks: set = set()
        
        # 실시간 전일 거래량 돌파 감지를 위한 관리
        self.breakout_stocks: set = set()  # 이미 돌파한 종목들
        self.volume_breakout_candidates: List[Dict] = []  # 돌파 후보 종목들
        
        # API Rate Limiting
        self.API_RATE_LIMIT = 5  # 초당 5건
        self.API_WINDOW = 1.0    # 1초
        self.api_call_timestamps = collections.deque(maxlen=self.API_RATE_LIMIT)
        self.api_rate_lock = threading.Lock()
        
        # 스캐닝 설정 (실제 거래 조건)
        self.scan_interval = 5  # 5초마다 스캔
        self.min_volume_ratio = 1.0  # 오늘 누적 거래량 ≥ 전일 총 거래량
        self.min_trade_value = 100_000_000  # 1분 거래대금 ≥ 1억원
        self.min_price_change = 0.02  # 등락률 ≥ +2%
        self.min_execution_strength = 1.2  # 체결강도 ≥ 120%
        
        # 자동매매 설정
        self.auto_trade_enabled = False
        self.auto_trade_stocks: Dict[str, Dict] = {}
        
        # 데이터베이스 매니저
        self.db = get_database_manager()
        
        logger.info("거래량 스캐너 초기화 완료")
    
    def set_order_manager(self, order_manager):
        """주문 매니저 설정"""
        self.order_manager = order_manager
        logger.info("주문 매니저가 거래량 스캐너에 연결되었습니다.")
    
    def acquire_api_rate_limit(self):
        """API 호출 속도 제한"""
        while True:
            with self.api_rate_lock:
                now = time.monotonic()
                if len(self.api_call_timestamps) >= self.API_RATE_LIMIT:
                    oldest = self.api_call_timestamps[0]
                    elapsed = now - oldest
                    if elapsed < self.API_WINDOW:
                        wait_time = self.API_WINDOW - elapsed
                    else:
                        wait_time = 0
                else:
                    wait_time = 0
                if wait_time == 0:
                    self.api_call_timestamps.append(now)
                    return
            if wait_time > 0:
                time.sleep(wait_time)
    
    async def get_volume_ranking(self) -> List[Dict]:
        """거래량 급증 종목 순위 조회"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                logger.error("유효한 토큰을 가져올 수 없습니다.")
                return []
            
            # 키움 API 거래량 급증 종목 조회 (실제 호스트 사용)
            if self.settings.ENVIRONMENT == "simulation":
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
                'trde_qty_tp': '50',  # 상위 50개
                'tm': '',
                'stk_cnd': '20',   # 거래량 급증 조건
                'pric_tp': '0',    # 전체 가격대
                'stex_tp': '3',    # 코스피
            }
            
            self.acquire_api_rate_limit()
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"거래량 순위 조회 실패: {response.status_code}")
                return []
            
            result = response.json()
            if result.get("return_code") != 0:
                logger.error(f"API 오류: {result.get('return_msg')}")
                return []
            
            return result.get("trde_qty_sdnin", [])
            
        except Exception as e:
            logger.error(f"거래량 순위 조회 중 오류: {e}")
            return []
    
    async def get_daily_chart_score(self, stock_code: str, current_price: int) -> int:
        """일봉 차트 기반 점수 계산"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                return 0
            
            # 일봉 데이터 조회
            url = self.settings.get_api_url("daily_chart")
            headers = self.settings.get_headers(tr_type="daily_chart")
            
            data = {
                "stk_cd": stock_code,
                "base_dt": datetime.now().strftime("%Y%m%d"),
                "upd_stkpc_tp": "1",
                "req_cnt": 80,
            }
            
            self.acquire_api_rate_limit()
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                return 0
            
            result = response.json()
            daily_data = result.get('stk_dt_pole_chart_qry', [])
            
            if not daily_data or len(daily_data) < 60:
                return 0
            
            # DataFrame 구성
            df = pd.DataFrame(daily_data)
            if 'dt' in df.columns:
                df = df.sort_values('dt').reset_index(drop=True)
            
            df['cur_prc'] = df['cur_prc'].astype(int).abs()
            df['MA10'] = df['cur_prc'].rolling(window=10).mean()
            df['MA20'] = df['cur_prc'].rolling(window=20).mean()
            df['MA60'] = df['cur_prc'].rolling(window=60).mean()
            df = df.dropna()
            
            if df.empty:
                return 0
            
            latest = df.iloc[-1]
            score = 0
            
            # MA10 > MA20 +2점
            if latest['MA10'] > latest['MA20']:
                score += 2
            
            # MA20 > MA60 +1점
            if latest['MA20'] > latest['MA60']:
                score += 1
            
            # 현재가 > MA10 +1점
            if current_price > latest['MA10']:
                score += 1
            
            # MA20 상승(3일 전 대비) +1점
            if len(df) >= 3 and latest['MA20'] > df.iloc[-3]['MA20']:
                score += 1
            
            # MA60 상승(3일 전 대비) +1점
            if len(df) >= 3 and latest['MA60'] > df.iloc[-3]['MA60']:
                score += 1
            
            # 10일 고점 돌파 체크
            if len(df) >= 10:
                high_10d = df.iloc[-10:]['cur_prc'].max()
                if current_price > high_10d:
                    score += 2
            
            return score
            
        except Exception as e:
            logger.error(f"일봉 차트 점수 계산 실패 ({stock_code}): {e}")
            return 0
    
    async def get_execution_strength(self, stock_code: str) -> float:
        """체결강도 조회 API"""
        try:
            token = await self.token_manager.get_valid_token()
            if not token:
                logger.error("유효한 토큰을 가져올 수 없습니다.")
                return 1.0
            
            # 키움 API 체결강도 조회
            if self.settings.ENVIRONMENT == "simulation":
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
            
            data = {
                'stk_cd': stock_code,
            }
            
            self.acquire_api_rate_limit()
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.warning(f"체결강도 조회 실패: {response.status_code} - {stock_code}")
                return 1.0
            
            result = response.json()
            if result.get("return_code") != 0:
                logger.warning(f"체결강도 API 오류: {result.get('return_msg')} - {stock_code}")
                return 1.0
            
            # 체결강도 데이터 파싱 (실제 응답 구조에 맞게 수정)
            execution_data = result.get("cntr_str_tm", [])
            if execution_data:
                # 가장 최근 체결강도 값 반환 (첫 번째 항목이 최신)
                latest_strength = execution_data[0].get("cntr_str", 1.0)
                return float(latest_strength)
            
            return 1.0
            
        except Exception as e:
            logger.error(f"체결강도 조회 중 오류: {e} - {stock_code}")
            return 1.0
    
    async def scan_volume_candidates(self) -> List[VolumeCandidate]:
        """거래량 급증 후보 종목 스캔"""
        try:
            logger.info("거래량 급증 종목 스캔 시작...")
            
            # 거래량 순위 조회
            volume_data = await self.get_volume_ranking()
            if not volume_data:
                logger.warning("거래량 데이터를 가져올 수 없습니다.")
                return []
            
            candidates = []
            
            for item in volume_data:
                try:
                    # 기본 데이터 파싱
                    stock_code = item.get("stk_cd", "")
                    stock_name = item.get("stk_nm", "")
                    current_price = abs(int(item.get("cur_prc", 0)))
                    volume_ratio = float(item.get("sdnin_rt", "0").replace("+", "").replace("%", ""))
                    price_change = float(item.get("flu_rt", 0))
                    
                    # 거래량 및 거래대금 계산
                    prev_qty = int(item.get("prev_trde_qty", 0))
                    now_qty = int(item.get("now_trde_qty", 0))
                    one_min_qty = now_qty - prev_qty
                    trade_value = one_min_qty * current_price
                    
                    # 🚀 전일 거래량 돌파 감지 (1차 필터)
                    is_breakout = self.check_volume_breakout(stock_code, now_qty, prev_qty)
                    if not is_breakout:
                        continue  # 돌파하지 않은 종목은 스킵
                    
                    # 2차 필터: 추가 조건 체크 (등락률, 거래대금 등)
                    if (price_change < self.min_price_change or 
                        trade_value < self.min_trade_value):
                        logger.info(f"[{stock_name}({stock_code})] 2차 필터 탈락 - 등락률: {price_change:.2f}%, 거래대금: {trade_value:,}원")
                        continue
                    
                    # 이미 처리된 종목 스킵
                    if stock_code in self.processed_stocks:
                        continue
                    
                    logger.info(f"[{stock_name}({stock_code})] 1차 필터 통과 - 거래량비율: {volume_ratio:.1f}%, 거래대금: {trade_value:,}원")
                    
                    # 2차 필터: 체결강도 조건 체크
                    execution_strength = await self.get_execution_strength(stock_code)
                    
                    if execution_strength >= self.min_execution_strength:
                        # 추세 판단
                        if price_change >= 0.05:  # 5% 이상 상승
                            ma_trend = "급등추세"
                        elif price_change >= 0.02:  # 2% 이상 상승
                            ma_trend = "상승추세"
                        else:
                            ma_trend = "보합추세"
                        
                        candidate = VolumeCandidate(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            current_price=current_price,
                            volume_ratio=volume_ratio,
                            price_change=price_change,
                            trade_value=trade_value,
                            score=execution_strength,  # 체결강도를 점수로 사용
                            timestamp=datetime.now(),
                            is_breakout=is_breakout,
                            ma_trend=ma_trend,
                            execution_strength=execution_strength
                        )
                        
                        candidates.append(candidate)
                        
                        logger.info(f"★★ 매수 후보 선정 ★★ {stock_name}({stock_code})")
                        logger.info(f"   현재가: {current_price:,}원")
                        logger.info(f"   거래량비율: {volume_ratio:.1f}%")
                        logger.info(f"   등락률: {price_change:.2f}%")
                        logger.info(f"   거래대금: {trade_value:,}원")
                        logger.info(f"   체결강도: {execution_strength:.1f}%")
                        logger.info(f"   시가상승: {'예' if is_breakout else '아니오'}")
                        logger.info(f"   추세: {ma_trend}")
                        
                        # 처리된 종목으로 등록
                        self.processed_stocks.add(stock_code)
                        
                        # 데이터베이스에 자동매매 후보 저장
                        candidate_data = {
                            'candidate_time': datetime.now(),
                            'current_price': current_price,
                            'price_change': price_change,
                            'trade_value': trade_value,
                            'execution_strength': execution_strength,
                            'volume_ratio': volume_ratio,
                            'ma_trend': ma_trend,
                            'status': 'ACTIVE'
                        }
                        self.db.save_auto_trading_candidate(stock_code, candidate_data)
                    else:
                        logger.info(f"[{stock_name}({stock_code})] 체결강도 조건 불만족 - 체결강도: {execution_strength:.1f}% (기준: {self.min_execution_strength:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"종목 데이터 처리 실패: {e}")
                    continue
            
            # 후보 목록 업데이트
            self.candidates = candidates
            
            logger.info(f"스캔 완료: {len(candidates)}개 후보 종목 발견")
            return candidates
            
        except Exception as e:
            logger.error(f"거래량 후보 스캔 실패: {e}")
            return []
    
    def add_auto_trade(self, stock_code: str, buy_price: int, stock_name: str = None):
        """자동매매 종목 추가"""
        if not self.auto_trade_enabled:
            logger.warning("자동매매가 비활성화되어 있습니다.")
            return False
        
        auto_trade_info = {
            'stock_code': stock_code,
            'stock_name': stock_name or stock_code,
            'buy_price': buy_price,
            'buy_time': datetime.now(),
            'status': 'monitoring',
            'sell_price': None,
            'sell_time': None,
            'profit_rate': 0.0,
            'reason': None
        }
        
        self.auto_trade_stocks[stock_code] = auto_trade_info
        logger.info(f"자동매매 등록: {stock_name}({stock_code}) @ {buy_price:,}원")
        
        return True
    
    def remove_auto_trade(self, stock_code: str, sell_price: int = None, reason: str = None):
        """자동매매 종목 제거"""
        if stock_code in self.auto_trade_stocks:
            trade_info = self.auto_trade_stocks[stock_code]
            trade_info['sell_price'] = sell_price
            trade_info['sell_time'] = datetime.now()
            trade_info['status'] = 'completed'
            trade_info['reason'] = reason
            
            if sell_price and trade_info['buy_price']:
                profit_rate = ((sell_price - trade_info['buy_price']) / trade_info['buy_price']) * 100
                trade_info['profit_rate'] = profit_rate
            
            logger.info(f"자동매매 완료: {trade_info['stock_name']}({stock_code}) - {reason}")
            logger.info(f"  매수가: {trade_info['buy_price']:,}원, 매도가: {sell_price:,}원")
            logger.info(f"  수익률: {trade_info['profit_rate']:.2f}%")
            
            # 완료된 거래는 별도 저장 (DB 연동 예정)
            del self.auto_trade_stocks[stock_code]
    
    def get_auto_trade_status(self) -> Dict[str, Any]:
        """자동매매 상태 반환"""
        return {
            'enabled': self.auto_trade_enabled,
            'active_trades': len(self.auto_trade_stocks),
            'candidates': len(self.candidates),
            'processed_stocks': len(self.processed_stocks)
        }
    
    async def start_scanning(self):
        """지속적인 스캐닝 시작"""
        logger.info("거래량 스캐닝 시작...")
        
        while True:
            try:
                # 거래량 후보 스캔
                candidates = await self.scan_volume_candidates()
                
                # 자동매매 후보 등록
                for candidate in candidates:
                    if self.auto_trade_enabled:
                        # 주문 매니저를 통한 자동매매 실행
                        if hasattr(self, 'order_manager') and self.order_manager:
                            try:
                                order = await self.order_manager.handle_volume_candidate(candidate)
                                if order:
                                    logger.info(f"거래량 급증 자동매매 실행: {candidate.stock_code}")
                                else:
                                    logger.info(f"거래량 급증 자동매매 조건 불만족: {candidate.stock_code}")
                            except Exception as e:
                                logger.error(f"거래량 급증 자동매매 실행 실패: {e}")
                        else:
                            # 주문 매니저가 없는 경우 기본 등록
                            self.add_auto_trade(
                                candidate.stock_code,
                                candidate.current_price,
                                candidate.stock_name
                            )
                
                # 스캔 간격 대기
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"스캐닝 중 오류: {e}")
                await asyncio.sleep(self.scan_interval)
    
    def get_candidates_summary(self) -> List[Dict]:
        """후보 종목 요약 반환"""
        return [
            {
                'stock_code': c.stock_code,
                'stock_name': c.stock_name,
                'current_price': c.current_price,
                'volume_ratio': c.volume_ratio,
                'trade_value': c.trade_value,
                'score': c.score,
                'is_breakout': c.is_breakout,
                'ma_trend': c.ma_trend,
                'timestamp': c.timestamp.isoformat()
            }
            for c in self.candidates
        ]
    
    def check_volume_breakout(self, stock_code: str, today_volume: int, prev_day_volume: int) -> bool:
        """전일 거래량 돌파 감지"""
        # 이미 돌파한 종목인지 확인
        if stock_code in self.breakout_stocks:
            return False
        
        # 전일 거래량 돌파 여부 확인
        if today_volume > prev_day_volume:
            # 돌파 순간 감지!
            self.breakout_stocks.add(stock_code)
            logger.info(f"[BREAKOUT] 전일 거래량 돌파 감지! {stock_code} - 오늘: {today_volume:,}주, 전일: {prev_day_volume:,}주")
            
            # 데이터베이스에 돌파 이벤트 저장
            breakout_data = {
                'breakout_time': datetime.now(),
                'today_volume': today_volume,
                'prev_day_volume': prev_day_volume,
                'volume_ratio': today_volume / prev_day_volume if prev_day_volume > 0 else 0,
                'price_at_breakout': 0,  # 나중에 업데이트
                'trade_value_at_breakout': 0  # 나중에 업데이트
            }
            self.db.save_volume_breakout(stock_code, breakout_data)
            
            return True
        
        return False
    
    def get_breakout_summary(self) -> Dict[str, Any]:
        """전일 거래량 돌파 현황 요약"""
        return {
            "total_breakouts": len(self.breakout_stocks),
            "breakout_stocks": list(self.breakout_stocks),
            "volume_breakout_candidates": len(self.volume_breakout_candidates),
            "last_scan_time": datetime.now().isoformat()
        }
    
    def clear_breakout_history(self):
        """돌파 이력 초기화 (새로운 거래일 시작 시)"""
        self.breakout_stocks.clear()
        self.volume_breakout_candidates.clear()
        logger.info("전일 거래량 돌파 이력이 초기화되었습니다.")
    
    def get_breakout_candidates(self) -> List[Dict]:
        """돌파 후보 종목 목록 반환"""
        return self.volume_breakout_candidates 