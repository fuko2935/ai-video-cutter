#!/bin/bash

# Port durumlarını kontrol et

echo "🔍 Port Durumu Kontrolü"
echo "======================="

check_port() {
    local port=$1
    local service=$2
    
    echo -n "$service (Port $port): "
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ Kullanımda"
        echo "   Process bilgisi:"
        lsof -Pi :$port -sTCP:LISTEN 2>/dev/null | tail -n +2 | while read line; do
            echo "   $line"
        done
    else
        echo "❌ Boş"
    fi
    echo ""
}

check_port 3000 "Frontend"
check_port 5000 "Backend"
check_port 6379 "Redis"

echo "💡 Tüm portları temizlemek için: ./start-all.sh"