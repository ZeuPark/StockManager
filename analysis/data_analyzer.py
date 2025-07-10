import time
import requests
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime, timedelta
import json

def save_minute_chart_to_csv(response_json, filename, prev_day_close: Optional[int]=None, prev_day_volume: Optional[int]=None):
    """
    키움 1분봉 차트 API 응답(JSON)을 받아 백테스트용 CSV로 저장
    필수 컬럼: datetime, stock_code, open, high, low, close, volume, trade_value
    추가 컬럼: price_change, volume_ratio, ma5, ma20
    """
    stock_code = response_json.get('stk_cd', '')
    data = response_json.get('stk_min_pole_chart_qry', [])
    if not data:
        print('No data in response.')
        return
    df = pd.DataFrame(data)
    # 체결시간 파싱
    df['datetime'] = pd.to_datetime(df['cntr_tm'], format='%Y%m%d%H%M%S')
    df['stock_code'] = stock_code
    # 숫자형 변환 (음수 방지)
    for col in ['cur_prc', 'trde_qty', 'open_pric', 'high_pric', 'low_pric']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).abs().astype(int)
    # 컬럼명 통일
    df = df.rename(columns={
        'cur_prc': 'close',
        'open_pric': 'open',
        'high_pric': 'high',
        'low_pric': 'low',
        'trde_qty': 'volume'
    })
    # 거래대금
    df['trade_value'] = df['close'] * df['volume']
    # 등락률
    if prev_day_close:
        df['price_change'] = (df['close'] - prev_day_close) / prev_day_close * 100
    else:
        df['price_change'] = 0
    # 누적 거래량/거래량비율
    df['cum_volume'] = df['volume'].cumsum()
    if prev_day_volume:
        df['volume_ratio'] = df['cum_volume'] / prev_day_volume * 100
    else:
        df['volume_ratio'] = 0
    # 이동평균선
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    # 저장 직전 abs/fillna(0) 반복 적용
    for col in ['open', 'high', 'low', 'close', 'volume', 'trade_value', 'ma5', 'ma20']:
        if col in df.columns:
            df[col] = df[col].abs()
    df.fillna(0, inplace=True)
    # sanity check
    if (df[['open','high','low','close','trade_value']].lt(0).any().any()):
        print('⚠️ 음수 데이터가 남아 있습니다!')
    if df.isnull().any().any():
        print('⚠️ NaN 데이터가 남아 있습니다!')
    # 최종 컬럼 순서
    cols = ['datetime', 'stock_code', 'open', 'high', 'low', 'close', 'volume', 'trade_value',
            'price_change', 'cum_volume', 'volume_ratio', 'ma5', 'ma20']
    df = df[cols]
    print(f"Date range: {df['datetime'].min()} ~ {df['datetime'].max()}")
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} rows to {filename}")

def get_kiwoom_stock_list(token, market_type='0'):
    """키움 API로 코스피/코스닥 전체 종목 리스트 받아오기"""
    url = 'https://api.kiwoom.com/api/dostk/stkinfo'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10099',
    }
    data = {'mrkt_tp': market_type}
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    if result['return_code'] == 0:
        df = pd.DataFrame(result['list'])
        return df
    else:
        print(result['return_msg'])
        return None

# 1년치 1분봉 데이터 수집 개선: start_date/end_date 활용

def fetch_minute_chart(token, stock_code, sleep_sec=1, max_loops=100):
    """키움 1분봉 차트(ka10080) 연속조회로 최대한 과거까지 데이터 받아오기 (next-key 방식)"""
    url = 'https://api.kiwoom.com/api/dostk/chart'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10080',
    }
    all_data = []
    next_key = ''
    for i in range(max_loops):
        if next_key:
            headers['next-key'] = next_key
            headers['cont-yn'] = 'Y'
        else:
            headers['next-key'] = ''
            headers['cont-yn'] = 'N'
        params = {
            'stk_cd': stock_code,
            'tic_scope': '1',
            'upd_stkpc_tp': '1',
        }
        try:
            response = requests.post(url, headers=headers, json=params)
            result = response.json()
            if result.get('return_code') != 0:
                print(f"{stock_code} {i+1}회차: API 오류 {result.get('return_msg')}")
                break
            data = result.get('stk_min_pole_chart_qry', [])
            all_data.extend(data)
            print(f"{stock_code} {i+1}회차: {len(data)}건 수집 (누적 {len(all_data)})")
            next_key = response.headers.get('next-key', '')
            if not next_key or len(data) == 0:
                break
            time.sleep(sleep_sec)
        except Exception as e:
            print(f"{stock_code} {i+1}회차: 예외 발생 {e}")
            break
    return all_data

