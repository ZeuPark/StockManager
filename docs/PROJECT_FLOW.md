# StockManager 프로젝트 구조 및 전략/기법 요약

## 1. 시스템 구조
- 실시간 트레이딩 엔진(core/real_time_trading.py)
- 전략 분석 및 백테스트(analysis/, core/)
- 주문/리스크 관리(orders/, config/)
- 데이터 수집 및 DB(database/, data_collection/)
- 유틸리티 및 모니터링(utils/, monitor/)

## 2. 폴더별 역할
- **core/**: 실시간 트레이딩, 백테스트, 실험 등 시스템의 핵심 로직
- **analysis/**: 전략 분석, 시각화, 데이터 분석 도구
- **api/**: 증권사 API 연동(REST, WebSocket)
- **orders/**: 주문 및 신호 처리, 주문 수량 계산 등
- **database/**: DB 관리, 테이블 초기화
- **config/**: 설정 파일, 파라미터 관리
- **utils/**: 보조 함수, 지표, 로깅, 토큰 관리
- **monitor/**: 모니터링, Prometheus 연동
- **news_trading/**: 뉴스 기반 크롤러 및 전략(별도 실험/예제)
- **tests/**: 테스트 코드

## 3. 주요 전략/기법
- **단타(갭, 모멘텀, 돌파)**
- **스윙(정배열, 눌림목, 거래량, 분할매도, 트레일링스탑)**
- **리스크 관리(최대 투자금, 보유수량, 손절/익절, 슬리피지)**
- **분석/최적화(파라미터 자동완화, 워크포워드, 민감도 분석)**
- **실시간 데이터/주문 처리(WebSocket, REST, 비동기 처리)**

## 4. 데이터 흐름
- 실시간 데이터 수집 → 전략 신호 감지 → 주문 실행 → 결과 기록/분석 → 리포트/시각화

## 5. 사용 기술/기법
- Python, asyncio, pandas, numpy, matplotlib, seaborn
- WebSocket, REST API, Prometheus, Docker
- 이벤트 드리븐 아키텍처, 데이터 파이프라인, 전략 모듈화
- 백테스트 자동화, 실시간 모니터링, 로그/알림 시스템

## 6. 참고 문서
- docs/SWING_TRADING_STRATEGY.md, docs/SWING_CHECKLIST.md, README.md

---

이 문서는 StockManager의 전체적인 구조와 흐름, 그리고 실제로 적용된 전략/기법을 한눈에 파악할 수 있도록 정리한 요약본입니다. 