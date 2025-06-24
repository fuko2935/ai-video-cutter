# AI Destekli Akıllı Video Kesici

Bu proje, kullanıcıların videolarını doğal dil komutlarıyla kesip düzenlemelerine olanak tanıyan bir web uygulamasıdır. Google Gemini API kullanarak video içeriğini analiz eder ve kullanıcının isteklerine göre kesim önerileri sunar.

## 🚀 Özellikler

- **Video Yükleme**: Sürükle-bırak desteği ile kolay video yükleme
- **AI Sohbet Arayüzü**: Doğal dilde komutlar vererek video kesimi
- **İnteraktif Timeline**: Kesim noktalarını görsel olarak görüntüleme
- **Video Önizleme**: Gerçek zamanlı video oynatıcı
- **Otomatik Video İşleme**: FFmpeg ile profesyonel video kesme ve birleştirme

## 🛠️ Teknoloji Stack'i

### Backend
- **Python Flask**: REST API
- **Celery + Redis**: Asenkron görev yönetimi
- **FFmpeg**: Video işleme
- **Google Gemini API**: AI video analizi

### Frontend
- **Next.js**: React framework
- **Material-UI**: UI komponenetleri
- **React Player**: Video oynatıcı
- **React Dropzone**: Dosya yükleme

## 📋 Gereksinimler

- Docker ve Docker Compose
- Google Gemini API anahtarı
- Minimum 4GB RAM
- FFmpeg (Docker image'ında mevcut)

## 🔧 Kurulum

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/fuko2935/ai-video-cutter.git
cd ai-video-cutter
```

### 2. Çevre Değişkenlerini Ayarlayın

Proje kök dizininde `.env` dosyası oluşturun:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Docker ile Başlatın

```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları takip et
docker-compose logs -f
```

### 4. Uygulamaya Erişin

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Redis: localhost:6379

## 🚀 Manuel Kurulum (Docker olmadan)

### Backend Kurulumu

```bash
cd backend

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Redis'i başlat (ayrı terminal)
redis-server

# Flask uygulamasını başlat
python app.py

# Celery worker'ı başlat (ayrı terminal)
celery -A celery_app.celery_app worker --loglevel=info
```

### Frontend Kurulumu

```bash
cd frontend

# Bağımlılıkları yükle
npm install

# Development server'ı başlat
npm run dev
```

## 📝 Kullanım

1. **Video Yükleyin**: Ana sayfada video dosyanızı sürükleyip bırakın veya tıklayarak seçin
2. **Komut Verin**: Sağ taraftaki sohbet arayüzünden doğal dilde komutlar verin:
   - "En komik anları bul"
   - "Sessiz yerleri at"
   - "İlk 30 saniyeyi kes"
   - "Sadece konuşmaların olduğu yerleri al"
3. **Kesimleri İnceleyin**: Timeline'da önerilen kesimleri görün
4. **Video Oluşturun**: "Kes ve Birleştir" butonuna tıklayın
5. **İndirin**: İşlem tamamlandığında videoyu indirin

## 🔍 API Endpoints

### Video Yükleme
```
POST /api/upload
Content-Type: multipart/form-data
Body: video (file)
```

### AI ile Sohbet
```
POST /api/chat/{video_id}
Content-Type: application/json
Body: { "prompt": "komut metni" }
```

### Durum Sorgulama
```
GET /api/status/{video_id}
```

### Video Birleştirme
```
POST /api/finalize
Content-Type: application/json
Body: { "video_id": "...", "cuts": [...] }
```

### Video İndirme
```
GET /api/download/{video_id}
```

## 🐛 Sorun Giderme

### Redis Bağlantı Hatası
```bash
# Redis'in çalıştığından emin olun
docker-compose ps redis
```

### FFmpeg Hatası
```bash
# FFmpeg'in yüklü olduğunu kontrol edin
docker-compose exec backend ffmpeg -version
```

### Gemini API Hatası
- API anahtarınızın geçerli olduğundan emin olun
- API kotanızı kontrol edin

## 📦 Proje Yapısı

```
ai-video-cutter/
├── backend/
│   ├── app.py              # Flask ana uygulama
│   ├── config.py           # Konfigürasyon
│   ├── gemini_client.py    # Gemini API istemcisi
│   ├── celery_app.py       # Celery konfigürasyonu
│   ├── tasks.py            # Asenkron görevler
│   ├── utils.py            # Yardımcı fonksiyonlar
│   └── requirements.txt
├── frontend/
│   ├── pages/
│   │   ├── _app.js
│   │   └── index.js        # Ana sayfa
│   ├── components/
│   │   ├── VideoUploader.js
│   │   ├── ChatInterface.js
│   │   ├── Timeline.js
│   │   └── VideoPlayer.js
│   ├── styles/
│   │   └── globals.css
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🙏 Teşekkürler

- Google Gemini API
- FFmpeg
- Next.js ve React topluluğu