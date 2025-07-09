from prometheus_client import start_http_server, Gauge, Counter
import time

# 메트릭 정의
websocket_status = Gauge('websocket_connected', '웹소켓 연결 상태 (1=연결, 0=해제)')
holdings_count = Gauge('holdings_count', '보유 종목 수')
error_count = Counter('error_count', '에러 발생 횟수')

# 실제 시스템에서 값을 갱신하는 함수 예시 (main.py 등에서 import해서 사용)
def set_websocket_status(connected: bool):
    websocket_status.set(1 if connected else 0)

def set_holdings_count(count: int):
    holdings_count.set(count)

def inc_error_count():
    error_count.inc()

if __name__ == '__main__':
    # 8000번 포트에서 메트릭 노출
    start_http_server(8000)
    print('Prometheus metrics server started on :8000')
    # 예시: 10초마다 임의 값 갱신
    import random
    while True:
        set_websocket_status(random.choice([0, 1]))
        set_holdings_count(random.randint(0, 15))
        time.sleep(10) 