# StockManager - Python 기반 인트라데이 트레이딩 시스템

## 📋 개요

이 프로젝트는 한국 주식 시장을 대상으로 하는 단기 인트라데이(intraday) 트레이딩 전략의 성과를 검증하기 위해 설계된 이벤트 기반 백테스팅 프레임워크입니다.

## 🚀 주요 기능

### 1. 백테스팅 시스템
- **이벤트 기반 백테스팅**: 1분봉 데이터를 활용한 정밀한 시뮬레이션
- **다중 전략 지원**: Strategy1 (갭 앤 고), Strategy2 (추세 추종)
- **동적 리스크 관리**: 트레일링 스탑, 동적 포지션 사이징
- **시장 국면 필터**: KOSPI 지수 기반 조광기 방식 투자 비율 조절
- **거래 비용 모델링**: 실제 수수료, 세금, 슬리피지 반영

### 2. 고급 분석 기능
- **워크 포워드 최적화**: 과적합 방지를 위한 파라미터 최적화
- **파라미터 민감도 분석**: 핵심 파라미터 변화에 따른 성과 분석
- **다중 백테스트**: 랜덤 기간 반복 테스트로 안정성 검증
- **실시간 성능 모니터링**: 거래 중 실시간 성과 추적

### 3. 실시간 거래 시스템
- **WebSocket 기반 실시간 데이터**: 실시간 주식 데이터 수신
- **자동 주문 실행**: 전략 신호에 따른 자동 매매
- **리스크 관리**: 실시간 포지션 및 손실 관리
- **API 연동**: 한국투자증권 API 연동 지원

## 📁 프로젝트 구조

```
StockManager/
├── backtest.py              # 메인 백테스팅 엔진
├── real_time_trading.py     # 실시간 거래 시스템
├── api_client.py            # 증권사 API 클라이언트
├── minute_data/             # 1분봉 데이터 (CSV)
├── market_data/             # 시장 데이터 (KOSPI 등)
├── config/
│   └── settings.py          # 시스템 설정
├── analysis/                # 전략 분석 모듈
├── orders/                  # 주문 관리
├── utils/                   # 유틸리티 함수
└── tests/                   # 테스트 코드
```

## 🛠️ 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 데이터 준비

```bash
# 1분봉 데이터 수집 (예시)
python data_collector.py

# KOSPI 지수 데이터 수집
python market_data_collector.py
```

### 3. API 설정 (실시간 거래용)

```bash
# API 설정 파일 생성
python api_client.py
```

`api_config.json` 파일을 편집하여 실제 API 키를 입력하세요:

```json
{
  "api_key": "your_api_key_here",
  "secret_key": "your_secret_key_here",
  "account_number": "your_account_number_here",
  "base_url": "https://openapi.koreainvestment.com:9443",
  "simulation_mode": true
}
```

## 📊 사용법

### 1. 기본 백테스트 실행

```bash
python backtest.py
```

### 2. 다중 백테스트 실행

```bash
# 10회 랜덤 백테스트
python backtest.py --repeat 10
```

### 3. 워크 포워드 최적화

```bash
# 파라미터 최적화 실행
python backtest.py --optimize
```

### 4. 파라미터 민감도 분석

```bash
# 핵심 파라미터 민감도 분석
python backtest.py --sensitivity
```

### 5. 실시간 거래 시스템

```bash
# 실시간 거래 시스템 시작
python real_time_trading.py
```

## ⚙️ 설정 옵션

### 백테스트 설정 (`backtest.py`)

```python
CONFIG = {
    # 자본 및 거래 설정
    'initial_capital': 10000000,  # 1천만원 시작 자본
    'max_positions': 2,           # 최대 보유 종목 수
    'position_size': 1000000,     # 종목당 투자 금액
    
    # 매수 조건
    'scan_start_time': '09:00',   # 매수 스캔 시작 시간
    'scan_end_time': '11:00',     # 매수 스캔 종료 시간
    
    # 매도 조건
    'stop_loss': -2.0,            # 손절 비율
    'take_profit': 5.0,           # 익절 비율
    'trailing_stop': 3.0,         # 트레일링 스탑 비율
    'max_hold_hours': 2,          # 최대 보유 시간
    
    # 거래 비용 설정
    'commission_rate': 0.015,      # 증권사 수수료
    'tax_rate': 0.18,             # 증권거래세
    'slippage_rate': 0.05,        # 슬리피지
    
    # 성능 최적화
    'scan_interval_minutes': 5,    # 스캔 간격
    'enable_market_filter': True,  # 시장 국면 필터 사용
}
```

