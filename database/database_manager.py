#!/usr/bin/env python3
"""
Stock Manager Database Manager
SQLite 기반 데이터베이스 관리 시스템
실시간 거래 데이터 저장, 조회, 분석 기능 제공
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from contextlib import contextmanager

from utils.logger import get_logger


class DatabaseManager:
    """SQLite 데이터베이스 관리자"""
    
    def __init__(self, db_path: str = "database/stock_manager.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = get_logger("database_manager")
        
        # 데이터베이스 초기화
        self._init_database()
        self.logger.info(f"데이터베이스 매니저 초기화 완료: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        try:
            yield conn
        except Exception as e:
            self.logger.error(f"데이터베이스 오류: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """데이터베이스 초기화 및 스키마 생성"""
        try:
            with self.get_connection() as conn:
                # SQL 스키마 파일 읽기
                schema_file = Path(__file__).parent / "init.sql"
                if schema_file.exists():
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    
                    # 스키마 실행
                    conn.executescript(schema_sql)
                    conn.commit()
                    self.logger.info("데이터베이스 스키마 생성 완료")
                else:
                    self.logger.error("스키마 파일을 찾을 수 없습니다: init.sql")
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    # ==================== 주식 데이터 관리 ====================
    
    def add_stock(self, symbol: str, name: str, exchange: str = "KOSPI", sector: str = None) -> bool:
        """주식 종목 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO stocks (symbol, name, exchange, sector)
                    VALUES (?, ?, ?, ?)
                """, (symbol, name, exchange, sector))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"주식 종목 추가: {symbol} ({name})")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"주식 종목 추가 실패: {e}")
            return False
    
    def get_stock(self, symbol: str) -> Optional[Dict]:
        """주식 종목 정보 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"주식 종목 조회 실패: {e}")
            return None
    
    def get_all_stocks(self) -> List[Dict]:
        """모든 주식 종목 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM stocks ORDER BY symbol")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"주식 종목 목록 조회 실패: {e}")
            return []
    
    # ==================== 실시간 거래 데이터 관리 ====================
    
    def save_market_data(self, stock_symbol: str, data: Dict) -> bool:
        """실시간 거래 데이터 저장"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                self.logger.warning(f"주식 종목이 존재하지 않음: {stock_symbol}")
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO market_data 
                    (stock_id, timestamp, open_price, high_price, low_price, close_price, 
                     volume, trade_value, price_change, execution_strength)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock['id'],
                    data.get('timestamp', datetime.now()),
                    data.get('open_price'),
                    data.get('high_price'),
                    data.get('low_price'),
                    data.get('close_price'),
                    data.get('volume'),
                    data.get('trade_value'),
                    data.get('price_change'),
                    data.get('execution_strength')
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"거래 데이터 저장 실패: {e}")
            return False
    
    def get_market_data(self, stock_symbol: str, limit: int = 100) -> List[Dict]:
        """주식 거래 데이터 조회"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                return []
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM market_data 
                    WHERE stock_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (stock['id'], limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"거래 데이터 조회 실패: {e}")
            return []
    
    def get_market_data_by_date(self, stock_symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """기간별 거래 데이터 조회"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                return []
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM market_data 
                    WHERE stock_id = ? AND timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                """, (stock['id'], start_date, end_date))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"기간별 거래 데이터 조회 실패: {e}")
            return []
    
    # ==================== 거래량 돌파 이벤트 관리 ====================
    
    def save_volume_breakout(self, stock_symbol: str, breakout_data: Dict) -> bool:
        """거래량 돌파 이벤트 저장"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO volume_breakouts 
                    (stock_id, breakout_time, today_volume, prev_day_volume, volume_ratio,
                     price_at_breakout, trade_value_at_breakout)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock['id'],
                    breakout_data.get('breakout_time', datetime.now()),
                    breakout_data.get('today_volume'),
                    breakout_data.get('prev_day_volume'),
                    breakout_data.get('volume_ratio'),
                    breakout_data.get('price_at_breakout'),
                    breakout_data.get('trade_value_at_breakout')
                ))
                conn.commit()
                self.logger.info(f"거래량 돌파 이벤트 저장: {stock_symbol}")
                return True
        except Exception as e:
            self.logger.error(f"거래량 돌파 이벤트 저장 실패: {e}")
            return False
    
    def get_volume_breakouts(self, stock_symbol: str = None, days: int = 7) -> List[Dict]:
        """거래량 돌파 이벤트 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if stock_symbol:
                    stock = self.get_stock(stock_symbol)
                    if not stock:
                        return []
                    
                    cursor.execute("""
                        SELECT vb.*, s.symbol, s.name 
                        FROM volume_breakouts vb
                        JOIN stocks s ON vb.stock_id = s.id
                        WHERE vb.stock_id = ? AND vb.breakout_time >= ?
                        ORDER BY vb.breakout_time DESC
                    """, (stock['id'], datetime.now() - timedelta(days=days)))
                else:
                    cursor.execute("""
                        SELECT vb.*, s.symbol, s.name 
                        FROM volume_breakouts vb
                        JOIN stocks s ON vb.stock_id = s.id
                        WHERE vb.breakout_time >= ?
                        ORDER BY vb.breakout_time DESC
                    """, (datetime.now() - timedelta(days=days),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"거래량 돌파 이벤트 조회 실패: {e}")
            return []
    
    # ==================== 자동매매 후보 관리 ====================
    
    def save_auto_trading_candidate(self, stock_symbol: str, candidate_data: Dict) -> bool:
        """자동매매 후보 종목 저장"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO auto_trading_candidates 
                    (stock_id, candidate_time, current_price, price_change, trade_value,
                     execution_strength, volume_ratio, ma_trend, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock['id'],
                    candidate_data.get('candidate_time', datetime.now()),
                    candidate_data.get('current_price'),
                    candidate_data.get('price_change'),
                    candidate_data.get('trade_value'),
                    candidate_data.get('execution_strength'),
                    candidate_data.get('volume_ratio'),
                    candidate_data.get('ma_trend'),
                    candidate_data.get('status', 'ACTIVE')
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"자동매매 후보 저장 실패: {e}")
            return False
    
    def get_active_candidates(self) -> List[Dict]:
        """활성 자동매매 후보 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT atc.*, s.symbol, s.name 
                    FROM auto_trading_candidates atc
                    JOIN stocks s ON atc.stock_id = s.id
                    WHERE atc.status = 'ACTIVE'
                    ORDER BY atc.candidate_time DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"자동매매 후보 조회 실패: {e}")
            return []
    
    def update_candidate_status(self, candidate_id: int, status: str) -> bool:
        """자동매매 후보 상태 업데이트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE auto_trading_candidates 
                    SET status = ? 
                    WHERE id = ?
                """, (status, candidate_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"자동매매 후보 상태 업데이트 실패: {e}")
            return False
    
    # ==================== 거래 신호 관리 ====================
    
    def save_trading_signal(self, stock_symbol: str, signal_data: Dict) -> bool:
        """거래 신호 저장"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trading_signals 
                    (stock_id, signal_type, confidence, indicators)
                    VALUES (?, ?, ?, ?)
                """, (
                    stock['id'],
                    signal_data.get('signal_type'),
                    signal_data.get('confidence'),
                    json.dumps(signal_data.get('indicators', {}), ensure_ascii=False)
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"거래 신호 저장 실패: {e}")
            return False
    
    def get_trading_signals(self, stock_symbol: str = None, days: int = 7) -> List[Dict]:
        """거래 신호 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if stock_symbol:
                    stock = self.get_stock(stock_symbol)
                    if not stock:
                        return []
                    
                    cursor.execute("""
                        SELECT ts.*, s.symbol, s.name 
                        FROM trading_signals ts
                        JOIN stocks s ON ts.stock_id = s.id
                        WHERE ts.stock_id = ? AND ts.created_at >= ?
                        ORDER BY ts.created_at DESC
                    """, (stock['id'], datetime.now() - timedelta(days=days)))
                else:
                    cursor.execute("""
                        SELECT ts.*, s.symbol, s.name 
                        FROM trading_signals ts
                        JOIN stocks s ON ts.stock_id = s.id
                        WHERE ts.created_at >= ?
                        ORDER BY ts.created_at DESC
                    """, (datetime.now() - timedelta(days=days),))
                
                results = []
                for row in cursor.fetchall():
                    data = dict(row)
                    # JSON 문자열을 딕셔너리로 변환
                    if data.get('indicators'):
                        try:
                            data['indicators'] = json.loads(data['indicators'])
                        except:
                            data['indicators'] = {}
                    results.append(data)
                
                return results
        except Exception as e:
            self.logger.error(f"거래 신호 조회 실패: {e}")
            return []
    
    # ==================== 시스템 로그 관리 ====================
    
    def save_system_log(self, level: str, message: str, module: str = None) -> bool:
        """시스템 로그 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_logs (level, message, module)
                    VALUES (?, ?, ?)
                """, (level, message, module))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"시스템 로그 저장 실패: {e}")
            return False
    
    def get_system_logs(self, level: str = None, days: int = 7) -> List[Dict]:
        """시스템 로그 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if level:
                    cursor.execute("""
                        SELECT * FROM system_logs 
                        WHERE level = ? AND created_at >= ?
                        ORDER BY created_at DESC
                    """, (level, datetime.now() - timedelta(days=days)))
                else:
                    cursor.execute("""
                        SELECT * FROM system_logs 
                        WHERE created_at >= ?
                        ORDER BY created_at DESC
                    """, (datetime.now() - timedelta(days=days),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"시스템 로그 조회 실패: {e}")
            return []
    
    # ==================== 성능 지표 관리 ====================
    
    def save_performance_metric(self, user_id: int, metric_name: str, metric_value: float) -> bool:
        """성능 지표 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO performance_metrics (user_id, metric_name, metric_value)
                    VALUES (?, ?, ?)
                """, (user_id, metric_name, metric_value))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"성능 지표 저장 실패: {e}")
            return False
    
    def get_performance_metrics(self, user_id: int = None, metric_name: str = None, days: int = 30) -> List[Dict]:
        """성능 지표 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if user_id and metric_name:
                    cursor.execute("""
                        SELECT * FROM performance_metrics 
                        WHERE user_id = ? AND metric_name = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (user_id, metric_name, datetime.now() - timedelta(days=days)))
                elif user_id:
                    cursor.execute("""
                        SELECT * FROM performance_metrics 
                        WHERE user_id = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (user_id, datetime.now() - timedelta(days=days)))
                else:
                    cursor.execute("""
                        SELECT * FROM performance_metrics 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (datetime.now() - timedelta(days=days),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"성능 지표 조회 실패: {e}")
            return []
    
    # ==================== 데이터 분석 기능 ====================
    
    def get_daily_summary(self, stock_symbol: str, date: datetime) -> Dict:
        """일일 거래 요약"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                return {}
            
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        MIN(close_price) as low_price,
                        MAX(close_price) as high_price,
                        AVG(close_price) as avg_price,
                        SUM(volume) as total_volume,
                        SUM(trade_value) as total_trade_value,
                        COUNT(*) as data_points
                    FROM market_data 
                    WHERE stock_id = ? AND timestamp BETWEEN ? AND ?
                """, (stock['id'], start_date, end_date))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return {}
        except Exception as e:
            self.logger.error(f"일일 요약 조회 실패: {e}")
            return {}
    
    def get_volume_analysis(self, days: int = 30) -> List[Dict]:
        """거래량 분석"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.symbol, s.name,
                        COUNT(vb.id) as breakout_count,
                        AVG(vb.volume_ratio) as avg_volume_ratio,
                        MAX(vb.today_volume) as max_volume
                    FROM stocks s
                    LEFT JOIN volume_breakouts vb ON s.id = vb.stock_id 
                        AND vb.breakout_time >= ?
                    GROUP BY s.id, s.symbol, s.name
                    ORDER BY breakout_count DESC, avg_volume_ratio DESC
                """, (datetime.now() - timedelta(days=days),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"거래량 분석 실패: {e}")
            return []
    
    # ==================== 데이터베이스 관리 ====================
    
    def backup_database(self, backup_path: str = None) -> bool:
        """데이터베이스 백업"""
        try:
            if not backup_path:
                backup_path = f"database/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(exist_ok=True)
            
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"데이터베이스 백업 완료: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"데이터베이스 백업 실패: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """오래된 데이터 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 오래된 거래 데이터 삭제
                cursor.execute("DELETE FROM market_data WHERE timestamp < ?", (cutoff_date,))
                deleted_count += cursor.rowcount
                
                # 오래된 시스템 로그 삭제
                cursor.execute("DELETE FROM system_logs WHERE created_at < ?", (cutoff_date,))
                deleted_count += cursor.rowcount
                
                # 오래된 성능 지표 삭제
                cursor.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_date,))
                deleted_count += cursor.rowcount
                
                conn.commit()
            
            self.logger.info(f"오래된 데이터 정리 완료: {deleted_count}개 레코드 삭제")
            return deleted_count
        except Exception as e:
            self.logger.error(f"데이터 정리 실패: {e}")
            return 0
    
    def get_database_stats(self) -> Dict:
        """데이터베이스 통계"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                
                # 테이블별 레코드 수
                tables = ['stocks', 'market_data', 'volume_breakouts', 'auto_trading_candidates', 
                         'trading_signals', 'system_logs', 'performance_metrics']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # 데이터베이스 크기
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            self.logger.error(f"데이터베이스 통계 조회 실패: {e}")
            return {}

    # ==================== 주문 관리 ====================
    
    def save_order(self, stock_symbol: str, order_data: Dict) -> bool:
        """주문(매수/매도) 내역 저장"""
        try:
            stock = self.get_stock(stock_symbol)
            if not stock:
                self.logger.error(f"종목 정보 없음: {stock_symbol}")
                return False

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO orders
                    (user_id, stock_id, order_type, quantity, price, status, created_at, filled_at, order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_data.get('user_id', 1),  # 기본 admin
                    stock['id'],
                    order_data.get('order_type', 'BUY'),  # BUY, SELL
                    order_data.get('quantity', 0),
                    order_data.get('price', 0),
                    order_data.get('status', 'PENDING'),  # PENDING, FILLED, CANCELLED, REJECTED
                    order_data.get('created_at', datetime.now()),
                    order_data.get('filled_at'),
                    order_data.get('order_id')
                ))
                conn.commit()
                self.logger.info(f"주문 내역 저장: {stock_symbol} - {order_data.get('order_type')} {order_data.get('quantity')}주")
                return True
        except Exception as e:
            self.logger.error(f"주문 내역 저장 실패: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str, filled_at: datetime = None) -> bool:
        """주문 상태 업데이트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if filled_at:
                    cursor.execute("""
                        UPDATE orders 
                        SET status = ?, filled_at = ? 
                        WHERE order_id = ?
                    """, (status, filled_at, order_id))
                else:
                    cursor.execute("""
                        UPDATE orders 
                        SET status = ? 
                        WHERE order_id = ?
                    """, (status, order_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"주문 상태 업데이트 실패: {e}")
            return False
    
    def get_orders(self, stock_symbol: str = None, user_id: int = None, days: int = 30) -> List[Dict]:
        """주문 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if stock_symbol:
                    stock = self.get_stock(stock_symbol)
                    if not stock:
                        return []
                    
                    cursor.execute("""
                        SELECT o.*, s.symbol, s.name 
                        FROM orders o
                        JOIN stocks s ON o.stock_id = s.id
                        WHERE o.stock_id = ? AND o.created_at >= ?
                        ORDER BY o.created_at DESC
                    """, (stock['id'], datetime.now() - timedelta(days=days)))
                elif user_id:
                    cursor.execute("""
                        SELECT o.*, s.symbol, s.name 
                        FROM orders o
                        JOIN stocks s ON o.stock_id = s.id
                        WHERE o.user_id = ? AND o.created_at >= ?
                        ORDER BY o.created_at DESC
                    """, (user_id, datetime.now() - timedelta(days=days)))
                else:
                    cursor.execute("""
                        SELECT o.*, s.symbol, s.name 
                        FROM orders o
                        JOIN stocks s ON o.stock_id = s.id
                        WHERE o.created_at >= ?
                        ORDER BY o.created_at DESC
                    """, (datetime.now() - timedelta(days=days),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"주문 내역 조회 실패: {e}")
            return []


# 전역 데이터베이스 매니저 인스턴스
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """전역 데이터베이스 매니저 인스턴스 반환"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database(db_path: str = "database/stock_manager.db") -> DatabaseManager:
    """데이터베이스 초기화"""
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    return _db_manager
