FROM python:3.11-slim

# FFmpeg kurulumu
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Upload ve processed klasörlerini oluştur
RUN mkdir -p uploads processed

# Port
EXPOSE 5000

# Varsayılan komut
CMD ["python", "app.py"]