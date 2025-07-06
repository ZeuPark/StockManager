import asyncio
import websockets
import json

SOCKET_URL = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'  # 모의투자
ACCESS_TOKEN = 'N1dj5oU3fgKOqnBhm3SySaM2YZQSdfFxQj6IiFNaMPXzhZfjTVEGdlrZ7QBtZXlxf4hgGnZpEclNSflbRM4Ifg'

async def main():
    async with websockets.connect(SOCKET_URL) as ws:
        print('서버 연결됨')

        # 로그인
        login_msg = {'trnm': 'LOGIN', 'token': ACCESS_TOKEN}
        await ws.send(json.dumps(login_msg))
        print('로그인 메시지 전송')

        # 응답 수신
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            print('수신:', data)

            if data.get('trnm') == 'LOGIN':
                if data.get('return_code') == 0:
                    print('로그인 성공')
                    # 실시간 등록 예시
                    reg_msg = {
                        'trnm': 'REG',
                        'grp_no': '1',
                        'refresh': '1',
                        'data': [{
                            'item': ['005930'],
                            'type': ['00'],
                        }]
                    }
                    await ws.send(json.dumps(reg_msg))
                    print('실시간 등록 메시지 전송')
                else:
                    print('로그인 실패:', data.get('return_msg'))
                    break
            elif data.get('trnm') == 'PING':
                await ws.send(json.dumps(data))  # 핑-퐁
            elif data.get('trnm') == 'REG':
                print('실시간 등록 응답:', data)
            # 필요시 추가 처리

if __name__ == '__main__':
    asyncio.run(main())