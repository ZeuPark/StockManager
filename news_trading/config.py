"""
News Trading Configuration
중앙 집중식 설정 관리
"""

# 뉴스 수집 설정
NEWS_SOURCES = {
    "naver": {
        "enabled": True,
        "categories": ["economy", "stock", "company"],
        "max_pages": 10,
        "update_interval": 3600,  # 1시간마다 업데이트
    }
}

# 스윙 트레이딩용 뉴스 데이터 설정
SWING_TRADING_NEWS_CONFIG = {
    "real_time": {
        "period": "1-2일",  # 실시간 모니터링
        "max_pages": 3,     # 최신 뉴스 3페이지
        "keywords": ["실적", "실적발표", "분기실적", "연간실적", "정책", "규제", "인수", "합병"]
    },
    "background": {
        "period": "2-4주",  # 배경 분석용
        "max_pages": 10,    # 2-4주치 뉴스
        "keywords": ["업계동향", "시장전망", "기업분석", "투자의견", "목표주가"]
    },
    "pattern": {
        "period": "1-3개월", # 패턴 분석용
        "max_pages": 30,     # 1-3개월치 뉴스
        "keywords": ["주가", "등락", "급등", "급락", "거래량", "외국인", "기관"]
    }
}

# 감정 분석 설정
SENTIMENT_CONFIG = {
    "positive_keywords": [
        "상승", "급등", "호재", "실적개선", "성장", "확대", "진출", "수주", "계약",
        "승인", "허가", "개발성공", "특허", "신제품", "해외진출", "수익증가"
    ],
    "negative_keywords": [
        "하락", "급락", "악재", "실적악화", "손실", "축소", "철수", "계약해지",
        "반대", "거부", "개발실패", "특허무효", "리콜", "해외철수", "수익감소"
    ],
    "swing_keywords": [
        "스윙", "단기", "중기", "보유", "매수", "매도", "목표가", "손절가",
        "기술적분석", "차트", "지지선", "저항선", "이동평균", "RSI", "MACD"
    ],
    "neutral_keywords": [
        "발표", "공시", "보고서", "분석", "전망", "예상", "추정", "평가",
        "검토", "검토중", "논의", "협의", "계획", "방안", "정책"
    ]
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