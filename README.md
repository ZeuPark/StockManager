# 📈 Stock Manager - 자동매매 시스템

> Python 기반의 자동화된 주식 거래 시스템

## 🚀 개요

Stock Manager는 Python으로 개발된 자동매매 시스템입니다. 실시간 시장 데이터 분석, 자동 주문 실행, 포트폴리오 모니터링 기능을 제공합니다.

## ✨ 주요 기능

- 📊 **실시간 시장 데이터 분석**
- 🤖 **자동 매매 신호 생성**
- 📈 **기술적 지표 분석** (RSI, MACD, 이동평균 등)
- 💰 **포트폴리오 관리**
- 📝 **거래 내역 추적**
- 📊 **성과 분석 및 리포팅**
- 🔍 **실시간 모니터링**
- 🛡️ **리스크 관리**

## 🏗️ 시스템 아키텍처

```
stock_manager/
├── main.py                   # 시스템 실행: 전체 컨트롤
├── config/
│   ├── secrets.json          # API Key/Secret/Token 보관
│   └── settings.py           # 전략 파라미터, 매매 임계값 등 설정
├── api/
│   └── api_caller.py         # APICaller 클래스 - 증권사 API 호출
├── analysis/
│   └── data_analyzer.py      # DataAnalyzer 클래스 - 조건/지표 분석
├── orders/
│   └── order_manager.py      # OrderManager 클래스 - 주문 생성/관리
├── database/
│   └── database_manager.py   # DatabaseManager 클래스 - 매매내역 저장/조회
├── account/
│   └── account_monitor.py    # AccountMonitor 클래스 - 계좌 모니터링
├── monitor/
│   └── monitoring.py         # Monitoring 클래스 - 시스템 상태 모니터링
├── utils/
│   └── logger.py             # 로깅 등 공통 유틸리티
└── tests/                    # 모듈별 유닛테스트
```

## 🛠️ 기술 스택

- **Backend**: Python 3.11
- **Database**: PostgreSQL
- **Cache**: Redis
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker & Docker Compose
- **Web Server**: Nginx
- **Data Analysis**: pandas, numpy, scikit-learn
- **Trading**: yfinance, ta-lib

## 🏆 시스템 설계 역량 / System Design Capabilities

### ✅ 1) 시스템 설계/아키텍처 / System Architecture Design
**English**: Object-oriented design (OOP) based architecture with separated responsibilities for maintainability. Modular architecture separated into configuration (config), sensitive information (secrets), and functional modules (api/analyzer/orders/monitoring, etc.). Demonstrates real-world system-level architectural design capabilities.

**한국어**: 객체지향 설계(OOP) 기반으로 각 책임을 분리하여 유지보수성을 확보한 구조 설계. 설정(config), 민감정보(secrets), 모듈(api/analyzer/orders/monitoring 등)로 분리된 아키텍처. 실전 시스템 수준의 구조 설계 능력을 보여줄 수 있음.

### ✅ 2) API 활용 능력 / API Integration Capabilities
**English**: Integration with securities OpenAPI (e.g., Kiwoom, eBEST). Understanding and implementation of complete API workflow including order placement, balance inquiry, execution inquiry, and real-time data reception.

**한국어**: 증권사 OpenAPI(예: 키움, 이베스트) 연동. 주문, 잔고조회, 체결조회, 실시간 데이터 수신 등 API 전체 흐름 이해 및 구현.

### ✅ 3) 실시간 데이터 처리 / Real-time Data Processing
**English**: 1-minute/tick-level market price/volume data collection. Event-driven trading signal generation based on volume spikes/execution strength. Real-time optimized logic design.

**한국어**: 1분/틱 단위 시세/거래량 데이터 수집. 이벤트 드리븐(거래량 급증/체결강도) 기반 매매 시그널 생성. 실시간성에 적합한 로직 설계.

### ✅ 4) 데이터베이스 관리 / Database Management
**English**: Database design and CRUD implementation for trading history, condition pass records, etc. Integration with relational databases like SQLite/MySQL.

**한국어**: 매매 내역, 조건 통과 기록 등 DB 설계 및 CRUD 구현. SQLite/MySQL 등 관계형 DB 연동.

### ✅ 5) 자동주문 로직 / Automated Order Logic
**English**: Order generation when trading conditions are met. Order status monitoring and error handling (slippage, execution failure, etc.). Safe operation design distinguishing between paper/real trading accounts.

