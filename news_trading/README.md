# 뉴스 기반 주식 거래 시스템

## 개요
이 시스템은 실시간 뉴스를 크롤링하고 감정 분석을 통해 주식 거래 신호를 생성하는 모듈화된 프레임워크입니다.

## 아키텍처 특징

### 🏗️ 모듈화 설계
- **플러그인 기반**: 새로운 뉴스 소스나 분석 방법을 쉽게 추가
- **단일 책임 원칙**: 각 모듈이 하나의 명확한 역할만 담당
- **의존성 분리**: 모듈 간 느슨한 결합으로 유지보수성 향상

### ⚡ 성능 최적화
- **비동기 처리**: `asyncio`를 활용한 동시 크롤링
- **배치 처리**: 대량 데이터 효율적 처리
- **메모리 관리**: 오래된 데이터 자동 정리

### 🔧 확장성
- **추상 클래스**: 새로운 기능 추가 시 표준 인터페이스 제공
- **설정 기반**: 코드 수정 없이 설정 변경으로 동작 조정
- **로깅 시스템**: 상세한 로그로 디버깅 및 모니터링

## 시스템 구조

```
news_trading/
├── __init__.py          # 패키지 초기화
├── config.py           # 중앙 설정 관리
├── news_crawler.py     # 뉴스 크롤링 모듈
├── sentiment_analyzer.py # 감정 분석 모듈
├── trading_signals.py  # 거래 신호 생성
├── main.py            # 메인 오케스트레이터
└── README.md          # 이 파일
```

## 주요 모듈

### 1. News Crawler (`news_crawler.py`)
- **플러그인 아키텍처**: 새로운 뉴스 소스 쉽게 추가
- **비동기 크롤링**: 여러 소스 동시 수집
- **에러 처리**: 개별 소스 실패 시 전체 시스템 영향 없음

### 2. Sentiment Analyzer (`sentiment_analyzer.py`)
- **다중 분석 방법**: 키워드 기반, 패턴 기반
- **조합 분석**: 여러 방법의 결과를 가중 평균으로 결합
- **신뢰도 측정**: 분석 결과의 신뢰성 평가

### 3. Trading Signals (`trading_signals.py`)
- **종목별 그룹화**: 뉴스를 종목별로 분류
- **중복 필터링**: 같은 종목의 반복 신호 방지
- **리스크 관리**: 손절가, 익절가 자동 계산

### 4. Main Orchestrator (`main.py`)
- **통합 관리**: 모든 모듈을 조율
- **CLI 인터페이스**: 사용자 친화적 명령행 도구
- **상태 모니터링**: 실시간 시스템 상태 확인

## 사용 방법

### 1. 기본 실행
```bash
python news_trading/main.py
```

### 2. 시스템 시작
```
=== 뉴스 기반 거래 시스템 ===
1. 시스템 시작
2. 시스템 상태 조회
3. 테스트 뉴스 분석
4. 종료

선택하세요 (1-4): 1
```

### 3. 설정 변경
`config.py`에서 다음 설정들을 조정할 수 있습니다:
- 뉴스 소스 URL
- 감정 분석 키워드
- 거래 신호 임계값
- 크롤링 간격

## 확장 방법

### 새로운 뉴스 소스 추가
```python
class NewNewsSource(NewsSource):
    async def fetch_news(self) -> List[Dict[str, Any]]:
        # 구현
        pass
    
    def parse_news(self, raw_data: Any) -> List[Dict[str, Any]]:
        # 구현
        pass

# NewsCrawlerManager에 추가
crawler = NewsCrawlerManager()
crawler.add_source('new_source', NewNewsSource())
```

### 새로운 감정 분석 방법 추가
```python
class NewAnalyzer(SentimentAnalyzer):
    def analyze(self, text: str) -> Dict[str, Any]:
        # 구현
        pass

# SentimentAnalyzerManager에 추가
analyzer = SentimentAnalyzerManager()
analyzer.add_analyzer('new_method', NewAnalyzer())
```

## 성능 특징

### 속도
- **비동기 크롤링**: 5개 뉴스 소스 동시 처리
- **배치 분석**: 100개 뉴스 동시 감정 분석
- **실시간 신호**: 1초 내 거래 신호 생성

### 안정성
- **에러 격리**: 한 모듈 실패 시 다른 모듈 영향 없음
- **자동 복구**: 네트워크 오류 시 자동 재시도
- **데이터 검증**: 수집된 데이터 유효성 검사

### 확장성
- **수평 확장**: 여러 서버에 분산 배포 가능
- **수직 확장**: 더 많은 뉴스 소스 및 분석 방법 추가
- **모듈 교체**: 기존 모듈을 개선된 버전으로 쉽게 교체

## 모니터링 및 로깅

### 로그 파일
- `logs/news_trading.log`: 상세한 시스템 로그
- 실시간 크롤링 상태
- 거래 신호 생성 과정
- 에러 및 경고 메시지

### 시스템 상태
- 활성 신호 개수
- 크롤링 성공률
- 처리된 뉴스 수
- 시스템 가동 시간

## 향후 개선 계획

1. **AI 모델 통합**: 딥러닝 기반 감정 분석
2. **실시간 거래**: 실제 거래소 API 연동
3. **웹 대시보드**: 시각적 모니터링 인터페이스
4. **백테스팅**: 과거 뉴스 데이터로 전략 검증
5. **알림 시스템**: 중요한 신호 발생 시 알림

## 기술 스택

- **Python 3.8+**: 메인 프로그래밍 언어
- **asyncio**: 비동기 프로그래밍
- **aiohttp**: 비동기 HTTP 클라이언트
- **logging**: 로깅 시스템
- **typing**: 타입 힌트

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 