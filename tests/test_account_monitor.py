#!/usr/bin/env python3
"""
계좌 모니터링 테스트
Account Monitor 모듈의 모든 기능을 테스트
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from config.settings import Settings
from utils.token_manager import TokenManager
from account.account_monitor import AccountMonitor, get_account_monitor

async def test_account_monitor():
    """계좌 모니터링 테스트"""
    print("=== 계좌 모니터링 테스트 시작 ===")
    
    try:
        # 설정 및 토큰 매니저 초기화
        settings = Settings()
        token_manager = TokenManager(settings)
        
        # 계좌 모니터 초기화
        account_monitor = get_account_monitor(settings, token_manager)
        
        print(f"환경: {settings.ENVIRONMENT}")
        print(f"API 호스트: {settings.API_HOST}")
        print(f"모니터링 간격: {account_monitor.monitoring_interval}초")
        
        # 1. 계좌 요약 정보 조회 테스트
        print("\n1. 계좌 요약 정보 조회 테스트")
        summary = await account_monitor.get_account_summary()
        if summary:
            print(f"  예수금: {summary.deposit:,}원")
            print(f"  총평가금액: {summary.total_evaluation:,}원")
            print(f"  총수익률: {summary.total_profit_rate:.2f}%")
            print(f"  총매입금액: {summary.total_purchase:,}원")
            print(f"  총손익: {summary.total_profit_loss:,}원")
            print(f"  추정자산: {summary.estimated_assets:,}원")
        else:
            print("  계좌 요약 정보 조회 실패")
        
        # 2. 포트폴리오 조회 테스트
        print("\n2. 포트폴리오 조회 테스트")
        portfolio = await account_monitor.get_portfolio()
        if portfolio:
            print(f"  보유 종목 수: {len(portfolio)}개")
            for i, item in enumerate(portfolio[:3], 1):  # 상위 3개만 표시
                print(f"    {i}. {item.stock_name}({item.stock_code})")
                print(f"       현재가: {item.current_price:,}원")
                print(f"       보유수량: {item.quantity:,}주")
                print(f"       평가금액: {item.evaluation_amount:,}원")
                print(f"       수익률: {item.profit_rate:.2f}%")
        else:
            print("  포트폴리오 조회 실패")
        
        # 3. 리스크 지표 계산 테스트
        print("\n3. 리스크 지표 계산 테스트")
        if summary and portfolio:
            risk_metrics = account_monitor.calculate_risk_metrics(portfolio, summary)
            print(f"  최대 손실률: {risk_metrics.max_loss_rate:.2f}%")
            print(f"  포트폴리오 집중도: {risk_metrics.portfolio_concentration:.1f}%")
            print(f"  일일 VaR: {risk_metrics.daily_var:.2f}%")
            print(f"  샤프 비율: {risk_metrics.sharpe_ratio:.2f}")
        else:
            print("  리스크 지표 계산을 위한 데이터 부족")
        
        # 4. 리스크 알림 테스트
        print("\n4. 리스크 알림 테스트")
        if summary and portfolio:
            risk_metrics = account_monitor.calculate_risk_metrics(portfolio, summary)
            alerts = account_monitor.check_risk_alerts(portfolio, summary, risk_metrics)
            if alerts:
                print(f"  발견된 알림: {len(alerts)}개")
                for alert in alerts:
                    print(f"    [{alert['level']}] {alert['message']}")
            else:
                print("  리스크 알림 없음")
        else:
            print("  리스크 알림 체크를 위한 데이터 부족")
        
        # 5. 계좌 상태 조회 테스트
        print("\n5. 계좌 상태 조회 테스트")
        status = account_monitor.get_account_status()
        print(f"  모니터링 활성화: {status['monitoring_active']}")
        print(f"  마지막 업데이트: {status['last_update']}")
        print(f"  최근 알림 수: {status['alert_count']}개")
        
        # 6. 포트폴리오 분석 테스트
        print("\n6. 포트폴리오 분석 테스트")
        analysis = account_monitor.get_portfolio_analysis()
        if analysis:
            print(f"  총 평가금액: {analysis['total_evaluation']:,}원")
            print(f"  총 손익: {analysis['total_profit_loss']:,}원")
            
            if analysis.get('top_performers'):
                print("  상위 성과 종목:")
                for item in analysis['top_performers']:
                    print(f"    {item['stock_name']}: {item['profit_rate']:.2f}% (비중: {item['weight']:.1f}%)")
            
            if analysis.get('worst_performers'):
                print("  하위 성과 종목:")
                for item in analysis['worst_performers']:
                    print(f"    {item['stock_name']}: {item['profit_rate']:.2f}% (비중: {item['weight']:.1f}%)")
        else:
            print("  포트폴리오 분석 데이터 없음")
        
        # 7. 최근 알림 조회 테스트
        print("\n7. 최근 알림 조회 테스트")
        recent_alerts = account_monitor.get_recent_alerts(hours=24)
        print(f"  최근 24시간 알림: {len(recent_alerts)}개")
        
        # 8. 리스크 임계값 업데이트 테스트
        print("\n8. 리스크 임계값 업데이트 테스트")
        new_thresholds = {
            'max_loss_rate': -15.0,
            'concentration_limit': 25.0,
            'daily_loss_limit': -3.0
        }
        account_monitor.update_risk_thresholds(new_thresholds)
        print(f"  업데이트된 임계값: {account_monitor.risk_thresholds}")
        
        print("\n=== 모든 테스트 완료 ===")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

async def test_monitoring_loop():
    """모니터링 루프 테스트 (짧은 시간)"""
    print("\n=== 모니터링 루프 테스트 (10초) ===")
    
    try:
        settings = Settings()
        token_manager = TokenManager(settings)
        account_monitor = get_account_monitor(settings, token_manager)
        
        # 10초간 모니터링
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < 10:
            summary = await account_monitor.get_account_summary()
            if summary:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 계좌 요약 - 예수금: {summary.deposit:,}원, 수익률: {summary.total_profit_rate:.2f}%")
            
            await asyncio.sleep(2)  # 2초마다 체크
        
        print("모니터링 루프 테스트 완료")
        
    except Exception as e:
        print(f"모니터링 루프 테스트 중 오류: {e}")

if __name__ == "__main__":
    # 기본 테스트 실행
    asyncio.run(test_account_monitor())
    
    # 모니터링 루프 테스트 (선택적)
    # asyncio.run(test_monitoring_loop()) 