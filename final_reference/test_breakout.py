import time
import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import threading
import random
import collections

# === 슬리피지, 수수료, 제세금 상수 및 계산 함수 추가 ===
SLIPPAGE_RATE = 0.002  # 0.2% 슬리피지
FEE_RATE = 0.00015     # 0.015% 매체수수료
TAX_RATE = 0.0015      # 0.15% 제세금 (매도시만)
QTY = 1                # 기본 주문수량

def calc_fee(amount):
    """매체수수료 계산 (10원 미만 절사)"""
    fee = int(amount * FEE_RATE)
    return (fee // 10) * 10  # 10원 미만 절사

def calc_tax(amount):
    """제세금 계산 (원 미만 절사)"""
    return int(amount * TAX_RATE)

def calc_kiwoom_profit_rate(buy_price, cur_price, qty):
    """키움 공식에 따른 수익률 계산"""
    # 매입금액
    buy_amount = buy_price * qty
    buy_fee = calc_fee(buy_amount)
    total_buy = buy_amount + buy_fee
    # 평가금액 (현재가 기준)
    cur_amount = cur_price * qty
    sell_fee = calc_fee(cur_amount)
    tax = calc_tax(cur_amount)
    total_eval = cur_amount - sell_fee - tax
    # 평가손익, 수익률
    profit = total_eval - total_buy
    profit_rate = profit / total_buy * 100
    return profit_rate, profit, total_eval, total_buy

# 토큰 로드 함수 (실전/모의투자 모드 지원)
def load_token(mode='real'):
    if mode == 'mock':
        json_path = os.path.join('fake', 'fake_keys.json')
    else:
        json_path = os.path.join('data', 'real_keys.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            token = data.get('token')
            if token:
                return token
    # txt fallback (실전만)
    if mode == 'real':
        txt_path = os.path.join('data', 'token.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                token = f.read().strip()
                if token:
                    return token
    raise RuntimeError(f"토큰 파일을 찾을 수 없거나 토큰이 없습니다. (mode={mode})")

# 실제 일봉 데이터 API 기반 2차 필터 점수 계산
# mode 인자 추가

# === 글로벌 일봉 API 호출 rate limiter 선언 ===
API_RATE_LIMIT = 5  # 초당 5건
API_WINDOW = 1.0    # 1초
api_call_timestamps = collections.deque(maxlen=API_RATE_LIMIT)
api_rate_lock = threading.Lock()

def acquire_api_rate_limit():
    while True:
        with api_rate_lock:
            now = time.monotonic()
            # 큐가 가득 차 있으면, 가장 오래된 호출과 현재 시간 차이 확인
            if len(api_call_timestamps) >= API_RATE_LIMIT:
                oldest = api_call_timestamps[0]
                elapsed = now - oldest
                if elapsed < API_WINDOW:
                    wait_time = API_WINDOW - elapsed
                else:
                    wait_time = 0
            else:
                wait_time = 0
            if wait_time == 0:
                api_call_timestamps.append(now)
                return
        if wait_time > 0:
            time.sleep(wait_time)

def get_daily_chart_and_score(token, stock_code, realtime_price, mode='real'):
    acquire_api_rate_limit()  # 글로벌 rate limiter 적용
    base_code = stock_code.split('_')[0]
    if mode == 'mock':
        host = 'https://mockapi.kiwoom.com'
    else:
        host = 'https://api.kiwoom.com'
    endpoint = '/api/dostk/chart'
    url = host + endpoint
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10081',
    }
    data = {
        "stk_cd": base_code,
        "base_dt": datetime.now().strftime("%Y%m%d"),
        "upd_stkpc_tp": "1",
        "req_cnt": 80,  # 80개만 요청
    }
    max_retries = 4
    backoff = 0.5
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 429:
            if attempt < max_retries - 1:
                print(f"[경고] {stock_code} 일봉 API 429(Too Many Requests) - {backoff:.1f}s 후 재시도 ({attempt+1}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2
                acquire_api_rate_limit()  # 재시도 전에도 rate limiter 적용
                continue
            else:
                return 'RATE_LIMIT'
        if response.status_code != 200:
            return 0
        daily_data = response.json().get('stk_dt_pole_chart_qry', [])
        if not daily_data or len(daily_data) < 60:
            return 0
        df = pd.DataFrame(daily_data)
        if 'dt' in df.columns:
            df = df.sort_values('dt').reset_index(drop=True)
        if len(df) > 80:
            df = df.iloc[-80:].reset_index(drop=True)
        df['cur_prc'] = df['cur_prc'].astype(int).abs()
        df['MA10'] = df['cur_prc'].rolling(window=10).mean()
        df['MA20'] = df['cur_prc'].rolling(window=20).mean()
        df['MA60'] = df['cur_prc'].rolling(window=60).mean()
        df = df.dropna()
        if df.empty:
            return 0
        latest = df.iloc[-1]
        score = 0
        # MA10 > MA20 +2점
        if latest['MA10'] > latest['MA20']:
            score += 2
        # MA20 > MA60 +1점
        if latest['MA20'] > latest['MA60']:
            score += 1
        # 현재가 > MA10 +1점
        if realtime_price > latest['MA10']:
            score += 1
        # MA20 상승(3일 전 대비) +1점
        if latest['MA20'] > df.iloc[-3]['MA20']:
            score += 1
        # MA60 상승(3일 전 대비) +1점
        if latest['MA60'] > df.iloc[-3]['MA60']:
            score += 1
        return score
    return 'RATE_LIMIT'


# 1차 + 2차 필터 통합 로직
def fn_ka10023(token, data, cont_yn='N', next_key='', mode='real'):
    if mode == 'mock':
        host = 'https://mockapi.kiwoom.com'
    else:
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
    data = data.copy()
    response = requests.post(url, headers=headers, json=data)
    resp_json = response.json()
    if resp_json.get("return_code") != 0:
        print('API Error:', resp_json.get("return_msg", "Unknown error"))
        return
    trde_qty_sdnin = resp_json.get("trde_qty_sdnin", [])
    print("\n=== 거래량 급증 + 고점돌파 + 누적거래대금 + 2차 필터 (>=3점) 만족 종목 ===")
    for item in trde_qty_sdnin:
        try:
            # 누적 거래량/거래대금, 전일 거래량, 10일 고점 계산
            cur_price = abs(int(item["cur_prc"]))
            today_qty = int(item["now_trde_qty"])
            prev_day_qty = int(item.get("prev_day_qty", 0))  # API에 따라 값이 없으면 0
            today_value = int(item.get("acc_trde_value", 0))  # 누적 거래대금
            # 10일 고점 돌파 여부 (일봉 데이터 필요)
            score_token = load_token(mode)
            daily_data = get_daily_chart_and_score(score_token, item['stk_cd'], cur_price, mode=mode)
            if daily_data == 'RATE_LIMIT' or daily_data == 0:
                continue
            # 10일 고점 돌파 체크
            daily_df = pd.DataFrame(requests.post(url, headers=headers, json={"stk_cd": item['stk_cd'], "base_dt": datetime.now().strftime("%Y%m%d"), "upd_stkpc_tp": "1", "req_cnt": 11}).json().get('stk_dt_pole_chart_qry', []))
            if not daily_df.empty:
                daily_df['cur_prc'] = daily_df['cur_prc'].astype(int).abs()
                high_10 = daily_df['cur_prc'][:-1].max()  # 오늘 제외 10일 고점
                if cur_price <= high_10:
                    continue  # 10일 고점 돌파 아니면 패스
            # 누적 거래량/거래대금 조건
            if prev_day_qty > 0 and today_qty < prev_day_qty * 1.2:
                continue
            if today_value < 500_000_000:  # 5억 미만이면 패스
                continue
            score = get_daily_chart_and_score(score_token, item['stk_cd'], cur_price, mode=mode)
            if score == 'RATE_LIMIT':
                print(f"[경고] {item['stk_cd']} 일봉 API 429(Too Many Requests) - 건너뜀")
                continue
            print(f" > 2차 점수: {score}점")
            if score >= 3:
                print(f"  ★★ 최종 매수 후보 선정 ★★ 현재가: {cur_price:,}원, 누적 거래대금: {today_value:,}원, 누적 거래량: {today_qty:,}주")
                save_candidate(item['stk_cd'], cur_price, mode=mode, stock_name=item['stk_nm'])
        except (KeyError, ValueError) as e:
            print(f"데이터 파싱 실패: {e}")



# 상태 파일 및 락 선언
AUTO_TRADE_FILE = "auto_trade.json"
auto_trade_lock = threading.Lock()
global_candidate_lock = threading.Lock()  # 글로벌 후보 등록 락

def load_json_file(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DEBUG][load_json_file] {filename} 읽기 예외: {e}")
            return default
    return default

def save_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def is_already_bought(stk_cd):
    with auto_trade_lock:
        auto_trades = load_json_file(AUTO_TRADE_FILE, {})
        return stk_cd in auto_trades

def add_auto_trade(stk_cd, buy_price, mode='real', stock_name=None):
    with auto_trade_lock:
        auto_trades = load_json_file(AUTO_TRADE_FILE, {})
        
        # 중복 체크 (이미 등록된 종목인지 확인)
        if stk_cd in auto_trades:
            print(f"[DEBUG][add_auto_trade] 이미 등록된 종목으로 등록 실패: {stock_name or stk_cd}({stk_cd})")
            return False
        
        auto_trades[stk_cd] = {
            "buy_price": buy_price,
            "buy_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "status": "holding",
            "stock_name": stock_name or stk_cd
        }
        save_json_file(AUTO_TRADE_FILE, auto_trades)
        print(f"[DEBUG][add_auto_trade] 자동매매 등록: {stock_name or stk_cd}({stk_cd}), 매수가: {buy_price}")
        return True

def remove_auto_trade(stk_cd, sell_price, reason):
    with auto_trade_lock:
        auto_trades = load_json_file(AUTO_TRADE_FILE, {})
        if stk_cd in auto_trades:
            trade_info = auto_trades[stk_cd]
            trade_info.update({
                "sell_price": sell_price,
                "sell_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reason": reason,
                "status": "completed"
            })
            # 완료된 거래는 별도 로그에 저장하고 현재 거래에서 제거
            completed_trades = load_json_file("completed_trades.json", [])
            completed_trades.append(trade_info)
            save_json_file("completed_trades.json", completed_trades)
            
            del auto_trades[stk_cd]
            save_json_file(AUTO_TRADE_FILE, auto_trades)
            
            # 종목명 가져오기 (fn_ka10023에서 받은 정보 활용)
            stock_name = trade_info.get("stock_name", stk_cd)
            print(f"[DEBUG][remove_auto_trade] 자동매매 완료: {stock_name}({stk_cd}), 매도가: {sell_price}, 사유: {reason}")

def get_auto_trade_info(stk_cd):
    with auto_trade_lock:
        auto_trades = load_json_file(AUTO_TRADE_FILE, {})
        return auto_trades.get(stk_cd)

def get_all_auto_trades():
    with auto_trade_lock:
        return load_json_file(AUTO_TRADE_FILE, {})

def add_processed_stock(stk_cd):
    """처리된 종목 목록에 추가 (같은 종목 중복 매수 방지)"""
    processed_stocks = load_json_file("processed_stocks.json", [])
    if stk_cd not in processed_stocks:
        processed_stocks.append(stk_cd)
        save_json_file("processed_stocks.json", processed_stocks)
        print(f"[DEBUG][add_processed_stock] 처리된 종목 추가: {stk_cd}")

def get_realtime_price_kiwoom(token, stk_cd, mode='real', buy_price=None):
    # 모의투자와 실전 모두 동일한 API 사용
    host = 'https://mockapi.kiwoom.com' if mode == 'mock' else 'https://api.kiwoom.com'
    endpoint = '/api/dostk/mrkcond'  # 호가 조회 API
    url = host + endpoint
    
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10004',  # 호가 조회 API ID
    }
    data = {
        "stk_cd": stk_cd.split('_')[0]  # 6자리 코드만 사용
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=3)
        print(f"[DEBUG][get_realtime_price_kiwoom] {stk_cd} 응답코드: {response.status_code}, 응답: {response.text}")
        if response.status_code == 200:
            resp_json = response.json()
            # 응답이 리스트인지 딕셔너리인지 확인
            if isinstance(resp_json, dict):
                # 매수 최우선 호가를 실시간 가격으로 사용
                price = resp_json.get('buy_fpr_bid')
                if price is not None and price != '0':
                    print(f"[DEBUG][get_realtime_price_kiwoom] {stk_cd} 매수 최우선 호가: {price}")
                    return int(price)
            elif isinstance(resp_json, list) and len(resp_json) > 0:
                # 리스트인 경우 첫 번째 항목에서 가격 추출 시도
                first_item = resp_json[0]
                if isinstance(first_item, dict):
                    price = first_item.get('buy_fpr_bid')
                    if price is not None and price != '0':
                        print(f"[DEBUG][get_realtime_price_kiwoom] {stk_cd} 매수 최우선 호가: {price}")
                        return int(price)
        print(f"[실시간 가격 API 실패] {stk_cd}: {response.status_code}")
    except Exception as e:
        print(f"[실시간 가격 API 예외] {stk_cd}: {e}")
    
    # API 실패 시 fallback (매수 가격 기준으로 작은 변동)
    if buy_price is not None:
        fluct = random.uniform(-0.01, 0.01)  # -1% ~ +1% 변동 (더 작게)
        fallback_price = int(int(buy_price) * (1 + fluct))
        print(f"[DEBUG][get_realtime_price_kiwoom] API 실패로 fallback 가격 사용: {fallback_price} (base={buy_price}, fluct={fluct:.3f})")
        return fallback_price
    else:
        print(f"[DEBUG][get_realtime_price_kiwoom] API 실패 및 buy_price 없음으로 10000 반환")
        return 10000

# 모의투자 주문 API 호출 함수
MOCK_ACCOUNT = '81049018'

def place_order_mock(token, stk_cd, qty, side, price=None):
    # 종목코드에서 _AL 등 접미사 제거 (6자리 숫자만 사용)
    base_code = stk_cd.split('_')[0]
    host = 'https://mockapi.kiwoom.com'
    endpoint = '/api/dostk/ordr'
    url = host + endpoint  # 반드시 정의
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'kt10001' if side == 'sell' else 'kt10000',
    }
    data = {
        'acno': MOCK_ACCOUNT,           # 계좌번호
        'dmst_stex_tp': 'KRX',          # 국내거래소구분
        'stk_cd': base_code,            # 종목코드(6자리)
        'ord_qty': str(qty),            # 주문수량
        'ord_uv': str(price) if price else '',  # 주문단가(시장가면 빈 문자열)
        'trde_tp': '3',                 # 매매구분 (시장가)
        'ord_dvsn': '1' if side == 'buy' else '2',  # 1: 매수, 2: 매도
    }
    # Rate Limit 재시도 로직
    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=5)
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    return None
            return response.json()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            return None
    return None

