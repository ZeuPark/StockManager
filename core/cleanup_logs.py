import os
import time

LOG_DIR = 'logs'
DAYS_TO_KEEP = 7
SIZE_LIMIT_MB = 10

now = time.time()

for fname in os.listdir(LOG_DIR):
    fpath = os.path.join(LOG_DIR, fname)
    if not os.path.isfile(fpath):
        continue
    # 1. 오래된 로그 삭제
    mtime = os.path.getmtime(fpath)
    if now - mtime > DAYS_TO_KEEP * 86400:
        print(f"[삭제] 오래된 로그: {fname}")
        os.remove(fpath)
        continue
    # 2. 대용량 로그 삭제
    size_mb = os.path.getsize(fpath) / (1024*1024)
    if size_mb > SIZE_LIMIT_MB:
        print(f"[삭제] 대용량 로그: {fname} ({size_mb:.1f}MB)")
        os.remove(fpath) 