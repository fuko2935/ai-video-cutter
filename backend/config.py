import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    # Flask ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = os.path.abspath(os.environ.get('UPLOAD_FOLDER') or 'backend/uploads')
    PROCESSED_FOLDER = os.path.abspath(os.environ.get('PROCESSED_FOLDER') or 'backend/processed')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB maksimum dosya boyutu
    
    # Redis ayarları
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery ayarları
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Gemini API ayarları
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # İzin verilen video formatları
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # Loglama ayarları
    LOG_FOLDER = 'logs'
    LOG_FILE = 'app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 3
    
    @staticmethod
    def init_app(app):
        # Upload, processed ve log klasörlerini oluştur
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)
        
        # Logging ayarları
        Config.setup_logging(app)
    
    @staticmethod
    def setup_logging(app):
        """Loglama sistemini ayarla"""
        log_file_path = os.path.join(Config.LOG_FOLDER, Config.LOG_FILE)
        
        # Başlangıçta log dosyasını temizle
        if os.path.exists(log_file_path):
            with open(log_file_path, 'w') as f:
                f.write(f"=== Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Flask app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.info(f"Logging system initialized - Log file: {log_file_path}")