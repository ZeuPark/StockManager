import requests
import json
import os
import gradio as gr
import pandas as pd


def load_token():
    """fake/fake_keys.json에서 인증 토큰을 읽어옵니다."""
    token_file = os.path.join('fake', 'fake_keys.json')
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                token = data.get('token')
                if token:
                    return token
        except Exception:
            pass
    raise RuntimeError('토큰 파일이 없거나 토큰이 없습니다.')


def call_kiwoom_api(token, api_id, params):
    """키움 모의투자 API를 호출해서 결과를 반환합니다."""
    url = 'https://mockapi.kiwoom.com/api/dostk/acnt'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': api_id,
        'cont-yn': 'N',
    }
    try:
        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        result = response.json()
        if result.get('return_code') != 0:
            return None
        return result
    except Exception:
        return None


def format_number(val, comma=True, float2=True):
    """숫자형 문자열을 보기 좋게 변환 (천단위 콤마, 소수점 2자리)"""
    try:
        s = str(val).replace('+', '').lstrip('0')
        if s in ('', '-'): s = '0'
        num = float(s)
        if float2:
            return f"{num:,.2f}" if comma else f"{num:.2f}"
        else:
            return f"{int(num):,}" if comma else str(int(num))
    except Exception:
        return val


def get_account_summary(token):
    """계좌 요약(예수금, 총평가, 총수익률, 총매입, 총손익, 추정자산) 반환"""
    url = 'https://mockapi.kiwoom.com/api/dostk/acnt'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'kt00018',
        'cont-yn': 'N',
    }
    data = {
        'qry_tp': '1',
        'dmst_stex_tp': 'KRX',
    }
    resp = requests.post(url, headers=headers, json=data)
    resp_json = resp.json()
    if resp.status_code != 200 or resp_json.get('return_code') != 0:
        return {
            '예수금': '-', '총평가': '-', '총수익률(%)': '-',
            '총매입': '-', '총손익': '-', '추정자산': '-'
        }
    def fmt(val):
        try:
            return f"{int(str(val).lstrip('0') or '0'):,}"
        except Exception:
            return val
    def fmt_rate(val):
        try:
            s = str(val).replace('+', '').lstrip('0')
            if s in ('', '-'): s = '0'
            return f"{float(s):.2f}"
        except Exception:
            return val
    return {
        '예수금': fmt(resp_json.get('prsm_dpst_aset_amt')),
        '총평가': fmt(resp_json.get('tot_evlt_amt')),
        '총수익률(%)': fmt_rate(resp_json.get('tot_prft_rt', '-')),
        '총매입': fmt(resp_json.get('tot_pur_amt')),
        '총손익': fmt(resp_json.get('tot_evlt_pl')),
        '추정자산': fmt(resp_json.get('tot_evlt_amt')),
    }


