# MASTER IMPLEMENTATION PROMPT — Minecraft ServerCreator

---

## ZORUNLU DAVRANIŞLAR VE KALİTE STANDARTLARI

Sen bir **Senior Software Engineer**'sın. Bu görevde amatörlük kesinlikle yasaktır. Her satır kod, bir production ortamına deploy ediliyormuş gibi yazılacaktır. Aşağıdaki standartlar tartışmaya kapalıdır:

- **Kurumsal dil**: Tüm yorum satırları, log mesajları, hata mesajları ve kullanıcıya yönelik metinler profesyonel, temiz ve kurumsal bir dille yazılacaktır. Kısaltmalar, argo veya belirsiz ifadeler yasaktır.
- **Sıfır bug toleransı**: Kodu teslim etmeden önce her modülü zihinsel olarak çalıştır. Edge case'leri düşün. Olası hataları öngör, try/except/finally bloklarıyla yönet. Eksik import, tanımsız değişken, yanlış yol, encoding hatası, race condition gibi yaygın tuzaklardan kaçın.
- **Profesyonel mimari**: Spaghetti kod yasaktır. Sorumlulukları net sınıflar/modüller/fonksiyonlar arasında böl. Her fonksiyon tek bir iş yapar.
- **Savunmacı programlama**: Kullanıcıdan gelen her girişi doğrula. Ağ çağrılarında timeout, retry ve fallback mekanizmaları uygula. Dosya işlemlerinde atomik yazma kullan.
- **Eksiksiz teslimat**: Çalıştırılabilir, bağımlılıkları yönetilmiş, dosya yapısı tam olan bir proje teslim et. "Bu kısım sana bırakıldı" veya "bu kısmı kendin tamamla" gibi ifadeler kesinlikle yasaktır.

---

## PROJE TANIMI

**Proje Adı:** ServerCreator  
**Tür:** Python tabanlı masaüstü GUI uygulaması  
**Platform:** Windows 10/11 (birincil hedef), Python 3.10+  
**Framework:** PyQt6  
**Amaç:** Kullanıcının teknik bilgiye ihtiyaç duymadan Minecraft Java Edition sunucusu kurmasını sağlayan, tam otomatik, çok dilli, profesyonel bir masaüstü uygulaması.

---

## LOGO VE İKON

Proje dizininde `assets/logo.ico` dosyası mevcuttur. Bu dosya kullanıcı tarafından sağlanmıştır ve aşağıdaki her yerde kullanılacaktır:

- **Pencere ikonu**: `QMainWindow.setWindowIcon(QIcon("assets/logo.ico"))` — tüm pencereler ve diyaloglar dahil.
- **Görev çubuğu ikonu**: `QApplication.setWindowIcon(QIcon("assets/logo.ico"))` — uygulama başlarken `QApplication` nesnesine atanır.
- **Üst bar logosu**: Sihirbazın her adımındaki üst bar sol köşesinde `logo.ico` dosyasından türetilmiş 32×32 px boyutunda `QLabel` + `QPixmap` ile gösterilir.
- **Karşılama ekranı**: Dil seçim ekranında ve karşılama adımında 64×64 px olarak ortalanmış biçimde gösterilir.
- **PyInstaller paketi**: `logo.ico`, `--icon=assets/logo.ico` parametresiyle EXE'ye gömülür. `sys._MEIPASS` farkındalığıyla kaynak yolu her ortamda doğru çözümlenir.

### Kaynak Yolu Çözümleme (Kritik):
```python
import sys
import os

def get_asset_path(relative_path: str) -> str:
    """
    PyInstaller ile paketlenmiş ortamda ve geliştirme ortamında
    doğru kaynak yolunu döndürür.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
```

Bu fonksiyon `main.py` veya ayrı bir `utils.py` modülünde tanımlanır ve ikon/logo yükleyen her yerde kullanılır. Sabit string yol kullanımı yasaktır.

