"""
Centralised translation dictionaries for ServerCreator.

The application supports Turkish (``tr``) and English (``en``). Every piece of
user-facing text is keyed here. The active language is chosen on first launch
and persisted; per the product requirements it cannot be changed afterwards.

Usage::

    from translations import Translator
    tr = Translator("tr")
    tr.t("welcome_title")
    tr.t("install_path_preview", path=r"C:\\Servers\\MyServer")
"""

from __future__ import annotations

from typing import Dict


SUPPORTED_LANGUAGES = ("en", "tr")
DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "tr": "Türkçe",
}


_STRINGS: Dict[str, Dict[str, str]] = {
    # ------------------------------------------------------------------ common
    "app_name": {"en": "ServerCreator", "tr": "ServerCreator"},
    "app_tagline": {
        "en": "Create a Minecraft Java server in minutes — no technical knowledge required.",
        "tr": "Dakikalar içinde Minecraft Java sunucusu kurun — teknik bilgi gerektirmez.",
    },
    "btn_back": {"en": "Back", "tr": "Geri"},
    "btn_next": {"en": "Next", "tr": "İleri"},
    "btn_start": {"en": "Start Installation", "tr": "Kurulumu Başlat"},
    "btn_close": {"en": "Close", "tr": "Kapat"},
    "btn_cancel": {"en": "Cancel", "tr": "İptal"},
    "btn_retry": {"en": "Retry", "tr": "Yeniden Dene"},
    "btn_yes": {"en": "Yes", "tr": "Evet"},
    "btn_no": {"en": "No", "tr": "Hayır"},
    "btn_browse": {"en": "Browse", "tr": "Gözat"},
    "btn_continue": {"en": "Continue", "tr": "Devam Et"},
    "publisher_by": {"en": "by X1NPAR1", "tr": "X1NPAR1 tarafından"},

    # ------------------------------------------------------------ language pick
    "language_title": {"en": "Choose your language", "tr": "Dilinizi seçin"},
    "language_subtitle": {
        "en": "This selection is permanent and cannot be changed later.",
        "tr": "Bu seçim kalıcıdır ve sonradan değiştirilemez.",
    },
    "language_confirm": {"en": "Confirm", "tr": "Onayla"},

    # ------------------------------------------------------- theme (selectable)
    "theme_label": {"en": "Theme", "tr": "Tema"},
    "theme_dark": {"en": "Dark", "tr": "Koyu"},
    "theme_light": {"en": "Light", "tr": "Açık"},

    # ------------------------------------------------------------ steps / nav
    "step_welcome": {"en": "Welcome", "tr": "Karşılama"},
    "step_version": {"en": "Version", "tr": "Sürüm"},
    "step_directory": {"en": "Name & Location", "tr": "Ad ve Konum"},
    "step_resources": {"en": "Performance", "tr": "Performans"},
    "step_config": {"en": "Configuration", "tr": "Yapılandırma"},
    "step_install": {"en": "Installation", "tr": "Kurulum"},
    "step_complete": {"en": "Complete", "tr": "Tamamlandı"},

    # ------------------------------------------------------------- step 1
    "welcome_title": {"en": "Choose a server platform", "tr": "Bir sunucu altyapısı seçin"},
    "welcome_help": {"en": "Which platform should I choose?", "tr": "Hangi altyapıyı seçmeliyim?"},
    "platform_recommended": {"en": "Recommended", "tr": "Önerilen"},
    "platform_vanilla_desc": {
        "en": "The official, unmodified Minecraft server from Mojang.",
        "tr": "Mojang'ın resmi, değiştirilmemiş Minecraft sunucusu.",
    },
    "platform_paper_desc": {
        "en": "High-performance fork of Spigot with plugin support. Best overall choice.",
        "tr": "Eklenti destekli, yüksek performanslı Spigot türevi. En iyi genel seçim.",
    },
    "platform_purpur_desc": {
        "en": "Paper fork with extensive configuration options.",
        "tr": "Geniş yapılandırma seçenekleri sunan Paper türevi.",
    },
    "platform_spigot_desc": {
        "en": "Plugin-capable server compiled locally with BuildTools.",
        "tr": "BuildTools ile yerel derlenen, eklenti destekli sunucu.",
    },
    "platform_craftbukkit_desc": {
        "en": "Classic plugin platform. Lower performance than Paper.",
        "tr": "Klasik eklenti platformu. Paper'dan daha düşük performans.",
    },
    "platform_fabric_desc": {
        "en": "Lightweight, modern modding platform.",
        "tr": "Hafif ve modern mod platformu.",
    },
    "platform_forge_desc": {
        "en": "The most widely used modding platform.",
        "tr": "En yaygın kullanılan mod platformu.",
    },
    "platform_neoforge_desc": {
        "en": "Modern community-driven fork of Forge.",
        "tr": "Forge'un modern, topluluk odaklı türevi.",
    },
    "platform_help_text": {
        "en": (
            "Vanilla is the pure Minecraft experience. Paper and Purpur offer the "
            "best performance and support plugins. Spigot and CraftBukkit are older "
            "plugin platforms. Fabric, Forge and NeoForge are for running mods."
        ),
        "tr": (
            "Vanilla saf Minecraft deneyimidir. Paper ve Purpur en iyi performansı "
            "sunar ve eklentileri destekler. Spigot ve CraftBukkit eski eklenti "
            "platformlarıdır. Fabric, Forge ve NeoForge modlar içindir."
        ),
    },

    # ------------------------------------------------------------- step 2
    "version_title": {"en": "Select a Minecraft version", "tr": "Bir Minecraft sürümü seçin"},
    "version_label": {"en": "Minecraft version", "tr": "Minecraft sürümü"},
    "version_loading": {"en": "Loading available versions…", "tr": "Mevcut sürümler yükleniyor…"},
    "version_load_failed": {
        "en": "Could not load versions. Showing the last cached list.",
        "tr": "Sürümler yüklenemedi. Son önbelleğe alınan liste gösteriliyor.",
    },
    "version_none": {
        "en": "No versions are available for this platform right now.",
        "tr": "Bu altyapı için şu anda uygun sürüm bulunmuyor.",
    },
    "version_java_note": {
        "en": "This version requires Java {java}+.",
        "tr": "Bu sürüm Java {java}+ gerektirir.",
    },

    # ------------------------------------------------------------- step 3
    "dir_title": {"en": "Server name and location", "tr": "Sunucu adı ve konumu"},
    "server_name_label": {"en": "Server Name", "tr": "Sunucu Adı"},
    "server_name_desc": {
        "en": "Choose a name for your server. It will be used as the installation folder name.",
        "tr": "Sunucunuz için bir ad belirleyin. Bu ad, kurulum klasörünün adı olarak kullanılacaktır.",
    },
    "install_loc_label": {"en": "Installation Location", "tr": "Kurulum Konumu"},
    "install_loc_desc": {
        "en": "Choose the parent folder for the server files. Your server will be installed into a "
              "'<Server Name>' subfolder inside it.",
        "tr": "Sunucu dosyalarının yerleştirileceği ana klasörü seçin. Sunucunuz bu klasörün içinde "
              "'<Sunucu Adı>' adlı bir alt klasöre kurulacaktır.",
    },
    "install_path_preview": {
        "en": "📁 Installation path: {path}",
        "tr": "📁 Kurulum Yolu: {path}",
    },
    "name_err_empty": {"en": "The server name cannot be empty.", "tr": "Sunucu adı boş bırakılamaz."},
    "name_err_length": {
        "en": "The name must be between 3 and 64 characters.",
        "tr": "Ad 3 ile 64 karakter arasında olmalıdır.",
    },
    "name_err_chars": {
        "en": "Only letters, digits, spaces, hyphens and underscores are allowed.",
        "tr": "Yalnızca harf, rakam, boşluk, tire ve alt çizgi karakterlerine izin verilir.",
    },
    "dir_err_writable": {
        "en": "The selected location is not writable. Please choose another folder.",
        "tr": "Seçilen konuma yazılamıyor. Lütfen başka bir klasör seçin.",
    },
    "dir_warn_space": {
        "en": "Low disk space (less than 2 GB free). Installation can continue but may fail.",
        "tr": "Düşük disk alanı (2 GB'tan az boş alan). Kurulum sürebilir ancak başarısız olabilir.",
    },

    # ------------------------------------------------------------- step 4
    "res_title": {"en": "Performance settings", "tr": "Performans ayarları"},
    "res_xmx": {"en": "Maximum RAM (Xmx)", "tr": "Maksimum RAM (Xmx)"},
    "res_xms": {"en": "Minimum RAM (Xms)", "tr": "Minimum RAM (Xms)"},
    "res_cores": {"en": "Detected CPU cores: {cores}", "tr": "Tespit edilen çekirdek sayısı: {cores}"},
    "res_total_ram": {"en": "Total system RAM: {ram}", "tr": "Toplam sistem RAM'i: {ram}"},
    "res_aikar": {"en": "Apply JVM optimization flags (Aikar's flags)", "tr": "JVM optimizasyon bayraklarını uygula (Aikar's flags)"},
    "res_script": {"en": "Generate start scripts (start.bat / start.sh)", "tr": "Başlatma betikleri üret (start.bat / start.sh)"},

    # ------------------------------------------------------------- step 5
    "cfg_title": {"en": "Server configuration", "tr": "Sunucu yapılandırması"},
    "cfg_online": {"en": "Premium (online-mode) login", "tr": "Premium (online-mode) girişi"},
    "cfg_max_players": {"en": "Maximum players", "tr": "Maksimum oyuncu sayısı"},
    "cfg_gamemode": {"en": "Default game mode", "tr": "Varsayılan oyun modu"},
    "cfg_hardcore": {"en": "Hardcore mode", "tr": "Zorlu (hardcore) mod"},
    "cfg_whitelist": {"en": "Enable whitelist", "tr": "Whitelist aktif"},
    "cfg_port": {"en": "Server port", "tr": "Sunucu portu"},
    "cfg_pvp": {"en": "Enable PvP", "tr": "PvP aktif"},
    "cfg_nether": {"en": "Allow the Nether", "tr": "Nether dünyası"},
    "cfg_seed": {"en": "World seed (optional)", "tr": "Dünya tohumu (opsiyonel)"},
    "gm_survival": {"en": "Survival", "tr": "Survival"},
    "gm_creative": {"en": "Creative", "tr": "Creative"},
    "gm_adventure": {"en": "Adventure", "tr": "Adventure"},
    "gm_spectator": {"en": "Spectator", "tr": "Spectator"},

    # ------------------------------------------------------------- step 6
    "install_title": {"en": "Installing your server", "tr": "Sunucunuz kuruluyor"},
    "btn_copy_log": {"en": "Copy Log", "tr": "Log'u Kopyala"},
    "btn_save_log": {"en": "Save Log", "tr": "Log'u Kaydet"},
    "log_saved": {"en": "Log saved to: {path}", "tr": "Log kaydedildi: {path}"},
    "log_creating_dir": {"en": "Creating installation directory: {path}", "tr": "Kurulum dizini oluşturuluyor: {path}"},
    "log_downloading": {"en": "Downloading {file}", "tr": "{file} indiriliyor"},
    "log_verifying": {"en": "Verifying download integrity", "tr": "İndirilen dosyanın bütünlüğü doğrulanıyor"},
    "log_verify_skip": {"en": "No checksum provided by the source; skipping verification.", "tr": "Kaynak sağlama değeri sunmadı; doğrulama atlandı."},
    "log_running_first": {"en": "Starting the server for the first time to generate files", "tr": "Dosyaları oluşturmak için sunucu ilk kez başlatılıyor"},
    "log_eula": {"en": "Accepting the EULA (eula=true)", "tr": "EULA kabul ediliyor (eula=true)"},
    "log_configuring": {"en": "Generating server.properties", "tr": "server.properties oluşturuluyor"},
    "log_editing": {"en": "Applying your configuration to server.properties", "tr": "Yapılandırmanız server.properties dosyasına uygulanıyor"},
    "log_motd": {"en": "Setting the message of the day (MOTD)", "tr": "Günün mesajı (MOTD) ayarlanıyor"},
    "log_scripts": {"en": "Creating start scripts", "tr": "Başlatma betikleri oluşturuluyor"},
    "log_done": {"en": "Installation completed successfully.", "tr": "Kurulum başarıyla tamamlandı."},
    "log_failed": {"en": "Installation failed: {error}", "tr": "Kurulum başarısız oldu: {error}"},
    "install_overwrite_title": {"en": "Folder already exists", "tr": "Klasör zaten mevcut"},
    "install_overwrite_text": {
        "en": "A server with this name already exists at this location. Overwrite it?",
        "tr": "Bu isimde bir sunucu bu konumda zaten mevcut. Üzerine yazmak ister misiniz?",
    },

    # ------------------------------------------------------------- step 7
    "complete_title": {"en": "Server successfully installed!", "tr": "Sunucu başarıyla kuruldu!"},
    "complete_path": {"en": "Installation path:", "tr": "Kurulum yolu:"},
    "btn_open_folder": {"en": "Open Folder", "tr": "Klasörü Aç"},
    "btn_launch_server": {"en": "Launch Server", "tr": "Sunucuyu Başlat"},
    "btn_new_server": {"en": "Create Another Server", "tr": "Yeni Sunucu Kur"},

    # ------------------------------------------------------------- java
    "java_missing_title": {"en": "Java not detected", "tr": "Java bulunamadı"},
    "java_missing_text": {
        "en": "Java {required}+ is required for this version but was not detected. You may continue, "
              "but the server may not start. Download Java?",
        "tr": "Bu sürüm için Java {required}+ gereklidir ancak tespit edilemedi. Devam edebilirsiniz "
              "ancak sunucu başlamayabilir. Java indirilsin mi?",
    },
    "java_outdated_text": {
        "en": "Detected Java {found}, but Java {required}+ is required. You may continue at your own risk.",
        "tr": "Java {found} tespit edildi ancak Java {required}+ gereklidir. Riski size ait olmak üzere devam edebilirsiniz.",
    },
    "java_download": {"en": "Download Java", "tr": "Java İndir"},

    # ------------------------------------------------------------- update
    "update_title": {"en": "Update available", "tr": "Güncelleme mevcut"},
    "update_text": {
        "en": "A new version ({version}) of ServerCreator is available. You are using {current}. "
              "Download and install it now?",
        "tr": "ServerCreator'ın yeni bir sürümü ({version}) mevcut. Şu anda {current} kullanıyorsunuz. "
              "Şimdi indirilip kurulsun mu?",
    },
    "update_downloading": {"en": "Downloading update…", "tr": "Güncelleme indiriliyor…"},
    "update_ready": {
        "en": "The update has been downloaded. The application will now close and the installer will start.",
        "tr": "Güncelleme indirildi. Uygulama şimdi kapanacak ve yükleyici başlayacak.",
    },
    "update_failed": {"en": "The update could not be downloaded.", "tr": "Güncelleme indirilemedi."},

    # ------------------------------------------------------------- navigation / shell
    "nav_create": {"en": "Create Server", "tr": "Sunucu Oluştur"},
    "nav_servers": {"en": "My Servers", "tr": "Sunucularım"},
    "btn_go_servers": {"en": "Go to My Servers", "tr": "Sunucularıma Git"},

    # ------------------------------------------------------------- my servers
    "servers_title": {"en": "My Servers", "tr": "Sunucularım"},
    "servers_empty": {
        "en": "You have no servers yet. Let's create your first one.",
        "tr": "Henüz bir sunucunuz yok. İlk sunucunuzu oluşturalım.",
    },
    "server_status_running": {"en": "Running", "tr": "Çalışıyor"},
    "server_status_stopped": {"en": "Stopped", "tr": "Kapalı"},
    "server_status_starting": {"en": "Starting…", "tr": "Başlatılıyor…"},
    "btn_start_server": {"en": "Start", "tr": "Başlat"},
    "btn_stop_server": {"en": "Stop", "tr": "Durdur"},
    "btn_open_folder": {"en": "Open Folder", "tr": "Klasörü Aç"},
    "btn_delete_server": {"en": "Delete Server", "tr": "Sunucuyu Sil"},
    "btn_back_to_list": {"en": "‹ Back", "tr": "‹ Geri"},
    "btn_manage": {"en": "Manage", "tr": "Yönet"},

    # detail tabs
    "tab_console": {"en": "Console", "tr": "Konsol"},
    "tab_properties": {"en": "Properties", "tr": "Özellikler"},
    "tab_worlds": {"en": "Worlds", "tr": "Dünyalar"},
    "tab_info": {"en": "Info", "tr": "Bilgi"},

    "console_input_placeholder": {"en": "Type a command and press Enter…", "tr": "Bir komut yazıp Enter'a basın…"},
    "console_server_off": {"en": "— Server is stopped —", "tr": "— Sunucu kapalı —"},
    "console_server_started": {"en": "— Server starting —", "tr": "— Sunucu başlatılıyor —"},

    "info_status": {"en": "Status", "tr": "Durum"},
    "info_players": {"en": "Online players", "tr": "Aktif oyuncular"},
    "info_uptime": {"en": "Uptime", "tr": "Çalışma süresi"},
    "info_cpu": {"en": "CPU usage", "tr": "İşlemci kullanımı"},
    "info_memory": {"en": "Memory usage", "tr": "Bellek kullanımı"},
    "info_platform": {"en": "Platform", "tr": "Altyapı"},
    "info_version": {"en": "Version", "tr": "Sürüm"},
    "info_port": {"en": "Port", "tr": "Port"},
    "info_path": {"en": "Location", "tr": "Konum"},
    "stat_not_available": {"en": "N/A", "tr": "—"},

    "props_save": {"en": "Save changes", "tr": "Değişiklikleri kaydet"},
    "props_saved": {"en": "Properties saved. Restart the server to apply.", "tr": "Özellikler kaydedildi. Uygulamak için sunucuyu yeniden başlatın."},
    "props_key": {"en": "Key", "tr": "Anahtar"},
    "props_value": {"en": "Value", "tr": "Değer"},

    "worlds_current": {"en": "Active world: {name}", "tr": "Aktif dünya: {name}"},
    "worlds_new": {"en": "New World", "tr": "Yeni Dünya"},
    "worlds_new_prompt": {"en": "Name for the new world:", "tr": "Yeni dünyanın adı:"},
    "worlds_new_done": {"en": "New world '{name}' set. It will be generated on the next start.", "tr": "Yeni dünya '{name}' ayarlandı. Bir sonraki başlatmada oluşturulacak."},
    "worlds_backup": {"en": "Back Up", "tr": "Yedekle"},
    "worlds_backup_done": {"en": "Backup created: {path}", "tr": "Yedek oluşturuldu: {path}"},
    "worlds_backup_running": {"en": "Stop the server before backing up the world.", "tr": "Dünyayı yedeklemeden önce sunucuyu durdurun."},

    "delete_confirm_title": {"en": "Delete server", "tr": "Sunucuyu sil"},
    "delete_confirm_text": {
        "en": "This will permanently delete '{name}' and all of its files. Continue?",
        "tr": "Bu işlem '{name}' sunucusunu ve tüm dosyalarını kalıcı olarak siler. Devam edilsin mi?",
    },

    "tray_show": {"en": "Open ServerCreator", "tr": "ServerCreator'ı Aç"},
    "tray_quit": {"en": "Quit", "tr": "Çıkış"},
    "tray_running_bg": {"en": "ServerCreator is still running in the background.", "tr": "ServerCreator arka planda çalışmaya devam ediyor."},
    "close_running_title": {"en": "Servers are running", "tr": "Sunucular çalışıyor"},
    "close_running_text": {
        "en": "The following servers are still running and will be stopped if you quit:\n\n{servers}\n\nQuit and stop them?",
        "tr": "Şu sunucular hâlâ çalışıyor ve çıkarsanız durdurulacaktır:\n\n{servers}\n\nÇıkıp durdurulsun mu?",
    },

    # ------------------------------------------------------------- generic
    "error_title": {"en": "Error", "tr": "Hata"},
    "warning_title": {"en": "Warning", "tr": "Uyarı"},
    "info_title": {"en": "Information", "tr": "Bilgi"},
    "network_error": {
        "en": "A network error occurred. Please check your connection and try again.",
        "tr": "Bir ağ hatası oluştu. Lütfen bağlantınızı kontrol edip yeniden deneyin.",
    },
}


class Translator:
    """
    Resolves translation keys for a fixed language.

    The language is decided once (at first launch) and the same instance is
    shared across the whole application. Unknown keys fall back to the key
    itself, which makes missing strings obvious during development without
    crashing the user interface.
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def t(self, key: str, **kwargs: object) -> str:
        """
        Return the translated string for ``key`` in the active language.

        Any keyword arguments are substituted into the string using
        ``str.format``. Substitution failures are tolerated and return the raw
        template so a formatting mistake never crashes the UI.
        """
        entry = _STRINGS.get(key)
        if entry is None:
            return key
        template = entry.get(self.language) or entry.get(DEFAULT_LANGUAGE) or key
        if not kwargs:
            return template
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template
