"""
Simple News Backtest
뉴스 데이터를 사용한 간단한 백테스트 프로그램
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleNewsBacktest:
    """간단한 뉴스 기반 백테스트"""
    
    def __init__(self, news_data_file: str):
        """
        백테스트 초기화
        
        Args:
            news_data_file: 뉴스 데이터 파일 경로 (CSV 또는 JSON)
        """
        self.news_data = self.load_news_data(news_data_file)
        self.results = []
        self.portfolio_value = 1000000  # 초기 자본 100만원
        self.initial_capital = self.portfolio_value
        
    def load_news_data(self, file_path: str) -> pd.DataFrame:
        """뉴스 데이터 로드"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                raise ValueError("지원하지 않는 파일 형식입니다. CSV 또는 JSON 파일을 사용하세요.")
            
            # 날짜 컬럼을 datetime으로 변환
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            logger.info(f"뉴스 데이터 로드 완료: {len(df)}개 뉴스")
            return df
            
        except Exception as e:
            logger.error(f"뉴스 데이터 로드 실패: {e}")
            raise
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        간단한 감정 분석
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            감정 분석 결과 (긍정, 부정, 중립 점수)
        """
        if not text or pd.isna(text):
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        text = str(text).lower()
        
        # 긍정 키워드
        positive_keywords = [
            '상승', '급등', '호재', '실적개선', '성장', '확대', '진출', '수주', '계약',
            '승인', '허가', '개발성공', '특허', '신제품', '해외진출', '수익증가',
            '매수', '투자', '기대', '전망', '긍정', '좋음', '강세'
        ]
        
        # 부정 키워드
        negative_keywords = [
            '하락', '급락', '악재', '실적악화', '손실', '축소', '철수', '계약해지',
            '반대', '거부', '개발실패', '특허무효', '리콜', '해외철수', '수익감소',
            '매도', '매도세', '부정', '나쁨', '약세', '위험'
        ]
        
        # 키워드 카운트
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        positive_score = positive_count / total_keywords
        negative_score = negative_count / total_keywords
        neutral_score = 1.0 - positive_score - negative_score
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }
    
    def get_daily_sentiment(self, date: datetime) -> Dict[str, float]:
        """특정 날짜의 전체 감정 분석"""
        daily_news = self.news_data[self.news_data['date'].dt.date == date.date()]
        
        if len(daily_news) == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        # 모든 뉴스의 감정 분석
        sentiments = []
        for _, news in daily_news.iterrows():
            title_sentiment = self.analyze_sentiment(news.get('title', ''))
            content_sentiment = self.analyze_sentiment(news.get('content', ''))
            
            # 제목과 본문의 가중 평균 (제목에 더 높은 가중치)
            combined_sentiment = {
                'positive': (title_sentiment['positive'] * 0.7 + content_sentiment['positive'] * 0.3),
                'negative': (title_sentiment['negative'] * 0.7 + content_sentiment['negative'] * 0.3),
                'neutral': (title_sentiment['neutral'] * 0.7 + content_sentiment['neutral'] * 0.3)
            }
            sentiments.append(combined_sentiment)
        
        # 일일 평균 감정 계산
        avg_sentiment = {
            'positive': np.mean([s['positive'] for s in sentiments]),
            'negative': np.mean([s['negative'] for s in sentiments]),
            'neutral': np.mean([s['neutral'] for s in sentiments])
        }
        
        return avg_sentiment
    
    def generate_signal(self, sentiment: Dict[str, float]) -> str:
        """
        감정 분석을 기반으로 매매 신호 생성
        
        Args:
            sentiment: 감정 분석 결과
        
        Returns:
            매매 신호 ('buy', 'sell', 'hold')
        """
        positive_threshold = 0.6
        negative_threshold = 0.6
        
        if sentiment['positive'] > positive_threshold:
            return 'buy'
        elif sentiment['negative'] > negative_threshold:
            return 'sell'
        else:
            return 'hold'
    
    def simulate_trading(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        거래 시뮬레이션 실행
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
        
        Returns:
            백테스트 결과 DataFrame
        """
        # 날짜 범위 설정
        if start_date:
            start_dt = pd.to_datetime(start_date)
            self.news_data = self.news_data[self.news_data['date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            self.news_data = self.news_data[self.news_data['date'] <= end_dt]
        
        # 고유한 날짜 목록
        unique_dates = sorted(self.news_data['date'].dt.date.unique())
        
        logger.info(f"백테스트 시작: {len(unique_dates)}일간")
        
        position = 0  # 0: 현금, 1: 주식 보유
        buy_price = 0
        trades = []
        
        for date in unique_dates:
            # 해당 날짜의 감정 분석
            sentiment = self.get_daily_sentiment(pd.to_datetime(date))
            signal = self.generate_signal(sentiment)
            
            # 가상 주가 (감정 점수 기반)
            # 실제로는 실제 주가 데이터를 사용해야 함
            virtual_price = 10000 + (sentiment['positive'] - sentiment['negative']) * 1000
            
            # 거래 로직
            if signal == 'buy' and position == 0:
                # 매수
                position = 1
                buy_price = virtual_price
                shares = self.portfolio_value / buy_price
                self.portfolio_value = 0
                trades.append({
                    'date': date,
                    'action': 'buy',
                    'price': buy_price,
                    'sentiment': sentiment,
                    'signal': signal,
                    'portfolio_value': shares * buy_price
                })
                
            elif signal == 'sell' and position == 1:
                # 매도
                position = 0
                sell_price = virtual_price
                shares = self.portfolio_value / buy_price
                self.portfolio_value = shares * sell_price
                trades.append({
                    'date': date,
                    'action': 'sell',
                    'price': sell_price,
                    'sentiment': sentiment,
                    'signal': signal,
                    'portfolio_value': self.portfolio_value
                })
            
            # 포지션 유지 중인 경우
            elif position == 1:
                shares = self.portfolio_value / buy_price
                current_value = shares * virtual_price
                trades.append({
                    'date': date,
                    'action': 'hold',
                    'price': virtual_price,
                    'sentiment': sentiment,
                    'signal': signal,
                    'portfolio_value': current_value
                })
            else:
                trades.append({
                    'date': date,
                    'action': 'hold',
                    'price': virtual_price,
                    'sentiment': sentiment,
                    'signal': signal,
                    'portfolio_value': self.portfolio_value
                })
        
        # 결과 DataFrame 생성
        results_df = pd.DataFrame(trades)
        results_df['date'] = pd.to_datetime(results_df['date'])
        
        # 수익률 계산
        results_df['return'] = (results_df['portfolio_value'] - self.initial_capital) / self.initial_capital * 100
        
        self.results = results_df
        return results_df
    
    def calculate_metrics(self) -> Dict[str, float]:
        """백테스트 성과 지표 계산"""
        if len(self.results) == 0:
            return {}
        
        # 최종 수익률
        final_return = (self.results['portfolio_value'].iloc[-1] - self.initial_capital) / self.initial_capital * 100
        
        # 최대 낙폭
        cumulative_returns = (self.results['portfolio_value'] - self.initial_capital) / self.initial_capital
        max_drawdown = (cumulative_returns - cumulative_returns.expanding().max()).min() * 100
        
        # 거래 횟수
        trade_count = len(self.results[self.results['action'].isin(['buy', 'sell'])])
        
        # 승률 (간단한 계산)
        if trade_count > 0:
            profitable_trades = len(self.results[self.results['return'] > 0])
            win_rate = profitable_trades / len(self.results) * 100
        else:
            win_rate = 0
        
        return {
            'final_return_pct': final_return,
            'max_drawdown_pct': max_drawdown,
            'trade_count': trade_count,
            'win_rate_pct': win_rate,
            'initial_capital': self.initial_capital,
            'final_capital': self.results['portfolio_value'].iloc[-1]
        }
    
    def plot_results(self, save_path: str = None):
        """백테스트 결과 시각화"""
        if len(self.results) == 0:
            logger.warning("시각화할 결과가 없습니다.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 포트폴리오 가치 변화
        axes[0, 0].plot(self.results['date'], self.results['portfolio_value'])
        axes[0, 0].set_title('포트폴리오 가치 변화')
        axes[0, 0].set_ylabel('포트폴리오 가치 (원)')
        axes[0, 0].grid(True)
        
        # 2. 수익률 변화
        axes[0, 1].plot(self.results['date'], self.results['return'])
        axes[0, 1].set_title('수익률 변화')
        axes[0, 1].set_ylabel('수익률 (%)')
        axes[0, 1].grid(True)
        
        # 3. 감정 점수 변화
        sentiment_data = pd.DataFrame([
            {
                'date': row['date'],
                'positive': row['sentiment']['positive'],
                'negative': row['sentiment']['negative'],
                'neutral': row['sentiment']['neutral']
            }
            for _, row in self.results.iterrows()
        ])
        
        axes[1, 0].plot(sentiment_data['date'], sentiment_data['positive'], label='긍정', color='green')
        axes[1, 0].plot(sentiment_data['date'], sentiment_data['negative'], label='부정', color='red')
        axes[1, 0].plot(sentiment_data['date'], sentiment_data['neutral'], label='중립', color='gray')
        axes[1, 0].set_title('감정 점수 변화')
        axes[1, 0].set_ylabel('감정 점수')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # 4. 거래 신호
        signal_counts = self.results['signal'].value_counts()
        axes[1, 1].pie(signal_counts.values, labels=signal_counts.index, autopct='%1.1f%%')
        axes[1, 1].set_title('거래 신호 분포')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"차트 저장 완료: {save_path}")
        
        plt.show()
    
    def save_results(self, filename: str):
        """백테스트 결과 저장"""
        try:
            # 결과 데이터 저장
            self.results.to_csv(filename, index=False, encoding='utf-8-sig')
            
            # 성과 지표 저장
            metrics = self.calculate_metrics()
            metrics_filename = filename.replace('.csv', '_metrics.json')
            with open(metrics_filename, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
            
            logger.info(f"백테스트 결과 저장 완료: {filename}, {metrics_filename}")
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")

def main():
    """메인 실행 함수"""
    # 뉴스 데이터 파일 경로 (크롤링 결과 파일)
    news_file = "naver_news_1year_20241201_120000.csv"  # 실제 파일명으로 변경
    
    try:
        # 백테스트 실행
        backtest = SimpleNewsBacktest(news_file)
        
        # 6개월 백테스트 (예시)
        results = backtest.simulate_trading(
            start_date="2024-06-01",
            end_date="2024-12-01"
        )
        
        # 성과 지표 계산
        metrics = backtest.calculate_metrics()
        print("\n=== 백테스트 결과 ===")
        for key, value in metrics.items():
            print(f"{key}: {value}")
        
        # 결과 시각화
        backtest.plot_results("backtest_results.png")
        
        # 결과 저장
        backtest.save_results("backtest_results.csv")
        
    except FileNotFoundError:
        logger.error(f"뉴스 데이터 파일을 찾을 수 없습니다: {news_file}")
        logger.info("먼저 simple_naver_crawler.py를 실행하여 뉴스 데이터를 수집하세요.")
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")

if __name__ == "__main__":
    main() 