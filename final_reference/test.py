import requests
import json
import os
import traceback


def fn_kt10001(token, data, cont_yn='N', next_key=''):
    host = 'https://mockapi.kiwoom.com'  # 모의투자
    endpoint = '/api/dostk/ordr'
    url = host + endpoint
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': 'kt10001',
    }
    try:
        print(f"[DEBUG] POST {url}")
        print(f"[DEBUG] headers: {headers}")
        print(f"[DEBUG] data: {data}")
        response = requests.post(url, headers=headers, json=data)
        print('Code:', response.status_code)
        print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
        print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))
        return response.json()
    except Exception as e:
        print(f"[fn_kt10001 예외] {e}")
        traceback.print_exc()
        return None


def load_token():
    token_file = os.path.join('fake', 'fake_keys.json')
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                token = data.get('token')
                if token:
                    return token
        except Exception as e:
            print(f"[토큰 로드 오류] {e}")
    raise RuntimeError('토큰 파일이 없거나 토큰이 없습니다.')


BOUGHT_FILE = "bought_stocks.json"


def load_bought_stocks():
    if os.path.exists(BOUGHT_FILE):
        try:
            with open(BOUGHT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_bought_stocks(bought_set):
    with open(BOUGHT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(bought_set), f, ensure_ascii=False)


BUY_PRICE_FILE = "buy_price.json"


def save_buy_price(stk_cd, price):
    with open(BUY_PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump({"stk_cd": stk_cd, "buy_price": price}, f, ensure_ascii=False)


def load_buy_price():
    if os.path.exists(BUY_PRICE_FILE):
        with open(BUY_PRICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_current_price(stk_cd):
    # 실제로는 실시간 시세 API를 써야 함. 예시로 랜덤 변동
    import random
    return 50000 + random.randint(-2000, 2000)


if __name__ == '__main__':
    try:
        MY_ACCESS_TOKEN = load_token()
    except Exception as e:
        print(f"[ERROR] 토큰 로드 실패: {e}")
        exit(1)

    params = {
        'dmst_stex_tp': 'KRX',
        'stk_cd': '005930',
        'ord_qty': '1',
        'ord_uv': '50000',
        'trde_tp': '0',
        'cond_uv': '',
    }

    bought_stocks = load_bought_stocks()
    stk_cd = params['stk_cd']

    익절률 = 0.06  # 6% 익절
    손절률 = -0.03 # -3% 손절

    buy_info = load_buy_price()
    holding = buy_info is not None

    while True:
        cur_price = get_current_price(stk_cd)
        print(f"[INFO] 현재가: {cur_price}")

        if not holding and stk_cd not in bought_stocks:
            if cur_price <= 50000:
                print("[매수 시그널] 매수 조건 충족!")
                resp = fn_kt10001(token=MY_ACCESS_TOKEN, data=params)
                if resp and str(resp.get('return_code')) == '0':
                    bought_stocks.add(stk_cd)
                    save_bought_stocks(bought_stocks)
                    save_buy_price(stk_cd, cur_price)
                    holding = True
                    print(f"[매수 체결] 매수가격: {cur_price}")
        elif holding:
            buy_price = load_buy_price()['buy_price']
            change_rate = (cur_price - buy_price) / buy_price
            print(f"[INFO] 수익률: {change_rate*100:.2f}%")
            if change_rate >= 익절률:
                print("[익절 시그널] 익절 조건 충족! (매도 주문)")
                # 매도 주문 로직 추가 가능
                break
            elif change_rate <= 손절률:
                print("[손절 시그널] 손절 조건 충족! (매도 주문)")
                # 매도 주문 로직 추가 가능
                break
        else:
            print("[대기] 조건 미충족")
        import time; time.sleep(5)
