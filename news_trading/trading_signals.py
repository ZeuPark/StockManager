"""
Trading Signal Generator
뉴스 감정 분석과 시장 데이터를 결합한 거래 신호 생성
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from .config import TRADING_SIGNALS
from .sentiment_analyzer import SentimentAnalyzerManager

logger = logging.getLogger(__name__)

class TradingSignal:
    """거래 신호 클래스"""
    
    def __init__(self, 
                 stock_code: str,
                 signal_type: str,  # 'buy', 'sell', 'hold'
                 confidence: float,
                 sentiment_score: float,
                 news_count: int,
                 timestamp: datetime,
                 reason: str,
                 target_price: Optional[float] = None,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None):
        
        self.stock_code = stock_code
        self.signal_type = signal_type
        self.confidence = confidence
        self.sentiment_score = sentiment_score
        self.news_count = news_count
        self.timestamp = timestamp
        self.reason = reason
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'stock_code': self.stock_code,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'sentiment_score': self.sentiment_score,
            'news_count': self.news_count,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }
    
    def __str__(self) -> str:
        return f"Signal({self.stock_code}, {self.signal_type}, conf:{self.confidence:.2f})"

class SignalGenerator:
    """거래 신호 생성기"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzerManager()
        self.min_confidence = TRADING_SIGNALS['min_confidence']
        self.max_position_size = TRADING_SIGNALS['max_position_size']
        self.stop_loss = TRADING_SIGNALS['stop_loss']
        self.take_profit = TRADING_SIGNALS['take_profit']
    
    def generate_signals(self, news_data: List[Dict[str, Any]], 
                        market_data: Optional[Dict[str, Any]] = None) -> List[TradingSignal]:
        """뉴스 데이터로부터 거래 신호 생성"""
        signals = []
        
        # 뉴스를 종목별로 그룹화
        stock_news = self._group_news_by_stock(news_data)
        
        for stock_code, news_list in stock_news.items():
            signal = self._analyze_stock_news(stock_code, news_list, market_data)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _group_news_by_stock(self, news_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """뉴스를 종목별로 그룹화"""
        stock_news = {}
        
        for news in news_data:
            # 뉴스에서 종목 코드 추출 (실제로는 더 정교한 로직 필요)
            stock_codes = self._extract_stock_codes(news['title'] + ' ' + news['content'])
            
            for stock_code in stock_codes:
                if stock_code not in stock_news:
                    stock_news[stock_code] = []
                stock_news[stock_code].append(news)
        
        return stock_news
    
    def _extract_stock_codes(self, text: str) -> List[str]:
        """텍스트에서 종목 코드 추출"""
        # 실제로는 더 정교한 로직 필요 (종목명-코드 매핑 등)
        # 여기서는 예시로 삼성전자만 반환
        if any(keyword in text for keyword in ['삼성전자', '삼성', '005930']):
            return ['005930']
        return []
    
    def _analyze_stock_news(self, stock_code: str, news_list: List[Dict[str, Any]], 
                           market_data: Optional[Dict[str, Any]] = None) -> Optional[TradingSignal]:
        """개별 종목 뉴스 분석"""
        if not news_list:
            return None
        
        # 최근 뉴스만 분석 (1시간 이내)
        recent_news = self._filter_recent_news(news_list, hours=1)
        if not recent_news:
            return None
        
        # 감정 분석
        combined_text = ' '.join([news['title'] + ' ' + news['content'] for news in recent_news])
        sentiment_result = self.sentiment_analyzer.analyze_text(combined_text)
        
        # 신뢰도가 너무 낮으면 신호 생성 안함
        if sentiment_result['confidence'] < self.min_confidence:
            return None
        
        # 거래 신호 결정
        signal_type, reason = self._determine_signal_type(sentiment_result, len(recent_news))
        
        if signal_type == 'hold':
            return None
        
        # 목표가, 손절가, 익절가 계산
        target_price, stop_loss, take_profit = self._calculate_prices(stock_code, market_data)
        
        return TradingSignal(
            stock_code=stock_code,
            signal_type=signal_type,
            confidence=sentiment_result['confidence'],
            sentiment_score=sentiment_result['score'],
            news_count=len(recent_news),
            timestamp=datetime.now(),
            reason=reason,
            target_price=target_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def _filter_recent_news(self, news_list: List[Dict[str, Any]], hours: int) -> List[Dict[str, Any]]:
        """최근 뉴스만 필터링"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [news for news in news_list if news['timestamp'] > cutoff_time]
    
    def _determine_signal_type(self, sentiment_result: Dict[str, Any], news_count: int) -> tuple:
        """감정 분석 결과로 거래 신호 결정"""
        score = sentiment_result['score']
        confidence = sentiment_result['confidence']
        
        # 뉴스 개수와 감정 점수를 종합적으로 고려
        if score > 0.3 and confidence > 0.5 and news_count >= 2:
            return 'buy', f"긍정적 뉴스 {news_count}개, 감정점수 {score:.2f}"
        elif score < -0.3 and confidence > 0.5 and news_count >= 2:
            return 'sell', f"부정적 뉴스 {news_count}개, 감정점수 {score:.2f}"
        else:
            return 'hold', "신호 없음"
    
    def _calculate_prices(self, stock_code: str, market_data: Optional[Dict[str, Any]]) -> tuple:
        """목표가, 손절가, 익절가 계산"""
        # 실제로는 현재가를 가져와서 계산
        # 여기서는 예시 값 반환
        current_price = 50000  # 예시 현재가
        
        target_price = current_price * 1.05  # 5% 상승 목표
        stop_loss = current_price * (1 - self.stop_loss)
        take_profit = current_price * (1 + self.take_profit)
        
        return target_price, stop_loss, take_profit

class SignalManager:
    """거래 신호 관리자"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.recent_signals = []  # 최근 신호들 저장
    
    def process_news(self, news_data: List[Dict[str, Any]]) -> List[TradingSignal]:
        """뉴스 처리 및 신호 생성"""
        signals = self.signal_generator.generate_signals(news_data)
        
        # 중복 신호 필터링
        filtered_signals = self._filter_duplicate_signals(signals)
        
        # 신호 저장
        self.recent_signals.extend(filtered_signals)
        
        # 오래된 신호 정리 (24시간 이전)
        self._cleanup_old_signals()
        
        return filtered_signals
    
    def _filter_duplicate_signals(self, new_signals: List[TradingSignal]) -> List[TradingSignal]:
        """중복 신호 필터링"""
        filtered = []
        
        for new_signal in new_signals:
            # 같은 종목의 최근 신호 확인
            recent_same_stock = [
                s for s in self.recent_signals 
                if s.stock_code == new_signal.stock_code 
                and s.timestamp > datetime.now() - timedelta(hours=6)
            ]
            
            # 같은 방향의 신호가 없으면 추가
            if not any(s.signal_type == new_signal.signal_type for s in recent_same_stock):
                filtered.append(new_signal)
        
        return filtered
    
    def _cleanup_old_signals(self):
        """오래된 신호 정리"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.recent_signals = [
            s for s in self.recent_signals 
            if s.timestamp > cutoff_time
        ]
    
    def get_active_signals(self) -> List[TradingSignal]:
        """활성 신호 조회"""
        return [s for s in self.recent_signals if s.signal_type in ['buy', 'sell']]

# 사용 예시
def main():
    signal_manager = SignalManager()
    
    # 예시 뉴스 데이터
    test_news = [
        {
            'title': '삼성전자 실적호전으로 상승세 전망',
            'content': '삼성전자가 예상보다 좋은 실적을 발표하여 주가 상승이 기대됩니다.',
            'timestamp': datetime.now(),
            'source': 'test'
        }
    ]
    
    signals = signal_manager.process_news(test_news)
    print(f"생성된 신호: {len(signals)}개")
    for signal in signals:
        print(signal)

if __name__ == "__main__":
    main() 