"""
Daily Financial News Analysis
어제 금융 뉴스를 수집하고 감정 분석으로 의미 있는 주식들을 찾는 프로그램
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import re
from collections import Counter
import logging

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_naver_crawler import SimpleNaverCrawler

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DailyNewsAnalyzer:
    """일일 뉴스 분석기"""
    
    def __init__(self):
        self.crawler = SimpleNaverCrawler()
        
        # 주식 관련 키워드 (종목명, 기업명)
        self.stock_keywords = [
            '삼성전자', 'SK하이닉스', 'LG에너지솔루션', '삼성바이오로직스', 'NAVER', '카카오',
            '현대차', '기아', 'LG화학', 'POSCO홀딩스', '삼성SDI', 'LG전자', '현대모비스',
            'KB금융', '신한지주', '하나금융지주', '우리금융지주', 'NH투자증권', '미래에셋증권',
            '삼성생명', '교보생명', '한화생명', 'DB손해보험', '메리츠화재',
            'SK이노베이션', 'SK텔레콤', 'KT', 'LG유플러스', 'SK바이오팜',
            'CJ대한통운', '한국전력', 'GS건설', '롯데건설', '포스코퓨처엠',
            'LG디스플레이', '삼성전기', '삼성화재', '한화에어로스페이스', '두산에너빌리티',
            'LG유플러스', 'SK스퀘어', 'LG화학', '삼성물산', '롯데정보통신',
            '현대중공업', '두산인프라코어', '한화시스템', 'LIG넥스원', '한화에어로스페이스',
            'CJ제일제당', '농심', '오리온', '롯데칠성', '동서', '롯데제과',
            '신세계', '이마트', '롯데쇼핑', 'CJ대한통운', '한진', '대한항공',
            '아시아나항공', '코웨이', 'LG생활건강', '아모레퍼시픽', 'LG화학',
            'SK바이오팜', '셀트리온', '한미약품', '유한양행', '동국제약',
            '대우건설', 'GS건설', '롯데건설', '포스코건설', '현대건설',
            '한국전력', '한국가스공사', 'GS칼텍스', 'S-OIL', 'SK이노베이션'
        ]
        
        # 감정 분석 키워드
        self.positive_keywords = [
            '상승', '급등', '호재', '실적개선', '성장', '확대', '진출', '수주', '계약',
            '승인', '허가', '개발성공', '특허', '신제품', '해외진출', '수익증가',
            '매수', '투자', '기대', '전망', '긍정', '좋음', '강세', '돌파',
            '상향', '증가', '개선', '회복', '반등', '상승세', '호조', '성장세'
        ]
        
        self.negative_keywords = [
            '하락', '급락', '악재', '실적악화', '손실', '축소', '철수', '계약해지',
            '반대', '거부', '개발실패', '특허무효', '리콜', '해외철수', '수익감소',
            '매도', '매도세', '부정', '나쁨', '약세', '위험', '하향', '감소',
            '악화', '손실', '폭락', '하락세', '약세', '부진', '실패', '실적부진'
        ]
    
    def collect_yesterday_news(self, date_str: str = None) -> list:
        """어제 뉴스 수집"""
        if date_str is None:
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')
        
        logger.info(f"{date_str} 뉴스 수집 시작...")
        
        all_news = []
        
        # 경제, 주식, 기업 뉴스 수집
        categories = ['economy', 'stock', 'company']
        for category in categories:
            try:
                news_list = self.crawler.get_news_by_date(date_str, category)
                all_news.extend(news_list)
                logger.info(f"{category} 뉴스 {len(news_list)}개 수집 완료")
            except Exception as e:
                logger.error(f"{category} 뉴스 수집 실패: {e}")
        
        logger.info(f"총 {len(all_news)}개 뉴스 수집 완료")
        return all_news
    
    def extract_stock_mentions(self, text: str) -> list:
        """텍스트에서 주식 키워드 추출"""
        mentions = []
        for keyword in self.stock_keywords:
            if keyword in text:
                mentions.append(keyword)
        return mentions
    
    def analyze_sentiment(self, text: str) -> dict:
        """감정 분석"""
        if not text or pd.isna(text):
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        text = str(text).lower()
        
        # 키워드 카운트
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)
        
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
    
    def analyze_news_with_stocks(self, news_list: list) -> pd.DataFrame:
        """뉴스에서 주식 언급과 감정 분석"""
        results = []
        
        for news in news_list:
            # 제목과 본문 결합
            full_text = f"{news.get('title', '')} {news.get('content', '')}"
            
            # 주식 키워드 추출
            stock_mentions = self.extract_stock_mentions(full_text)
            
            if stock_mentions:  # 주식이 언급된 뉴스만 분석
                # 감정 분석
                sentiment = self.analyze_sentiment(full_text)
                
                for stock in stock_mentions:
                    results.append({
                        'date': news.get('date'),
                        'stock': stock,
                        'title': news.get('title', ''),
                        'source': news.get('source', ''),
                        'url': news.get('url', ''),
                        'positive_score': sentiment['positive'],
                        'negative_score': sentiment['negative'],
                        'neutral_score': sentiment['neutral'],
                        'sentiment_direction': 'positive' if sentiment['positive'] > sentiment['negative'] else 'negative' if sentiment['negative'] > sentiment['positive'] else 'neutral'
                    })
        
        return pd.DataFrame(results)
    
    def get_significant_stocks(self, df: pd.DataFrame, min_mentions: int = 2) -> pd.DataFrame:
        """의미 있는 주식들 추출"""
        if len(df) == 0:
            return pd.DataFrame()
        
        # 주식별 통계
        stock_stats = df.groupby('stock').agg({
            'positive_score': ['mean', 'sum'],
            'negative_score': ['mean', 'sum'],
            'neutral_score': 'mean',
            'sentiment_direction': lambda x: x.value_counts().index[0] if len(x) > 0 else 'neutral'
        }).round(3)
        
        # 컬럼명 정리
        stock_stats.columns = ['avg_positive', 'total_positive', 'avg_negative', 'total_negative', 'avg_neutral', 'dominant_sentiment']
        
        # 언급 횟수 추가
        mention_counts = df['stock'].value_counts()
        stock_stats['mention_count'] = mention_counts
        
        # 최소 언급 횟수 필터링
        significant_stocks = stock_stats[stock_stats['mention_count'] >= min_mentions]
        
        # 감정 점수 차이 계산
        significant_stocks['sentiment_diff'] = significant_stocks['avg_positive'] - significant_stocks['avg_negative']
        
        # 순위 매기기 (긍정 점수 높은 순)
        significant_stocks = significant_stocks.sort_values('avg_positive', ascending=False)
        
        return significant_stocks
    
    def print_analysis_results(self, df: pd.DataFrame, stock_stats: pd.DataFrame):
        """분석 결과 출력"""
        print(f"\n=== {df['date'].iloc[0] if len(df) > 0 else 'N/A'} 금융 뉴스 분석 결과 ===")
        print(f"총 뉴스 수: {len(df)}개")
        print(f"언급된 주식 수: {len(stock_stats)}개")
        
        if len(stock_stats) == 0:
            print("분석할 주식이 없습니다.")
            return
        
        print(f"\n=== 의미 있는 주식 TOP 10 ===")
        print("순위 | 종목명 | 언급횟수 | 평균긍정점수 | 평균부정점수 | 감정방향 | 감정차이")
        print("-" * 80)
        
        for i, (stock, row) in enumerate(stock_stats.head(10).iterrows(), 1):
            sentiment_emoji = "📈" if row['dominant_sentiment'] == 'positive' else "📉" if row['dominant_sentiment'] == 'negative' else "➡️"
            print(f"{i:2d} | {stock:12s} | {row['mention_count']:8d} | {row['avg_positive']:12.3f} | {row['avg_negative']:12.3f} | {sentiment_emoji} {row['dominant_sentiment']:8s} | {row['sentiment_diff']:8.3f}")
        
        # 긍정적인 주식들
        positive_stocks = stock_stats[stock_stats['dominant_sentiment'] == 'positive'].head(5)
        if len(positive_stocks) > 0:
            print(f"\n=== 📈 긍정적인 주식 TOP 5 ===")
            for i, (stock, row) in enumerate(positive_stocks.iterrows(), 1):
                print(f"{i}. {stock} (언급: {row['mention_count']}회, 긍정점수: {row['avg_positive']:.3f})")
        
        # 부정적인 주식들
        negative_stocks = stock_stats[stock_stats['dominant_sentiment'] == 'negative'].head(5)
        if len(negative_stocks) > 0:
            print(f"\n=== 📉 부정적인 주식 TOP 5 ===")
            for i, (stock, row) in enumerate(negative_stocks.iterrows(), 1):
                print(f"{i}. {stock} (언급: {row['mention_count']}회, 부정점수: {row['avg_negative']:.3f})")
    
    def save_results(self, df: pd.DataFrame, stock_stats: pd.DataFrame, date_str: str):
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 상세 데이터 저장
        detail_filename = f"daily_analysis_{date_str}_{timestamp}.csv"
        df.to_csv(detail_filename, index=False, encoding='utf-8-sig')
        
        # 주식 통계 저장
        stats_filename = f"stock_stats_{date_str}_{timestamp}.csv"
        stock_stats.to_csv(stats_filename, encoding='utf-8-sig')
        
        print(f"\n=== 결과 저장 완료 ===")
        print(f"상세 데이터: {detail_filename}")
        print(f"주식 통계: {stats_filename}")

def main():
    """메인 실행 함수"""
    analyzer = DailyNewsAnalyzer()
    
    # 어제 날짜 (2025-07-16)
    target_date = "2025-07-16"
    
    print(f"=== {target_date} 금융 뉴스 분석 시작 ===")
    
    try:
        # 1. 뉴스 수집
        print("1. 뉴스 수집 중...")
        news_list = analyzer.collect_yesterday_news(target_date)
        
        if not news_list:
            print("수집된 뉴스가 없습니다.")
            return
        
        # 2. 주식 언급 및 감정 분석
        print("2. 주식 언급 및 감정 분석 중...")
        analysis_df = analyzer.analyze_news_with_stocks(news_list)
        
        if len(analysis_df) == 0:
            print("주식이 언급된 뉴스가 없습니다.")
            return
        
        # 3. 의미 있는 주식 추출
        print("3. 의미 있는 주식 추출 중...")
        stock_stats = analyzer.get_significant_stocks(analysis_df, min_mentions=2)
        
        # 4. 결과 출력
        analyzer.print_analysis_results(analysis_df, stock_stats)
        
        # 5. 결과 저장
        analyzer.save_results(analysis_df, stock_stats, target_date)
        
    except Exception as e:
        print(f"분석 실패: {e}")
        logger.error(f"분석 실패: {e}")

if __name__ == "__main__":
    main() 