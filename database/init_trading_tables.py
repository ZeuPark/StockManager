import sqlite3

def init_trading_tables():
    conn = sqlite3.connect('database/stock_manager.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT,
        stock_name TEXT,
        buy_price INTEGER,
        sell_price INTEGER,
        quantity INTEGER,
        buy_time DATETIME,
        sell_time DATETIME,
        profit_rate REAL,
        profit_amount INTEGER,
        result TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trade_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,
        volume_ratio REAL,
        trade_value INTEGER,
        execution_strength REAL,
        price_change REAL,
        market_cap INTEGER,
        FOREIGN KEY(trade_id) REFERENCES trades(id)
    );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_trading_tables()
    print("거래 분석용 테이블 생성 완료!") 