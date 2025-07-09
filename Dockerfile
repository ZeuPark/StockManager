# 기존 Python 앱 빌드 (main.py, requirements.txt 등)
FROM python:3.10-slim as app
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# 메트릭 서버 실행용 (main.py 또는 monitor/prometheus_metrics.py)
CMD ["python", "main.py"] 