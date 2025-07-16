import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class AnalysisVisualizer:
    """백테스트 결과 분석 및 시각화 클래스"""
    
    def __init__(self):
        self.trades_df = None
        self.metrics = None
    
    def load_trades(self, file_path):
        """거래 데이터 로드"""
        self.trades_df = pd.read_csv(file_path)
        self.trades_df['date'] = pd.to_datetime(self.trades_df['date'])
        self.trades_df['entry_time'] = pd.to_datetime(self.trades_df['entry_time'])
        self.trades_df['exit_time'] = pd.to_datetime(self.trades_df['exit_time'])
        
        print(f"거래 데이터 로드 완료: {len(self.trades_df)} 건")
        return self.trades_df
    
    def calculate_metrics(self):
        """성과 지표 계산"""
        if self.trades_df is None or len(self.trades_df) == 0:
            return {}
        
        metrics = {
            'total_trades': len(self.trades_df),
            'win_rate': (self.trades_df['pnl'] > 0).mean(),
            'avg_return': self.trades_df['pnl'].mean(),
            'std_return': self.trades_df['pnl'].std(),
            'sharpe_ratio': self.trades_df['pnl'].mean() / self.trades_df['pnl'].std() if self.trades_df['pnl'].std() > 0 else 0,
            'max_drawdown': self.trades_df['pnl'].cumsum().min(),
            'total_return': self.trades_df['pnl'].sum(),
            'expectancy': self.trades_df['pnl'].mean() * len(self.trades_df),
            'best_trade': self.trades_df['pnl'].max(),
            'worst_trade': self.trades_df['pnl'].min(),
            'avg_win': self.trades_df[self.trades_df['pnl'] > 0]['pnl'].mean(),
            'avg_loss': self.trades_df[self.trades_df['pnl'] < 0]['pnl'].mean(),
            'profit_factor': abs(self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum() / 
                               self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum()) if self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum() != 0 else np.inf
        }
        
        self.metrics = metrics
        return metrics
    
    def plot_cumulative_returns(self, save_path=None):
        """누적 수익률 및 최대 드로우다운 차트"""
        if self.trades_df is None:
            print("거래 데이터가 없습니다.")
            return
        
        # 거래별 누적 수익률 계산
        cumulative_returns = self.trades_df['pnl'].cumsum()
        # 최대 드로우다운 계산
        running_max = cumulative_returns.cummax()
        drawdown = cumulative_returns - running_max
        max_drawdown = drawdown.min()
        
        plt.figure(figsize=(12, 6))
        plt.plot(cumulative_returns.index, cumulative_returns.values, linewidth=2, color='blue', label='누적 수익률')
        plt.plot(drawdown.index, drawdown.values, color='red', linestyle='--', alpha=0.5, label='드로우다운')
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
        plt.title('누적 수익률 및 최대 드로우다운', fontsize=14, fontweight='bold')
        plt.xlabel('거래 순서')
        plt.ylabel('수익률')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # 최대 드로우다운 표시
        min_idx = drawdown.idxmin()
        plt.scatter(min_idx, drawdown.iloc[min_idx], color='red', s=100, zorder=5)
        plt.annotate(f'Max DD: {max_drawdown:.2%}', 
                    xy=(min_idx, drawdown.iloc[min_idx]), 
                    xytext=(min_idx+2, drawdown.iloc[min_idx]-0.05),
                    arrowprops=dict(arrowstyle='->', color='red'))
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_monthly_performance(self, save_path=None):
        """월별 성과 차트"""
        if self.trades_df is None:
            print("거래 데이터가 없습니다.")
            return
        
        # 월별 성과 계산
        self.trades_df['month'] = self.trades_df['date'].dt.to_period('M')
        monthly_perf = self.trades_df.groupby('month').agg({
            'pnl': ['sum', 'mean', 'count']
        }).round(4)
        monthly_perf.columns = ['total_return', 'avg_return', 'trade_count']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 월별 총 수익률
        monthly_perf['total_return'].plot(kind='bar', ax=ax1, color='skyblue')
        ax1.set_title('월별 총 수익률', fontsize=12, fontweight='bold')
        ax1.set_ylabel('총 수익률')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax1.grid(True, alpha=0.3)
        
        # 월별 거래 수
        monthly_perf['trade_count'].plot(kind='bar', ax=ax2, color='lightcoral')
        ax2.set_title('월별 거래 수', fontsize=12, fontweight='bold')
        ax2.set_ylabel('거래 수')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_return_distribution(self, save_path=None):
        """수익률 분포 히스토그램"""
        if self.trades_df is None:
            print("거래 데이터가 없습니다.")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 전체 수익률 분포
        ax1.hist(self.trades_df['pnl'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(self.trades_df['pnl'].mean(), color='red', linestyle='--', label=f'평균: {self.trades_df["pnl"].mean():.2%}')
        ax1.set_title('수익률 분포', fontsize=12, fontweight='bold')
        ax1.set_xlabel('수익률')
        ax1.set_ylabel('빈도')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 승/패 분포
        win_trades = self.trades_df[self.trades_df['pnl'] > 0]
        loss_trades = self.trades_df[self.trades_df['pnl'] < 0]
        
        ax2.hist(win_trades['pnl'], bins=20, alpha=0.7, color='green', label='승리', edgecolor='black')
        ax2.hist(loss_trades['pnl'], bins=20, alpha=0.7, color='red', label='손실', edgecolor='black')
        ax2.set_title('승/패 수익률 분포', fontsize=12, fontweight='bold')
        ax2.set_xlabel('수익률')
        ax2.set_ylabel('빈도')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_exit_reason_analysis(self, save_path=None):
        """청산 이유 분석"""
        if self.trades_df is None:
            print("거래 데이터가 없습니다.")
            return
        
        # 청산 이유별 통계
        exit_stats = self.trades_df.groupby('exit_reason').agg({
            'pnl': ['count', 'mean', 'sum']
        }).round(4)
        exit_stats.columns = ['count', 'avg_return', 'total_return']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 청산 이유별 거래 수
        exit_stats['count'].plot(kind='bar', ax=ax1, color='lightblue')
        ax1.set_title('청산 이유별 거래 수', fontsize=12, fontweight='bold')
        ax1.set_ylabel('거래 수')
        ax1.grid(True, alpha=0.3)
        
        # 청산 이유별 평균 수익률
        exit_stats['avg_return'].plot(kind='bar', ax=ax2, color='lightcoral')
        ax2.set_title('청산 이유별 평균 수익률', fontsize=12, fontweight='bold')
        ax2.set_ylabel('평균 수익률')
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        return exit_stats
    
    def plot_stock_performance(self, top_n=10, save_path=None):
        """종목별 성과 분석"""
        if self.trades_df is None:
            print("거래 데이터가 없습니다.")
            return
        
        # 종목별 성과 계산
        stock_perf = self.trades_df.groupby('stock_code').agg({
            'pnl': ['count', 'mean', 'sum']
        }).round(4)
        stock_perf.columns = ['trade_count', 'avg_return', 'total_return']
        
        # 거래 수 기준 상위 종목
        top_stocks = stock_perf.nlargest(top_n, 'trade_count')
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 거래 수 상위 종목
        top_stocks['trade_count'].plot(kind='bar', ax=ax1, color='skyblue')
        ax1.set_title(f'거래 수 상위 {top_n} 종목', fontsize=12, fontweight='bold')
        ax1.set_ylabel('거래 수')
        ax1.grid(True, alpha=0.3)
        
        # 수익률 상위 종목
        top_return_stocks = stock_perf.nlargest(top_n, 'total_return')
        top_return_stocks['total_return'].plot(kind='bar', ax=ax2, color='lightcoral')
        ax2.set_title(f'총 수익률 상위 {top_n} 종목', fontsize=12, fontweight='bold')
        ax2.set_ylabel('총 수익률')
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        return stock_perf
    
    def print_detailed_metrics(self):
        """상세 성과 지표 출력"""
        if self.metrics is None:
            self.calculate_metrics()
        
        print("="*60)
        print("상세 성과 지표")
        print("="*60)
        
        print(f"총 거래 수: {self.metrics['total_trades']}")
        print(f"승률: {self.metrics['win_rate']:.2%}")
        print(f"평균 수익률: {self.metrics['avg_return']:.2%}")
        print(f"수익률 표준편차: {self.metrics['std_return']:.2%}")
        print(f"샤프 비율: {self.metrics['sharpe_ratio']:.3f}")
        print(f"총 수익률: {self.metrics['total_return']:.2%}")
        print(f"최대 손실: {self.metrics['max_drawdown']:.2%}")
        print(f"기대값: {self.metrics['expectancy']:.2%}")
        print(f"최고 수익: {self.metrics['best_trade']:.2%}")
        print(f"최저 수익: {self.metrics['worst_trade']:.2%}")
        print(f"평균 승리: {self.metrics['avg_win']:.2%}")
        print(f"평균 손실: {self.metrics['avg_loss']:.2%}")
        print(f"수익 팩터: {self.metrics['profit_factor']:.2f}")
        
        # 월별 통계
        if len(self.trades_df) > 0:
            self.trades_df['month'] = self.trades_df['date'].dt.to_period('M')
            monthly_stats = self.trades_df.groupby('month').agg({
                'pnl': ['count', 'sum', 'mean']
            }).round(4)
            monthly_stats.columns = ['거래수', '총수익률', '평균수익률']
            
            print(f"\n월별 통계:")
            print(monthly_stats)
    
    def create_comprehensive_report(self, output_dir="analysis_results"):
        """종합 분석 리포트 생성"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 기본 지표 계산
        self.calculate_metrics()
        
        # 2. 차트 생성
        self.plot_cumulative_returns(f"{output_dir}/cumulative_returns.png")
        self.plot_monthly_performance(f"{output_dir}/monthly_performance.png")
        self.plot_return_distribution(f"{output_dir}/return_distribution.png")
        self.plot_exit_reason_analysis(f"{output_dir}/exit_reason_analysis.png")
        self.plot_stock_performance(save_path=f"{output_dir}/stock_performance.png")
        
        # 3. 상세 지표 출력
        self.print_detailed_metrics()
        
        # 4. 종목별 성과 저장
        stock_perf = self.plot_stock_performance()
        if stock_perf is not None:
            stock_perf.to_csv(f"{output_dir}/stock_performance.csv")
        
        print(f"\n분석 결과가 '{output_dir}' 폴더에 저장되었습니다.")

def main():
    """메인 실행 함수"""
    visualizer = AnalysisVisualizer()
    
    # 거래 데이터 로드 (파일명에 따라 수정)
    try:
        visualizer.load_trades('gradual_rise_trades.csv')
    except FileNotFoundError:
        try:
            visualizer.load_trades('optimized_trades.csv')
        except FileNotFoundError:
            print("거래 데이터 파일을 찾을 수 없습니다.")
            print("먼저 백테스트를 실행해주세요.")
            return
    
    # 종합 분석 리포트 생성
    visualizer.create_comprehensive_report()

if __name__ == "__main__":
    main() 