def load_token(env='production'):
    with open('config/keys.json', 'r', encoding='utf-8') as f:
        keys = json.load(f)
    return keys[env]['token']

def crawl_all_stocks_minute_data(token, sleep_sec=1, save_dir='.'):
    """
    전체 코스피/코스닥 종목에 대해 1분봉 데이터를 수집하여 개별 CSV로 저장
    """
    import os
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    # 1. 전체 종목 리스트 조회 (코스피+코스닥)
    stock_df = get_kiwoom_stock_list(token, market_type='0')  # 코스피
    stock_df_kosdaq = get_kiwoom_stock_list(token, market_type='1')  # 코스닥
    stock_df = pd.concat([stock_df, stock_df_kosdaq], ignore_index=True)

    # # 2. 필터링 (예시: 투자유의종목, 상장 1년 미만 등)
    # today = pd.Timestamp.today()
    # stock_df['list_date'] = pd.to_datetime(stock_df['list_date'], errors='coerce')
    # if 'warning_yn' in stock_df.columns:
    #     stock_df = stock_df[(stock_df['warning_yn'] == 'N')]
    # stock_df = stock_df[(stock_df['list_date'] < today - pd.Timedelta(days=365))]

    # 3. 종목별 1분봉 데이터 수집
    for idx, row in stock_df.iterrows():
        # Robustly extract stock code and name regardless of column naming
        code = None
        name = None
        # Try all possible column names for code
        for code_col in ['stock_code', '종목코드', 'code']:
            if code_col in row.index:
                code = row[code_col]
                break
        # Try all possible column names for name
        for name_col in ['stock_name', '종목명', 'name']:
            if name_col in row.index:
                name = row[name_col]
                break
        if code is None:
            raise KeyError(f"No stock code column found in row: available columns are {list(row.index)}")
        if name is None:
            name = ''
        print(f"{code}({name}) 1분봉 데이터 수집 시작...")
        try:
            minute_data = fetch_minute_chart(token, code, sleep_sec=sleep_sec)
            if minute_data:
                save_minute_chart_to_csv({'stk_cd': code, 'stk_min_pole_chart_qry': minute_data}, os.path.join(save_dir, f'{code}_1min.csv'))
            else:
                print(f"{code}: 데이터 없음")
        except Exception as e:
            print(f"{code}: 예외 발생 {e}")

# 테스트 예시
if __name__ == '__main__':
    # === 테스트: 한 종목(삼성전자)만 1년치 1분봉 데이터 수집 ===
    MY_ACCESS_TOKEN = load_token('production')  # 'simulation'도 가능
    TEST_STOCK_CODE = '005930'  # 삼성전자
    months = 12
    sleep_sec = 1
    print(f"{TEST_STOCK_CODE} 1년치 1분봉 데이터 수집 시작...")
    minute_data = fetch_minute_chart(MY_ACCESS_TOKEN, TEST_STOCK_CODE, sleep_sec=sleep_sec)
    if minute_data:
        save_minute_chart_to_csv({'stk_cd': TEST_STOCK_CODE, 'stk_min_pole_chart_qry': minute_data}, f'{TEST_STOCK_CODE}_1min_test.csv')
    else:
        print(f"{TEST_STOCK_CODE}: 데이터 없음")
    # === 이하 전체 자동화 코드는 주석 처리 ===
    # ... (전체 종목 자동화 루프는 주석 처리) ...
