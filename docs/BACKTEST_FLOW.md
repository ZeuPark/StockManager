# StockManager 백테스트 구조 및 흐름

## 1. 백테스트 개요
- 1분봉 데이터 기반 이벤트 드리븐 백테스트
- 다양한 전략(단타, 스윙, 모멘텀, 돌파 등) 지원
- 실전과 유사한 거래비용(수수료, 세금, 슬리피지) 반영
- 전략별 진입/청산 조건, 리스크 관리, 성과 분석 자동화

## 2. 주요 백테스트 파일/모듈
- **core/backtest_gradual_riser.py**: 점진적 상승(단타) 전략 백테스트
- **core/backtest_gradual_riser_trailing.py**: 트레일링스탑 포함 고급 백테스트
- **analysis/analysis_visualizer.py**: 백테스트 결과 시각화 및 성과 분석
- **analysis/analyze_gradual_risers.py**: 조건별 종목 분석 및 통계
- **core/parameter_optimizer.py, auto_parameter_adjuster.py**: 파라미터 최적화/완화 루프

## 3. 백테스트 흐름

1. **데이터 로딩**
   - minute_data/ 폴더의 1분봉 CSV 파일을 종목별로 로딩
   - pandas DataFrame으로 변환, 결측치/이상치 처리

2. **지표 계산**
   - VWAP, RSI, 이동평균 등 주요 기술적 지표 계산
   - 거래량, 고가/저가, 변동성 등 추가 feature 생성

3. **진입(매수) 조건 평가**
   - 전략별 진입 구간(예: 10:15~10:45)에서 조건 탐색
   - 예시: VWAP 상회, 고가 근접, 거래량 급증, RSI 과열/과매도 등

4. **청산(매도) 조건 평가**
   - TP(익절), SL(손절), 트레일링스탑, VWAP 이탈, RSI 과열, EOD(장마감) 등
   - 각 조건별로 실제 매도 시점/가격 기록

5. **성과 기록**
   - 거래별 수익률, 최대이익, 최대손실, 청산 사유 등 기록
   - 전체 결과 DataFrame으로 집계 및 CSV 저장

6. **성과 분석/시각화**
   - 누적 수익률, 월별/종목별/이유별 통계, 분포 히스토그램 등 시각화
   - Sharpe Ratio, Max Drawdown, Profit Factor 등 주요 지표 산출

## 4. 주요 기법/특징
- 이벤트 드리븐 방식(신호 발생 시점에만 거래)
- 1일 1매수 원칙(과최적화 방지)
- 실전과 유사한 거래비용 반영
- 다양한 전략/파라미터 실험 및 자동화
- 결과 자동 저장 및 시각화

## 5. 사용법 예시

```bash
# 단일 전략 백테스트
python core/backtest_gradual_riser.py

# 트레일링스탑 포함 고급 백테스트
python core/backtest_gradual_riser_trailing.py

# 파라미터 자동 완화/최적화
python core/auto_parameter_adjuster.py
python core/parameter_optimizer.py

# 결과 시각화/분석
python analysis/analysis_visualizer.py
```

## 6. 결과 해석
- **backtest_gradual_riser_combined.csv**: 거래별 상세 기록
- **backtest_analysis_plots.png**: 수익률/청산사유/분포 시각화
- **auto_parameter_adjustment_YYYYMMDD_HHMMSS.csv**: 파라미터 실험 결과
- **analysis_results/**: 종합 분석 리포트 및 차트

## 7. 참고/확장
- 전략별 조건 및 파라미터는 core/analysis/ 폴더 내 코드에서 쉽게 수정 가능
- 신규 전략 추가, 리스크 관리 강화, 실시간 연동 등 확장 용이

---

이 문서는 StockManager의 백테스트 구조와 흐름, 실제 적용된 기법, 사용법, 결과 해석을 한눈에 파악할 수 있도록 정리한 요약본입니다. 