"""
Analyze Yesterday Stocks
어제 수집된 뉴스 데이터를 분석해서 의미 있는 주식들을 찾는 프로그램
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import logging
from collections import Counter

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockAnalyzer:
    """주식 분석기"""
    
    def __init__(self):
        # 주요 주식 키워드 (종목명, 기업명)
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
            '한국전력', '한국가스공사', 'GS칼텍스', 'S-OIL', 'SK이노베이션',
            # 추가 주식들
            'LG전자', '삼성전기', '삼성화재', '한화에어로스페이스', '두산에너빌리티',
            '현대중공업', '두산인프라코어', '한화시스템', 'LIG넥스원',
            'CJ제일제당', '농심', '오리온', '롯데칠성', '동서', '롯데제과',
            '신세계', '이마트', '롯데쇼핑', '한진', '대한항공',
            '아시아나항공', '코웨이', 'LG생활건강', '아모레퍼시픽',
            'SK바이오팜', '셀트리온', '한미약품', '유한양행', '동국제약',
            '대우건설', 'GS건설', '롯데건설', '포스코건설', '현대건설',
            '한국전력', '한국가스공사', 'GS칼텍스', 'S-OIL'
        ]
        
        # 감정 분석 키워드
        self.positive_keywords = [
            '상승', '급등', '호재', '실적개선', '성장', '확대', '진출', '수주', '계약',
            '승인', '허가', '개발성공', '특허', '신제품', '해외진출', '수익증가',
            '매수', '투자', '기대', '전망', '긍정', '좋음', '강세', '돌파',
            '상향', '증가', '개선', '회복', '반등', '상승세', '호조', '성장세',
            '돌파', '상승', '강세', '호조', '개선', '증가', '성장', '확대'
        ]
        
        self.negative_keywords = [
            '하락', '급락', '악재', '실적악화', '손실', '축소', '철수', '계약해지',
            '반대', '거부', '개발실패', '특허무효', '리콜', '해외철수', '수익감소',
            '매도', '매도세', '부정', '나쁨', '약세', '위험', '하향', '감소',
            '악화', '손실', '폭락', '하락세', '약세', '부진', '실패', '실적부진',
            '하락', '약세', '부진', '감소', '악화', '손실', '폭락'
        ]
    
    def load_news_data(self, filename: str) -> pd.DataFrame:
        """뉴스 데이터 로드"""
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename)
            elif filename.endswith('.json'):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                raise ValueError("지원하지 않는 파일 형식입니다.")
            
            logger.info(f"뉴스 데이터 로드 완료: {len(df)}개")
            return df
            
        except Exception as e:
            logger.error(f"뉴스 데이터 로드 실패: {e}")
            raise
    
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
    
    def analyze_news_with_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """뉴스에서 주식 언급과 감정 분석"""
        results = []
        
        for _, news in df.iterrows():
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
    
    def get_significant_stocks(self, df: pd.DataFrame, min_mentions: int = 1) -> pd.DataFrame:
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
        
        # 중립적인 주식들
        neutral_stocks = stock_stats[stock_stats['dominant_sentiment'] == 'neutral'].head(5)
        if len(neutral_stocks) > 0:
            print(f"\n=== ➡️ 중립적인 주식 TOP 5 ===")
            for i, (stock, row) in enumerate(neutral_stocks.iterrows(), 1):
                print(f"{i}. {stock} (언급: {row['mention_count']}회, 중립점수: {row['avg_neutral']:.3f})")
    
    def print_news_summary(self, df: pd.DataFrame):
        """뉴스 요약 출력"""
        print(f"\n=== 📰 뉴스 요약 ===")
        print(f"총 뉴스 수: {len(df)}개")
        
        # 출처별 분포
        source_counts = df['source'].value_counts()
        print(f"\n출처별 분포:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}개")
        
        # 첫 번째 뉴스들 미리보기
        print(f"\n=== 첫 번째 뉴스들 미리보기 ===")
        for i, (_, news) in enumerate(df.head(3).iterrows(), 1):
            print(f"\n{i}. {news['title']}")
            print(f"   출처: {news['source']}")
            print(f"   본문 길이: {len(news['content'])}자")
            if len(news['content']) > 100:
                print(f"   요약: {news['content'][:100]}...")

def main():
    """메인 실행 함수"""
    analyzer = StockAnalyzer()
    
    # 어제 수집된 뉴스 파일
    news_file = "improved_naver_stock_2025-07-16_20250716_093200.csv"
    
    try:
        print(f"=== {news_file} 분석 시작 ===")
        
        # 1. 뉴스 데이터 로드
        print("1. 뉴스 데이터 로드 중...")
        news_df = analyzer.load_news_data(news_file)
        
        # 2. 뉴스 요약 출력
        analyzer.print_news_summary(news_df)
        
        # 3. 주식 언급 및 감정 분석
        print("\n2. 주식 언급 및 감정 분석 중...")
        analysis_df = analyzer.analyze_news_with_stocks(news_df)
        
        if len(analysis_df) == 0:
            print("주식이 언급된 뉴스가 없습니다.")
            return
        
        # 4. 의미 있는 주식 추출
        print("3. 의미 있는 주식 추출 중...")
        stock_stats = analyzer.get_significant_stocks(analysis_df, min_mentions=1)
        
        # 5. 결과 출력
        analyzer.print_analysis_results(analysis_df, stock_stats)
        
        # 6. 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        analysis_df.to_csv(f"stock_analysis_{timestamp}.csv", index=False, encoding='utf-8-sig')
        stock_stats.to_csv(f"stock_stats_{timestamp}.csv", encoding='utf-8-sig')
        
        print(f"\n=== 분석 완료 ===")
        print(f"분석 결과 저장: stock_analysis_{timestamp}.csv")
        print(f"주식 통계 저장: stock_stats_{timestamp}.csv")
        
    except FileNotFoundError:
        print(f"뉴스 파일을 찾을 수 없습니다: {news_file}")
        print("먼저 improved_naver_crawler.py를 실행하여 뉴스 데이터를 수집하세요.")
    except Exception as e:
        print(f"분석 실패: {e}")
        logger.error(f"분석 실패: {e}")

if __name__ == "__main__":
    main() 