# 실전/모의투자 주문 API 호출 함수
def place_order_real(token, stk_cd, qty, side, price=None):
    host = 'https://mockapi.kiwoom.com'  # 실전이면 실전 주소로 변경
    endpoint = '/api/dostk/ordr'
    url = host + endpoint
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'kt10001' if side == 'sell' else 'kt10000',
    }
    data = {
        'dmst_stex_tp': 'KRX',
        'stk_cd': stk_cd.split('_')[0],  # 6자리 코드만
        'ord_qty': str(qty),
        'ord_uv': str(price) if price else '',
        'trde_tp': '3',  # 시장가
        'cond_uv': '',
    }
    
    # Rate Limit 재시도 로직
    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=5)
            print(f"[DEBUG][place_order_real] 응답: {response.status_code}, {response.text}")
            
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"[DEBUG][place_order_real] Rate Limit 초과, {backoff:.1f}초 후 재시도 ({attempt+1}/{max_retries})")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    print(f"[DEBUG][place_order_real] Rate Limit 재시도 실패")
                    return None
            
            return response.json()
        except Exception as e:
            print(f"[DEBUG][place_order_real] 예외: {e}")
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            return None
    
    return None

# 단순화된 모니터링 함수
def monitor_stock(stk_cd, buy_price, mode='real', stock_name=None):
    try:
        # 현재 매수 중인 종목이 있는지 확인 (한 번에 하나만 매수)
        auto_trades = get_all_auto_trades()
        if auto_trades:
            return
        
        # 모니터링 시작 전 중복 체크 (Race Condition 방지)
        if is_already_bought(stk_cd):
            print(f"[DEBUG][monitor_stock] 이미 매수된 종목으로 모니터링 중단: {stock_name or stk_cd}({stk_cd})")
            return
        
        # 완료된 거래에서도 중복 체크
        completed_trades = load_json_file("completed_trades.json", [])
        for trade in completed_trades:
            if trade.get('stk_cd') == stk_cd:
                print(f"[DEBUG][monitor_stock] 이미 거래 완료된 종목으로 모니터링 중단: {stock_name or stk_cd}({stk_cd})")
                return
        
        # save_candidate에서 이미 처리된 종목 체크를 했으므로 여기서는 제거
        # (Race Condition 방지를 위해 save_candidate에서 즉시 처리됨)
        
        buy_price = int(buy_price)
        token = load_token(mode)
        
        # 슬리피지 적용 매수가
        buy_price_slip = int(buy_price * (1 + SLIPPAGE_RATE))
        buy_fee = calc_fee(buy_price_slip * QTY)
        buy_total = buy_price_slip * QTY + buy_fee
        print(f"[DEBUG][monitor_stock] 원가: {buy_price}, 슬리피지 적용 매수가: {buy_price_slip}, 매수수수료: {buy_fee}, 총매입: {buy_total}")

        # 매수 주문 실행
        order_success = False  # 기본값을 False로 변경
        if mode == 'mock':
            order_resp = place_order_mock(token, stk_cd, qty=QTY, side='buy')
            print(f"[DEBUG][monitor_stock] 매수 주문 응답: {order_resp}")
            # 더 엄격한 성공 조건 체크
            if (order_resp and 
                order_resp.get('return_code') == 0 and 
                ('정상적으로 처리되었습니다' in order_resp.get('return_msg', '') or 
                 '매수주문완료' in order_resp.get('return_msg', ''))):
                print(f"[DEBUG][monitor_stock] 매수 주문 성공: {stock_name or stk_cd}({stk_cd})")
                order_success = True
            else:
                print(f"[DEBUG][monitor_stock] 매수 주문 실패: {stock_name or stk_cd}({stk_cd}), 응답: {order_resp}")
                order_success = False
        else:
            # 실전/모의투자 모드에서 실제 매수 주문 실행
            order_resp = place_order_real(token, stk_cd, qty=QTY, side='buy')
            if order_resp and (order_resp.get('return_code') == 0 or str(order_resp.get('return_code')) == '0'):
                print(f"[DEBUG][monitor_stock] 실전/모의투자 매수 주문 성공: {stock_name or stk_cd}({stk_cd})")
                order_success = True
            else:
                print(f"[DEBUG][monitor_stock] 실전/모의투자 매수 주문 실패: {stock_name or stk_cd}({stk_cd}), 응답: {order_resp}")
                order_success = False
        
        if order_success:
            # 자동매매 등록 (종목명 포함) - 매수 주문 성공 시에만
            if not add_auto_trade(stk_cd, buy_price_slip, mode, stock_name):
                print(f"[DEBUG][monitor_stock] 중복 등록으로 모니터링 중단: {stock_name or stk_cd}({stk_cd})")
                return
        else:
            print(f"[DEBUG][monitor_stock] 매수 실패로 모니터링 중단: {stock_name or stk_cd}({stk_cd})")
            return

        # 모니터링 루프
        loop_count = 0
        max_retries = 10  # 최대 재시도 횟수
        retry_count = 0
        
        while True:
            loop_count += 1
            print(f"[DEBUG][{stk_cd}] 모니터링 루프 {loop_count}회차 시작")
            
            # 현재 가격 조회
            cur_price = get_realtime_price_kiwoom(token, stk_cd, mode, buy_price_slip)
            print(f"[DEBUG][{stk_cd}] 실시간 가격 조회 결과: {cur_price}")
            if cur_price is None:
                retry_count += 1
                print(f"[DEBUG][{stk_cd}] 실시간 가격 조회 실패, 2초 후 재시도 ({retry_count}/{max_retries})")
                if retry_count >= max_retries:
                    print(f"[DEBUG][{stk_cd}] 최대 재시도 횟수 초과로 모니터링 중단")
                    break
                time.sleep(2)
                continue
            retry_count = 0  # 성공 시 재시도 카운트 리셋
            
            # 키움 공식에 따른 수익률 계산
            try:
                profit_rate, profit, total_eval, total_buy = calc_kiwoom_profit_rate(buy_price_slip, cur_price, QTY)
            except Exception as e:
                print(f"[DEBUG][{stk_cd}] 수익률 계산 오류: {e}")
                break
            
            print(f"[DEBUG][{stk_cd}] 현재가: {cur_price}, 수익률: {profit_rate:.2f}%")
            
            # 매도 시에만 슬리피지와 제세금 적용
            sell_price_slip = int(cur_price * (1 - SLIPPAGE_RATE))
            sell_fee = calc_fee(sell_price_slip * QTY)
            sell_tax = calc_tax(sell_price_slip * QTY)  # 매도 시에만 제세금
            sell_total = sell_price_slip * QTY - sell_fee - sell_tax
            
            # 자동매도 조건 확인
            if profit_rate >= 10.0:
                print(f"🎯 [익절 매도] {stock_name or stk_cd}({stk_cd}) {sell_total} (+{profit_rate:.2f}%)")
                sell_success = True
                if mode == 'mock':
                    sell_resp = place_order_mock(token, stk_cd, qty=QTY, side='sell')
                    print(f"[DEBUG][monitor_stock] 익절 매도 주문 응답: {sell_resp}")
                    if not sell_resp or (sell_resp.get('return_code') != 0 or 
                                       ('정상적으로 처리되었습니다' not in sell_resp.get('return_msg', '') and 
                                        '매도주문완료' not in sell_resp.get('return_msg', ''))):
                        print(f"[DEBUG][monitor_stock] 매도 주문 실패: {stock_name or stk_cd}({stk_cd}), 응답: {sell_resp}")
                        sell_success = False
                else:
                    # 실전/모의투자 모드에서 실제 매도 주문 실행
                    sell_resp = place_order_real(token, stk_cd, qty=QTY, side='sell')
                    if not sell_resp or (sell_resp.get('return_code') != 0 and str(sell_resp.get('return_code')) != '0'):
                        print(f"[DEBUG][monitor_stock] 실전/모의투자 매도 주문 실패: {stock_name or stk_cd}({stk_cd}), 응답: {sell_resp}")
                        sell_success = False
                    else:
                        print(f"[DEBUG][monitor_stock] 실전/모의투자 매도 주문 성공: {stock_name or stk_cd}({stk_cd})")
                
                if sell_success:
                    remove_auto_trade(stk_cd, sell_total, "자동매도")
                    break
                else:
                    print(f"[DEBUG][monitor_stock] 매도 실패로 계속 모니터링: {stock_name or stk_cd}({stk_cd}) - 수익률: {profit_rate:.2f}%")
                    # 매도 실패 시에만 자동 정리 (안전장치)
                    if loop_count > 50:  # 100초(50회 * 2초) 후 자동 정리
                        print(f"[DEBUG][monitor_stock] 매도 실패로 인한 자동 정리: {stock_name or stk_cd}({stk_cd}) - 수익률: {profit_rate:.2f}%")
                        remove_auto_trade(stk_cd, sell_total, "매도실패_자동정리")
                        break
            elif profit_rate <= -5.0:
                print(f"💔 [손절 매도] {stock_name or stk_cd}({stk_cd}) {sell_total} ({profit_rate:.2f}%)")
                sell_success = True
                if mode == 'mock':
                    sell_resp = place_order_mock(token, stk_cd, qty=QTY, side='sell')
                    print(f"[DEBUG][monitor_stock] 손절 매도 주문 응답: {sell_resp}")
                    if not sell_resp or (sell_resp.get('return_code') != 0 or 
                                       ('정상적으로 처리되었습니다' not in sell_resp.get('return_msg', '') and 
                                        '매도주문완료' not in sell_resp.get('return_msg', ''))):
                        print(f"[DEBUG][monitor_stock] 매도 주문 실패: {stock_name or stk_cd}({stk_cd}), 응답: {sell_resp}")
                        sell_success = False
                else:
                    # 실전/모의투자 모드에서 실제 매도 주문 실행
                    sell_resp = place_order_real(token, stk_cd, qty=QTY, side='sell')
                    if not sell_resp or (sell_resp.get('return_code') != 0 and str(sell_resp.get('return_code')) != '0'):
                        print(f"[DEBUG][monitor_stock] 실전/모의투자 매도 주문 실패: {stock_name or stk_cd}({stk_cd}), 응답: {sell_resp}")
                        sell_success = False
                    else:
                        print(f"[DEBUG][monitor_stock] 실전/모의투자 매도 주문 성공: {stock_name or stk_cd}({stk_cd})")
                
                if sell_success:
                    remove_auto_trade(stk_cd, sell_total, "자동매도")
                    break
                else:
                    print(f"[DEBUG][monitor_stock] 매도 실패로 계속 모니터링: {stock_name or stk_cd}({stk_cd}) - 수익률: {profit_rate:.2f}%")
                    # 매도 실패 시에만 자동 정리 (안전장치)
                    if loop_count > 50:  # 100초(50회 * 2초) 후 자동 정리
                        print(f"[DEBUG][monitor_stock] 매도 실패로 인한 자동 정리: {stock_name or stk_cd}({stk_cd}) - 수익률: {profit_rate:.2f}%")
                        remove_auto_trade(stk_cd, sell_total, "매도실패_자동정리")
                        break
            else:
                print(f"[DEBUG][{stk_cd}] 자동매도 조건 미충족")
                # 조건 미충족 시에는 계속 모니터링 (자동 정리 없음)
            
            time.sleep(2)
        
        print(f"[DEBUG][{stk_cd}] 모니터링 종료")
    except Exception as e:
        print(f"[DEBUG][monitor_stock] 예외 발생: {e}")

