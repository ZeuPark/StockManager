#!/usr/bin/env python3
"""
Test Volume Scanner
거래량 스캐너 기능 테스트
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.volume_scanner import VolumeScanner, VolumeCandidate
from config.settings import Settings
from utils.token_manager import TokenManager

class TestVolumeScanner(unittest.TestCase):
    """거래량 스캐너 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.settings = Settings()
        self.token_manager = Mock(spec=TokenManager)
        self.scanner = VolumeScanner(self.settings, self.token_manager)
    
    def test_volume_candidate_creation(self):
        """VolumeCandidate 생성 테스트"""
        candidate = VolumeCandidate(
            stock_code="005930",
            stock_name="삼성전자",
            current_price=70000,
            volume_ratio=2.5,
            price_change=3.2,
            trade_value=100000000,
            score=7,
            timestamp=datetime.now(),
            is_breakout=True,
            ma_trend="상승추세"
        )
        
        self.assertEqual(candidate.stock_code, "005930")
        self.assertEqual(candidate.stock_name, "삼성전자")
        self.assertEqual(candidate.current_price, 70000)
        self.assertEqual(candidate.volume_ratio, 2.5)
        self.assertEqual(candidate.score, 7)
        self.assertTrue(candidate.is_breakout)
        self.assertEqual(candidate.ma_trend, "상승추세")
    
    def test_scanner_initialization(self):
        """스캐너 초기화 테스트"""
        self.assertEqual(self.scanner.scan_interval, 5)
        self.assertEqual(self.scanner.min_volume_ratio, 2.0)
        self.assertEqual(self.scanner.min_trade_value, 50_000_000)
        self.assertEqual(self.scanner.min_score, 5)
        self.assertFalse(self.scanner.auto_trade_enabled)
        self.assertEqual(len(self.scanner.candidates), 0)
        self.assertEqual(len(self.scanner.processed_stocks), 0)
    
    @patch('analysis.volume_scanner.requests.post')
    def test_get_volume_ranking(self, mock_post):
        """거래량 순위 조회 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "return_code": 0,
            "trde_qty_sdnin": [
                {
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "cur_prc": "70000",
                    "sdnin_rt": "+250%",
                    "flu_rt": 3.2,
                    "prev_trde_qty": "1000000",
                    "now_trde_qty": "2500000"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # 토큰 Mock 설정
        self.token_manager.get_valid_token = AsyncMock(return_value="test_token")
        
        # 테스트 실행
        asyncio.run(self.scanner.get_volume_ranking())
        
        # API 호출 확인
        mock_post.assert_called_once()
    
    @patch('analysis.volume_scanner.requests.post')
    def test_get_daily_chart_score(self, mock_post):
        """일봉 차트 점수 계산 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "stk_dt_pole_chart_qry": [
                {"dt": "20240101", "cur_prc": "65000"},
                {"dt": "20240102", "cur_prc": "66000"},
                {"dt": "20240103", "cur_prc": "67000"},
                {"dt": "20240104", "cur_prc": "68000"},
                {"dt": "20240105", "cur_prc": "69000"},
                {"dt": "20240106", "cur_prc": "70000"}
            ]
        }
        mock_post.return_value = mock_response
        
        # 토큰 Mock 설정
        self.token_manager.get_valid_token = AsyncMock(return_value="test_token")
        
        # 테스트 실행
        score = asyncio.run(self.scanner.get_daily_chart_score("005930", 70000))
        
        # 점수 계산 확인
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
    
    def test_add_auto_trade(self):
        """자동매매 추가 테스트"""
        # 자동매매 비활성화 상태에서 테스트
        result = self.scanner.add_auto_trade("005930", 70000, "삼성전자")
        self.assertFalse(result)
        
        # 자동매매 활성화
        self.scanner.auto_trade_enabled = True
        result = self.scanner.add_auto_trade("005930", 70000, "삼성전자")
        self.assertTrue(result)
        
        # 포지션 확인
        self.assertIn("005930", self.scanner.auto_trade_stocks)
        position = self.scanner.auto_trade_stocks["005930"]
        self.assertEqual(position['buy_price'], 70000)
        self.assertEqual(position['stock_name'], "삼성전자")
        self.assertEqual(position['status'], "monitoring")
    
    def test_remove_auto_trade(self):
        """자동매매 제거 테스트"""
        # 자동매매 추가
        self.scanner.auto_trade_enabled = True
        self.scanner.add_auto_trade("005930", 70000, "삼성전자")
        
        # 자동매매 제거
        self.scanner.remove_auto_trade("005930", 75000, "익절")
        
        # 포지션 제거 확인
        self.assertNotIn("005930", self.scanner.auto_trade_stocks)
    
    def test_get_auto_trade_status(self):
        """자동매매 상태 조회 테스트"""
        status = self.scanner.get_auto_trade_status()
        
        self.assertIn('enabled', status)
        self.assertIn('active_trades', status)
        self.assertIn('candidates', status)
        self.assertIn('processed_stocks', status)
        
        self.assertFalse(status['enabled'])
        self.assertEqual(status['active_trades'], 0)
        self.assertEqual(status['candidates'], 0)
        self.assertEqual(status['processed_stocks'], 0)
    
    def test_get_candidates_summary(self):
        """후보 종목 요약 테스트"""
        # 후보 종목 추가
        candidate = VolumeCandidate(
            stock_code="005930",
            stock_name="삼성전자",
            current_price=70000,
            volume_ratio=2.5,
            price_change=3.2,
            trade_value=100000000,
            score=7,
            timestamp=datetime.now(),
            is_breakout=True,
            ma_trend="상승추세"
        )
        self.scanner.candidates.append(candidate)
        
        # 요약 조회
        summary = self.scanner.get_candidates_summary()
        
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['stock_code'], "005930")
        self.assertEqual(summary[0]['stock_name'], "삼성전자")
        self.assertEqual(summary[0]['current_price'], 70000)
        self.assertEqual(summary[0]['volume_ratio'], 2.5)
        self.assertEqual(summary[0]['score'], 7)
        self.assertTrue(summary[0]['is_breakout'])
        self.assertEqual(summary[0]['ma_trend'], "상승추세")

class TestVolumeScannerIntegration(unittest.TestCase):
    """거래량 스캐너 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.settings = Settings()
        self.token_manager = Mock(spec=TokenManager)
        self.scanner = VolumeScanner(self.settings, self.token_manager)
    
    @patch('analysis.volume_scanner.requests.post')
    def test_full_scanning_process(self, mock_post):
        """전체 스캐닝 프로세스 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "return_code": 0,
            "trde_qty_sdnin": [
                {
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "cur_prc": "70000",
                    "sdnin_rt": "+250%",
                    "flu_rt": 3.2,
                    "prev_trde_qty": "1000000",
                    "now_trde_qty": "2500000"
                },
                {
                    "stk_cd": "000660",
                    "stk_nm": "SK하이닉스",
                    "cur_prc": "120000",
                    "sdnin_rt": "+180%",
                    "flu_rt": 2.1,
                    "prev_trde_qty": "500000",
                    "now_trde_qty": "900000"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # 토큰 Mock 설정
        self.token_manager.get_valid_token = AsyncMock(return_value="test_token")
        
        # 스캐닝 실행
        candidates = asyncio.run(self.scanner.scan_volume_candidates())
        
        # 결과 확인
        self.assertIsInstance(candidates, list)
        # 실제 API 호출이 없으므로 빈 리스트 반환
        self.assertEqual(len(candidates), 0)

if __name__ == '__main__':
    unittest.main() 