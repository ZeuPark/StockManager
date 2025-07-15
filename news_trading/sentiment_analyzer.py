"""
Sentiment Analyzer Module
다양한 감정 분석 방법을 지원하는 모듈
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
import re
from collections import Counter
import logging
from .config import SENTIMENT_CONFIG

logger = logging.getLogger(__name__)

class SentimentAnalyzer(ABC):
    """감정 분석 추상 클래스"""
    
    @abstractmethod
    def analyze(self, text: str) -> Dict[str, Any]:
        """텍스트 감정 분석"""
        pass

class KeywordBasedAnalyzer(SentimentAnalyzer):
    """키워드 기반 감정 분석"""
    
    def __init__(self):
        self.positive_keywords = SENTIMENT_CONFIG['positive_keywords']
        self.negative_keywords = SENTIMENT_CONFIG['negative_keywords']
        self.neutral_keywords = SENTIMENT_CONFIG['neutral_keywords']
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """키워드 기반 감정 분석"""
        text_lower = text.lower()
        
        # 키워드 카운트
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        neutral_count = sum(1 for keyword in self.neutral_keywords if keyword in text_lower)
        
        # 감정 점수 계산
        total_keywords = positive_count + negative_count + neutral_count
        if total_keywords == 0:
            sentiment_score = 0
            confidence = 0
        else:
            sentiment_score = (positive_count - negative_count) / total_keywords
            confidence = total_keywords / len(text.split())  # 키워드 밀도
        
        return {
            'sentiment': self._get_sentiment_label(sentiment_score),
            'score': sentiment_score,
            'confidence': min(confidence, 1.0),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'method': 'keyword_based'
        }
    
    def _get_sentiment_label(self, score: float) -> str:
        """점수를 감정 라벨로 변환"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'

class PatternBasedAnalyzer(SentimentAnalyzer):
    """패턴 기반 감정 분석"""
    
    def __init__(self):
        self.patterns = {
            'positive': [
                r'상승세|급등|호재|성장|실적호전|신기술|계약|성공',
                r'기대|전망|긍정|유리|강세|돌파|신고가'
            ],
            'negative': [
                r'하락세|급락|악재|손실|실적악화|리스크|규제|실패',
                r'우려|부정|불리|약세|하향|신저가'
            ]
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """패턴 기반 감정 분석"""
        positive_matches = 0
        negative_matches = 0
        
        for pattern in self.patterns['positive']:
            positive_matches += len(re.findall(pattern, text))
        
        for pattern in self.patterns['negative']:
            negative_matches += len(re.findall(pattern, text))
        
        total_matches = positive_matches + negative_matches
        if total_matches == 0:
            sentiment_score = 0
            confidence = 0
        else:
            sentiment_score = (positive_matches - negative_matches) / total_matches
            confidence = total_matches / len(text.split())
        
        return {
            'sentiment': self._get_sentiment_label(sentiment_score),
            'score': sentiment_score,
            'confidence': min(confidence, 1.0),
            'positive_matches': positive_matches,
            'negative_matches': negative_matches,
            'method': 'pattern_based'
        }
    
    def _get_sentiment_label(self, score: float) -> str:
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'

class SentimentAnalyzerManager:
    """감정 분석 관리자 - 여러 방법을 조합"""
    
    def __init__(self):
        self.analyzers = {
            'keyword': KeywordBasedAnalyzer(),
            'pattern': PatternBasedAnalyzer()
        }
    
    def analyze_text(self, text: str, method: str = 'combined') -> Dict[str, Any]:
        """텍스트 감정 분석"""
        if method == 'combined':
            return self._analyze_combined(text)
        elif method in self.analyzers:
            return self.analyzers[method].analyze(text)
        else:
            raise ValueError(f"지원하지 않는 분석 방법: {method}")
    
    def _analyze_combined(self, text: str) -> Dict[str, Any]:
        """여러 방법을 조합한 분석"""
        results = {}
        for name, analyzer in self.analyzers.items():
            results[name] = analyzer.analyze(text)
        
        # 가중 평균으로 최종 점수 계산
        total_score = 0
        total_confidence = 0
        weight_sum = 0
        
        for name, result in results.items():
            weight = result['confidence']  # 신뢰도를 가중치로 사용
            total_score += result['score'] * weight
            total_confidence += weight
            weight_sum += weight
        
        if weight_sum > 0:
            final_score = total_score / weight_sum
            final_confidence = total_confidence / len(results)
        else:
            final_score = 0
            final_confidence = 0
        
        return {
            'sentiment': self._get_sentiment_label(final_score),
            'score': final_score,
            'confidence': final_confidence,
            'method': 'combined',
            'individual_results': results
        }
    
    def _get_sentiment_label(self, score: float) -> str:
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def add_analyzer(self, name: str, analyzer: SentimentAnalyzer):
        """새로운 분석기 추가"""
        self.analyzers[name] = analyzer
        logger.info(f"새로운 감정 분석기 추가: {name}")

# 사용 예시
def main():
    analyzer = SentimentAnalyzerManager()
    
    test_text = "삼성전자 실적호전으로 상승세 전망, 신기술 개발 성공"
    result = analyzer.analyze_text(test_text)
    
    print(f"분석 결과: {result}")

if __name__ == "__main__":
    main() 