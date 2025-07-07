# Stock Manager - Automated Trading System

## Overview
Stock Manager is a Python-based automated stock trading system. It provides real-time data analysis, automated order execution, account/system monitoring, robust logging, and database integration.

## Key Features
- **Real-time volume/momentum analysis and automated trading**
- **Real-time account/portfolio/risk monitoring**
- **System resource monitoring (CPU/Memory/Disk)**
- **SQLite-based data storage/analysis/backup**
- **Environment-specific configuration and token management**
- **Test/production code separation with Docker support**

## Project Structure
```
StockManager/
├── main.py                  # Main execution/integration entry point
├── volumetrading/
│   ├── app.py              # Volume-based automated trading execution file
│   └── __init__.py
├── account/                # Account monitoring
│   └── account_monitor.py
├── analysis/               # Data/strategy analysis
│   ├── volume_scanner.py
│   ├── momentum_analyzer.py
│   └── data_analyzer.py
├── api/                    # API/WS integration
│   ├── api_caller.py
│   ├── kiwoom_client.py
│   └── websocket_client.py
├── orders/                 # Order/signal processing
│   ├── order_manager.py
│   └── signal_processor.py
├── database/               # Database management
│   ├── database_manager.py
│   └── init.sql
├── monitor/                # System monitoring
│   └── monitoring.py
├── config/                 # Configuration
│   └── settings.py
├── utils/                  # Common utilities
│   ├── logger.py
│   ├── token_manager.py
│   └── __init__.py
├── tests/                  # Test code
│   ├── test_account_monitor.py
│   ├── test_momentum_analyzer.py
│   ├── test_volume_scanner.py
│   ├── test_signal_processor.py
│   ├── test_trading_signals.py
│   ├── test_websocket.py
│   └── __init__.py
├── logs/                   # Log files
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
```
> **Note:** `examples/`, `final_reference/`, `temp_test_files/` and other example/temporary folders have been cleaned up and no longer exist.

## How to Run

### 1. Environment Setup
```bash
# Create virtual environment and install packages
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables (e.g., simulation)
export ENVIRONMENT=simulation
```

### 2. Run Main System
```bash
python main.py
```

### 3. Run Volume-based Automated Trading
```bash
python volumetrading/app.py
```

### 4. Run Tests
```bash
# Run all tests
python -m pytest tests/

# Run individual tests
python tests/test_account_monitor.py
python tests/test_volume_scanner.py
```

