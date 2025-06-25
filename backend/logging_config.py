import os
import sys
import logging
import logging.handlers
from datetime import datetime
import json
from functools import wraps
import time
import traceback

class ColoredFormatter(logging.Formatter):
    """Renkli console output için formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatında loglama için"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'video_id'):
            log_data['video_id'] = record.video_id
            
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(app_name='ai-video-cutter', log_level='DEBUG'):
    """Ana loglama sistemi kurulumu"""
    
    # Log klasörlerini oluştur
    log_dirs = ['logs', 'logs/app', 'logs/api', 'logs/celery', 'logs/errors']
    for dir_path in log_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Tüm handler'ları temizle
    root_logger.handlers = []
    
    # 1. Console Handler (Renkli)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 2. General Log File (JSON)
    general_handler = logging.handlers.RotatingFileHandler(
        'logs/app/general.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    general_handler.setLevel(logging.INFO)
    general_handler.setFormatter(JSONFormatter())
    
    # 3. Debug Log File (Detaylı)
    debug_handler = logging.handlers.RotatingFileHandler(
        'logs/app/debug.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    debug_handler.setFormatter(debug_formatter)
    
    # 4. Error Log File
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/errors/errors.log',
        maxBytes=10*1024*1024,
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d\n'
        '%(message)s\n'
        '%(exc_info)s\n'
        '-' * 80
    )
    error_handler.setFormatter(error_formatter)
    
    # 5. API Request Log
    api_handler = logging.handlers.RotatingFileHandler(
        'logs/api/requests.log',
        maxBytes=20*1024*1024,
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(JSONFormatter())
    
    # Handler'ları ekle
    root_logger.addHandler(console_handler)
    root_logger.addHandler(general_handler)
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(error_handler)
    
    # API logger
    api_logger = logging.getLogger('api')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    # Celery logger
    celery_handler = logging.handlers.RotatingFileHandler(
        'logs/celery/tasks.log',
        maxBytes=20*1024*1024,
        backupCount=5
    )
    celery_handler.setFormatter(JSONFormatter())
    celery_logger = logging.getLogger('celery')
    celery_logger.addHandler(celery_handler)
    
    # Performance logger
    perf_handler = logging.handlers.RotatingFileHandler(
        'logs/app/performance.log',
        maxBytes=10*1024*1024,
        backupCount=3
    )
    perf_handler.setFormatter(JSONFormatter())
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    
    return root_logger

def get_logger(name):
    """Logger instance al"""
    return logging.getLogger(name)

def log_execution_time(logger=None):
    """Fonksiyon çalışma süresini logla"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            log = logger or logging.getLogger(func.__module__)
            
            log.debug(f"Starting {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                log.info(
                    f"Completed {func.__name__} in {duration:.3f}s",
                    extra={'duration': duration}
                )
                
                # Performance logger'a da yaz
                perf_logger = logging.getLogger('performance')
                perf_logger.info(
                    f"{func.__module__}.{func.__name__}",
                    extra={'duration': duration}
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log.error(
                    f"Error in {func.__name__} after {duration:.3f}s: {str(e)}",
                    exc_info=True,
                    extra={'duration': duration}
                )
                raise
                
        return wrapper
    return decorator

def log_api_request(request, response=None, duration=None):
    """API isteklerini logla"""
    api_logger = logging.getLogger('api')
    
    log_data = {
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'request_id': getattr(request, 'request_id', None),
    }
    
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.is_json:
            log_data['body'] = request.get_json()
        elif request.form:
            log_data['form'] = dict(request.form)
            
    if response:
        log_data['status_code'] = response.status_code
        
    if duration:
        log_data['duration'] = duration
        
    api_logger.info(f"API Request: {request.path}", extra=log_data)

class LoggerMixin:
    """Class'lara loglama yeteneği ekler"""
    
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger
    
    def log_debug(self, message, **kwargs):
        self.logger.debug(message, extra=kwargs)
        
    def log_info(self, message, **kwargs):
        self.logger.info(message, extra=kwargs)
        
    def log_warning(self, message, **kwargs):
        self.logger.warning(message, extra=kwargs)
        
    def log_error(self, message, exc_info=False, **kwargs):
        self.logger.error(message, exc_info=exc_info, extra=kwargs)