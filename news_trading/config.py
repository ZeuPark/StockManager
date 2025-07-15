"""
News Trading Configuration
중앙 집중식 설정 관리
"""

# 뉴스 소스 설정
NEWS_SOURCES = {
    'korean': {
        'naver': 'https://news.naver.com/',
        'mk': 'https://www.mk.co.kr/',
        'hankyung': 'https://www.hankyung.com/'
    },
    'global': {
        'reuters': 'https://www.reuters.com/',
        'bloomberg': 'https://www.bloomberg.com/',
        'yahoo_finance': 'https://finance.yahoo.com/'
    }
}

# 감정 분석 설정
SENTIMENT_CONFIG = {
    'positive_keywords': ['상승', '급등', '호재', '성장', '실적호전', '신기술', '계약'],
    'negative_keywords': ['하락', '급락', '악재', '손실', '실적악화', '리스크', '규제'],
    'neutral_keywords': ['발표', '공시', '보고서', '분석', '전망']
}

# 거래 신호 설정
TRADING_SIGNALS = {
    'min_confidence': 0.7,  # 최소 신뢰도
    'max_position_size': 0.1,  # 최대 포지션 크기 (10%)
    'stop_loss': 0.05,  # 손절 기준 (5%)
    'take_profit': 0.15  # 익절 기준 (15%)
}

# 데이터베이스 설정
DB_CONFIG = {
    'news_table': 'news_data',
    'sentiment_table': 'sentiment_analysis',
    'signals_table': 'trading_signals'
}

# 성능 설정
PERFORMANCE_CONFIG = {
    'crawl_interval': 300,  # 크롤링 간격 (5분)
    'max_news_age': 3600,  # 최대 뉴스 나이 (1시간)
    'batch_size': 100  # 배치 처리 크기
} 