def get_account_info():
    """계좌 잔고/수익률을 DataFrame으로 반환 (숫자 보기 좋게 변환)"""
    try:
        token = load_token()
    except Exception:
        test_balance = pd.DataFrame({
            '종목코드': ['005930', '000660'],
            '종목명': ['삼성전자', 'SK하이닉스'],
            '현재가': ['70,000', '120,000'],
            '보유수량': ['10', '5'],
            '평가금액': ['700,000', '600,000']
        })
        test_profit = pd.DataFrame({
            '총평가금액': ['1,300,000'],
            '총수익률(%)': ['5.20']
        })
        test_summary = pd.DataFrame({
            '예수금': ['1,000,000'],
            '총평가': ['1,300,000'],
            '총수익률(%)': ['5.20'],
            '총매입': ['1,200,000'],
            '총손익': ['100,000'],
            '추정자산': ['1,400,000']
        })
        return test_balance, test_profit, test_summary

    params_balance = {'qry_tp': '1', 'dmst_stex_tp': 'KRX'}
    balance_result = call_kiwoom_api(token, 'kt00018', params_balance)
    balance_list = balance_result.get('acnt_evlt_remn_indv_tot', []) if balance_result else []
    if balance_list:
        balance_df = pd.DataFrame(balance_list)
        col_map = {
            'stk_cd': '종목코드', 'stk_nm': '종목명', 'cur_prc': '현재가', 'rmnd_qty': '보유수량',
            'evlt_amt': '평가금액', 'evltv_prft': '평가손익', 'prft_rt': '수익률(%)', 'pur_amt': '매입금액',
            'trde_able_qty': '주문가능수량', 'pur_pric': '매입단가',
        }
        balance_df = balance_df.rename(columns=col_map)
        # 주요 컬럼 변환
        for col in ['현재가', '보유수량', '평가금액', '평가손익', '매입금액', '주문가능수량', '매입단가']:
            if col in balance_df.columns:
                balance_df[col] = balance_df[col].apply(lambda x: format_number(x, comma=True, float2=False))
        if '수익률(%)' in balance_df.columns:
            balance_df['수익률(%)'] = balance_df['수익률(%)'].apply(lambda x: format_number(x, comma=False, float2=True))
        # 남아있는 zero-padding 숫자형 컬럼도 일괄 변환 (숫자만 있는 문자열이면 모두 변환)
        for col in balance_df.columns:
            if balance_df[col].dtype == object:
                if balance_df[col].str.fullmatch(r'[+-]?\d+').any():
                    balance_df[col] = balance_df[col].apply(lambda x: format_number(x, comma=True, float2=False))
        # 꼭 보여줄 컬럼만 남기기
        show_balance_cols = ['종목코드', '종목명', '현재가', '보유수량', '매입단가', '매입금액', '평가금액', '평가손익', '수익률(%)']
        balance_df = balance_df[[col for col in show_balance_cols if col in balance_df.columns]]
    else:
        balance_df = pd.DataFrame({
            '종목코드': ['-'],
            '종목명': ['보유 종목 없음'],
            '상태': ['현재 보유 중인 종목이 없습니다.']
        })

    params_profit = {'stex_tp': '0'}
    profit_result = call_kiwoom_api(token, 'ka10085', params_profit)
    profit_list = profit_result.get('acnt_prft_rt', []) if profit_result else []
    if profit_list:
        profit_df = pd.DataFrame(profit_list)
        col_map = {
            'stk_cd': '종목코드', 'stk_nm': '종목명', 'cur_prc': '현재가',
            'pur_pric': '매입단가', 'pur_amt': '매입금액', 'rmnd_qty': '보유수량',
        }
        profit_df = profit_df.rename(columns=col_map)
        for col in ['현재가', '매입단가', '매입금액', '보유수량']:
            if col in profit_df.columns:
                profit_df[col] = profit_df[col].apply(lambda x: format_number(x, comma=True, float2=False))
        # 종목코드는 숫자라도 컴마 없이 문자열로 변환
        if '종목코드' in profit_df.columns:
            profit_df['종목코드'] = profit_df['종목코드'].astype(str)
        for col in profit_df.columns:
            if profit_df[col].dtype == object and col != '종목코드':
                if profit_df[col].str.fullmatch(r'[+-]?\d+').any():
                    profit_df[col] = profit_df[col].apply(lambda x: format_number(x, comma=True, float2=False))
        # 꼭 보여줄 컬럼만 남기기
        show_profit_cols = ['종목코드', '종목명', '현재가', '매입단가', '매입금액', '보유수량']
        profit_df = profit_df[[col for col in show_profit_cols if col in profit_df.columns]]
    else:
        profit_df = pd.DataFrame({
            '상태': ['API 연결 실패'],
            '메시지': ['토큰 또는 API 확인 필요']
        })
    # 계좌 요약 정보도 함께 반환
    summary = get_account_summary(token)
    summary_df = pd.DataFrame([summary])
    return balance_df, profit_df, summary_df