## 📈 전략 설명

### Strategy1: 갭 앤 고 (Gap and Go)
- **목적**: 시초가 갭과 거래량 급증을 활용한 단기 매매
- **조건**:
  - 시초가 갭 > 0.2%
  - 9시 거래량 > 30,000주
  - 20일 이동평균선 아래 시작
- **특징**: 역발상적 접근, 뉴스 기반 이벤트 트레이딩

### Strategy2: 추세 추종 (Trend Following)
- **목적**: 당일 추세가 확립된 후 진입
- **조건**:
  - 당일 시가 대비 1% 이상 상승
  - MA5 > MA20 (골든 크로스)
  - 거래량 비율 > 80%
- **특징**: 추세 추종, 모멘텀 기반

## 🔧 고급 기능

### 워크 포워드 최적화
과적합을 방지하기 위해 In-Sample 기간에서 파라미터를 최적화하고, Out-Sample 기간에서 검증하는 방식입니다.

```python
# 워크 포워드 최적화 실행
optimization_result = optimize_parameters_walk_forward(
    stock_data, 
    market_data,
    in_sample_months=6,    # 학습 기간
    out_sample_months=1,   # 검증 기간
    total_months=12        # 전체 기간
)
```

### 파라미터 민감도 분석
핵심 파라미터의 변화에 따른 성과 변화를 분석하여 안정적인 파라미터 범위를 찾습니다.

```python
# 민감도 분석 실행
analyze_parameter_sensitivity(stock_data, market_data)
```

### 실시간 성능 모니터링
거래 중 실시간으로 성과를 추적하고 분석합니다.

```python
monitor = PerformanceMonitor()
monitor.update_metrics(trade)
summary = monitor.get_summary()
```

## 📊 결과 분석

### 주요 성과 지표
- **총 수익률**: 전체 기간 수익률
- **승률**: 수익 거래 비율
- **최대 낙폭 (MDD)**: 최대 손실 폭
- **평균 수익/손실**: 거래당 평균 수익/손실
- **거래 비용**: 총 거래 비용 및 비용 비율

### 리스크 관리
- **포지션 한도**: 최대 보유 종목 수 제한
- **일일 손실 한도**: 일일 최대 손실 비율 제한
- **동적 포지션 사이징**: 전략 신뢰도에 따른 투자 금액 조절
- **시장 국면 필터**: 시장 상황에 따른 투자 비율 조절

## 🚨 주의사항

### 백테스팅 한계
1. **거래 비용**: 실제 거래에서는 수수료, 세금, 슬리피지가 발생
2. **유동성**: 대량 주문 시 시장 영향 고려 필요
3. **시장 미시구조**: 실제 호가창과 차이 존재
4. **과적합**: 과거 데이터에 최적화된 전략의 미래 성과 보장 불가

### 실시간 거래 주의사항
1. **API 제한**: 증권사 API 호출 제한 확인
2. **네트워크 지연**: 실시간 데이터 수신 지연 고려
3. **시스템 장애**: 자동 거래 시스템 장애 대비
4. **규정 준수**: 금융 규정 및 내부 규정 준수

## 🔄 업데이트 내역

### v2.0 (최신)
- ✅ 거래 비용 모델링 추가
- ✅ 워크 포워드 최적화 구현
- ✅ 파라미터 민감도 분석 추가
- ✅ 실시간 거래 시스템 구현
- ✅ API 클라이언트 모듈 추가
- ✅ 성능 최적화 및 메모리 효율성 개선
- ✅ 시장 국면 필터 로직 수정
- ✅ 5분 간격 스캔 로직 개선

### v1.0
- ✅ 기본 백테스팅 엔진
- ✅ 다중 전략 지원
- ✅ 리스크 관리 기능
- ✅ 결과 분석 모듈

## 📞 지원

문제가 발생하거나 개선 사항이 있으시면 이슈를 등록해 주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**⚠️ 투자 경고**: 이 시스템은 교육 및 연구 목적으로 제작되었습니다. 실제 투자에 사용하기 전에 충분한 검증과 테스트가 필요합니다. 투자는 본인의 판단과 책임 하에 진행하시기 바랍니다. 