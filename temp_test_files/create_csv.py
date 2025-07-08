import pandas as pd

# 원본 파일 경로
src = 'C:/Users/user/Downloads/2025-07-08 당일매매손익표.csv'
# 저장할 파일 경로
dst = '2025-07-08_당일매매손익표_utf8.csv'

# cp949로 읽어서 utf-8-sig로 저장
df = pd.read_csv(src, encoding='cp949')
df.to_csv(dst, index=False, encoding='utf-8-sig')
print(f'한글이 깨지지 않게 {dst}로 저장 완료!') 