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