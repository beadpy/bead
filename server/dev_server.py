# bead/server/dev_server.py

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
import os
import sys
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .router import get_routes
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware 

# Bu fonksiyon hata işleyici olarak tanımlandığı için Starlette uygulaması içinde olmalıdır.
async def not_found(request, exc):
    return HTMLResponse("<h1>404 Sayfa Bulunamadı</h1>", status_code=404)

def get_app(project_path):
    routes = get_routes(project_path)
    SECRET_KEY = os.environ.get("SECRET_KEY", "gizli-ve-guclu-bir-anahtar")
    middleware = [
        Middleware(SessionMiddleware, secret_key=SECRET_KEY),
        Middleware(LoggingMiddleware),
        Middleware(SecurityHeadersMiddleware)
    ]
    app = Starlette(debug=True, routes=routes, exception_handlers={404: not_found}, middleware=middleware)
    app.state.project_path = project_path
    return app

class ChangeEventHandler(FileSystemEventHandler):
    def __init__(self, server_process, shutdown_event):
        self.server_process = server_process
        self.shutdown_event = shutdown_event

    def on_any_event(self, event):
        if event.is_directory:
            return None
        
        # Değişiklik algılandığında sunucuyu yeniden başlatmak için olayı tetikle
        print(f"INFO:  Değişiklik algılandı: {event.src_path}")
        self.shutdown_event.set()

def start_dev_server(project_path):
    """
    Belirtilen proje yolu için geliştirme sunucusunu başlatır.
    """
    full_path = os.path.abspath(project_path)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

    print("Bead Geliştirme Sunucusu başlatılıyor...")
    print("Uygulama: http://localhost:8000")
    print("Dosya değişiklikleri izleniyor...")

    while True:
        try:
            shutdown_event = threading.Event()
            
            # Sunucuyu ayrı bir iş parçacığında (thread) başlat
            server_thread = threading.Thread(target=uvicorn.run, 
                                            args=(get_app(full_path),),
                                            kwargs={"host": "0.0.0.0", "port": 8000},
                                            daemon=True)
            server_thread.start()

            # Watchdog ile dosya değişikliklerini izle
            event_handler = ChangeEventHandler(server_thread, shutdown_event)
            observer = Observer()
            observer.schedule(event_handler, full_path, recursive=True)
            observer.start()

            # Sunucu durdurma sinyali bekler
            shutdown_event.wait()
            
            # Sunucu iş parçağını durdur
            server_thread.join(timeout=1)
            
            # Watchdog izleyicisini durdur
            observer.stop()
            observer.join()

            print("INFO:  Sunucu yeniden başlatılıyor...")
            time.sleep(1) # Yeniden başlatma için bekle
        
        except KeyboardInterrupt:
            print("INFO:  Sunucu durduruluyor.")
            break
        except Exception as e:
            print(f"Hata oluştu: {e}")
            break

if __name__ == "__main__":
    start_dev_server(".")