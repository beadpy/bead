# bead/server/dev_server.py

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware # Yeni import
import os
import sys

from .router import get_routes
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware 

async def render_page_as_html(file_path, request=None):
    # Bu kısım ileride gerçek derleyici ile değiştirilecek.
    if "index.bead" in file_path:
        return "<h1>Merhaba, Bead!</h1>"
    return "<h1>404 Sayfa Bulunamadı</h1>"

async def not_found(request, exc):
    return HTMLResponse("<h1>404 Sayfa Bulunamadı</h1>", status_code=404)

def get_app(project_path):
    routes = get_routes(project_path)
    
    # Güvenlik için gizli bir anahtar belirle
    # Üretim ortamında bu değerin bir ortam değişkeninden gelmesi gerekir
    SECRET_KEY = os.environ.get("SECRET_KEY", "gizli-ve-guclu-bir-anahtar")

    # Middleware'ı burada Starlette uygulamasına ekliyoruz
    # Sıralama önemlidir! Oturum middleware'ı ilk sırada olmalı
    middleware = [
        Middleware(SessionMiddleware, secret_key=SECRET_KEY),
        Middleware(LoggingMiddleware),
        Middleware(SecurityHeadersMiddleware)
    ]

    app = Starlette(debug=True, routes=routes, exception_handlers={404: not_found}, middleware=middleware)
    # Proje yolunu uygulama durumuna ekliyoruz.
    app.state.project_path = project_path
    return app

def start_dev_server(project_path):
    """
    Belirtilen proje yolu için geliştirme sunucusunu başlatır.
    """
    full_path = os.path.abspath(project_path)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

    print("Bead Geliştirme Sunucusu başlatılıyor...")
    print("Uygulama: http://localhost:8000")
    uvicorn.run(get_app(full_path), host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_dev_server(".")