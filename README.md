# Stock Manager - Automated Trading System

## Overview
Stock Manager is a Python-based automated stock trading system that integrates with Kiwoom APIs. It provides real-time market data analysis, automated order execution, portfolio monitoring, and robust logging/monitoring for both simulation and production environments.

## Features
- **Real-time market data collection**: WebSocket-based real-time data processing with Kiwoom APIs
- **Momentum-based trading signals**: Volume spikes, execution strength, price breakout analysis
- **Multi-environment support**: Simulation and production modes with separate configurations
- **Object-oriented design**: Modular, extensible, and maintainable architecture
- **Configuration-driven conditions**: Easy adjustment of all trading conditions in settings.py
- **Automated trading signal generation**: Event-driven signal generation based on configured conditions
- **Order management and execution**: Comprehensive order handling with error management
- **Portfolio and account monitoring**: Real-time position and account tracking
- **Database integration**: Trade history and analytics storage with PostgreSQL
- **Containerized deployment**: Docker and Docker Compose support
- **System logging and monitoring**: Prometheus and Grafana integration
- **Token management**: Automatic token refresh and validation for API access

## Project Structure
```
stock_manager/
├── main.py                      # Main trading system entry point
├── config/
│   ├── secrets.json             # API keys/secrets (simulation & production)
│   └── settings.py              # Strategy parameters, momentum conditions
├── api/
│   ├── api_caller.py            # REST API client for Kiwoom APIs
│   └── websocket_client.py      # WebSocket client for real-time data
├── analysis/
│   ├── momentum_analyzer.py     # Momentum condition analyzer
│   └── data_analyzer.py         # Data analysis utilities
├── orders/
│   ├── order_manager.py         # Order execution and management
│   └── signal_processor.py      # Trading signal processor
├── account/
│   └── account_monitor.py       # Account/position monitoring
├── database/
│   ├── database_manager.py      # Database operations
│   └── init.sql                 # Database initialization script
├── utils/
│   ├── logger.py                # Logging utilities
│   ├── token_manager.py         # Token management utilities
│   └── __init__.py
├── monitoring/
│   ├── prometheus.yml           # Prometheus configuration
│   └── grafana/                 # Grafana dashboards and datasources
├── nginx/
│   └── nginx.conf               # Nginx reverse proxy configuration
├── monitor/
│   └── monitoring.py            # System monitoring utilities
├── tests/
│   ├── test_momentum_analyzer.py
│   ├── test_signal_processor.py
│   ├── test_trading_signals.py  # Integration tests and simulations
│   └── __init__.py
├── examples/
│   └── trading_example.py       # Usage examples
├── logs/                        # Log files directory
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Tech Stack
- **Python 3.11+**
- **Database**: PostgreSQL, Redis
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker, Docker Compose
- **Reverse Proxy**: Nginx
- **Data Analysis**: pandas, numpy, scikit-learn
- **API Integration**: Kiwoom REST API, WebSocket

## Requirements
- Python 3.11+
- Docker & Docker Compose
- Kiwoom API account (simulation/production)
- PostgreSQL database

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/stock_manager.git
cd stock_manager
```

### 2. Configure secrets
```bash
# Create secrets.json with your API keys
cp config/secrets.json.example config/secrets.json
# Edit config/secrets.json with your Kiwoom API credentials
```

### 3. Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the System

#### Simulation Mode (Recommended for testing)
```bash
# Set environment to simulation
export ENVIRONMENT=simulation

# Run main system
python main.py

# Run with specific stocks
python main.py --stocks 005930 000660 035420
```

#### Production Mode
```bash
# Set environment to production
export ENVIRONMENT=production

# Run main system
python main.py
```

#### Docker Deployment
```bash
# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_trading_signals.py

# Run integration test with momentum conditions
python tests/test_trading_signals.py
```

## Configuration

### API Configuration (config/secrets.json)
```json
{
    "simulation": {
        "appkey": "YOUR_SIMULATION_APPKEY",
        "secretkey": "YOUR_SIMULATION_SECRETKEY",
        "token": "YOUR_SIMULATION_TOKEN"
    },
    "production": {
        "appkey": "YOUR_PRODUCTION_APPKEY",
        "secretkey": "YOUR_PRODUCTION_SECRETKEY",
        "token": "YOUR_PRODUCTION_TOKEN"
    }
}
```

