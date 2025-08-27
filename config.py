import json
import os

class Config:
    """Projenin tüm global ayarlarını tutar."""
    def __init__(self, settings: dict):
        self.settings = settings
        
    def get(self, key: str, default: any = None):
        """Ayarları güvenli bir şekilde alır."""
        return self.settings.get(key, default)
        
    def __repr__(self):
        return f"Config({self.settings})"
        
def load_config(project_path: str) -> Config:
    """bead.config.json dosyasından ayarları yükler."""
    config_path = os.path.join(project_path, "bead.config.json")
    
    # Varsayılan ayarlar
    default_settings = {
        "server": {
            "port": 8000
        },
        "theme": {},
        "security": {
            "csrf": False,
            "csp": None
        }
    }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_settings = json.load(f)
            # Varsayılan ayarları, kullanıcı ayarları ile birleştir
            settings = {**default_settings, **user_settings}
            # İç içe sözlükleri de birleştir
            for key in default_settings:
                if isinstance(default_settings[key], dict) and key in user_settings:
                    settings[key] = {**default_settings[key], **user_settings[key]}
            
    except FileNotFoundError:
        print("Uyarı: 'bead.config.json' dosyası bulunamadı, varsayılan ayarlar kullanılıyor.")
        settings = default_settings
    except json.JSONDecodeError:
        print("Hata: 'bead.config.json' dosyası geçersiz JSON formatında. Varsayılan ayarlar kullanılıyor.")
        settings = default_settings
        
    return Config(settings)

# Global olarak erişilebilir bir konfigürasyon objesi
# Uygulama başladığında bu yüklenir.
# config_obj = load_config(".")