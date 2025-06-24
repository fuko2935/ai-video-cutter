#!/bin/bash

# Tüm servisleri başlatan script (Project IDX için)

echo "🚀 AI Video Cutter Başlatılıyor..."
echo "==============================="

# Log klasörünü oluştur ve eski logları temizle
mkdir -p logs
echo "=== New Session Started at $(date) ===" > logs/app.log
echo "📝 Log dosyası temizlendi"

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Environment dosyasını kontrol et
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env dosyası bulunamadı!${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Lütfen .env dosyasında GEMINI_API_KEY'i ayarlayın ve scripti tekrar çalıştırın.${NC}"
    exit 1
fi

# GEMINI_API_KEY kontrolü
if grep -q "your_gemini_api_key_here" .env; then
    echo -e "${RED}❗ GEMINI_API_KEY henüz ayarlanmamış!${NC}"
    echo -e "${YELLOW}Lütfen .env dosyasını düzenleyip API anahtarınızı girin.${NC}"
    exit 1
fi

# Redis'i başlat
echo "📦 Redis başlatılıyor..."
redis-server --daemonize yes

# Redis'in başlamasını bekle
sleep 2

# Redis kontrolü
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis başarıyla başlatıldı${NC}"
else
    echo -e "${RED}❌ Redis başlatılamadı!${NC}"
    exit 1
fi

# Environment değişkenlerini yükle
export $(cat .env | grep -v '^#' | xargs)
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Backend için virtual environment kontrolü
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Python virtual environment bulunamadı, oluşturuluyor...${NC}"
    python -m venv backend/venv
    source backend/venv/bin/activate
    pip install -r backend/requirements.txt
else
    source backend/venv/bin/activate
fi

# Gerekli klasörleri oluştur
mkdir -p backend/uploads backend/processed

# Celery worker'ı başlat
echo "🔧 Celery worker başlatılıyor..."
cd backend
celery -A celery_app.celery_app worker --loglevel=info --detach
cd ..

# Backend'i başlat
echo "🖥️  Backend başlatılıyor..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Backend'in başlamasını bekle
echo "⏳ Backend'in hazır olması bekleniyor..."
sleep 5

# Backend kontrolü
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo -e "${GREEN}✅ Backend başarıyla başlatıldı${NC}"
else
    echo -e "${YELLOW}⚠️  Backend henüz hazır değil${NC}"
fi

# Frontend bağımlılıklarını kontrol et
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend bağımlılıkları bulunamadı, yükleniyor...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Frontend'i başlat
echo "🎨 Frontend başlatılıyor..."
echo ""
echo "========================================="
echo -e "${GREEN}✅ Tüm servisler başlatıldı!${NC}"
echo "========================================="
echo ""
echo "📌 Frontend: Aşağıda gösterilecek"
echo "📌 Backend API: http://localhost:5000"
echo ""
echo "💡 Durdurmak için: Ctrl+C"
echo ""

# Frontend'i ön planda çalıştır
cd frontend
npm run dev

# Cleanup (Ctrl+C ile çıkıldığında)
trap cleanup EXIT

cleanup() {
    echo ""
    echo "🛑 Servisler durduruluyor..."
    
    # Backend process'ini durdur
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    
    # Celery'yi durdur
    pkill -f "celery worker" 2>/dev/null
    
    # Redis'i durdur (opsiyonel)
    # redis-cli shutdown
    
    echo "✅ Temizlik tamamlandı"
}