### Strategy Settings (config/settings.py)
```python
# Momentum conditions
MOMENTUM_CONDITIONS = {
    "volume_spike": {
        "enabled": True,
        "threshold": 1.2,  # Current volume ≥ 120% of previous
        "description": "거래량 급증 조건"
    },
    "execution_strength": {
        "enabled": True,
        "threshold": 1.5,  # Execution strength 150%
        "consecutive_ticks": 3,  # 3 consecutive ticks
        "description": "체결강도 조건"
    },
    "price_breakout": {
        "enabled": True,
        "breakout_ticks": 3,  # Break 3-tick high (test mode)
        "rise_threshold": 0.005,  # 0.5% rise after breakout
        "description": "가격 돌파 조건"
    }
}

# Risk management
RISK_MANAGEMENT = {
    "max_position_size": 0.1,  # 10% of total assets
    "position_size_ratio": 0.05,  # 5% of account balance
    "max_daily_loss": 0.05,  # 5% daily loss limit
    "stop_loss": 0.05,  # 5% stop loss
    "take_profit": 0.15,  # 15% take profit
    "max_positions": 5,  # Maximum 5 positions
    "min_trade_amount": 100000,  # Minimum 100,000 KRW
    "min_position_size": 1,  # Minimum 1 share
    "max_per_stock": 1000000  # Maximum 1M KRW per stock
}

# Target stocks
TARGET_STOCKS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
    "051910",  # LG화학
    "006400",  # 삼성SDI
    "035720",  # 카카오
    "207940",  # 삼성바이오로직스
    "068270",  # 셀트리온
    "323410",  # 카카오뱅크
    "373220"   # LG에너지솔루션
]
```

## Monitoring & Logging

### Web Interfaces
- **Grafana**: http://localhost:3000 (default: admin/admin)
- **Prometheus**: http://localhost:9090
- **Nginx**: http://localhost:80

### Log Files
- **Application logs**: `logs/stock_manager.log`
- **Trading logs**: `logs/trading.log`
- **Debug logs**: `logs/debug.log`
- **Error logs**: `logs/error.log`

### Log Levels
- **INFO**: General system information
- **DEBUG**: Detailed debugging information
- **ERROR**: Error messages and exceptions

## Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_momentum_analyzer.py

