import json
import os

class Config:
    def __init__(self, settings: dict):
        self.settings = settings
        
    def get(self, key: str, default: any = None):
        return self.settings.get(key, default)
        
    def __repr__(self):
        return f"Config({self.settings})"
        
def load_config(project_path: str) -> Config:
    config_path = os.path.join(project_path, "bead.config.json")
    
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
            settings = {**default_settings, **user_settings}
    
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