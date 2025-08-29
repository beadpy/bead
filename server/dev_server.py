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
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import socket

from .router import get_routes
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware
from bead.compiler.parser import clear_cache
from bead.config import load_config

async def not_found(request, exc):
    return HTMLResponse("<h1>404 Sayfa Bulunamadı</h1>", status_code=404)

def get_app(project_path):
    config = load_config(project_path)
    routes = get_routes(project_path)
    SECRET_KEY = config.get("security", {}).get("secret_key", os.environ.get("SECRET_KEY", "a-secret-key-that-should-be-changed"))
    middleware = [
        Middleware(SessionMiddleware, secret_key=SECRET_KEY),
        Middleware(LoggingMiddleware),
        Middleware(SecurityHeadersMiddleware)
    ]
    app = Starlette(debug=True, routes=routes, exception_handlers={404: not_found}, middleware=middleware)
    app.state.project_path = project_path
    app.state.config = config
    return app

def run_server(config):
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

class ChangeEventHandler(FileSystemEventHandler):
    def __init__(self, loop, restart_event):
        self.loop = loop
        self.restart_event = restart_event

    def on_any_event(self, event):
        if event.is_directory:
            return None
        clear_cache()
        print(f"INFO:  Değişiklik algılandı: {event.src_path}")
        self.loop.call_soon_threadsafe(self.restart_event.set)

def start_dev_server(project_path):
    """
    Starts the development server for the specified project path.
    """
    full_path = os.path.abspath(project_path)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

    print("Bead Geliştirme Sunucusu başlatılıyor...")
    
    try:
        config_obj = load_config(full_path)
        port = config_obj.get("server", {}).get("port", 8000)
    except Exception:
        port = 8000
    
    print(f"Uygulama: http://localhost:{port}")
    print("Dosya değişiklikleri izleniyor...")

    while True:
        try:
            restart_event = asyncio.Future()
            
            app = get_app(full_path)
            config = uvicorn.Config(app, host="0.0.0.0", port=port)
            server_process = threading.Thread(target=run_server, args=(config,), daemon=True)
            
            # Sunucu iş parçağını başlat
            server_process.start()

            # Watchdog ile dosya değişikliklerini izle
            event_handler = ChangeEventHandler(asyncio.get_event_loop(), restart_event)
            observer = Observer()
            observer.schedule(event_handler, full_path, recursive=True)
            observer.start()

            # Yeniden başlatma sinyalini bekle
            try:
                asyncio.get_event_loop().run_until_complete(restart_event)
            except KeyboardInterrupt:
                print("INFO:  Sunucu durduruluyor...")
                break
            
            # Watchdog izleyicisini durdur
            observer.stop()
            observer.join()

            print("INFO:  Sunucu yeniden başlatılıyor...")
            time.sleep(1)
        
        except KeyboardInterrupt:
            print("INFO:  Sunucu durduruldu.")
            break
        except Exception as e:
            if isinstance(e, socket.error) and e.errno == 10048:
                print(f"HATA: Port {port} zaten kullanımda. Lütfen başka bir işlem tarafından kullanılıp kullanılmadığını kontrol edin veya başka bir port belirtin.")
                return
            else:
                print(f"Bir hata oluştu: {e}")
                return

if __name__ == "__main__":
    start_dev_server(".")