## Key Folders/Files Description
- **main.py**: Main system integration execution entry point
- **volumetrading/app.py**: Volume breakout/automated trading execution
- **account/account_monitor.py**: Account/portfolio/risk monitoring
- **monitor/monitoring.py**: System (CPU/Memory/Disk) monitoring
- **database/database_manager.py**: SQLite-based data storage/query/analysis
- **analysis/**: Volume/momentum/data analysis strategies
- **api/**: REST/WebSocket API integration
- **orders/**: Order/signal processing
- **config/settings.py**: Environment-specific configuration and strategy parameters
- **utils/**: Logging, token, and other common utilities
- **tests/**: Test code for all major features

## Additional Information
- **Docker Support**: Run all services with `docker-compose up -d`
- **Logging/DB/Monitoring**: All major events/states are recorded in DB and logs
- **Extension/Operation/Analysis**: Modularized by folders for easy maintenance and extension

---

# Stock Manager - 자동화된 주식 거래 시스템

## 개요
Stock Manager는 Python 기반의 자동 주식 트레이딩 시스템입니다. 실시간 데이터 분석, 자동 주문, 계좌/시스템 모니터링, 강력한 로깅 및 DB 연동을 제공합니다.

## 주요 기능
- **실시간 거래량/모멘텀 분석 및 자동매매**
- **계좌/포트폴리오/리스크 실시간 모니터링**
- **시스템 리소스(CPU/메모리/디스크) 모니터링**
- **SQLite 기반 데이터 저장/분석/백업**
- **환경별 설정 및 토큰 관리**
- **테스트/운영 코드 분리, Docker 지원**

## 폴더 구조
```
StockManager/
├── main.py                  # 메인 실행/통합 진입점
├── volumetrading/
│   ├── app.py              # 거래량 기반 자동매매 실행 파일
│   └── __init__.py
├── account/                # 계좌 모니터링
│   └── account_monitor.py
├── analysis/               # 데이터/전략 분석
│   ├── volume_scanner.py
│   ├── momentum_analyzer.py
│   └── data_analyzer.py
├── api/                    # API/WS 연동
│   ├── api_caller.py
│   ├── kiwoom_client.py
│   └── websocket_client.py
├── orders/                 # 주문/신호 처리
│   ├── order_manager.py
│   └── signal_processor.py
├── database/               # DB 관리
│   ├── database_manager.py
│   └── init.sql
├── monitor/                # 시스템 모니터링
│   └── monitoring.py
├── config/                 # 환경설정
│   └── settings.py
├── utils/                  # 공통 유틸
│   ├── logger.py
│   ├── token_manager.py
│   └── __init__.py
├── tests/                  # 테스트 코드
│   ├── test_account_monitor.py
│   ├── test_momentum_analyzer.py
│   ├── test_volume_scanner.py
│   ├── test_signal_processor.py
│   ├── test_trading_signals.py
│   ├── test_websocket.py
│   └── __init__.py
├── logs/                   # 로그 파일
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
```
> **참고:** `examples/`, `final_reference/`, `temp_test_files/` 등 예제/임시 폴더는 정리되어 더 이상 존재하지 않습니다.

## 실행 방법

### 1. 환경설정
```bash
# 가상환경 생성 및 패키지 설치
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 환경 변수 설정 (예: 시뮬레이션)
export ENVIRONMENT=simulation
```

### 2. 메인 시스템 실행
```bash
python main.py
```

### 3. 거래량 기반 자동매매 실행
```bash
python volumetrading/app.py
```

### 4. 테스트 실행
```bash
# 전체 테스트
python -m pytest tests/

# 개별 테스트
python tests/test_account_monitor.py
python tests/test_volume_scanner.py
```

## 주요 폴더/파일 설명
- **main.py**: 전체 시스템 통합 실행 진입점
- **volumetrading/app.py**: 거래량 돌파/자동매매 실행
- **account/account_monitor.py**: 계좌/포트폴리오/리스크 모니터링
- **monitor/monitoring.py**: 시스템(CPU/메모리/디스크) 모니터링
- **database/database_manager.py**: SQLite 기반 데이터 저장/조회/분석
- **analysis/**: 거래량/모멘텀/데이터 분석 전략
- **api/**: REST/WebSocket API 연동
- **orders/**: 주문/신호 처리
- **config/settings.py**: 환경별 설정 및 전략 파라미터
- **utils/**: 로깅, 토큰 등 공통 유틸
- **tests/**: 모든 주요 기능별 테스트 코드

## 기타
- **Docker 지원**: `docker-compose up -d`로 전체 서비스 실행 가능
- **로그/DB/모니터링**: 모든 주요 이벤트/상태가 DB 및 로그로 기록됨
- **확장/운영/분석**: 폴더별로 모듈화되어 유지보수 및 확장 용이

---

추가적인 실행법, 배포, 운영 자동화, 문서화가 필요하면 언제든 요청해 주세요! 
이걸 깃헙에다 올린 이유는 당연히 이렇게 해도 돈이 안벌려서 그런거고, 저처럼 주식으로 돈을 벌 수 있을거라는 허망된 꿈을 가지고 있는 새로운 개발자에게 조금이나마 도움이 될 수 있도록 여기에 올립니다. 
만약 조금의 수익을 얻은 사람이 있다면 저에게 커피 한잔만 사주십쇼. 