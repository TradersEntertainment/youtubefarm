#!/usr/bin/env python3
“””
YouTube Video Downloader - Render Uyumlu
MrBeast kanalından ve diğer kanallardan video indirme sistemi
“””

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import yt_dlp
import requests

# Logging konfigürasyonu

logging.basicConfig(
level=logging.INFO,
format=’%(asctime)s - %(levelname)s - %(message)s’,
handlers=[
logging.StreamHandler(sys.stdout),
logging.FileHandler(‘downloader.log’)
]
)

logger = logging.getLogger(**name**)

class YouTubeDownloader:
def **init**(self):
self.download_dir = os.getenv(‘DOWNLOAD_DIR’, ‘./downloads’)
self.email_notifications = os.getenv(‘EMAIL_NOTIFICATIONS’, ‘false’).lower() == ‘true’
self.channels = self.get_channels_to_monitor()
self.max_videos = int(os.getenv(‘MAX_VIDEOS’, ‘5’))
self.quality = os.getenv(‘VIDEO_QUALITY’, ‘best[height<=720]’)

```
    # İndirme klasörünü oluştur
    Path(self.download_dir).mkdir(parents=True, exist_ok=True)
    
    # İstatistik dosyası
    self.stats_file = 'download_stats.json'
    
    logger.info("YouTube Downloader başlatıldı")
    logger.info(f"İndirme klasörü: {self.download_dir}")
    logger.info(f"Monitör edilecek kanallar: {len(self.channels)}")
    
    print("✅ YouTube Downloader hazır!")
    print(f"📁 İndirme klasörü: {self.download_dir}")
    print(f"📺 Takip edilen kanal sayısı: {len(self.channels)}")

def get_channels_to_monitor(self):
    """Monitör edilecek kanalları döndür"""
    channels = []
    
    # Environment variable'dan kanal listesi al
    channels_env = os.getenv('YOUTUBE_CHANNELS', '')
    if channels_env:
        channels = [ch.strip() for ch in channels_env.split(',')]
    
    # Varsayılan olarak MrBeast kanalını ekle
    if not channels:
        channels = [
            'https://www.youtube.com/@MrBeast',
            'https://www.youtube.com/@MrBeast6000'
        ]
    
    return channels

def save_download_stats(self, video_info):
    """İndirme istatistiklerini kaydet"""
    try:
        stats = self.load_download_stats()
        
        new_entry = {
            'timestamp': datetime.now().isoformat(),
            'title': video_info.get('title', 'Bilinmeyen'),
            'uploader': video_info.get('uploader', 'Bilinmeyen'),
            'duration': video_info.get('duration', 0),
            'view_count': video_info.get('view_count', 0),
            'url': video_info.get('webpage_url', '')
        }
        
        stats.append(new_entry)
        
        # Son 100 kaydı tut
        if len(stats) > 100:
            stats = stats[-100:]
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"İstatistik kaydetme hatası: {e}")

def load_download_stats(self):
    """İndirme istatistiklerini yükle"""
    try:
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"İstatistik yükleme hatası: {e}")
        return []

def print_success_notification(self, video_info):
    """Başarılı indirme bildirimi"""
    title = video_info.get('title', 'Bilinmeyen Video')
    uploader = video_info.get('uploader', 'Bilinmeyen Kanal')
    duration = video_info.get('duration', 0)
    
    print("\n" + "="*60)
    print("🎉 YENİ VİDEO İNDİRİLDİ!")
    print(f"📹 Başlık: {title}")
    print(f"👤 Kanal: {uploader}")
    print(f"⏱️  Süre: {duration//60}:{duration%60:02d}")
    print(f"📅 İndirilme Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

def get_video_info(self, url):
    """Video bilgilerini al"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        logger.error(f"Video bilgisi alınamadı {url}: {e}")
        return None

def download_video(self, url, video_info=None):
    """Tekil video indir"""
    logger.info(f"Video indiriliyor: {url}")
    
    # İndirme klasörünü oluştur
    os.makedirs(self.download_dir, exist_ok=True)
    
    ydl_opts = {
        'format': self.quality,
        'outtmpl': os.path.join(self.download_dir, '%(uploader)s - %(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'writeinfojson': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['tr', 'en'],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        logger.info(f"✅ Video başarıyla indirildi: {url}")
        
        # Konsol bildirimi ve istatistik kaydet
        if video_info:
            self.print_success_notification(video_info)
            self.save_download_stats(video_info)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Video indirme hatası {url}: {e}")
        return False

def get_channel_latest_videos(self, channel_url):
    """Kanalın son videolarını al"""
    logger.info(f"Kanal kontrol ediliyor: {channel_url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlistend': self.max_videos,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                videos = []
                for entry in info['entries'][:self.max_videos]:
                    if entry:
                        videos.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'uploader': info.get('uploader', 'Unknown')
                        })
                return videos
            else:
                logger.warning(f"Kanal videolarına erişilemedi: {channel_url}")
                return []
                
    except Exception as e:
        logger.error(f"Kanal video listesi alınamadı {channel_url}: {e}")
        return []

def load_downloaded_videos(self):
    """Daha önce indirilen videoları yükle"""
    db_file = 'downloaded_videos.json'
    try:
        if os.path.exists(db_file):
            with open(db_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    except Exception as e:
        logger.error(f"İndirilen video veritabanı yüklenemedi: {e}")
        return set()

def save_downloaded_video(self, video_id):
    """İndirilen video ID'sini kaydet"""
    db_file = 'downloaded_videos.json'
    try:
        downloaded = self.load_downloaded_videos()
        downloaded.add(video_id)
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(list(downloaded), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"İndirilen video veritabanı kaydedilemedi: {e}")

def monitor_channels(self):
    """Kanalları monitör et ve yeni videoları indir"""
    logger.info("Kanal monitörleme başlatıldı")
    
    downloaded_videos = self.load_downloaded_videos()
    new_downloads = 0
    
    for channel_url in self.channels:
        try:
            videos = self.get_channel_latest_videos(channel_url)
            
            for video in videos:
                video_id = video['id']
                
                if video_id not in downloaded_videos:
                    logger.info(f"Yeni video bulundu: {video['title']}")
                    
                    # Video detaylarını al
                    video_info = self.get_video_info(video['url'])
                    
                    if self.download_video(video['url'], video_info):
                        self.save_downloaded_video(video_id)
                        new_downloads += 1
                        
                        # Her video arasında kısa bekleme
                        time.sleep(5)
                else:
                    logger.debug(f"Video zaten indirilmiş: {video['title']}")
                    
        except Exception as e:
            logger.error(f"Kanal işleme hatası {channel_url}: {e}")
            continue
    
    logger.info(f"Monitörleme tamamlandı. {new_downloads} yeni video indirildi.")
    
    if new_downloads == 0:
        print("🔍 Kanal monitörleme tamamlandı. Yeni video bulunamadı.")
    else:
        print(f"🎉 Toplam {new_downloads} yeni video indirildi!")
    
    return new_downloads

def download_single_video(self, url):
    """Tek bir video indir (manuel kullanım için)"""
    logger.info(f"Manuel video indirme: {url}")
    
    video_info = self.get_video_info(url)
    if video_info:
        success = self.download_video(url, video_info)
        if success:
            self.save_downloaded_video(video_info.get('id'))
        return success
    return False

def cleanup_old_videos(self, days=7):
    """Eski videoları temizle"""
    logger.info(f"Son {days} günden eski videolar temizleniyor...")
    
    try:
        download_path = Path(self.download_dir)
        if not download_path.exists():
            return
        
        current_time = time.time()
        deleted_count = 0
        
        for file_path in download_path.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (days * 24 * 3600):
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Eski dosya silindi: {file_path.name}")
        
        logger.info(f"Temizlik tamamlandı. {deleted_count} dosya silindi.")
        
    except Exception as e:
        logger.error(f"Dosya temizleme hatası: {e}")
```

