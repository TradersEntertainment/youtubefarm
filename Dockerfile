FROM python:3.11-slim

# Sistem güncellemeleri ve gerekli paketler
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# İndirme klasörünü oluştur
RUN mkdir -p /app/downloads

# Log dosyaları için izinler
RUN chmod 755 /app

# Port (Render için gerekli ama kullanmayacağız)
EXPOSE 10000

# Varsayılan komut
CMD ["python", "main.py", "monitor"]
