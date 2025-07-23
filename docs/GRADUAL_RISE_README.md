# 완만 상승 패턴 백테스트 시스템

## 📌 개요

1년치 1분봉 데이터를 활용하여 "완만 상승 종목" 패턴을 찾는 백테스트 시스템입니다.

### 핵심 개념

| 구분 | 정의 | 기대 효과 |
|------|------|-----------|
| **Opening Spike** | 첫 1분봉 수익률 ≥ θ_spike (ex. +2%) | 급격한 상승 후 되돌림 빈번 → 제외 필터 |
| **Gradual Rise** | (i) 첫 1분 수익률 < θ_spike_low (ex. +0.5%)<br>(ii) 15분 누적 수익률 ≥ θ_15m (ex. +2%)<br>(iii) 저점 하락폭 ≥ -θ_pull (ex. -0.3%) | 완만한 누적 상승·저점 높이기 구조 |
| **Volume Confirmation** | 첫 15분 거래량 / 전일 총 거래량 ≥ θ_vol (ex. 5%) | 수급 실린 "진짜" 매수세 구분 |
| **ORB Delay** | 30분 이내 고가 돌파 시 매수, 단 최초 5분은 진입 금지 | 급등 시초봉 피하고, 패턴 확인 후 진입 |

## 🚀 빠른 시작

### 1. 기본 백테스트 실행

```bash
python gradual_rise_backtest.py
```

### 2. 파라미터 최적화

```bash
python parameter_optimizer.py
```

### 3. 결과 분석 및 시각화

```bash
python analysis_visualizer.py
```

### 4. 테스트 실행

```bash
python test_backtest.py
```

## 📊 주요 Feature

### Return-Based Features
- `r_1`: 첫 1분 수익률
- `cum_r_15`: 15분 누적 수익률
- `slope_15`: 선형회귀 기울기 (15분)

### Trend Features
- `hl_score`: Higher-Low Score (#(close > SMA_5) / 15)
- `max_drawdown_15`: 최초 high 대비 저점하락폭
- `vwap_gap`: VWAP 대비 수급이익 여부

### Volume Features
- `volume_15min`: 첫 15분 거래량
- `v_ratio_15`: V_{15} / 전일 V_total

## ⚙️ 파라미터 설정

### 기본 파라미터
```python
parameters = {
    'theta_spike': 0.02,      # 첫 1분 수익률 임계값 (2%)
    'theta_spike_low': 0.005,  # 첫 1분 최소 수익률 (0.5%)
    'theta_15m': 0.02,        # 15분 누적 수익률 임계값 (2%)
    'theta_vol': 0.05,        # 거래량 비율 임계값 (5%)
    'theta_pull': 0.003,      # 저점 하락 임계값 (0.3%)
    'tp_pct': 0.04,           # 익절 수익률 (4%)
    'sl_pct': 0.02,           # 손절 수익률 (2%)
    'orb_delay_min': 5,       # ORB 진입 최소 대기시간 (분)
    'orb_max_min': 30         # ORB 진입 최대 대기시간 (분)
}
```

## 📈 백테스트 절차

### 1. 전처리
- 1분봉 데이터 정렬 및 결측 제거
- 전일 종가·거래량 결합

### 2. Feature Engineering
- 벡터화 연산으로 속도 최적화
- 15분간 패턴 분석

### 3. 필터 적용
- Opening Spike 제외
- Gradual Rise 확인
- Volume Confirmation

### 4. ORB 진입점 탐색
- 5분 이후 ~ 30분 이내 고가 돌파
- 보수적 진입가 (다음 봉 시가)

### 5. 거래 시뮬레이션
- **TP**: +4% 도달 시 익절
- **SL**: -2% 도달 시 손절
- **Close**: 종가 청산

## 📊 성과 지표

### 기본 지표
- **총 거래 수**: 전체 거래 건수
- **승률**: 수익 거래 비율
- **평균 수익률**: 거래별 평균 수익률
- **샤프 비율**: 수익률 / 표준편차
- **최대 손실**: 누적 수익률 최저점

### 고급 지표
- **수익 팩터**: 총 수익 / 총 손실
- **기대값**: 평균 수익률 × 거래 수
- **평균 승리/손실**: 승리/손실 거래의 평균

## 🔧 사용 예제

### 기본 백테스트
```python
from gradual_rise_backtest import GradualRiseBacktest

# 백테스트 인스턴스 생성
backtest = GradualRiseBacktest()

# 파라미터 설정
backtest.parameters.update({
    'theta_spike': 0.02,
    'theta_15m': 0.015,
    'tp_pct': 0.04,
    'sl_pct': 0.02,
})

# 백테스트 실행
metrics, trades = backtest.run_backtest()
```

### 파라미터 최적화
```python
from parameter_optimizer import ParameterOptimizer

optimizer = ParameterOptimizer()
best_params = optimizer.optimize(n_trials=100)
metrics, trades = optimizer.validate_best_params()
```

### 결과 분석
```python
from analysis_visualizer import AnalysisVisualizer

visualizer = AnalysisVisualizer()
visualizer.load_trades('gradual_rise_trades.csv')
visualizer.create_comprehensive_report()
```

## 📁 출력 파일

### 거래 내역
- `gradual_rise_trades.csv`: 기본 백테스트 결과
- `optimized_trades.csv`: 최적화된 백테스트 결과
- `test_trades.csv`: 테스트 결과

### 분석 결과
- `analysis_results/`: 종합 분석 리포트
  - `cumulative_returns.png`: 누적 수익률 차트
  - `monthly_performance.png`: 월별 성과 차트
  - `return_distribution.png`: 수익률 분포 히스토그램
  - `exit_reason_analysis.png`: 청산 이유 분석
  - `stock_performance.png`: 종목별 성과 분석
  - `stock_performance.csv`: 종목별 성과 데이터

## 🎯 최적화 전략

### 1. Grid Search
- θ_spike ∈ [1.5%, 3%]
- θ_15m ∈ [1%, 3%]
- θ_vol ∈ [3%, 10%]

### 2. Bayesian Optimization
- Optuna를 활용한 효율적 탐색
- 목표함수: Sharpe Ratio + Win Rate + Total Return

### 3. Walk-Forward Analysis
- 시계열 분할 검증
- 3개월 Training → 1개월 Testing

## ⚠️ 주의사항

1. **데이터 품질**: 1분봉 데이터의 정확성 확인
2. **과적합 방지**: 충분한 샘플 수 확보
3. **거래 비용**: 수수료, 슬리피지 고려
4. **리스크 관리**: 포지션 사이징 중요

## 🔍 문제 해결

### 거래가 발생하지 않는 경우
1. 파라미터를 더 관대하게 조정
2. 데이터 기간 확인
3. 종목 수 증가

### 성과가 좋지 않은 경우
1. 파라미터 최적화 실행
2. 시장 상황별 분석
3. 추가 필터 조건 검토

## 📞 지원

문제가 발생하거나 개선 사항이 있으면 이슈를 등록해주세요.

---

**핵심 가설**: "완만-상승" 패턴은 (i) 시초봉 과열 미발생 + (ii) 15분 누적 우상향 + (iii) 실질 매수 거래량이 동시에 확인될 때, 당일 실현 수익률 기대값이 가장 높다. 