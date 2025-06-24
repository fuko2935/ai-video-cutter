import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    # Flask ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    PROCESSED_FOLDER = os.environ.get('PROCESSED_FOLDER') or 'processed'
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
    
    @staticmethod
    def init_app(app):
        # Upload ve processed klasörlerini oluştur
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)