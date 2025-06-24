from celery import Celery
from config import Config

# Celery uygulamasını oluştur
celery_app = Celery(
    'video_cutter',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['tasks']
)

# Celery ayarları
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Uzun süren video işlemleri için timeout ayarları
    task_soft_time_limit=1800,  # 30 dakika soft limit
    task_time_limit=3600,  # 1 saat hard limit
    # Retry ayarları
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 60 saniye
    task_max_retries=3,
)