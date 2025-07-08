import pandas as pd
import re

# CSV 파일 읽기
df = pd.read_csv('2025-07-08_당일매매손익표_utf8.csv', encoding='utf-8-sig')

# 종목코드에서 따옴표 제거
df['종목코드'] = df['종목코드'].astype(str).str.replace("'", "")

# 수익률에서 % 제거하고 숫자로 변환
df['수익률'] = df['수익률'].astype(str).str.replace('%', '').astype(float)

# 수익/손실 종목 분리
profit_stocks = df[df['수익률'] > 0]
loss_stocks = df[df['수익률'] < 0]

print("=== 수익 종목들 ===")
for _, row in profit_stocks.iterrows():
    code = row['종목코드'].strip()
    name = row['종목명'].strip()
    profit_rate = row['수익률']
    print(f"{code} {name}: {profit_rate:.2f}%")

print(f"\n=== 손실 종목들 ===")
for _, row in loss_stocks.iterrows():
    code = row['종목코드'].strip()
    name = row['종목명'].strip()
    profit_rate = row['수익률']
    print(f"{code} {name}: {profit_rate:.2f}%")

# 로그 파일에서 종목별 매수 조건 찾기
print(f"\n=== 로그에서 매수 조건 분석 ===")

def find_stock_in_logs(stock_code, stock_name):
    """로그에서 특정 종목의 매수 조건을 찾습니다."""
    with open('logs/stock_manager.log', 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # 종목코드나 종목명으로 검색
    patterns = [
        rf"{stock_code}.*필터 통과",
        rf"{stock_name}.*필터 통과",
        rf"{stock_code}.*매수",
        rf"{stock_name}.*매수",
        rf"{stock_code}.*체결",
        rf"{stock_name}.*체결",
        rf"{stock_code}.*익절",
        rf"{stock_name}.*익절",
        rf"{stock_code}.*손절",
        rf"{stock_name}.*손절"
    ]
    
    found_lines = []
    for pattern in patterns:
        matches = re.findall(pattern, log_content, re.MULTILINE)
        found_lines.extend(matches)
    
    return found_lines

# 수익 종목들의 로그 분석
print("\n=== 수익 종목들의 매수 조건 ===")
for _, row in profit_stocks.iterrows():
    code = row['종목코드'].strip()
    name = row['종목명'].strip()
    print(f"\n{code} {name}:")
    
    log_lines = find_stock_in_logs(code, name)
    if log_lines:
        for line in log_lines[:3]:  # 최대 3개까지만 출력
            print(f"  - {line}")
    else:
        print("  - 로그에서 해당 종목을 찾을 수 없습니다.")

# 손실 종목들의 로그 분석
print("\n=== 손실 종목들의 매수 조건 ===")
for _, row in loss_stocks.iterrows():
    code = row['종목코드'].strip()
    name = row['종목명'].strip()
    print(f"\n{code} {name}:")
    
    log_lines = find_stock_in_logs(code, name)
    if log_lines:
        for line in log_lines[:3]:  # 최대 3개까지만 출력
            print(f"  - {line}")
    else:
        print("  - 로그에서 해당 종목을 찾을 수 없습니다.")

# 통계 출력
print(f"\n=== 거래 통계 ===")
print(f"총 거래 종목 수: {len(df)}")
print(f"수익 종목 수: {len(profit_stocks)}")
print(f"손실 종목 수: {len(loss_stocks)}")
print(f"수익률: {len(profit_stocks)/len(df)*100:.1f}%")

if len(profit_stocks) > 0:
    avg_profit = profit_stocks['수익률'].mean()
    print(f"평균 수익률: {avg_profit:.2f}%")

if len(loss_stocks) > 0:
    avg_loss = loss_stocks['수익률'].mean()
    print(f"평균 손실률: {avg_loss:.2f}%") 