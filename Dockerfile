FROM python:3.10-slim

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 \
    libglib2.0-0 libgl1-mesa-glx libgtk-3-0 libnss3 libxss1 libasound2 \
    libxcomposite1 libxrandr2 libxdamage1 libx11-xcb1 libxkbcommon0 \
    curl unzip xvfb

# Python paketleri
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium kurulumu
RUN pip install playwright && playwright install chromium

# Kod dosyaları
COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
