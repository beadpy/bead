# bead/server/middleware.py

from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.middleware.sessions import SessionMiddleware # Yeni import

# Diğer middleware sınıfları burada kalacak
# ...

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # İstek işlenmeden önce yapılacaklar
        print("INFO:  Middleware: Gelen istek:", scope['path'])

        # Uygulamayı çağır
        await self.app(scope, receive, send)

        # Yanıt gönderildikten sonra yapılacaklar
        print("INFO:  Middleware: İstek tamamlandı.")

class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Güvenlik başlıklarını ekle
                message["headers"].append([b"X-Frame-Options", b"DENY"])
                message["headers"].append([b"X-Content-Type-Options", b"nosniff"])

            await send(message)

        await self.app(scope, receive, send_with_headers)