-- Stock Manager Database Initialization (SQLite)
-- This file creates the initial database schema for SQLite

-- Create tables for stock trading system

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Stocks table
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    exchange VARCHAR(20),
    sector VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    stock_id INTEGER REFERENCES stocks(id),
    order_type VARCHAR(10) NOT NULL CHECK (order_type IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    filled_at DATETIME,
    order_id VARCHAR(50) UNIQUE
);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    stock_id INTEGER REFERENCES stocks(id),
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stock_id)
);

-- Market data table (실시간 거래 데이터)
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER REFERENCES stocks(id),
    timestamp DATETIME NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    trade_value BIGINT,  -- 거래대금
    price_change DECIMAL(5,2),  -- 등락률
    execution_strength DECIMAL(5,2),  -- 체결강도
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Volume breakout events (전일 거래량 돌파 이벤트)
CREATE TABLE IF NOT EXISTS volume_breakouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER REFERENCES stocks(id),
    breakout_time DATETIME NOT NULL,
    today_volume BIGINT NOT NULL,
    prev_day_volume BIGINT NOT NULL,
    volume_ratio DECIMAL(5,2),  -- 거래량 비율
    price_at_breakout DECIMAL(10,2),
    trade_value_at_breakout BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trading signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER REFERENCES stocks(id),
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    confidence DECIMAL(5,4),
    indicators TEXT,  -- JSON 문자열로 저장
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,4),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Auto trading candidates (자동매매 후보 종목)
CREATE TABLE IF NOT EXISTS auto_trading_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER REFERENCES stocks(id),
    candidate_time DATETIME NOT NULL,
    current_price DECIMAL(10,2),
    price_change DECIMAL(5,2),
    trade_value BIGINT,
    execution_strength DECIMAL(5,2),
    volume_ratio DECIMAL(5,2),
    ma_trend VARCHAR(20),  -- 이동평균 추세
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'EXECUTED', 'EXPIRED')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_stock_id ON orders(stock_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_market_data_stock_timestamp ON market_data(stock_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_volume_breakouts_stock_time ON volume_breakouts(stock_id, breakout_time);
CREATE INDEX IF NOT EXISTS idx_trading_signals_stock_id ON trading_signals(stock_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_auto_trading_candidates_status ON auto_trading_candidates(status);

-- Insert sample data
INSERT OR IGNORE INTO users (username, email) VALUES 
    ('admin', 'admin@stockmanager.com'),
    ('trader1', 'trader1@example.com');

INSERT OR IGNORE INTO stocks (symbol, name, exchange, sector) VALUES 
    ('005930', '삼성전자', 'KOSPI', 'Technology'),
    ('000660', 'SK하이닉스', 'KOSPI', 'Technology'),
    ('035420', 'NAVER', 'KOSPI', 'Technology'),
    ('051910', 'LG화학', 'KOSPI', 'Materials'),
    ('006400', '삼성SDI', 'KOSPI', 'Technology'),
    ('373220', 'LG에너지솔루션', 'KOSPI', 'Technology'),
    ('207940', '삼성바이오로직스', 'KOSPI', 'Healthcare'),
    ('068270', '셀트리온', 'KOSPI', 'Healthcare'),
    ('323410', '카카오뱅크', 'KOSPI', 'Financial'),
    ('035720', '카카오', 'KOSPI', 'Technology'); 