# Makefile'a eklenecek yeni komutlar

# Port durumunu kontrol et
check-ports:
	@chmod +x check-ports.sh
	@./check-ports.sh

# Tüm process'leri temizle
kill-all:
	@echo "🛑 Tüm process'ler durduruluyor..."
	@pkill -f "node.*next" || true
	@pkill -f "node.*dev" || true
	@pkill -f "python.*app.py" || true
	@pkill -f "flask" || true
	@pkill -f "celery.*worker" || true
	@redis-cli shutdown || true
	@echo "✅ Temizlik tamamlandı"

# Güvenli başlatma (önce temizle, sonra başlat)
safe-start:
	@make kill-all
	@sleep 2
	@./start-all.sh

# Log izleme
watch-logs:
	@tail -f logs/app/debug.log

watch-errors:
	@tail -f logs/errors/errors.log

watch-api:
	@tail -f logs/api/requests.log