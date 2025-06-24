#!/bin/bash

# Backend başlatma scripti (Project IDX için)

cd backend

# Virtual environment'ı aktifle
source venv/bin/activate

# Environment değişkenlerini yükle
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Redis URL'ini ayarla (local)
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Celery worker'ı arka planda başlat
celery -A celery_app.celery_app worker --loglevel=info --detach

# Flask uygulamasını başlat
python app.py