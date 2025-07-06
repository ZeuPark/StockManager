# Stock Manager - Automated Trading System

## Overview
Stock Manager is a Python-based automated stock trading system. It provides real-time market data analysis, automated order execution, portfolio monitoring, and robust logging/monitoring for production use.

## Features
- Real-time market data collection and analysis
- Automated trading signal generation (event-driven, e.g., volume spikes)
- Order management and execution (with error handling)
- Portfolio and account monitoring
- Database integration for trade history and analytics
- Containerized deployment (Docker, Docker Compose)
- System logging and monitoring (Prometheus, Grafana)

## Architecture
```
stock_manager/
├── main.py                   # System entry point
├── config/
│   ├── secrets.json          # API keys/secrets (gitignored)
│   └── settings.py           # Strategy parameters, thresholds
├── api/
│   └── api_caller.py         # APICaller class - broker API integration
├── analysis/
│   └── data_analyzer.py      # DataAnalyzer class - indicators/logic
├── orders/
│   └── order_manager.py      # OrderManager class - order management
├── database/
│   └── database_manager.py   # DatabaseManager class - DB operations
├── account/
│   └── account_monitor.py    # AccountMonitor class - account/position
├── monitor/
│   └── monitoring.py         # Monitoring class - system/metrics
├── utils/
│   └── logger.py             # Logging utilities
└── tests/                    # Unit tests
```

## Tech Stack
- Python 3.11
- PostgreSQL, Redis
- Prometheus, Grafana
- Docker, Docker Compose
- Nginx (reverse proxy)
- pandas, numpy, scikit-learn, yfinance, ta-lib

## Requirements
- Python 3.11+
- Docker & Docker Compose
- Broker OpenAPI account (e.g., Kiwoom, eBEST)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/stock_manager.git
cd stock_manager
```

### 2. Configure secrets
```bash
cp config/secrets.json.example config/secrets.json
# Edit config/secrets.json with your API keys
```

### 3. Run with Docker
```bash
docker-compose up -d
```

### 4. Local development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Configuration

### API Keys (config/secrets.json)
```json
{
    "api_keys": {
        "broker_api_key": "YOUR_BROKER_API_KEY",
        "broker_secret_key": "YOUR_BROKER_SECRET_KEY",
        "broker_access_token": "YOUR_BROKER_ACCESS_TOKEN"
    }
}
```

### Strategy Settings (config/settings.py)
```python
TRADING_STRATEGY = {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "ma_short": 5,
    "ma_long": 20
}
RISK_MANAGEMENT = {
    "max_position_size": 0.1,
    "stop_loss": 0.05,
    "take_profit": 0.15
}
```

## Monitoring
- Grafana: http://localhost:3000 (default: admin/admin)
- Prometheus: http://localhost:9090
- Nginx: http://localhost:80

## Testing
```bash
pytest tests/
```

## License
MIT License. See [LICENSE](LICENSE) for details. 