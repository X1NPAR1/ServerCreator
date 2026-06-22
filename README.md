# ServerCreator

<p align="center">
  <img src="assets/logo.ico" width="72" alt="ServerCreator logo">
</p>

<p align="center"><b>v1.76.1</b> — by <b>X1NPAR1</b></p>

> A fully automated, multilingual desktop application that lets anyone create a
> Minecraft Java Edition server without any technical knowledge.

---

## English

### Features
- **Wizard-driven**: pick a platform, version, name, RAM and configuration —
  ServerCreator does the rest.
- **Platforms**: Vanilla, Paper, Purpur, Spigot, CraftBukkit, Fabric, Forge,
  NeoForge — only the versions each platform actually supports are shown.
- **Permanent language choice**: choose Turkish or English on first launch.
  The selection is permanent and shapes the whole application.
- **Consistent themes**: a dark and a light theme, both fully styled — no
  unreadable text or mismatched panels in either mode. The theme can be changed
  at any time.
- **Automatic updates**: on every launch the app checks the release repository
  for a newer setup and, with your approval, downloads and installs it.
- **Java awareness**: detects your Java version and warns when the chosen
  Minecraft version needs a newer one.
- **Server manager ("My Servers")**: start/stop servers, an in-app console with
  command input (no external command window), live status, player count,
  uptime, CPU and memory, an editable `server.properties`, plus world creation
  and backup. Closing the window keeps servers running in the tray; quitting
  warns you first and stops them cleanly.

### Running from source
```bash
pip install -r requirements.txt
python main.py
```

### Building the installer
```bash
pip install pyinstaller
pyinstaller ServerCreator.spec --noconfirm
# then compile the installer with Inno Setup 6:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\ServerCreator.iss
```
The setup file is written to `installer/Output/`.

### Repositories
- **Source**: `github.com/X1NPAR1/ServerCreator`
- **Releases (setup files)**: `github.com/X1NPAR1/ServerCreator-Release`

---

## Türkçe

### Özellikler
- **Sihirbaz tabanlı**: altyapı, sürüm, ad, RAM ve yapılandırmayı seçin —
  gerisini ServerCreator halleder.
- **Altyapılar**: Vanilla, Paper, Purpur, Spigot, CraftBukkit, Fabric, Forge,
  NeoForge — yalnızca her altyapının gerçekten desteklediği sürümler gösterilir.
- **Kalıcı dil seçimi**: ilk açılışta Türkçe veya İngilizce seçin. Bu seçim
  kalıcıdır ve tüm uygulamanın dilini belirler; sonradan değiştirilemez.
- **Uyumlu temalar**: tamamen biçimlendirilmiş koyu ve açık tema — hiçbir modda
  okunamayan yazı veya uyumsuz panel yoktur. Tema istediğiniz zaman
  değiştirilebilir.
- **Otomatik güncelleme**: uygulama her açılışta sürüm deposunu denetler ve
  onayınızla yeni kurulumu indirip yükler.
- **Java denetimi**: Java sürümünüzü tespit eder ve seçtiğiniz Minecraft sürümü
  daha yeni bir Java gerektirdiğinde sizi uyarır.
- **Sunucu yöneticisi ("Sunucularım")**: sunucuları başlatıp durdurun, uygulama
  içi konsoldan komut gönderin (harici cmd penceresi açılmaz), canlı durum,
  oyuncu sayısı, çalışma süresi, CPU ve bellek görün, `server.properties`
  düzenleyin, yeni dünya oluşturup yedek alın. Pencereyi kapatınca sunucular
  tepside çalışmaya devam eder; çıkışta önce uyarılır ve düzgünce durdurulur.

### Kaynaktan çalıştırma
```bash
pip install -r requirements.txt
python main.py
```

### Kurulum dosyasını derleme
```bash
pip install pyinstaller
pyinstaller ServerCreator.spec --noconfirm
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\ServerCreator.iss
```
Kurulum dosyası `installer/Output/` klasörüne yazılır.

---

© 2026 X1NPAR1. ServerCreator.
