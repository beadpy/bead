from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.middleware.sessions import SessionMiddleware

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        print("INFO:  Middleware: Gelen istek:", scope['path'])
        
        await self.app(scope, receive, send)
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
                message["headers"].append([b"X-Frame-Options", b"DENY"])
                message["headers"].append([b"X-Content-Type-Options", b"nosniff"])

                config = scope['app'].state.config
                csp_policy = config.get("security", {}).get("csp")
                if csp_policy:
                    message["headers"].append([b"Content-Security-Policy", csp_policy.encode('utf-8')])

            await send(message)

        await self.app(scope, receive, send_with_headers)