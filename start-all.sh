#!/bin/bash

# Tüm servisleri başlatan script (Project IDX için)

echo "🚀 AI Video Cutter Başlatılıyor..."
echo "==============================="

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Kullanılan portlar
FRONTEND_PORT=3000
BACKEND_PORT=5000
REDIS_PORT=6379

# Port kontrolü ve temizleme fonksiyonu
cleanup_port() {
    local port=$1
    local service=$2
    
    echo -e "${BLUE}🔍 $service için port $port kontrol ediliyor...${NC}"
    
    # Port kullanan process'leri bul
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  Port $port kullanımda. Process'ler kapatılıyor...${NC}"
        for pid in $pids; do
            # Process bilgisini göster
            ps -p $pid -o comm= 2>/dev/null && echo "   PID: $pid"
            kill -9 $pid 2>/dev/null
        done
        sleep 1
        echo -e "${GREEN}✅ Port $port temizlendi${NC}"
    else
        echo -e "${GREEN}✅ Port $port boş${NC}"
    fi
}

# Eski process'leri temizle
cleanup_processes() {
    echo -e "${BLUE}🧹 Eski process'ler temizleniyor...${NC}"
    
    # Node.js process'leri (Frontend)
    echo -e "${BLUE}   Cleaning Node.js processes...${NC}"
    pkill -f "node.*next" 2>/dev/null
    pkill -f "node.*dev" 2>/dev/null
    
    # Python process'leri (Backend)
    echo -e "${BLUE}   Cleaning Python processes...${NC}"
    pkill -f "python.*app.py" 2>/dev/null
    pkill -f "flask" 2>/dev/null
    
    # Celery process'leri
    echo -e "${BLUE}   Cleaning Celery processes...${NC}"
    pkill -f "celery.*worker" 2>/dev/null
    
    # Redis process'i (eğer redis-server ile başlatılmışsa)
    echo -e "${BLUE}   Checking Redis...${NC}"
    redis-cli shutdown 2>/dev/null || true
    
    sleep 2
}

# Log klasörünü oluştur ve temizle
setup_logs() {
    echo -e "${BLUE}📝 Log sistemi hazırlanıyor...${NC}"
    
    # Log klasörlerini oluştur
    mkdir -p logs/app logs/api logs/celery logs/errors
    
    # Eski logları temizle
    echo "=== New Session Started at $(date) ===" > logs/app/general.log
    echo "=== New Session Started at $(date) ===" > logs/app/debug.log
    echo "=== New Session Started at $(date) ===" > logs/errors/errors.log
    echo "=== New Session Started at $(date) ===" > logs/api/requests.log
    
    echo -e "${GREEN}✅ Log dosyaları temizlendi${NC}"
}

# Environment kontrolü
check_environment() {
    echo -e "${BLUE}🔍 Environment kontrol ediliyor...${NC}"
    
    # .env dosyası kontrolü
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
    
    echo -e "${GREEN}✅ Environment ayarları OK${NC}"
}

# Sistem durumunu göster
show_status() {
    echo ""
    echo -e "${BLUE}📊 Sistem Durumu:${NC}"
    echo "==============================="
    
    # Redis durumu
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "Redis:    ${GREEN}✅ Çalışıyor${NC}"
    else
        echo -e "Redis:    ${RED}❌ Çalışmıyor${NC}"
    fi
    
    # Backend durumu
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo -e "Backend:  ${GREEN}✅ Çalışıyor${NC}"
    else
        echo -e "Backend:  ${YELLOW}⏳ Başlatılıyor...${NC}"
    fi
    
    # Frontend durumu
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "Frontend: ${GREEN}✅ Çalışıyor${NC}"
    else
        echo -e "Frontend: ${YELLOW}⏳ Başlatılıyor...${NC}"
    fi
    
    echo "==============================="
}

# Ana başlatma fonksiyonu
main() {
    # Environment kontrolü
    check_environment
    
    # Eski process'leri temizle
    cleanup_processes
    
    # Portları temizle
    cleanup_port $REDIS_PORT "Redis"
    cleanup_port $BACKEND_PORT "Backend"
    cleanup_port $FRONTEND_PORT "Frontend"
    
    # Log sistemini hazırla
    setup_logs
    
    # Redis'i başlat
    echo -e "${BLUE}📦 Redis başlatılıyor...${NC}"
    redis-server --daemonize yes --logfile logs/redis.log
    
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
    echo -e "${BLUE}🔧 Celery worker başlatılıyor...${NC}"
    cd backend
    celery -A celery_app.celery_app worker --loglevel=info --logfile=../logs/celery/worker.log --detach
    cd ..
    
    # Backend'i başlat
    echo -e "${BLUE}🖥️  Backend başlatılıyor...${NC}"
    cd backend
    python app.py > ../logs/app/backend.log 2>&1 & # Log çıktısını dosyaya yönlendir
    BACKEND_PID=$!
    cd ..
    
    # Backend'in başlamasını bekle
    echo -e "${YELLOW}⏳ Backend'in hazır olması bekleniyor...${NC}"
    for i in {1..10}; do
        if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend başarıyla başlatıldı${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    # Frontend bağımlılıklarını kontrol et
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}⚠️  Frontend bağımlılıkları bulunamadı, yükleniyor...${NC}"
        cd frontend
        npm install
        cd ..
    fi
    
    # Sistem durumunu göster
    show_status
    
    # Frontend'i başlat
    echo -e "${BLUE}🎨 Frontend başlatılıyor...${NC}"
    echo ""
    echo "========================================="
    echo -e "${GREEN}✅ Tüm servisler başlatıldı!${NC}"
    echo "========================================="
    echo ""
    echo "📌 Frontend: http://localhost:3000"
    echo "📌 Backend API: http://localhost:5000"
    echo "📌 Logs: ./logs/"
    echo ""
    echo "💡 İpuçları:"
    echo "   - Logları izlemek için: tail -f logs/app/debug.log"
    echo "   - Sistem durumu için: curl http://localhost:5000/api/health"
    echo "   - Durdurmak için: Ctrl+C"
    echo ""
    
    # Frontend'i ön planda çalıştır
    cd frontend
    npm run dev
}

# Cleanup fonksiyonu (Ctrl+C ile çıkıldığında)
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Servisler durduruluyor...${NC}"
    
    # Backend process'ini durdur
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    
    # Tüm ilgili process'leri temizle
    cleanup_processes
    
    # Son durumu göster
    echo -e "${GREEN}✅ Temizlik tamamlandı${NC}"
    
    # Log dosyalarının konumunu hatırlat
    echo ""
    echo "📋 Log dosyaları ./logs/ klasöründe saklandı"
}

# Trap ayarla
trap cleanup EXIT

# Ana fonksiyonu çalıştır
main