# Run integration test
python tests/test_trading_signals.py
```

### Code Structure
- **analysis/**: Market data analysis and condition evaluation
- **api/**: API client implementations for Kiwoom
- **orders/**: Order management and signal processing
- **account/**: Account and position monitoring
- **utils/**: Common utilities (logging, token management)
- **tests/**: Unit and integration tests
- **examples/**: Usage examples and demonstrations

### Adding New Features
1. Create new modules in appropriate directories
2. Add corresponding tests in `tests/`
3. Update configuration in `config/settings.py` if needed
4. Update documentation

## Troubleshooting

### Common Issues
1. **Token Expired**: Run token refresh utility
2. **API Connection Failed**: Check network and API credentials
3. **Database Connection Error**: Verify PostgreSQL is running
4. **Permission Denied**: Check file permissions for logs directory

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## License
MIT License. See [LICENSE](LICENSE) for details.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support
For issues and questions, please open an issue on GitHub or contact the development team.

---

# Stock Manager - 자동화된 주식 거래 시스템

## 개요
Stock Manager는 Kiwoom API와 연동되는 Python 기반 자동화 주식 거래 시스템입니다. 실시간 시장 데이터 분석, 자동 주문 실행, 포트폴리오 모니터링, 그리고 시뮬레이션 및 프로덕션 환경을 위한 견고한 로깅/모니터링을 제공합니다.

## 주요 기능
- **실시간 시장 데이터 수집**: Kiwoom API를 통한 WebSocket 기반 실시간 데이터 처리
- **모멘텀 기반 거래 신호**: 거래량 급증, 체결강도, 가격 돌파 분석
- **멀티 환경 지원**: 시뮬레이션과 프로덕션 모드를 위한 별도 설정
- **객체지향 설계**: 모듈화되고 확장 가능하며 유지보수가 용이한 아키텍처
- **설정 기반 조건**: settings.py에서 모든 거래 조건을 쉽게 조정
- **자동화된 거래 신호 생성**: 설정된 조건에 기반한 이벤트 기반 신호 생성
- **주문 관리 및 실행**: 오류 관리가 포함된 포괄적인 주문 처리
- **포트폴리오 및 계좌 모니터링**: 실시간 포지션 및 계좌 추적
- **데이터베이스 통합**: PostgreSQL을 통한 거래 이력 및 분석 저장
- **컨테이너화된 배포**: Docker 및 Docker Compose 지원
- **시스템 로깅 및 모니터링**: Prometheus 및 Grafana 통합
- **토큰 관리**: API 접근을 위한 자동 토큰 갱신 및 검증

## 프로젝트 구조
```
stock_manager/
├── main.py                      # 메인 거래 시스템 진입점
├── config/
│   ├── secrets.json             # API 키/시크릿 (시뮬레이션 & 프로덕션)
│   └── settings.py              # 전략 파라미터, 모멘텀 조건
├── api/
│   ├── api_caller.py            # Kiwoom API용 REST API 클라이언트
│   └── websocket_client.py      # 실시간 데이터용 WebSocket 클라이언트
├── analysis/
│   ├── momentum_analyzer.py     # 모멘텀 조건 분석기
│   └── data_analyzer.py         # 데이터 분석 유틸리티
├── orders/
│   ├── order_manager.py         # 주문 실행 및 관리
│   └── signal_processor.py      # 거래 신호 처리기
├── account/
│   └── account_monitor.py       # 계좌/포지션 모니터링
├── database/
│   ├── database_manager.py      # 데이터베이스 작업
│   └── init.sql                 # 데이터베이스 초기화 스크립트
├── utils/
│   ├── logger.py                # 로깅 유틸리티
│   ├── token_manager.py         # 토큰 관리 유틸리티
│   └── __init__.py
├── monitoring/
│   ├── prometheus.yml           # Prometheus 설정
│   └── grafana/                 # Grafana 대시보드 및 데이터소스
├── nginx/
│   └── nginx.conf               # Nginx 리버스 프록시 설정
├── monitor/
│   └── monitoring.py            # 시스템 모니터링 유틸리티
├── tests/
│   ├── test_momentum_analyzer.py
│   ├── test_signal_processor.py
│   ├── test_trading_signals.py  # 통합 테스트 및 시뮬레이션
│   └── __init__.py
├── examples/
│   └── trading_example.py       # 사용 예제
├── logs/                        # 로그 파일 디렉터리
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 기술 스택
- **Python 3.11+**
- **데이터베이스**: PostgreSQL, Redis
- **모니터링**: Prometheus, Grafana
- **컨테이너화**: Docker, Docker Compose
- **리버스 프록시**: Nginx
- **데이터 분석**: pandas, numpy, scikit-learn
- **API 통합**: Kiwoom REST API, WebSocket

## 요구사항
- Python 3.11+
- Docker & Docker Compose
- Kiwoom API 계정 (시뮬레이션/프로덕션)
- PostgreSQL 데이터베이스

## 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/stock_manager.git
cd stock_manager
```

### 2. 시크릿 설정
```bash
# API 키로 secrets.json 생성
cp config/secrets.json.example config/secrets.json
# config/secrets.json을 Kiwoom API 자격증명으로 편집
```

### 3. 환경 설정
```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 4. 시스템 실행

#### 시뮬레이션 모드 (테스트 권장)
```bash
# 환경을 시뮬레이션으로 설정
export ENVIRONMENT=simulation

# 메인 시스템 실행
python main.py

# 특정 종목으로 실행
python main.py --stocks 005930 000660 035420
```

#### 프로덕션 모드
```bash
# 환경을 프로덕션으로 설정
export ENVIRONMENT=production

# 메인 시스템 실행
python main.py
```

#### Docker 배포
```bash
# Docker Compose로 실행
docker-compose up -d

# 로그 보기
docker-compose logs -f
```

### 5. 테스트
```bash
# 모든 테스트 실행
python -m pytest tests/

# 특정 테스트 실행
python tests/test_trading_signals.py

# 모멘텀 조건으로 통합 테스트 실행
python tests/test_trading_signals.py
```

## 설정

### API 설정 (config/secrets.json)
```json
{
    "simulation": {
        "appkey": "YOUR_SIMULATION_APPKEY",
        "secretkey": "YOUR_SIMULATION_SECRETKEY",
        "token": "YOUR_SIMULATION_TOKEN"
    },
    "production": {
        "appkey": "YOUR_PRODUCTION_APPKEY",
        "secretkey": "YOUR_PRODUCTION_SECRETKEY",
        "token": "YOUR_PRODUCTION_TOKEN"
    }
}
```

