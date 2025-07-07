#!/usr/bin/env python3
"""
System Monitoring Module
- CPU, Memory, Disk, Network, Process 상태 실시간 모니터링
- 임계값 초과 시 알림/로그
- Prometheus 메트릭 함수 제공
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import psutil
from utils.logger import get_logger
from database.database_manager import get_database_manager

logger = get_logger("system_monitor")

class SystemMonitor:
    """시스템 모니터링 클래스"""
    def __init__(self, interval: int = 10):
        self.interval = interval  # 모니터링 주기(초)
        self.db = get_database_manager()
        self.last_metrics: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.alert_history: List[Dict] = []
        self.thresholds = {
            'cpu': 90.0,      # CPU 사용률 90% 초과 시 경고
            'memory': 90.0,   # 메모리 사용률 90% 초과 시 경고
            'disk': 90.0,     # 디스크 사용률 90% 초과 시 경고
            'net_sent': None, # 네트워크 송신 임계값 (MB/s)
            'net_recv': None  # 네트워크 수신 임계값 (MB/s)
        }
        self.monitoring_active = False
        logger.info("시스템 모니터링 초기화 완료")

    def collect_metrics(self) -> Dict[str, Any]:
        """시스템 리소스 메트릭 수집"""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        proc_count = len(psutil.pids())
        
        metrics = {
            'timestamp': datetime.now(),
            'cpu_percent': cpu,
            'memory_percent': mem.percent,
            'memory_used': mem.used,
            'memory_total': mem.total,
            'disk_percent': disk.percent,
            'disk_used': disk.used,
            'disk_total': disk.total,
            'net_bytes_sent': net.bytes_sent,
            'net_bytes_recv': net.bytes_recv,
            'process_count': proc_count
        }
        return metrics

    def check_thresholds(self, metrics: Dict[str, Any]) -> List[Dict]:
        """임계값 초과 체크 및 알림 반환"""
        alerts = []
        if metrics['cpu_percent'] > self.thresholds['cpu']:
            alerts.append({'type': 'CPU', 'level': 'HIGH', 'message': f"CPU 사용률 {metrics['cpu_percent']:.1f}% 초과", 'timestamp': datetime.now()})
        if metrics['memory_percent'] > self.thresholds['memory']:
            alerts.append({'type': 'MEMORY', 'level': 'HIGH', 'message': f"메모리 사용률 {metrics['memory_percent']:.1f}% 초과", 'timestamp': datetime.now()})
        if metrics['disk_percent'] > self.thresholds['disk']:
            alerts.append({'type': 'DISK', 'level': 'HIGH', 'message': f"디스크 사용률 {metrics['disk_percent']:.1f}% 초과", 'timestamp': datetime.now()})
        # 네트워크 임계값은 필요시 구현
        return alerts

    def save_metrics(self, metrics: Dict[str, Any]):
        """DB 및 로그에 메트릭 저장"""
        try:
            self.db.save_performance_metric(1, "cpu_percent", metrics['cpu_percent'])
            self.db.save_performance_metric(1, "memory_percent", metrics['memory_percent'])
            self.db.save_performance_metric(1, "disk_percent", metrics['disk_percent'])
            self.db.save_performance_metric(1, "process_count", metrics['process_count'])
            self.db.save_system_log("INFO", f"시스템 메트릭: CPU {metrics['cpu_percent']}%, MEM {metrics['memory_percent']}%, DISK {metrics['disk_percent']}%", "system_monitor")
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")

    def start_monitoring(self):
        """백그라운드 모니터링 시작 (스레드)"""
        if self.monitoring_active:
            logger.info("이미 모니터링이 실행 중입니다.")
            return
        self.monitoring_active = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        logger.info("시스템 모니터링 시작!")

    def _monitor_loop(self):
        while self.monitoring_active:
            try:
                metrics = self.collect_metrics()
                self.last_metrics = metrics
                self.last_update = datetime.now()
                self.save_metrics(metrics)
                alerts = self.check_thresholds(metrics)
                for alert in alerts:
                    logger.warning(f"[ALERT] {alert['message']}")
                    self.db.save_system_log("WARNING", alert['message'], "system_monitor")
                    self.alert_history.append(alert)
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(self.interval)

    def stop_monitoring(self):
        self.monitoring_active = False
        logger.info("시스템 모니터링 중지!")

    def get_status(self) -> Dict[str, Any]:
        """최근 메트릭/상태 반환"""
        return {
            'last_metrics': self.last_metrics,
            'last_update': self.last_update,
            'alert_count': len([a for a in self.alert_history if (datetime.now() - a['timestamp']).seconds < 3600]),
            'monitoring_active': self.monitoring_active
        }

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alert_history if a['timestamp'] > cutoff]

    # Prometheus 메트릭 함수 예시
    def prometheus_metrics(self) -> str:
        """Prometheus 포맷 메트릭 반환 (텍스트)"""
        m = self.last_metrics
        if not m:
            return ""
        lines = [
            f"system_cpu_percent {m['cpu_percent']}",
            f"system_memory_percent {m['memory_percent']}",
            f"system_disk_percent {m['disk_percent']}",
            f"system_process_count {m['process_count']}"
        ]
        return '\n'.join(lines)

# 전역 인스턴스
_system_monitor = None

def get_system_monitor(interval: int = 10) -> SystemMonitor:
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(interval)
    return _system_monitor