---

## DİL DESTEĞİ

Uygulama **Türkçe** ve **İngilizce** olmak üzere iki dili tam olarak destekleyecektir.

### Teknik Gereksinimler:
- Tüm kullanıcıya görünen metinler (butonlar, etiketler, başlıklar, bildirimler, hata mesajları, log çıktıları, kurulum adım açıklamaları, soru metinleri) bir `translations.py` modülünde merkezi sözlük yapısıyla yönetilecektir.
- Seçilen dil `config.json` dosyasında kalıcı olarak saklanacaktır.
- Dil değişikliği anlık olarak tüm aktif widget'lara yansıyacaktır (dinamik retranslation).
- Kurulum sürecinde yaratılan tüm log mesajları, kurulum adım başlıkları ve durum bildirimleri seçili dilde gösterilecektir.
- Desteklenen diller: `tr` (Türkçe), `en` (İngilizce).
- Varsayılan dil: İngilizce (`en`). İlk çalıştırmada dil seçim ekranı gösterilecektir.

---

## DOSYA VE PROJE YAPISI

```
ServerCreator/
├── main.py                    # Uygulama giriş noktası
├── config.json                # Kullanıcı tercihleri (dil, tema, son kullanılan yol)
├── requirements.txt           # Tüm Python bağımlılıkları
├── translations.py            # TR/EN metin sözlükleri
├── utils.py                   # Yardımcı fonksiyonlar (get_asset_path vb.)
├── version_cache.json         # Tarama sonucu sürüm/altyapı cache'i
├── assets/
│   └── logo.ico               # Uygulama logosu ve ikonu (kullanıcı tarafından sağlandı)
├── core/
│   ├── __init__.py
│   ├── version_manager.py     # Sürüm tarama, cache yönetimi
│   ├── downloader.py          # Dosya indirme, doğrulama
│   ├── installer.py           # Kurulum süreci yöneticisi
│   ├── server_configurator.py # server.properties ve eula.txt yönetimi
│   └── java_manager.py        # Java sürüm tespiti ve yönetimi
└── ui/
    ├── __init__.py
    ├── main_window.py         # Ana pencere ve navigasyon
    ├── language_selector.py   # İlk çalıştırma dil seçimi
    ├── step_welcome.py        # Adım 1: Karşılama ve altyapı seçimi
    ├── step_version.py        # Adım 2: Sürüm seçimi
    ├── step_directory.py      # Adım 3: Sunucu adı ve kurulum dizini
    ├── step_resources.py      # Adım 4: RAM ve performans ayarları
    ├── step_config.py         # Adım 5: Sunucu yapılandırma soruları
    ├── step_install.py        # Adım 6: Kurulum ekranı (canlı log)
    ├── step_complete.py       # Adım 7: Tamamlanma ekranı
    └── widgets/
        ├── __init__.py
        ├── animated_progress.py
        ├── styled_combo.py
        └── log_viewer.py
```

---

## ALTYAPI VE SÜRÜM YÖNETİMİ

### Desteklenen Altyapılar:
| Altyapı | Resmi Kaynak | İndirme Mekanizması |
|---|---|---|
| **Vanilla** | `launchermeta.mojang.com` | Manifest JSON |
| **Spigot** | `getbukkit.org` + BuildTools | BuildTools.jar ile derleme |
| **CraftBukkit** | `getbukkit.org` | Doğrudan JAR indirme |
| **Paper** | `api.papermc.io/v2` | REST API (stabil build) |
| **Fabric** | `meta.fabricmc.net` | REST API |
| **Forge** | `files.minecraftforge.net` | HTML parse veya RSS |
| **NeoForge** | `maven.neoforged.net` / `neoforged.net` | Maven metadata veya REST |
| **Purpur** | `api.purpurmc.org/v2` | REST API |