def create_dashboard():
    """Gradio 대시보드를 생성합니다."""
    
    # 다크 테마 CSS
    custom_css = """
    /* 전역 스타일 - 다크 테마 */
    * {
        box-sizing: border-box;
    }
    
    body {
        margin: 0;
        padding: 0;
        background: #0d1117 !important;
        color: #f0f6fc !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', Roboto, sans-serif !important;
    }
    
    .gradio-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
        background: #0d1117 !important;
        min-height: 100vh;
        color: #f0f6fc !important;
    }
    
    /* 메인 컨테이너 - 스타일 다크 */
    .main-container {
        background: #161b22 !important;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #30363d;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* 헤더 -  스타일 */
    .header-title {
        text-align: center;
        margin-bottom: 32px;
        padding: 32px 24px;
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        border-radius: 16px;
        position: relative;
        overflow: hidden;
        border: 1px solid #238636;
    }
    
    .header-title h1 {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    
    .header-title p {
        font-size: 16px;
        color: rgba(255, 255, 255, 0.9);
        margin: 8px 0 0 0;
        font-weight: 400;
    }
    
    /* 섹션 헤더 - 토스 스타일 */
    .section-header {
        background: #21262d;
        color: #f0f6fc;
        padding: 16px 20px;
        margin: 24px 0 16px 0;
        border-radius: 12px;
        font-size: 18px;
        font-weight: 600;
        border: 1px solid #30363d;
        letter-spacing: -0.3px;
    }
    
    /* 카드 스타일 - 토스 다크 */
    .card {
        background: #0d1117 !important;
        border-radius: 16px;
        padding: 0;
        margin: 16px 0;
        border: 1px solid #30363d;
        transition: all 0.2s ease;
    }
    
    .card:hover {
        border-color: #238636;
        box-shadow: 0 8px 24px rgba(35, 134, 54, 0.1);
    }
    
    /* 데이터프레임 테이블 - 토스 다크 스타일 */
    .dataframe {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', Roboto, sans-serif !important;
        border-collapse: collapse;
        width: 100%;
        margin: 0;
        background: #0d1117 !important;
        border-radius: 12px;
        overflow: hidden;
        font-size: 14px;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #30363d;
    }
    
    .summary-table .dataframe {
        max-height: 200px;
    }
    
    .balance-table .dataframe,
    .profit-table .dataframe {
        max-height: 450px;
    }
    
    .dataframe th {
        background: #21262d !important;
        color: #f0f6fc !important;
        padding: 16px 12px;
        text-align: center;
        font-weight: 600;
        border: none;
        font-size: 13px;
        letter-spacing: -0.2px;
        border-bottom: 1px solid #30363d;
    }
    
    .dataframe td {
        padding: 14px 12px;
        text-align: center;
        background: #0d1117 !important;
        color: #f0f6fc !important;
        border: none;
        border-bottom: 1px solid #21262d;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    
    .dataframe tr:hover td {
        background: #161b22 !important;
        color: #f0f6fc !important;
    }
    
    /* 양수/음수 색상 - 토스 스타일 */
    .dataframe td:has-text('+'),
    .dataframe td[style*="color: #27ae60"],
    .performance-positive {
        color: #2ea043 !important;
        font-weight: 600;
    }
    
    .dataframe td:has-text('-'),
    .dataframe td[style*="color: #e74c3c"],
    .performance-negative {
        color: #f85149 !important;
        font-weight: 600;
    }
    
    /* 새로고침 버튼 - 토스 스타일 */
    .refresh-button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: #ffffff !important;
        border: none;
        padding: 14px 32px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 600;
        margin: 24px auto;
        display: block;
        cursor: pointer;
        transition: all 0.2s ease;
        letter-spacing: -0.2px;
        border: 1px solid #238636;
    }
    
    .refresh-button:hover {
        background: linear-gradient(135deg, #2ea043 0%, #238636 100%) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(35, 134, 54, 0.3);
    }
    
    .refresh-button:active {
        transform: translateY(0);
    }
    
    /* 스크롤바 - 다크 테마 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #21262d;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    
    /* Gradio 특정 요소들 다크 테마 적용 */
    .gradio-container .prose {
        color: #f0f6fc !important;
    }
    
    .gradio-container button {
        background: #21262d !important;
        color: #f0f6fc !important;
        border: 1px solid #30363d !important;
    }
    
    .gradio-container button:hover {
        background: #30363d !important;
    }
    
    /* 상태 표시 텍스트 */
    .status-text {
        text-align: center;
        color: #8b949e;
        font-size: 14px;
        margin-top: 16px;
    }
    
    .status-text span {
        display: block;
        margin: 4px 0;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 16px;
        }
        
        .main-container {
            padding: 16px;
            border-radius: 12px;
        }
        
        .header-title {
            padding: 24px 16px;
        }
        
        .header-title h1 {
            font-size: 24px;
        }
        
        .dataframe {
            font-size: 13px;
        }
        
        .dataframe th, .dataframe td {
            padding: 10px 8px;
        }
        
        .refresh-button {
            padding: 12px 24px;
            font-size: 14px;
        }
    }
    
    /* 로딩 애니메이션 */
    .loading {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #30363d;
        border-top: 2px solid #2ea043;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    """
    
    with gr.Blocks(css=custom_css, title="📈모의투자 대시보드", theme=gr.themes.Base(primary_hue="green", secondary_hue="gray", neutral_hue="slate")) as demo:
        # 메인 컨테이너
        with gr.Column(elem_classes="main-container"):
            # 제목
            gr.HTML('''
                <div class="header-title">
                    <h1>📈 모의투자 계좌 실시간 대시보드</h1>
                    <p style="margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9;">
                        실시간으로 업데이트되는 포트폴리오 현황을 확인하세요
                    </p>
                </div>
            ''')
            
            # 계좌 요약 섹션
            with gr.Column(elem_classes="card"):
                gr.HTML('<div class="section-header">💰 계좌 요약 정보</div>')
                summary_table = gr.Dataframe(
                    interactive=False,
                    wrap=True,
                    elem_classes="summary-table"
                )
            
            # 계좌 평가 잔고 섹션
            with gr.Column(elem_classes="card"):
                gr.HTML('<div class="section-header">💼 보유 종목 평가 잔고</div>')
                balance_table = gr.Dataframe(
                    interactive=False,
                    wrap=True,
                    elem_classes="balance-table"
                )
            
            # 계좌 수익률 섹션
            with gr.Column(elem_classes="card"):
                gr.HTML('<div class="section-header">📊 종목별 수익률 현황</div>')
                profit_table = gr.Dataframe(
                    interactive=False,
                    wrap=True,
                    elem_classes="profit-table"
                )
            
            # 새로고침 버튼과 상태 표시
            with gr.Row():
                with gr.Column():
                    refresh_btn = gr.Button(
                        "🔄 데이터 새로고침", 
                        elem_classes="refresh-button", 
                        size="lg"
                    )
                    gr.HTML('''
                        <div class="status-text">
                            <span id="last-update">마지막 업데이트: 페이지 로드 시</span>
                            <span>30초마다 자동 새로고침됩니다</span>
                        </div>
                    ''')
        
        # 이벤트 핸들러
        refresh_btn.click(
            fn=get_account_info,
            outputs=[balance_table, profit_table, summary_table]
        )
        
        # 페이지 로드 시 초기 데이터 로드
        demo.load(
            fn=get_account_info,
            outputs=[balance_table, profit_table, summary_table]
        )
        
        # 개선된 자동 새로고침 스크립트
        gr.HTML(
            """
            <script>
            let refreshInterval;
            let countdownInterval;
            let timeLeft = 30;
            
            function updateCountdown() {
                const updateElement = document.getElementById('last-update');
                if (updateElement) {
                    const now = new Date();
                    const timeString = now.toLocaleTimeString('ko-KR');
                    updateElement.innerHTML = `마지막 업데이트: ${timeString} (다음 업데이트까지 ${timeLeft}초)`;
                }
                
                timeLeft--;
                if (timeLeft < 0) {
                    timeLeft = 30;
                    const refreshBtn = document.querySelector('button[class*="refresh-button"]');
                    if (refreshBtn) {
                        refreshBtn.click();
                    }
                }
            }
            
            // 1초마다 카운트다운 업데이트
            countdownInterval = setInterval(updateCountdown, 1000);
            
            // 30초마다 자동 새로고침
            refreshInterval = setInterval(function() {
                const refreshBtn = document.querySelector('button[class*="refresh-button"]');
                if (refreshBtn) {
                    refreshBtn.click();
                }
                timeLeft = 30;
            }, 30000);
            
            // 페이지 언로드 시 인터벌 정리
            window.addEventListener('beforeunload', function() {
                if (refreshInterval) clearInterval(refreshInterval);
                if (countdownInterval) clearInterval(countdownInterval);
            });
            </script>
            """
        )
    
    return demo


if __name__ == '__main__':
    dashboard = create_dashboard()
    dashboard.launch(share=True)