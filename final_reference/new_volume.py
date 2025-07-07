import time
import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# 토큰 로드 함수
def load_token():
    json_path = os.path.join('data', 'real_keys.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            token = data.get('token')
            if token:
                return token
    txt_path = os.path.join('data', 'token.txt')
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            token = f.read().strip()
            if token:
                return token
    raise RuntimeError('토큰 파일을 찾을 수 없거나 토큰이 없습니다.')

# 실제 일봉 데이터 API 기반 2차 필터 점수 계산
def get_daily_chart_and_score(token, stock_code, realtime_price):
    host = 'https://api.kiwoom.com'
    endpoint = '/api/dostk/chart'  # 실제 제공 일봉 엔드포인트
    url = host + endpoint

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10081',  # 키움 예제 기준
    }

    data = {
        "stk_cd": stock_code,
        "base_dt": datetime.now().strftime("%Y%m%d"),  # 기준일자: 오늘
        "upd_stkpc_tp": "1",  # 수정주가 포함
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"[{stock_code}] 일봉 API 호출 실패: {response.status_code}")
        return 0

    daily_data = response.json().get('stk_dt_pole_chart_qry', [])
    if not daily_data or len(daily_data) < 60:
        print(f"[{stock_code}] 일봉 데이터 부족")
        return 0

    # 일봉 데이터 DataFrame 구성
    df = pd.DataFrame(daily_data)
    df['cur_prc'] = df['cur_prc'].astype(int).abs()
    df['MA5'] = df['cur_prc'].rolling(window=5).mean().abs()
    df['MA20'] = df['cur_prc'].rolling(window=20).mean().abs()
    df['MA60'] = df['cur_prc'].rolling(window=60).mean().abs()
    df = df.dropna()
    if df.empty:
        return 0

    latest = df.iloc[-1]
    score = 0
    if realtime_price > latest['MA5'] > latest['MA20'] > latest['MA60']:
        score += 3
    if latest['MA20'] > df.iloc[-5]['MA20']:
        score += 2
    if abs(latest['MA5'] / latest['MA20']) > abs(df.iloc[-2]['MA5'] / df.iloc[-2]['MA20']):
        score += 2

    return score


# 1차 + 2차 필터 통합 로직
def fn_ka10023(token, data, cont_yn='N', next_key=''):
    host = 'https://api.kiwoom.com'
    endpoint = '/api/dostk/rkinfo'
    url = host + endpoint

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': 'ka10023',
    }

    response = requests.post(url, headers=headers, json=data)
    print('Code:', response.status_code)
    resp_json = response.json()
    print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))

    if resp_json.get("return_code") != 0:
        print('API Error:', resp_json.get("return_msg", "Unknown error"))
        return

    print('Body:', json.dumps(resp_json, indent=4, ensure_ascii=False))

    trde_qty_sdnin = resp_json.get("trde_qty_sdnin", [])
    print("\n=== 거래량 급증 + 상승 + 거래대금 + 2차 필터 (>=5점) 만족 종목 ===")
    for item in trde_qty_sdnin:
        try:
            sdnin_rt = float(item["sdnin_rt"].replace("+", "").replace("%", ""))
            flu_rt = float(item["flu_rt"])
            prev_qty = int(item["prev_trde_qty"])
            now_qty = int(item["now_trde_qty"])
            cur_price = abs(int(item["cur_prc"]))
            one_min_qty = now_qty - prev_qty
            one_min_value = one_min_qty * cur_price

            if sdnin_rt >= 10.0 and flu_rt > 0 and one_min_value >= 50_000_000:
                print(f"\n[{item['stk_nm']} ({item['stk_cd']})] 1차 필터 통과! 2차 분석 중...")
                score = get_daily_chart_and_score(token, item['stk_cd'], cur_price)
                print(f" > 2차 점수: {score}점")
                if score >= 5:
                    print(f"  ★★ 최종 매수 후보 선정 ★★ "
                          f"현재가: {cur_price:,}원, 1분 거래대금: {one_min_value:,}원, 1분 거래량: {one_min_qty:,}주")
        except (KeyError, ValueError) as e:
            print(f"데이터 파싱 실패: {e}")



if __name__ == '__main__':
    MY_ACCESS_TOKEN = load_token()

    params = {
        'mrkt_tp': '000', 
        'sort_tp': '1',
        'tm_tp': '1', 
        'trde_qty_tp': '50',
        'tm': '',
        'stk_cnd': '20',
        'pric_tp': '0',
        'stex_tp': '3',
    }

    while True:
        fn_ka10023(token=MY_ACCESS_TOKEN, data=params)
        time.sleep(5)