def main():
“”“Ana fonksiyon”””
logger.info(”=== YouTube Downloader Başlatılıyor ===”)

```
try:
    downloader = YouTubeDownloader()
    
    # Komut satırı argümanlarını kontrol et
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'monitor':
            # Kanal monitörleme modu
            downloader.monitor_channels()
            
        elif command == 'download' and len(sys.argv) > 2:
            # Tek video indirme modu
            video_url = sys.argv[2]
            print(f"🔄 Tek video indiriliyor: {video_url}")
            success = downloader.download_single_video(video_url)
            if success:
                print("✅ Video başarıyla indirildi!")
            else:
                print("❌ Video indirilemedi!")
                
        elif command == 'cleanup':
            # Eski dosyaları temizleme
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            downloader.cleanup_old_videos(days)
            
        elif command == 'stats':
            # İstatistikleri göster
            stats = downloader.load_download_stats()
            print(f"\n📊 Toplam indirilen video: {len(stats)}")
            if stats:
                print("\n🕐 Son 5 indirilen video:")
                for i, stat in enumerate(stats[-5:], 1):
                    print(f"{i}. {stat['title']} - {stat['uploader']}")
                    print(f"   📅 {stat['timestamp'][:19]}")
            
        else:
            print("❌ Geçersiz komut!")
            print("Kullanım:")
            print("  python main.py monitor          - Kanalları monitör et")
            print("  python main.py download [URL]   - Tek video indir")
            print("  python main.py cleanup [days]   - Eski dosyaları temizle")
            print("  python main.py stats            - İstatistikleri göster")
    else:
        # Varsayılan olarak monitörleme yap
        print("🚀 Varsayılan mod: Kanal monitörleme başlatılıyor...")
        downloader.monitor_channels()
        
except KeyboardInterrupt:
    logger.info("Program kullanıcı tarafından durduruldu")
    print("\n👋 Program durduruldu!")
    
except Exception as e:
    logger.error(f"Beklenmeyen hata: {e}")
    print(f"❌ Hata oluştu: {e}")
    sys.exit(1)
```

if **name** == “**main**”:
main()