# 자동매매 후보 등록 함수
def save_candidate(stk_cd, cur_price, mode='real', stock_name=None):
    # 글로벌 락으로 Race Condition 방지
    with global_candidate_lock:
        # 현재 매수 중인 종목이 있는지 확인 (한 번에 하나만 매수)
        auto_trades = get_all_auto_trades()
        if auto_trades:
            return
        
        # 이미 매수된 종목인지 확인
        if is_already_bought(stk_cd):
            return
        
        # 완료된 거래에서도 중복 체크 (같은 종목을 다시 매수하지 않도록)
        completed_trades = load_json_file("completed_trades.json", [])
        for trade in completed_trades:
            if trade.get('stk_cd') == stk_cd:
                return
        
        # 현재 세션에서 이미 처리된 종목인지 확인 (같은 종목 중복 매수 방지)
        processed_stocks = load_json_file("processed_stocks.json", [])
        if stk_cd in processed_stocks:
            return
        
        # 즉시 처리된 종목 목록에 추가 (Race Condition 방지)
        add_processed_stock(stk_cd)
        
        # 모니터링 스레드 시작 (종목명도 전달)
        t = threading.Thread(target=monitor_stock, args=(stk_cd, cur_price, mode, stock_name), daemon=True)
        t.start()

if __name__ == '__main__':
    MODE = 'mock'  # 'real' 또는 'mock'으로 변경
    MY_ACCESS_TOKEN = load_token(MODE)

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
    counter = 0
    print(f"[자동 매매 시스템 시작] (mode={MODE})")
    while True:
        counter += 1
        print(f"\n{counter}번째 실행")
        fn_ka10023(token=MY_ACCESS_TOKEN, data=params, mode=MODE)
        print(f"[DEBUG][test_breakout] 5초 대기 후 다음 실행")
        time.sleep(5)
