"""
스윙 트레이딩 뉴스 수집기
3-7일 보유 기간에 최적화된 뉴스 데이터 수집
"""

import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
from .naver_crawler import NaverNewsCrawler
from .config import SWING_TRADING_NEWS_CONFIG, SENTIMENT_CONFIG

logger = logging.getLogger(__name__)

class SwingNewsCollector:
    """스윙 트레이딩용 뉴스 수집기"""
    
    def __init__(self):
        self.crawler = NaverNewsCrawler(headless=True)
        self.config = SWING_TRADING_NEWS_CONFIG
        
    def collect_daily_news(self, days: int = 5) -> pd.DataFrame:
        """일간 매매 판단용 뉴스 수집 (전일 + 금일 새벽)"""
        logger.info(f"일간 매매용 뉴스 수집 시작: 최근 {days}일")
        
        all_news = []
        
        # 각 카테고리별로 수집
        categories = ["economy", "stock", "company"]
        
        for category in categories:
            try:
                if category == "economy":
                    news = self.crawler.crawl_economy_news(max_pages=3)
                elif category == "stock":
                    news = self.crawler.crawl_stock_news(max_pages=3)
                elif category == "company":
                    news = self.crawler.crawl_company_news(max_pages=3)
                
                all_news.extend(news)
                logger.info(f"{category} 뉴스: {len(news)}개 수집")
                
            except Exception as e:
                logger.error(f"{category} 뉴스 수집 실패: {e}")
                continue
        
        # DataFrame으로 변환
        df = pd.DataFrame(all_news)
        
        if not df.empty:
            # 타임스탬프 파싱
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            # 최근 N일 필터링
            cutoff_date = datetime.now().date() - timedelta(days=days)
            df = df[df['date'] >= cutoff_date]
            
            # 중복 제거
            df = df.drop_duplicates(subset=['url'])
            
            logger.info(f"일간 뉴스 수집 완료: {len(df)}개")
            
            # CSV 저장
            filename = f"swing_daily_news_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            logger.info(f"저장 완료: {filename}")
        
        return df
    
    def collect_trigger_news(self, days: int = 7) -> pd.DataFrame:
        """트리거 이벤트 탐색용 뉴스 수집 (3-7일치)"""
        logger.info(f"트리거 이벤트용 뉴스 수집 시작: 최근 {days}일")
        
        # 키워드 기반 필터링
        trigger_keywords = self.config["real_time"]["keywords"]
        
        df = self.collect_daily_news(days)
        
        if not df.empty:
            # 키워드 필터링
            filtered_news = []
            for _, row in df.iterrows():
                title_content = f"{row['title']} {row['content']}"
                
                # 키워드 매칭
                matched_keywords = []
                for keyword in trigger_keywords:
                    if keyword in title_content:
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    row_dict = row.to_dict()
                    row_dict['matched_keywords'] = ', '.join(matched_keywords)
                    row_dict['keyword_count'] = len(matched_keywords)
                    filtered_news.append(row_dict)
            
            if filtered_news:
                trigger_df = pd.DataFrame(filtered_news)
                trigger_df = trigger_df.sort_values('keyword_count', ascending=False)
                
                # CSV 저장
                filename = f"swing_trigger_news_{datetime.now().strftime('%Y%m%d')}.csv"
                trigger_df.to_csv(filename, index=False, encoding="utf-8-sig")
                logger.info(f"트리거 뉴스 저장 완료: {filename} ({len(trigger_df)}개)")
                
                return trigger_df
        
        return pd.DataFrame()
    
    def collect_trend_news(self, weeks: int = 2) -> pd.DataFrame:
        """전체 트렌드 분석용 뉴스 수집 (2-4주)"""
        logger.info(f"트렌드 분석용 뉴스 수집 시작: 최근 {weeks}주")
        
        days = weeks * 7
        df = self.collect_daily_news(days)
        
        if not df.empty:
            # 주차별 그룹핑
            df['week'] = df['timestamp'].dt.isocalendar().week
            df['year'] = df['timestamp'].dt.year
            
            # 카테고리별 통계
            category_stats = df.groupby('category').agg({
                'title': 'count',
                'timestamp': ['min', 'max']
            }).round(2)
            
            logger.info(f"카테고리별 통계:\n{category_stats}")
            
            # CSV 저장
            filename = f"swing_trend_news_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            logger.info(f"트렌드 뉴스 저장 완료: {filename}")
        
        return df
    
    def analyze_news_patterns(self, months: int = 1) -> Dict[str, Any]:
        """뉴스-주가 반응 패턴 분석 (1-3개월)"""
        logger.info(f"뉴스 패턴 분석 시작: 최근 {months}개월")
        
        days = months * 30
        df = self.collect_daily_news(days)
        
        if df.empty:
            return {}
        
        # 감정 분석
        positive_keywords = SENTIMENT_CONFIG["positive_keywords"]
        negative_keywords = SENTIMENT_CONFIG["negative_keywords"]
        
        sentiment_analysis = []
        
        for _, row in df.iterrows():
            title_content = f"{row['title']} {row['content']}"
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in title_content)
            negative_count = sum(1 for keyword in negative_keywords if keyword in title_content)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            sentiment_analysis.append({
                'title': row['title'],
                'category': row['category'],
                'sentiment': sentiment,
                'positive_score': positive_count,
                'negative_score': negative_count,
                'date': row['date']
            })
        
        sentiment_df = pd.DataFrame(sentiment_analysis)
        
        # 감정별 통계
        sentiment_stats = sentiment_df.groupby(['sentiment', 'category']).size().unstack(fill_value=0)
        
        # CSV 저장
        filename = f"swing_sentiment_analysis_{datetime.now().strftime('%Y%m%d')}.csv"
        sentiment_df.to_csv(filename, index=False, encoding="utf-8-sig")
        
        logger.info(f"감정 분석 완료: {filename}")
        logger.info(f"감정별 통계:\n{sentiment_stats}")
        
        return {
            'sentiment_df': sentiment_df,
            'sentiment_stats': sentiment_stats,
            'total_news': len(df)
        }
    
    def get_swing_recommendations(self) -> Dict[str, Any]:
        """스윙 트레이딩 추천 뉴스"""
        logger.info("스윙 트레이딩 추천 뉴스 분석 시작")
        
        # 1. 일간 뉴스 (최근 5일)
        daily_news = self.collect_daily_news(5)
        
        # 2. 트리거 뉴스 (최근 7일)
        trigger_news = self.collect_trigger_news(7)
        
        # 3. 감정 분석 (최근 1개월)
        sentiment_analysis = self.analyze_news_patterns(1)
        
        recommendations = {
            'daily_news_count': len(daily_news),
            'trigger_news_count': len(trigger_news),
            'top_triggers': trigger_news.head(10).to_dict('records') if not trigger_news.empty else [],
            'sentiment_summary': sentiment_analysis.get('sentiment_stats', {}),
            'recommendation': self._generate_recommendation(daily_news, trigger_news, sentiment_analysis)
        }
        
        return recommendations
    
    def _generate_recommendation(self, daily_news: pd.DataFrame, 
                               trigger_news: pd.DataFrame, 
                               sentiment_analysis: Dict) -> str:
        """추천 메시지 생성"""
        if daily_news.empty:
            return "수집된 뉴스가 없습니다."
        
        # 트리거 뉴스가 많으면 활발한 시장
        if len(trigger_news) > 20:
            market_condition = "매우 활발"
        elif len(trigger_news) > 10:
            market_condition = "활발"
        else:
            market_condition = "보통"
        
        # 감정 분석 결과
        sentiment_stats = sentiment_analysis.get('sentiment_stats', {})
        if hasattr(sentiment_stats, 'sum') and 'positive' in sentiment_stats.index:
            positive_ratio = sentiment_stats.loc['positive'].sum() / sentiment_stats.sum().sum()
            if positive_ratio > 0.6:
                sentiment = "긍정적"
            elif positive_ratio < 0.4:
                sentiment = "부정적"
            else:
                sentiment = "중립적"
        else:
            sentiment = "분석 불가"
        
        recommendation = f"""
📊 스윙 트레이딩 시장 분석 결과

📈 시장 활성도: {market_condition}
💭 시장 감정: {sentiment}
📰 일간 뉴스: {len(daily_news)}개
🎯 트리거 뉴스: {len(trigger_news)}개

💡 추천:
- {market_condition}한 시장에서는 단기 스윙(2-3일) 전략 고려
- {sentiment} 감정에서는 신중한 진입과 빠른 손절 권장
- 트리거 뉴스가 많을 때는 이슈 기반 매매 기회 증가
        """
        
        return recommendation
    
    def close(self):
        """크롤러 종료"""
        self.crawler.close()

# 사용 예시
def main():
    collector = SwingNewsCollector()
    
    try:
        # 스윙 트레이딩 추천 분석
        recommendations = collector.get_swing_recommendations()
        
        print("=== 스윙 트레이딩 뉴스 분석 결과 ===")
        print(f"일간 뉴스: {recommendations['daily_news_count']}개")
        print(f"트리거 뉴스: {recommendations['trigger_news_count']}개")
        print("\n" + recommendations['recommendation'])
        
        # 상위 트리거 뉴스 출력
        if recommendations['top_triggers']:
            print("\n=== 상위 트리거 뉴스 ===")
            for i, news in enumerate(recommendations['top_triggers'][:5], 1):
                print(f"{i}. {news['title']}")
                print(f"   키워드: {news.get('matched_keywords', 'N/A')}")
                print()
        
    finally:
        collector.close()

if __name__ == "__main__":
    main() 