**한국어**: 매매 조건 충족 시 주문 생성. 주문 상태 모니터링 및 에러 처리(슬리피지, 체결 실패 등). 모의/실계좌 구분하여 안전한 운영 설계.

### ✅ 6) 인프라/배포 환경 / Infrastructure/Deployment Environment
**English**: Containerized application execution environment using Dockerfile and docker-compose. GitHub version control and security management with gitignore. Development/operation environment consistency maintenance capabilities.

**한국어**: Dockerfile, docker-compose로 앱 실행 환경을 컨테이너화. GitHub 버전 관리 및 gitignore로 보안 관리. 개발/운영 환경 일관성 유지 역량.

### ✅ 7) 설정 관리/유연성 / Configuration Management/Flexibility
**English**: Strategy parameters separated from code and managed through config/settings.py. Immediate reflection of investment condition changes through configuration values without code modification.

**한국어**: 전략 파라미터를 코드와 분리해 config/settings.py로 관리. 투자 조건 변경 시 코드 수정 없이 설정값으로 즉시 반영 가능.

### ✅ 8) 로깅/모니터링 / Logging/Monitoring
**English**: System operation status and order/error logging. Capability to track failures/errors during operation.

**한국어**: 시스템 동작 상태와 주문/에러 기록. 운영 중 장애/오류 추적 가능.

## 📋 요구사항

- Python 3.11+
- Docker & Docker Compose
- 증권사 API 계정 (키움, 대신, 이베스트 등)

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/stock_manager.git
cd stock_manager
```

### 2. 환경 설정
```bash
# config/secrets.json 파일 생성 및 API 키 설정
cp config/secrets.json.example config/secrets.json
# secrets.json 파일에 실제 API 키 입력
```

### 3. Docker로 실행
```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f stock-manager

# 시스템 중지
docker-compose down
```

### 4. 로컬 개발 환경
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
export PYTHONPATH=$PWD

# 실행
python main.py
```

## ⚙️ 설정

### API 설정 (config/secrets.json)
```json
{
    "api_keys": {
        "broker_api_key": "YOUR_BROKER_API_KEY",
        "broker_secret_key": "YOUR_BROKER_SECRET_KEY",
        "broker_access_token": "YOUR_BROKER_ACCESS_TOKEN"
    }
}
```

### 시스템 설정 (config/settings.py)
```python
# 매매 전략 파라미터
TRADING_STRATEGY = {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "ma_short": 5,
    "ma_long": 20
}

# 리스크 관리
RISK_MANAGEMENT = {
    "max_position_size": 0.1,  # 전체 자산의 10%
    "stop_loss": 0.05,         # 5% 손절
    "take_profit": 0.15        # 15% 익절
}
```

## 📊 모니터링

### 웹 대시보드 접속
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Nginx**: http://localhost:80

### 주요 메트릭
- 거래 성과 (수익률, 승률)
- 시스템 상태 (API 연결, 데이터 수신)
- 포트폴리오 현황
- 실시간 알림

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest tests/

# 특정 모듈 테스트
pytest tests/test_api_caller.py

# 커버리지 포함 테스트
pytest --cov=. tests/
```

## 📝 로그

로그는 `logs/` 디렉토리에 저장됩니다:
- `trading.log`: 거래 관련 로그
- `system.log`: 시스템 로그
- `error.log`: 오류 로그

## 🔧 개발

### 코드 스타일
```bash
# 코드 포맷팅
black .

# 린팅
flake8 .

# 타입 체크
mypy .
```

### 새로운 기능 추가
1. 해당 모듈에 기능 구현
2. 테스트 코드 작성
3. 문서 업데이트
4. PR 생성

## 🚨 주의사항

⚠️ **중요**: 이 시스템은 교육 및 연구 목적으로 제작되었습니다.

- **실제 거래에 사용하기 전에 충분한 테스트가 필요합니다**
- **모의투자 환경에서 먼저 검증하세요**
- **투자 손실에 대한 책임은 사용자에게 있습니다**
- **API 키는 절대 공개하지 마세요**

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/yourusername/stock_manager/issues)
- **문서**: [Wiki](https://github.com/yourusername/stock_manager/wiki)
- **이메일**: support@stockmanager.com

## 🙏 감사의 말

- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance 데이터
- [ta-lib](https://github.com/mrjbq7/ta-lib) - 기술적 분석 라이브러리
- [pandas](https://pandas.pydata.org/) - 데이터 분석
- [Docker](https://www.docker.com/) - 컨테이너화

---

⭐ **이 프로젝트가 도움이 되었다면 스타를 눌러주세요!** 