import os
import sys
import time
import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import yt_dlp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("downloader.log")
    ]
)

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.download_dir = os.getenv("DOWNLOAD_DIR", "./downloads")
        self.channels = self.get_channels_to_monitor()
        self.max_videos = int(os.getenv("MAX_VIDEOS", "5"))
        self.quality = os.getenv("VIDEO_QUALITY", "best[height<=720]")
        
        # Manuel YouTube cookies - Bot korumasını aşar!
        self.youtube_cookies = os.getenv("YOUTUBE_COOKIES", "")
        
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        self.stats_file = "download_stats.json"
        
        logger.info("YouTube Downloader baslatildi")
        logger.info(f"Indirme klasoru: {self.download_dir}")
        logger.info(f"Monitor edilecek kanallar: {len(self.channels)}")
        logger.info(f"Manuel cookies: {'AKTIF' if self.youtube_cookies else 'YOK'}")
        
        print("YouTube Downloader hazir!")
        print(f"Indirme klasoru: {self.download_dir}")
        print(f"Takip edilen kanal sayisi: {len(self.channels)}")
        print(f"Cookie durumu: {'✅ AKTIF' if self.youtube_cookies else '❌ YOK'}")
    
    def get_channels_to_monitor(self):
        channels = []
        channels_env = os.getenv("YOUTUBE_CHANNELS", "")
        if channels_env:
            channels = [ch.strip() for ch in channels_env.split(",")]
        
        if not channels:
            # Stable channel ID format - more reliable than @handle
            channels = [
                "https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA"
            ]
        
        return channels
    
    def save_download_stats(self, video_info):
        try:
            stats = self.load_download_stats()
            
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "title": video_info.get("title", "Bilinmeyen"),
                "uploader": video_info.get("uploader", "Bilinmeyen"),
                "duration": video_info.get("duration", 0),
                "view_count": video_info.get("view_count", 0),
                "url": video_info.get("webpage_url", "")
            }
            
            stats.append(new_entry)
            
            if len(stats) > 100:
                stats = stats[-100:]
            
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Istatistik kaydetme hatasi: {e}")
    
    def load_download_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Istatistik yukleme hatasi: {e}")
            return []
    
    def print_success_notification(self, video_info):
        title = video_info.get("title", "Bilinmeyen Video")
        uploader = video_info.get("uploader", "Bilinmeyen Kanal")
        duration = video_info.get("duration", 0)
        
        print("\n" + "="*60)
        print("YENI VIDEO INDIRILDI!")
        print(f"Baslik: {title}")
        print(f"Kanal: {uploader}")
        print(f"Sure: {duration//60}:{duration%60:02d}")
        print(f"Indirilme Zamani: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
    
    def create_cookie_jar(self):
        """Manuel cookie'lerden cookie jar oluştur"""
        if not self.youtube_cookies:
            return None
            
        try:
            import tempfile
            import http.cookiejar
            
            # Cookie jar oluştur
            cookie_jar = http.cookiejar.MozillaCookieJar()
            
            # JSON parse et
            cookies_dict = json.loads(self.youtube_cookies)
            
            # Her cookie için entry oluştur
            for name, value in cookies_dict.items():
                cookie_jar.set_cookie(http.cookiejar.Cookie(
                    version=0, name=name, value=value,
                    port=None, port_specified=False,
                    domain='.youtube.com', domain_specified=True, domain_initial_dot=True,
                    path='/', path_specified=True,
                    secure=True, expires=None, discard=True, comment=None,
                    comment_url=None, rest={}
                ))
            
            # Temporary file'a kaydet
            cookie_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            cookie_jar.save(cookie_file.name)
            cookie_file.close()
            
            logger.info(f"Cookie jar olusturuldu: {len(cookies_dict)} cookie")
            return cookie_file.name
            
        except Exception as e:
            logger.error(f"Cookie jar olusturma hatasi: {e}")
            return None
    def get_video_info(self, url):
        # Önce manuel cookie'ler ile dene
        if self.youtube_cookies:
            logger.info("Manuel cookie'ler ile video bilgisi aliniyor...")
            cookie_file = self.create_cookie_jar()
            if cookie_file:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "cookiefile": cookie_file,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        logger.info("Manuel cookie'ler ile video bilgisi BASARILI!")
                        # Cookie file'ı temizle
                        try:
                            os.unlink(cookie_file)
                        except:
                            pass
                        return info
                except Exception as e:
                    logger.warning(f"Manuel cookie'ler basarisiz: {e}")
                    # Cookie file'ı temizle
                    try:
                        os.unlink(cookie_file)
                    except:
                        pass
        
        # Fallback: Android client
        logger.info("Fallback: Android client deneniyor...")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "user_agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 12; TR) gzip",
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                    "player_skip": ["webpage", "configs"]
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Video bilgisi alinamadi {url}: {e}")
            return None
    
    
    def download_video(self, url, video_info=None):
        logger.info(f"Video indiriliyor: {url}")
        
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Önce manuel cookie'ler ile dene
        if self.youtube_cookies:
            logger.info("Manuel cookie'ler ile video indiriliyor...")
            cookie_file = self.create_cookie_jar()
            if cookie_file:
                ydl_opts = {
                    "format": self.quality,
                    "outtmpl": os.path.join(self.download_dir, "%(uploader)s - %(title)s.%(ext)s"),
                    "restrictfilenames": True,
                    "noplaylist": True,
                    "writeinfojson": True,
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": ["tr", "en"],
                    "cookiefile": cookie_file,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    logger.info(f"Manuel cookie'ler ile video BASARILI: {url}")
                    
                    if video_info:
                        self.print_success_notification(video_info)
                        self.save_download_stats(video_info)
                    
                    # Cookie file'ı temizle
                    try:
                        os.unlink(cookie_file)
                    except:
                        pass
                    return True
                    
                except Exception as e:
                    logger.warning(f"Manuel cookie'ler ile indirme basarisiz: {e}")
                    # Cookie file'ı temizle
                    try:
                        os.unlink(cookie_file)
                    except:
                        pass
        
        # Fallback: Android client
        logger.info("Fallback: Android client ile indirme deneniyor...")
        ydl_opts = {
            "format": self.quality,
            "outtmpl": os.path.join(self.download_dir, "%(uploader)s - %(title)s.%(ext)s"),
            "restrictfilenames": True,
            "noplaylist": True,
            "writeinfojson": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["tr", "en"],
            "user_agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 12; TR) gzip",
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                    "player_skip": ["webpage", "configs"]
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            logger.info(f"Android client ile video indirildi: {url}")
            
            if video_info:
                self.print_success_notification(video_info)
                self.save_download_stats(video_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Video indirme hatasi {url}: {e}")
            return False
    
    def get_channel_latest_videos_rss(self, channel_url):
        """RSS Feed ile video listesi al - Bot koruması yok!"""
        logger.info(f"RSS Feed ile kanal kontrol ediliyor: {channel_url}")
        
        # Extract channel ID from URL
        channel_id = None
        if "/channel/" in channel_url:
            channel_id = channel_url.split("/channel/")[1].split("/")[0]
        else:
            logger.error("Channel ID bulunamadi - sadece /channel/ URL'leri destekleniyor")
            return []
        
        # YouTube RSS Feed URL
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        logger.info(f"RSS URL: {rss_url}")
        
        try:
            # RSS Feed al
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # XML parse et
            root = ET.fromstring(response.content)
            
            # Namespace tanımları
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015',
                'media': 'http://search.yahoo.com/mrss/'
            }
            
            videos = []
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries[:self.max_videos]:
                # Video ID
                video_id = entry.find('yt:videoId', namespaces)
                if video_id is not None:
                    vid_id = video_id.text
                    
                    # Video title
                    title_elem = entry.find('atom:title', namespaces)
                    title = title_elem.text if title_elem is not None else "Unknown Title"
                    
                    # Channel name
                    author_elem = entry.find('atom:author/atom:name', namespaces)
                    uploader = author_elem.text if author_elem is not None else "Unknown Channel"
                    
                    videos.append({
                        "id": vid_id,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "uploader": uploader
                    })
            
            logger.info(f"RSS Feed ile {len(videos)} video bulundu!")
            return videos
            
        except Exception as e:
            logger.error(f"RSS Feed hatasi: {e}")
            return []
    def get_channel_latest_videos(self, channel_url):
        logger.info(f"Kanal kontrol ediliyor: {channel_url}")
        
        # Önce RSS Feed dene - En stabil yöntem!
        videos = self.get_channel_latest_videos_rss(channel_url)
        if videos:
            return videos
        
        logger.warning("RSS Feed basarisiz - Chrome cookies deneniyor...")
        
        # Handle URL warning
        if "/@" in channel_url:
            logger.warning("Handle URL tespit edildi. Daha stabil bir 'channel' veya 'c/' URL kullanilmasi onerilir.")
        
        # Safe /videos addition with format detection
        if "/channel/" in channel_url:
            if not channel_url.endswith("/videos"):
                channel_url = channel_url.rstrip("/") + "/videos"
        elif "/c/" in channel_url:
            if not channel_url.endswith("/videos"):
                channel_url = channel_url.rstrip("/") + "/videos"
        elif "/@" in channel_url:
            if not channel_url.endswith("/videos"):
                channel_url = channel_url.rstrip("/") + "/videos"
        
        logger.info(f"Final URL: {channel_url}")
        
        # First try with Chrome cookies
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": self.max_videos,
            "cookies_from_browser": ("chrome", None, None, None),
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        try:
            logger.info("Chrome cookie'leri ile deneniyor...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                if "entries" in info:
                    videos = []
                    for entry in info["entries"][:self.max_videos]:
                        if entry and entry.get("id") and len(entry.get("id", "")) == 11:
                            videos.append({
                                "id": entry.get("id"),
                                "title": entry.get("title"),
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "uploader": info.get("uploader", "Unknown")
                            })
                    logger.info(f"Chrome cookie'leri ile {len(videos)} video bulundu!")
                    return videos
                else:
                    logger.warning(f"Chrome cookie'leri ile videolara erisilemedi")
                    
        except Exception as e:
            logger.warning(f"Chrome cookie'leri basarisiz: {e}")
        
        # Fallback to Android client
        logger.info("Fallback: Android client deneniyor...")
        ydl_opts_fallback = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": self.max_videos,
            "user_agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 12; TR) gzip",
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                    "player_skip": ["webpage", "configs"]
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                if "entries" in info:
                    videos = []
                    for entry in info["entries"][:self.max_videos]:
                        if entry and entry.get("id") and len(entry.get("id", "")) == 11:
                            videos.append({
                                "id": entry.get("id"),
                                "title": entry.get("title"),
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "uploader": info.get("uploader", "Unknown")
                            })
                    logger.info(f"Android client ile {len(videos)} video bulundu!")
                    return videos
                else:
                    logger.warning(f"Android client ile videolara erisilemedi")
                    return []
                    
        except Exception as e:
            logger.error(f"Android client de basarisiz: {e}")
            return []
    
    def load_downloaded_videos(self):
        db_file = "downloaded_videos.json"
        try:
            if os.path.exists(db_file):
                with open(db_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Indirilen video veritabani yuklenemedi: {e}")
            return set()
    
    def save_downloaded_video(self, video_id):
        db_file = "downloaded_videos.json"
        try:
            downloaded = self.load_downloaded_videos()
            downloaded.add(video_id)
            with open(db_file, "w", encoding="utf-8") as f:
                json.dump(list(downloaded), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Indirilen video veritabani kaydedilemedi: {e}")
    
    def monitor_channels(self):
        logger.info("Kanal monitorleme baslatildi")
        logger.info(f"Environment YOUTUBE_CHANNELS: {os.getenv('YOUTUBE_CHANNELS', 'TANIMSIZ')}")
        logger.info(f"Kullanilacak kanallar: {self.channels}")
        
        downloaded_videos = self.load_downloaded_videos()
        new_downloads = 0
        
        for channel_url in self.channels:
            try:
                videos = self.get_channel_latest_videos(channel_url)
                
                # Kanal listesi alındıktan sonra kısa bekleme
                time.sleep(3)
                
                for video in videos:
                    video_id = video["id"]
                    
                    if video_id not in downloaded_videos:
                        logger.info(f"Yeni video bulundu: {video['title']}")
                        
                        # Video bilgisini almadan önce bekleme
                        time.sleep(2)
                        video_info = self.get_video_info(video["url"])
                        
                        if self.download_video(video["url"], video_info):
                            self.save_downloaded_video(video_id)
                            new_downloads += 1
                            
                            # Çok uzun bekleme süresi - bot algılamasını azaltır
                            time.sleep(15)
                    else:
                        logger.debug(f"Video zaten indirilmis: {video['title']}")
                        
            except Exception as e:
                logger.error(f"Kanal isleme hatasi {channel_url}: {e}")
                continue
        
        logger.info(f"Monitorleme tamamlandi. {new_downloads} yeni video indirildi.")
        
        if new_downloads == 0:
            print("Kanal monitorleme tamamlandi. Yeni video bulunamadi.")
        else:
            print(f"Toplam {new_downloads} yeni video indirildi!")
        
        return new_downloads
    
    def download_single_video(self, url):
        logger.info(f"Manuel video indirme: {url}")
        
        video_info = self.get_video_info(url)
        if video_info:
            success = self.download_video(url, video_info)
            if success:
                self.save_downloaded_video(video_info.get("id"))
            return success
        return False
    
    def cleanup_old_videos(self, days=7):
        logger.info(f"Son {days} gunken eski videolar temizleniyor...")
        
        try:
            download_path = Path(self.download_dir)
            if not download_path.exists():
                return
            
            current_time = time.time()
            deleted_count = 0
            
            for file_path in download_path.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > (days * 24 * 3600):
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Eski dosya silindi: {file_path.name}")
            
            logger.info(f"Temizlik tamamlandi. {deleted_count} dosya silindi.")
            
        except Exception as e:
            logger.error(f"Dosya temizleme hatasi: {e}")

def main():
    logger.info("=== YouTube Downloader Baslatiliyor ===")
    
    try:
        downloader = YouTubeDownloader()
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "monitor":
                downloader.monitor_channels()
                
            elif command == "download" and len(sys.argv) > 2:
                video_url = sys.argv[2]
                print(f"Tek video indiriliyor: {video_url}")
                success = downloader.download_single_video(video_url)
                if success:
                    print("Video basariyla indirildi!")
                else:
                    print("Video indirilemedi!")
                    
            elif command == "cleanup":
                days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
                downloader.cleanup_old_videos(days)
                
            elif command == "stats":
                stats = downloader.load_download_stats()
                print(f"\nToplam indirilen video: {len(stats)}")
                if stats:
                    print("\nSon 5 indirilen video:")
                    for i, stat in enumerate(stats[-5:], 1):
                        print(f"{i}. {stat['title']} - {stat['uploader']}")
                        print(f"   {stat['timestamp'][:19]}")
                
            else:
                print("Gecersiz komut!")
                print("Kullanim:")
                print("  python main.py monitor          - Kanallari monitor et")
                print("  python main.py download [URL]   - Tek video indir")
                print("  python main.py cleanup [days]   - Eski dosyalari temizle")
                print("  python main.py stats            - Istatistikleri goster")
        else:
            print("Varsayilan mod: Kanal monitorleme baslatiliyor...")
            downloader.monitor_channels()
            
    except KeyboardInterrupt:
        logger.info("Program kullanici tarafindan durduruldu")
        print("\nProgram durduruldu!")
        
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        print(f"Hata olustu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
