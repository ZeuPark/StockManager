# 간단한 네이버 뉴스 크롤러 & 백테스트

복잡한 기존 프로그램 대신 간단하게 네이버 뉴스를 크롤링하고 백테스트할 수 있는 프로그램입니다.

## 📁 파일 구조

```
news_trading/
├── simple_naver_crawler.py    # 간단한 네이버 뉴스 크롤러
├── simple_backtest.py         # 뉴스 기반 백테스트 프로그램
├── run_simple_crawler.py      # 크롤러 실행 스크립트
└── SIMPLE_README.md          # 이 파일
```

## 🚀 빠른 시작

### 1. 필요한 패키지 설치

```bash
pip install requests beautifulsoup4 pandas numpy matplotlib seaborn
```

### 2. 뉴스 크롤링

#### 방법 1: 기본 실행 (1년치 경제 뉴스)
```bash
cd news_trading
python run_simple_crawler.py
```

#### 방법 2: 커스텀 설정
```bash
# 특정 기간 경제 뉴스
python run_simple_crawler.py --start-date 2024-01-01 --end-date 2024-12-01 --category economy

# 주식 뉴스만
python run_simple_crawler.py --category stock --output my_stock_news

# 기업 뉴스만
python run_simple_crawler.py --category company --output my_company_news
```

### 3. 백테스트 실행

```bash
# 크롤링 결과 파일로 백테스트
python simple_backtest.py
```

## 📊 크롤링 결과

크롤링이 완료되면 다음 파일들이 생성됩니다:

- `naver_news_economy_20241201_120000.csv` - CSV 형식
- `naver_news_economy_20241201_120000.json` - JSON 형식

### 데이터 구조
```csv
date,title,url,category,content,summary,source,crawl_time
2024-01-01,뉴스 제목,https://...,economy,뉴스 본문,요약,출처,2024-12-01T12:00:00
```

## 📈 백테스트 결과

백테스트가 완료되면 다음 파일들이 생성됩니다:

- `backtest_results.csv` - 일별 거래 기록
- `backtest_results_metrics.json` - 성과 지표
- `backtest_results.png` - 시각화 차트

### 성과 지표
- `final_return_pct`: 최종 수익률 (%)
- `max_drawdown_pct`: 최대 낙폭 (%)
- `trade_count`: 거래 횟수
- `win_rate_pct`: 승률 (%)

## 🔧 설정 옵션

### 크롤러 설정

`simple_naver_crawler.py`에서 다음 설정을 변경할 수 있습니다:

```python
# 서버 부하 방지 딜레이 (초)
time.sleep(0.5)  # 뉴스 상세 정보 수집 간격
time.sleep(1)    # 일별 크롤링 간격

# User-Agent 설정
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...'
```

### 백테스트 설정

`simple_backtest.py`에서 다음 설정을 변경할 수 있습니다:

```python
# 초기 자본
self.portfolio_value = 1000000  # 100만원

# 감정 분석 임계값
positive_threshold = 0.6  # 긍정 신호 임계값
negative_threshold = 0.6  # 부정 신호 임계값

# 키워드 추가/수정
positive_keywords = ['상승', '급등', '호재', ...]
negative_keywords = ['하락', '급락', '악재', ...]
```

## 📋 사용 예시

### 예시 1: 6개월 경제 뉴스 수집
```bash
python run_simple_crawler.py --start-date 2024-06-01 --end-date 2024-12-01 --category economy --output economy_6months
```

### 예시 2: 주식 뉴스 백테스트
```bash
# 1. 주식 뉴스 수집
python run_simple_crawler.py --category stock --output stock_news

# 2. 백테스트 실행 (simple_backtest.py에서 파일명 수정)
python simple_backtest.py
```

### 예시 3: 여러 카테고리 수집
```bash
# 경제 뉴스
python run_simple_crawler.py --category economy --output economy_news

# 주식 뉴스  
python run_simple_crawler.py --category stock --output stock_news

# 기업 뉴스
python run_simple_crawler.py --category company --output company_news
```

## ⚠️ 주의사항

1. **서버 부하 방지**: 크롤링 간격을 너무 짧게 설정하지 마세요
2. **파일 경로**: 백테스트 실행 시 올바른 뉴스 데이터 파일 경로를 지정하세요
3. **네트워크**: 안정적인 인터넷 연결이 필요합니다
4. **저장 공간**: 1년치 뉴스는 수백 MB의 용량이 필요할 수 있습니다

## 🔍 문제 해결

### 크롤링이 안 되는 경우
- 네트워크 연결 확인
- User-Agent 설정 확인
- 딜레이 시간 증가

### 백테스트 오류
- 뉴스 데이터 파일 경로 확인
- 파일 형식 확인 (CSV 또는 JSON)
- 날짜 형식 확인 (YYYY-MM-DD)

### 메모리 부족
- 크롤링 기간을 줄이기
- 카테고리를 하나씩 수집하기

## 📞 도움말

문제가 발생하면 다음을 확인하세요:

1. 로그 메시지 확인
2. 파일 경로 확인
3. 네트워크 연결 확인
4. Python 패키지 설치 확인

---

**간단하고 빠르게 네이버 뉴스 크롤링과 백테스트를 시작하세요!** 🚀 