### Otomatik Sürüm Taraması:
- Uygulama her gün **bir kez** (son tarama zamanı `version_cache.json`'da tutulur) tüm altyapılar için desteklenen Minecraft sürümlerini ilgili API/endpoint'lerden çeker.
- Tarama sonuçları `version_cache.json`'a kaydedilir (TTL: 24 saat). Uygulama açıkken cache süresi dolmuşsa arka planda `QThread` ile yenilenir.
- Her altyapı için yalnızca **o altyapının desteklediği** Minecraft sürümleri gösterilir. Desteklenmeyen sürümler arayüzde gözükmez.
- Tarama başarısız olursa (ağ hatası vb.) son geçerli cache kullanılır ve kullanıcı bilgilendirilir.
- Sürümler arayüzde **en yeniden en eskiye** sıralı gösterilir.

### Java Yönetimi:
- `java_manager.py` sistemde yüklü Java sürümünü tespit eder (`java -version` çıktısı parse edilir).
- Seçilen Minecraft sürümüne göre gereken Java sürümü belirlenir (MC 1.17+ → Java 16+, MC 1.20.5+ → Java 21+).
- Java eksik veya uyumsuzsa kullanıcıya açık bir uyarı verilir ve resmi Java indirme sayfasına yönlendiren bağlantı sunulur. Kurulum durdurulmaz; kullanıcı devam etmeyi seçebilir ancak risk konusunda bilgilendirilir.

---

## KURULUM SÜRECİ — ADIM ADIM AKIM

### Adım 1: Karşılama & Altyapı Seçimi
- Üst alanda `logo.ico` (64×64 px), "ServerCreator" başlığı ve kısa uygulama açıklaması.
- Altyapı seçim kartları (her kart: altyapı adı, kısa açıklama, "Önerilen" etiketi uygunsa).
- "Hangi altyapıyı seçmeliyim?" yardım butonu → bilgi paneli açılır.

### Adım 2: Sürüm Seçimi
- Seçilen altyapı için desteklenen sürümler dropdown'dan seçilir.
- Sürümler yüklenirken spinner gösterilir.
- Seçilen sürüme ait notlar (örn. "Bu sürüm için Java 21 gereklidir") altında gösterilir.

### Adım 3: Sunucu Adı ve Kurulum Dizini ← YENİ
Bu adım kurulum başlamadan önce iki temel bilgiyi alır:

#### 3A — Sunucu Adı:
- **Alan tipi**: Tek satır metin girişi (`QLineEdit`).
- **Etiket**: "Sunucu Adı" / "Server Name"
- **Açıklama**: "Sunucunuz için bir ad belirleyin. Bu ad, kurulum klasörünün adı olarak kullanılacaktır."
- **Doğrulama kuralları** (anlık, kullanıcı yazarken):
  - Boş bırakılamaz.
  - Minimum 3, maksimum 64 karakter.
  - Yalnızca harf, rakam, tire (`-`) ve alt çizgi (`_`) ve boşluk karakterine izin verilir.
  - Windows'ta geçersiz dosya adı karakterleri (`\ / : * ? " < > |`) kesinlikle reddedilir; kullanıcıya anlık uyarı gösterilir.
  - Girişin baş ve sonundaki boşluklar otomatik olarak temizlenir (trim).
  - Geçerli bir girişte "İleri" butonu aktif olur; geçersizde pasif kalır.
- **Varsayılan**: Boş (kullanıcı mutlaka doldurmak zorundadır).

#### 3B — Kurulum Dizini:
- **Alan tipi**: Salt okunur metin (`QLineEdit`) + "Gözat" butonu.
- **Etiket**: "Kurulum Konumu" / "Installation Location"
- **Açıklama**: "Sunucu dosyalarının yerleştirileceği ana klasörü seçin. Sunucunuz bu klasörün içinde '<Sunucu Adı>' adlı bir alt klasöre kurulacaktır."
- **Varsayılan yol**: `C:\Users\<kullanıcı>\AppData\Roaming\ServerCreator\Servers\`
- **Gerçek kurulum yolu önizlemesi**: Her iki alan da dolduğunda aşağıda önizleme satırı gösterilir:
  ```
  📁 Kurulum Yolu: C:\...\Servers\BenimSunucum\
  ```
- **Doğrulama**:
  - Dizin mevcut değilse oluşturulabilir olmalıdır (üst dizin yazılabilir olmalı).
  - Disk alanı kontrolü: seçilen sürücüde minimum 2 GB boş alan önerilir; yetersizse uyarı gösterilir ama engellenmez.
  - Dizin yazma izni `os.access(path, os.W_OK)` ile kontrol edilir; izin yoksa hata mesajı ve farklı dizin seçim isteği gösterilir.

#### Klasör Oluşturma Mantığı:
Kurulum başladığında (`step_install.py`) aşağıdaki sıra izlenir:
```
seçilen_dizin / sunucu_adı /
```
Örnek: Kullanıcı `C:\Servers` seçtiyse ve sunucu adı `BenimSunucum` ise:
```
C:\Servers\BenimSunucum\
```
Bu klasör kurulumun ilk adımında `os.makedirs(path, exist_ok=False)` ile oluşturulur. `exist_ok=False` kullanılır çünkü aynı isimde klasör zaten varsa kullanıcıya "Bu isimde bir sunucu zaten mevcut. Üzerine yazmak ister misiniz?" diyaloğu gösterilir. Kullanıcı "Hayır" derse Adım 3'e geri döner.

### Adım 4: Performans Ayarları
Kullanıcıya aşağıdaki ayarlar sorulur, akıllı varsayılanlar önerilir:

| Ayar | Tip | Varsayılan | Açıklama |
|---|---|---|---|
| Maksimum RAM (Xmx) | Slider + Spinbox (MB) | Sistem RAM'inin %50'si | Min: 512 MB, Max: Sistem RAM'inin %80'i |
| Minimum RAM (Xms) | Slider + Spinbox (MB) | Xmx ile eşit | Genellikle Xmx'e eşit tutulması önerilir |
| Çekirdek sayısı | Bilgi gösterimi | N/A | Bilgilendirme amaçlı gösterilir |
| JVM Optimizasyon Bayrağları | Checkbox | ✅ Etkin | Aikars flags veya G1GC flags eklenir |
| start.bat / start.sh üret | Checkbox | ✅ Etkin | Kurulum sonrası başlatma script'i |

Sistem RAM'i `psutil` ile tespit edilir.

### Adım 5: Sunucu Yapılandırma
Kullanıcıya aşağıdaki sorular sorulur. Her soru için varsayılan değer ve açıklama gösterilir:

| Soru | Tip | Varsayılan | server.properties Karşılığı |
|---|---|---|---|
| Premium (online-mode) girişi | Toggle/Radio | Evet (true) | `online-mode=true/false` |
| Maksimum oyuncu sayısı | Spinbox | 20 | `max-players=N` |
| Varsayılan Oyun Modu | Dropdown | Survival | `gamemode=survival/creative/adventure/spectator` |
| Zorlu (hardcore) mod | Toggle | Hayır | `hardcore=true/false` |
| Whitelist aktif mi? | Toggle | Hayır | `white-list=true/false` |
| Sunucu portu | Spinbox | 25565 | `server-port=N` |
| PvP aktif mi? | Toggle | Evet | `pvp=true/false` |
| Nether dünyası | Toggle | Evet | `allow-nether=true/false` |
| Seed (opsiyonel) | Metin | (boş) | `level-seed=...` |

### Adım 6: Kurulum
Kurulum aşağıdaki sırayla ilerler ve her adım log panelinde canlı olarak gösterilir:

1. **[BAŞLATILIYOR]** Kurulum dizini oluşturuluyor: `<seçilen_yol>\<sunucu_adı>\`
2. **[İNDİRİLİYOR]** `<altyapı>-<sürüm>.jar` indiriliyor. İlerleme çubuğu (byte/toplam, %, hız, kalan süre) gösterilir.
3. **[DOĞRULANIYIYOR]** İndirilen dosyanın SHA-256/MD5 checksum'ı doğrulanır (API'nin sağladığı hash ile).
4. **[ÇALIŞTIRILIYOR]** Sunucu ilk kez başlatılır (`java -jar server.jar nogui`). Bu adımda `eula.txt` oluşturulur.
5. **[EULA]** `eula.txt` dosyası otomatik olarak `eula=true` olarak güncellenir.
6. **[YAPILANDIRILIYOR]** Sunucu ikinci kez başlatılır, `server.properties` oluşturulur.
7. **[DÜZENLENİYOR]** `server.properties` dosyası kullanıcının seçimlerine göre güncellenir.
8. **[MOTD]** `motd` alanı şu şekilde ayarlanır (dile göre):
   - TR: `motd=\u00A7fBu sunucu \u00A7aServerCreator\u00A7f tarafından oluşturulmuştur.`
   - EN: `motd=\u00A7fThis server was created by \u00A7aServerCreator\u00A7f.`
9. **[SCRIPT]** `start.bat` (Windows) ve `start.sh` (Linux/macOS) dosyaları oluşturulur.
10. **[TAMAMLANDI]** Kurulum başarıyla tamamlandı.

Her adım `[✓]`, `[!]` (uyarı) veya `[✗]` (hata) simgesiyle işaretlenir.

**Kritik**: Herhangi bir adım başarısız olursa hata mesajı log'a yazılır, kullanıcıya açıklayıcı bir diyalog gösterilir ve kurulum güvenli biçimde durdurulur. Kullanıcı "Yeniden Dene" veya "İptal Et" seçeneğine sahiptir.

### Adım 7: Tamamlanma Ekranı
- `logo.ico` (64×64 px) ve yeşil onay simgesi yan yana.
- "Sunucu başarıyla kuruldu!" / "Server successfully installed!" başlığı.
- Sunucu adı ve tam kurulum yolu (tıklanabilir, Windows Explorer'da açar).
- "Sunucuyu Başlat" butonu (`start.bat` çalıştırır).
- "Yeni Sunucu Kur" butonu (sihirbazı sıfırlar, tüm state temizlenir).
- "Kapat" butonu.

---

## EULA.TXT YÖNETİMİ

`eula.txt` dosyası oluştuğunda:
1. Dosya UTF-8 ile okunur.
2. `eula=false` satırı `eula=true` ile değiştirilir.
3. Dosya UTF-8 kodlamasıyla geri yazılır.
4. İşlem log'a yazılır.
5. Kurulum kaldığı yerden devam eder.

---

## SERVER.PROPERTIES MOTD FORMATI

Türkçe dil seçiliyken:
```
motd=\u00A7fBu sunucu \u00A7aServerCreator\u00A7f tarafından oluşturulmuştur.
```

İngilizce dil seçiliyken:
```
motd=\u00A7fThis server was created by \u00A7aServerCreator\u00A7f.
```

- `\u00A7f` = Beyaz (`§f`)
- `\u00A7a` = Yeşil (`§a`)

---

## TASARIM VE ARAYÜZ

### Genel Estetik:
- **Tema**: Koyu, profesyonel. `#0D1117` arka plan, `#161B22` kart/panel, `#21262D` kenarlık.
- **Vurgu rengi**: `#3FB950` (Minecraft'ın yeşili — marka tutarlılığı).
- **Metin**: `#E6EDF3` birincil, `#8B949E` ikincil.
- **Hata**: `#F85149`, **Uyarı**: `#D29922`, **Başarı**: `#3FB950`.
- **Font**: `Segoe UI` (Windows sistem fontu, fallback: `Arial`). Kod/log alanlarında `Consolas` veya `Courier New`.
- **Köşe yuvarlaklığı**: 8px (kartlar), 4px (butonlar, inputlar).
- **Kenar boşlukları**: Tutarlı 16px/24px grid sistemi.

### Sihirbaz Navigasyonu:
- Sol panelde dikey adım indikatörü (1–7 adım, mevcut adım vurgulu, tamamlananlar onaylı).
- Üst bar: `logo.ico` (32×32 px) + "ServerCreator" metni sol köşede; dil seçici ve versiyon bilgisi sağda.
- Alt bar: "Geri" ve "İleri / Başlat" butonları. Aktif olmayan adımlarda "İleri" butonu devre dışı.

### Adım 3 Arayüzü (Sunucu Adı + Dizin):
- İki bölüm net görsel ayırıcıyla bölünmüş: üstte "Sunucu Adı", altta "Kurulum Konumu".
- Her bölümde başlık, açıklama metni, input ve anlık doğrulama mesajı.
- Önizleme satırı: her iki alan geçerliyken gerçek kurulum yolunu yeşil metin ile gösterir.
- Geçersiz durumda input kenarlığı kırmızı (`#F85149`), geçerlide yeşil (`#3FB950`).

### Log Görüntüleyici (Adım 6):
- Satıra özgü renk kodlaması: `[INFO]` beyaz, `[WARNING]` sarı, `[ERROR]` kırmızı, `[SUCCESS]` yeşil.
- Otomatik scroll (yeni satır geldiğinde alta kaydırır, kullanıcı kaydırdıysa otomatik scroll durur).
- "Log'u Kopyala" butonu.
- "Log'u Kaydet" butonu (`.txt` dosyasına kaydeder).

---

## VERİ AKTARIMI: SESSION STATE

Adımlar arası tüm veriler merkezi bir `ServerSession` dataclass'ında tutulur:

```python
@dataclass
class ServerSession:
    # Adım 1
    platform: str = ""           # "vanilla", "paper", "fabric", vb.
    # Adım 2
    mc_version: str = ""         # "1.21.1", "1.20.4", vb.
    # Adım 3
    server_name: str = ""        # "BenimSunucum"
    base_directory: str = ""     # "C:\Servers\"
    install_path: str = ""       # "C:\Servers\BenimSunucum\" (otomatik hesaplanır)
    # Adım 4
    xms_mb: int = 1024
    xmx_mb: int = 2048
    use_aikar_flags: bool = True
    generate_start_script: bool = True
    # Adım 5
    online_mode: bool = True
    max_players: int = 20
    gamemode: str = "survival"
    hardcore: bool = False
    whitelist: bool = False
    server_port: int = 25565
    pvp: bool = True
    allow_nether: bool = True
    level_seed: str = ""
```

`install_path`, `server_name` veya `base_directory` değiştiğinde otomatik olarak `os.path.join(base_directory, server_name)` ile güncellenir.

---

## ARKA PLAN İŞ PARÇACIKLARI (QThread)

Arayüz donmaması için şu işlemler `QThread` veya `QRunnable` ile arka planda çalıştırılır:
- Sürüm taraması
- Dosya indirme
- Java sürümü tespiti
- Sunucu JAR'ının ilk çalıştırılması
- Disk alanı kontrolü

Her thread tamamlandığında `pyqtSignal` ile ana thread'e bildirim gönderir.

---

## BAĞIMLILIKLAR (requirements.txt)

```
PyQt6>=6.6.0
requests>=2.31.0
psutil>=5.9.0
packaging>=23.0
```

---

## KRİTİK HATA YÖNETİMİ SENARYOLARI

| Senaryo | Beklenen Davranış |
|---|---|
| Ağ bağlantısı yok | Cache kullanılır; indirme adımında hata diyaloğu + yeniden dene |
| İndirme yarıda kesildi | Kısmi dosya silinir, yeniden deneme seçeneği sunulur |
| Checksum uyuşmazlığı | Dosya silinir, kullanıcı bilgilendirilir, yeniden dene önerilir |
| Java bulunamadı | Uyarı verilir, download linki sunulur |
| Yazma izni yok | Farklı dizin seçmesi istenir |
| Disk alanı yetersiz | Kurulum başlamadan uyarı verilir |
| `server.properties` bulunamadı | Varsayılan şablondan oluşturulur |
| JAR çalıştırma hatası | stderr çıktısı log'a yazılır, kullanıcıya önerilir |
| API rate limit / timeout | Exponential backoff (3 deneme), ardından cache fallback |
| Sunucu adı geçersiz karakter içeriyor | Anlık validation, "İleri" butonu devre dışı, kırmızı uyarı metni |
| Klasör zaten mevcut | "Üzerine yaz / Geri dön" diyaloğu gösterilir |
| `logo.ico` dosyası bulunamadı | Hata fırlatılmaz; ikon atamaları sessizce atlanır, uygulama çalışmaya devam eder |

---

## START.BAT İÇERİĞİ (Windows)

```bat
@echo off
chcp 65001 > nul
title {SERVER_NAME} — Minecraft Server (ServerCreator)
echo [ServerCreator] "{SERVER_NAME}" sunucusu baslatiliyor...
java -Xms{XMS}M -Xmx{XMX}M {JVM_FLAGS} -jar server.jar nogui
pause
```

`{SERVER_NAME}`, `{XMS}`, `{XMX}` ve `{JVM_FLAGS}` `ServerSession` verisinden doldurulur.

Aikars JVM bayrakları (`-XX:+UseG1GC` vb.) kullanıcı onayladıysa eklenir.

---

## TAŞINABILIRLIK VE DAĞITIM

- Tüm kullanıcı verileri (`config.json`, `version_cache.json`) `%APPDATA%\ServerCreator\` altında tutulur.
- `PyInstaller` ile tek EXE'ye paketlenebilir olmalıdır.
- `assets/logo.ico` PyInstaller spec dosyasında `datas` listesine dahil edilir ve `--icon=assets/logo.ico` ile EXE'ye gömülür.
- Tüm kaynak yüklemeleri `get_asset_path()` fonksiyonu üzerinden yapılır.

---

## GELİŞTİRME VE TESLİMAT TALİMATLARI

1. Yukarıdaki dosya yapısını eksiksiz oluştur. Her dosyayı yaz.
2. `translations.py` içindeki tüm metin anahtarlarının TR ve EN karşılıklarını doldur.
3. `ServerSession` dataclass'ını merkezi state yönetimi olarak tüm adım widget'larına enjekte et.
4. Adım 3'teki sunucu adı doğrulamasını (validasyon) eksiksiz ve anlık çalışır biçimde uygula.
5. Klasör oluşturma mantığını kurulum başında, tüm diğer işlemlerden önce çalıştır.
6. `get_asset_path()` fonksiyonunu `utils.py`'de tanımla ve `logo.ico`'yu yükleyen her yerde kullan.
7. Her modülü ayrı ayrı uygula. Modüller arası bağımlılıkları `__init__.py` dosyalarıyla yönet.
8. Her sınıf ve public fonksiyon için docstring yaz.
9. Kodu tamamladıktan sonra potansiyel hataları gözden geçir ve düzelt.
10. `requirements.txt` dosyasını yaz.
11. Kurulum ve çalıştırma talimatlarını içeren `README.md` dosyasını yaz (TR ve EN).
12. `main.py` dosyasını, `python main.py` komutuyla sorunsuz çalışacak şekilde yaz.

**Hiçbir modülü yarım bırakma. Hiçbir fonksiyonu "TODO" ile geç. Bu bir production projesidir.**
