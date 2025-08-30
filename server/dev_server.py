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
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_MODIFIED
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

# Uvicorn'un 'reload' için çağıracağı yeni fabrika fonksiyonu
def create_app():
    # Bu fonksiyon, projenin kök dizinini bilmek için sys.path kullanır
    project_path = os.getcwd()
    return get_app(project_path)

def start_dev_server(project_path):
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
    print("CTRL+C tuşuna basarak çıkabilirsiniz.")

    # Uvicorn'un yerleşik hot-reload özelliğini kullanın
    # 'create_app' fonksiyonunun içe aktarma dizesini iletin
    uvicorn.run(
        "bead.server.dev_server:create_app",
        host="0.0.0.0",
        port=port,
        factory=True,
        reload=True,
        reload_dirs=[full_path],
        log_level="info"
    )

if __name__ == "__main__":
    start_dev_server(".")