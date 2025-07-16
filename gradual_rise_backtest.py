import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class GradualRiseBacktest:
    """
    완만 상승 패턴 백테스트 시스템
    
    핵심 조건:
    1. Opening Spike 제외 (첫 1분 급등)
    2. Gradual Rise 확인 (15분 누적 상승)
    3. Volume Confirmation (거래량 확인)
    4. ORB Delay (30분 이내 고가 돌파)
    """
    
    def __init__(self, data_path="minute_data"):
        self.data_path = data_path
        self.results = []
        self.parameters = {
            'theta_spike': 0.03,      # 첫 1분 수익률 임계값 (3%)
            'theta_spike_low': 0.001,  # 첫 1분 최소 수익률 (0.1%)
            'theta_15m': 0.005,       # 15분 누적 수익률 임계값 (0.5%)
            'theta_vol': 0.05,        # 거래량 비율 임계값 (5%)
            'theta_pull': 0.05,       # 저점 하락 임계값 (5%) - 더 관대하게
            'tp_pct': 0.04,           # 익절 수익률 (4%)
            'sl_pct': 0.02,           # 손절 수익률 (2%)
            'orb_delay_min': 5,       # ORB 진입 최소 대기시간 (분)
            'orb_max_min': 30         # ORB 진입 최대 대기시간 (분)
        }
    
    def load_data(self, stock_codes=None, date_range=None):
        """1분봉 데이터 로드 (기간 필터링 지원)"""
        print("데이터 로딩 중...")
        
        all_data = []
        import pandas as pd
        csv_files = glob.glob(os.path.join(self.data_path, "*_1min.csv"))
        
        if stock_codes:
            csv_files = [f for f in csv_files if any(code in f for code in stock_codes)]
        
        for file_path in csv_files:
            try:
                stock_code = os.path.basename(file_path).split('_')[0]
                df = pd.read_csv(file_path)
                df['stock_code'] = stock_code
                df['datetime'] = pd.to_datetime(df['datetime'])
                df['date'] = df['datetime'].dt.date
                df['time'] = df['datetime'].dt.time
                
                # 거래일별로 정렬
                df = df.sort_values(['date', 'time'])
                
                # 기간 필터링
                if date_range is not None:
                    start, end = date_range
                    df = df[(df['date'] >= pd.to_datetime(start).date()) & (df['date'] <= pd.to_datetime(end).date())]
                
                all_data.append(df)
                print(f"로드 완료: {stock_code} ({len(df)} rows)")
                
            except Exception as e:
                print(f"에러 - {file_path}: {e}")
                continue
        
        if not all_data:
            raise ValueError("로드된 데이터가 없습니다.")
        
        self.data = pd.concat(all_data, ignore_index=True)
        print(f"총 {len(self.data)} rows, {self.data['stock_code'].nunique()} 종목 로드 완료")
        
        return self.data
    
    def calculate_features(self, df):
        """Feature Engineering (변동성, 시장상황 feature 추가: KOSPI 일별 수익률/변동성)"""
        import pandas as pd
        import os
        # KOSPI 일별 데이터 로드 (최초 1회만)
        kospi_path = os.path.join('data_collection', 'market_data', 'KOSPI_daily.csv')
        kospi_df = pd.read_csv(kospi_path)
        kospi_df['date'] = pd.to_datetime(kospi_df['date']).dt.date
        kospi_df = kospi_df.sort_values('date')
        kospi_df['prev_close'] = kospi_df['close'].shift(1)
        kospi_df['kospi_return'] = (kospi_df['close'] / kospi_df['prev_close']) - 1
        kospi_df['kospi_volatility'] = (kospi_df['high'] - kospi_df['low']) / kospi_df['prev_close']
        kospi_map = kospi_df.set_index('date')[['kospi_return', 'kospi_volatility']].to_dict('index')

        features = []
        
        for (stock_code, date), day_df in df.groupby(['stock_code', 'date']):
            if len(day_df) < 30:  # 최소 30분 데이터 필요
                continue
                
            # 기본 정보
            open_price = day_df.iloc[0]['open']
            close_1min = day_df.iloc[0]['close']
            
            # 1. 첫 1분 수익률
            r_1 = (close_1min / open_price) - 1
            
            # 2. 15분 누적 수익률
            if len(day_df) >= 15:
                close_15min = day_df.iloc[14]['close']
                cum_r_15 = (close_15min / open_price) - 1
            else:
                cum_r_15 = np.nan
            
            # 3. 거래량 비율 (전일 대비)
            volume_15min = day_df.iloc[:15]['volume'].sum()
            
            # 4. 15분간 저점 하락폭
            high_15min = day_df.iloc[:15]['high'].max()
            low_15min = day_df.iloc[:15]['low'].min()
            max_drawdown_15 = (low_15min / high_15min) - 1
            
            # 5. 선형 회귀 기울기 (15분)
            if len(day_df) >= 15:
                x = np.arange(15)
                y = day_df.iloc[:15]['close'].values
                slope_15 = np.polyfit(x, y, 1)[0] / open_price  # 정규화된 기울기
            else:
                slope_15 = np.nan
            
            # 6. Higher-Low Score
            if len(day_df) >= 15:
                closes = day_df.iloc[:15]['close'].values
                sma_5 = pd.Series(closes).rolling(5).mean().values
                hl_score = np.sum(closes[4:] > sma_5[3:-1]) / 11  # 5분 이후부터 계산
            else:
                hl_score = np.nan
            
            # 7. VWAP Gap
            if len(day_df) >= 15:
                vwap_15 = (day_df.iloc[:15]['close'] * day_df.iloc[:15]['volume']).sum() / volume_15min
                vwap_gap = (close_15min - vwap_15) / vwap_15
            else:
                vwap_gap = np.nan
            
            # 8. 변동성 (15분 high-low)
            volatility_15 = high_15min - low_15min
            
            # 9. 시장상황 (KOSPI 일별 수익률/변동성)
            kospi_return_15 = 0
            kospi_volatility_15 = 0
            if date in kospi_map:
                kospi_return_15 = kospi_map[date]['kospi_return']
                kospi_volatility_15 = kospi_map[date]['kospi_volatility']
            
            features.append({
                'stock_code': stock_code,
                'date': date,
                'open_price': open_price,
                'r_1': r_1,
                'cum_r_15': cum_r_15,
                'volume_15min': volume_15min,
                'max_drawdown_15': max_drawdown_15,
                'slope_15': slope_15,
                'hl_score': hl_score,
                'vwap_gap': vwap_gap,
                'volatility_15': volatility_15,
                'kospi_return_15': kospi_return_15,
                'kospi_volatility_15': kospi_volatility_15,
                'day_data': day_df
            })
        
        return pd.DataFrame(features)
    
    def apply_filters(self, features_df):
        """패턴 필터 적용"""
        filtered = features_df.copy()
        
        # 1. Opening Spike 제외
        spike_mask = filtered['r_1'] >= self.parameters['theta_spike']
        filtered = filtered[~spike_mask]
        print(f"Opening Spike 제외: {spike_mask.sum()} 건")
        
        # 2. 첫 1분 최소 수익률 확인
        min_r1_mask = filtered['r_1'] >= self.parameters['theta_spike_low']
        filtered = filtered[min_r1_mask]
        print(f"최소 수익률 필터: {len(filtered)} 건")
        
        # 3. 15분 누적 수익률 확인
        r15_mask = filtered['cum_r_15'] >= self.parameters['theta_15m']
        filtered = filtered[r15_mask]
        print(f"15분 누적 수익률 필터: {len(filtered)} 건")
        
        # 4. 저점 하락폭 확인
        pull_mask = filtered['max_drawdown_15'] >= -self.parameters['theta_pull']
        filtered = filtered[pull_mask]
        print(f"저점 하락폭 필터: {len(filtered)} 건")
        
        # 5. 거래량 확인 (임시로 제외 - 전일 데이터 필요)
        # volume_mask = filtered['volume_15min'] >= volume_threshold
        # filtered = filtered[volume_mask]
        
        return filtered
    
    def find_orb_entries(self, filtered_df):
        """ORB 진입점 찾기"""
        entries = []
        
        for _, row in filtered_df.iterrows():
            day_df = row['day_data']
            
            # ORB High 계산 (첫 5분 고가)
            orb_high = day_df.iloc[:self.parameters['orb_delay_min']]['high'].max()
            
            # ORB 돌파 지점 찾기 (5분 이후 ~ 30분)
            entry_window = day_df.iloc[self.parameters['orb_delay_min']:self.parameters['orb_max_min']]
            
            for idx, bar in entry_window.iterrows():
                if bar['high'] > orb_high:
                    # 진입가: 다음 봉 시가 (보수적)
                    entry_price = bar['open']
                    entry_time = bar['datetime']
                    
                    # TP/SL 계산
                    tp_price = entry_price * (1 + self.parameters['tp_pct'])
                    sl_price = entry_price * (1 - self.parameters['sl_pct'])
                    
                    entries.append({
                        'stock_code': row['stock_code'],
                        'date': row['date'],
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price,
                        'orb_high': orb_high,
                        'features': row
                    })
                    break  # 첫 번째 돌파에서 진입
        
        return pd.DataFrame(entries)
    
    def simulate_trades(self, entries_df):
        """거래 시뮬레이션 (수수료/슬리피지 반영)"""
        trades = []
        commission = 0.001  # 0.1%
        slippage = 0.001    # 0.1%
        
        for _, entry in entries_df.iterrows():
            stock_code = entry['stock_code']
            date = entry['date']
            entry_time = entry['entry_time']
            
            # 해당 일의 데이터 가져오기
            day_data = entry['features']['day_data']
            
            # 진입 시점 이후 데이터
            entry_idx = day_data[day_data['datetime'] >= entry_time].index[0]
            remaining_data = day_data.loc[entry_idx:]
            
            # 진입/청산가에 슬리피지 반영
            entry_price = entry['entry_price'] * (1 + slippage)
            tp_price = entry['tp_price'] * (1 - slippage)
            sl_price = entry['sl_price'] * (1 - slippage)
            
            # 청산 조건 확인
            exit_price = None
            exit_time = None
            exit_reason = None
            
            for _, bar in remaining_data.iterrows():
                # TP 도달
                if bar['high'] >= tp_price:
                    exit_price = tp_price
                    exit_time = bar['datetime']
                    exit_reason = 'TP'
                    break
                
                # SL 도달
                if bar['low'] <= sl_price:
                    exit_price = sl_price
                    exit_time = bar['datetime']
                    exit_reason = 'SL'
                    break
            
            # 종가 청산 (TP/SL 미도달)
            if exit_price is None:
                exit_price = remaining_data.iloc[-1]['close'] * (1 - slippage)
                exit_time = remaining_data.iloc[-1]['datetime']
                exit_reason = 'Close'
            
            # 수수료 반영 (진입+청산)
            pnl = (exit_price / entry_price) - 1 - 2 * commission
            
            trades.append({
                'stock_code': stock_code,
                'date': date,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': exit_reason
            })
        
        return pd.DataFrame(trades)
    
    def calculate_metrics(self, trades_df):
        """성과 지표 계산"""
        if len(trades_df) == 0:
            return {}
        
        metrics = {
            'total_trades': len(trades_df),
            'win_rate': (trades_df['pnl'] > 0).mean(),
            'avg_return': trades_df['pnl'].mean(),
            'std_return': trades_df['pnl'].std(),
            'sharpe_ratio': trades_df['pnl'].mean() / trades_df['pnl'].std() if trades_df['pnl'].std() > 0 else 0,
            'max_drawdown': trades_df['pnl'].cumsum().min(),
            'total_return': trades_df['pnl'].sum(),
            'expectancy': trades_df['pnl'].mean() * len(trades_df),
            'best_trade': trades_df['pnl'].max(),
            'worst_trade': trades_df['pnl'].min()
        }
        
        return metrics
    
    def run_backtest(self, stock_codes=None, date_range=None):
        """전체 백테스트 실행 (기간 필터링 지원)"""
        print("=== 완만 상승 패턴 백테스트 시작 ===")
        
        # 1. 데이터 로드
        data = self.load_data(stock_codes, date_range=date_range)
        
        # 2. Feature 계산
        print("\nFeature 계산 중...")
        features = self.calculate_features(data)
        print(f"Feature 계산 완료: {len(features)} 일")
        
        # 3. 필터 적용
        print("\n패턴 필터 적용 중...")
        filtered = self.apply_filters(features)
        print(f"필터 적용 완료: {len(filtered)} 건")
        
        # 4. ORB 진입점 찾기
        print("\nORB 진입점 탐색 중...")
        entries = self.find_orb_entries(filtered)
        print(f"진입점 발견: {len(entries)} 건")
        
        # 5. 거래 시뮬레이션
        print("\n거래 시뮬레이션 중...")
        trades = self.simulate_trades(entries)
        print(f"거래 완료: {len(trades)} 건")
        
        # 6. 성과 지표 계산
        print("\n성과 지표 계산 중...")
        metrics = self.calculate_metrics(trades)
        
        # 7. 결과 출력
        self.print_results(metrics, trades)
        
        return metrics, trades
    
    def print_results(self, metrics, trades_df):
        """결과 출력"""
        print("\n" + "="*50)
        print("백테스트 결과")
        print("="*50)
        
        if len(trades_df) == 0:
            print("거래가 없습니다.")
            return
        
        print(f"총 거래 수: {metrics['total_trades']}")
        print(f"승률: {metrics['win_rate']:.2%}")
        print(f"평균 수익률: {metrics['avg_return']:.2%}")
        print(f"총 수익률: {metrics['total_return']:.2%}")
        print(f"샤프 비율: {metrics['sharpe_ratio']:.3f}")
        print(f"최대 손실: {metrics['max_drawdown']:.2%}")
        print(f"기대값: {metrics['expectancy']:.2%}")
        print(f"최고 수익: {metrics['best_trade']:.2%}")
        print(f"최저 수익: {metrics['worst_trade']:.2%}")
        
        # 월별 성과
        if len(trades_df) > 0:
            trades_df['date'] = pd.to_datetime(trades_df['date'])
            trades_df['month'] = trades_df['date'].dt.to_period('M')
            monthly_perf = trades_df.groupby('month')['pnl'].sum()
            print(f"\n월별 성과:")
            for month, pnl in monthly_perf.items():
                print(f"  {month}: {pnl:.2%}")

def main():
    """메인 실행 함수"""
    # 백테스트 인스턴스 생성
    backtest = GradualRiseBacktest()
    
    # 파라미터 설정 (필요시 조정)
    backtest.parameters.update({
        'theta_spike': 0.02,      # 2%
        'theta_15m': 0.015,       # 1.5%
        'theta_vol': 0.05,        # 5%
        'tp_pct': 0.04,           # 4%
        'sl_pct': 0.02,           # 2%
    })
    
    # 백테스트 실행
    metrics, trades = backtest.run_backtest()
    
    # 결과 저장
    if len(trades) > 0:
        trades.to_csv('gradual_rise_trades.csv', index=False)
        print(f"\n거래 내역이 'gradual_rise_trades.csv'에 저장되었습니다.")

if __name__ == "__main__":
    main() 