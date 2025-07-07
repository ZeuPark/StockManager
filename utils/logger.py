#!/usr/bin/env python3
"""
Logging System for Stock Manager
Provides structured logging with different levels, file rotation, and monitoring integration
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class StockManagerLogger:
    """Centralized logging system for Stock Manager"""
    
    def __init__(self, name: str = "stock_manager", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup different log handlers for different purposes"""
        
        # Console handler (INFO level and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handlers with rotation
        self._setup_file_handlers()
    
    def _setup_file_handlers(self):
        """Setup file handlers for different log levels"""
        
        # General log file (INFO level and above)
        general_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "stock_manager.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # 한글 인코딩 문제 해결
        )
        general_handler.setLevel(logging.INFO)
        general_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        general_handler.setFormatter(general_formatter)
        self.logger.addHandler(general_handler)
        
        # Error log file (ERROR level and above)
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'  # 한글 인코딩 문제 해결
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # Trading log file (trading specific events)
        trading_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "trading.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'  # 한글 인코딩 문제 해결
        )
        trading_handler.setLevel(logging.INFO)
        trading_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        trading_handler.setFormatter(trading_formatter)
        self.trading_handler = trading_handler
        self.logger.addHandler(trading_handler)
        
        # Debug log file (DEBUG level and above)
        debug_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "debug.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3,
            encoding='utf-8'  # 한글 인코딩 문제 해결
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        debug_handler.setFormatter(debug_formatter)
        self.logger.addHandler(debug_handler)
    
    def get_logger(self, module_name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance for a specific module"""
        if module_name:
            return logging.getLogger(f"{self.name}.{module_name}")
        return self.logger
    
    def log_trading_event(self, event_type: str, symbol: str, action: str, 
                         quantity: int = None, price: float = None, 
                         order_id: str = None, **kwargs):
        """Log trading specific events with structured data"""
        message = f"TRADING_EVENT - Type: {event_type}, Symbol: {symbol}, Action: {action}"
        
        if quantity is not None:
            message += f", Quantity: {quantity}"
        if price is not None:
            message += f", Price: {price}"
        if order_id is not None:
            message += f", OrderID: {order_id}"
        
        # Add additional kwargs
        for key, value in kwargs.items():
            message += f", {key}: {value}"
        
        self.logger.info(message)
    
    def log_api_call(self, api_name: str, endpoint: str, status: str, 
                    response_time: float = None, error: str = None):
        """Log API calls with performance metrics"""
        message = f"API_CALL - Service: {api_name}, Endpoint: {endpoint}, Status: {status}"
        
        if response_time is not None:
            message += f", ResponseTime: {response_time:.3f}s"
        if error is not None:
            message += f", Error: {error}"
        
        self.logger.info(message)
    
    def log_system_metric(self, metric_name: str, value: float, unit: str = None):
        """Log system performance metrics"""
        message = f"SYSTEM_METRIC - {metric_name}: {value}"
        if unit:
            message += f" {unit}"
        
        self.logger.info(message)
    
    def log_security_event(self, event_type: str, description: str, severity: str = "INFO"):
        """Log security related events"""
        message = f"SECURITY_EVENT - Type: {event_type}, Severity: {severity}, Description: {description}"
        
        if severity.upper() in ["ERROR", "CRITICAL"]:
            self.logger.error(message)
        else:
            self.logger.warning(message)
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up log files older than specified days"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old log file: {log_file}")
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")


# Global logger instance
_logger_instance = None


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StockManagerLogger()
    return _logger_instance.get_logger(module_name)


def setup_logging(log_dir: str = "logs") -> StockManagerLogger:
    """Setup and return the global logger instance"""
    global _logger_instance
    _logger_instance = StockManagerLogger(log_dir=log_dir)
    return _logger_instance


# Convenience functions for quick logging
def info(message: str, module_name: Optional[str] = None):
    """Log info message"""
    get_logger(module_name).info(message)


def warning(message: str, module_name: Optional[str] = None):
    """Log warning message"""
    get_logger(module_name).warning(message)


def error(message: str, module_name: Optional[str] = None, exc_info: bool = True):
    """Log error message"""
    get_logger(module_name).error(message, exc_info=exc_info)


def debug(message: str, module_name: Optional[str] = None):
    """Log debug message"""
    get_logger(module_name).debug(message)


def critical(message: str, module_name: Optional[str] = None, exc_info: bool = True):
    """Log critical message"""
    get_logger(module_name).critical(message, exc_info=exc_info)


if __name__ == "__main__":
    # Test the logging system
    logger = setup_logging()
    
    # Test different log levels
    logger.logger.info("Stock Manager logging system initialized")
    logger.logger.warning("This is a warning message")
    logger.logger.error("This is an error message")
    logger.logger.debug("This is a debug message")
    
    # Test trading event logging
    logger.log_trading_event(
        event_type="ORDER_PLACED",
        symbol="AAPL",
        action="BUY",
        quantity=100,
        price=150.25,
        order_id="ORD123456"
    )
    
    # Test API call logging
    logger.log_api_call(
        api_name="KiwoomAPI",
        endpoint="/order/place",
        status="SUCCESS",
        response_time=0.245
    )
    
    print("Logging system test completed. Check logs/ directory for output files.")