### 전략 설정 (config/settings.py)
```python
# 모멘텀 조건
MOMENTUM_CONDITIONS = {
    "volume_spike": {
        "enabled": True,
        "threshold": 1.2,  # 현재 거래량 ≥ 이전 거래량의 120%
        "description": "거래량 급증 조건"
    },
    "execution_strength": {
        "enabled": True,
        "threshold": 1.5,  # 체결강도 150%
        "consecutive_ticks": 3,  # 3틱 연속
        "description": "체결강도 조건"
    },
    "price_breakout": {
        "enabled": True,
        "breakout_ticks": 3,  # 3틱 최고가 돌파 (테스트 모드)
        "rise_threshold": 0.005,  # 돌파 후 0.5% 상승
        "description": "가격 돌파 조건"
    }
}

# 리스크 관리
RISK_MANAGEMENT = {
    "max_position_size": 0.1,  # 전체 자산의 10%
    "position_size_ratio": 0.05,  # 계좌 잔고의 5%
    "max_daily_loss": 0.05,  # 일일 최대 손실 5%
    "stop_loss": 0.05,  # 손절 5%
    "take_profit": 0.15,  # 익절 15%
    "max_positions": 5,  # 최대 5개 포지션
    "min_trade_amount": 100000,  # 최소 10만원
    "min_position_size": 1,  # 최소 1주
    "max_per_stock": 1000000  # 종목당 최대 100만원
}

# 대상 종목
TARGET_STOCKS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
    "051910",  # LG화학
    "006400",  # 삼성SDI
    "035720",  # 카카오
    "207940",  # 삼성바이오로직스
    "068270",  # 셀트리온
    "323410",  # 카카오뱅크
    "373220"   # LG에너지솔루션
]
```

## 모니터링 및 로깅

### 웹 인터페이스
- **Grafana**: http://localhost:3000 (기본값: admin/admin)
- **Prometheus**: http://localhost:9090
- **Nginx**: http://localhost:80

### 로그 파일
- **애플리케이션 로그**: `logs/stock_manager.log`
- **거래 로그**: `logs/trading.log`
- **디버그 로그**: `logs/debug.log`
- **에러 로그**: `logs/error.log`

### 로그 레벨
- **INFO**: 일반 시스템 정보
- **DEBUG**: 상세 디버깅 정보
- **ERROR**: 에러 메시지 및 예외

## 개발

### 테스트 실행
```bash
# 모든 테스트 실행
python -m pytest tests/

# 특정 테스트 파일 실행
python tests/test_momentum_analyzer.py

# 통합 테스트 실행
python tests/test_trading_signals.py
```

### 코드 구조
- **analysis/**: 시장 데이터 분석 및 조건 평가
- **api/**: Kiwoom용 API 클라이언트 구현
- **orders/**: 주문 관리 및 신호 처리
- **account/**: 계좌 및 포지션 모니터링
- **utils/**: 공통 유틸리티 (로깅, 토큰 관리)
- **tests/**: 단위 및 통합 테스트
- **examples/**: 사용 예제 및 데모

### 새 기능 추가
1. 적절한 디렉터리에 새 모듈 생성
2. `tests/`에 해당 테스트 추가
3. 필요한 경우 `config/settings.py`에서 설정 업데이트
4. 문서 업데이트

## 문제 해결

### 일반적인 문제
1. **토큰 만료**: 토큰 갱신 유틸리티 실행
2. **API 연결 실패**: 네트워크 및 API 자격증명 확인
3. **데이터베이스 연결 오류**: PostgreSQL 실행 확인
4. **권한 거부**: logs 디렉터리의 파일 권한 확인

### 디버그 모드
```bash
# 디버그 로깅 활성화
export LOG_LEVEL=DEBUG
python main.py
```

## 라이선스
MIT 라이선스. 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

## 기여하기
1. 저장소를 포크
2. 기능 브랜치 생성
3. 변경사항 작성
4. 새 기능에 대한 테스트 추가
5. 풀 리퀘스트 제출

## 지원
문제 및 질문이 있으시면 GitHub에서 이슈를 열거나 개발팀에 문의하세요. 