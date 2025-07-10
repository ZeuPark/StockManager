import os
from data_analyzer import load_token, crawl_all_stocks_minute_data

if __name__ == '__main__':
    token = load_token('production')
    save_dir = 'minute_data'
    sleep_sec = 1
    print(f'전체 종목 1분봉 데이터 수집 시작... (저장 폴더: {save_dir})')
    crawl_all_stocks_minute_data(token, sleep_sec=sleep_sec, save_dir=save_dir)
    print('모든 종목 데이터 수집 완료!') 