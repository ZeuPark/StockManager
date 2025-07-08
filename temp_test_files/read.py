import pandas as pd

src = 'C:/Users/user/Downloads/2025-07-08 당일매매손익표.csv'
dst = '2025-07-08_당일매매손익표_utf8.csv'

df = pd.read_csv(src, encoding='cp949')
df.to_csv(dst, index=False, encoding='utf-8-sig')
print(f'한글이 깨지지 않게 {dst}로 저장 완료!')
