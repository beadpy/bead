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
import socket # Eklenen import

from .router import get_routes
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware
from bead.compiler.parser import parse_bead_file
from bead.exceptions import CompilerError
from bead.config import load_config

# This function is defined as an exception handler, so it must be inside the Starlette application.
async def not_found(request, exc):
    return HTMLResponse("<h1>404 Page Not Found</h1>", status_code=404)

def get_app(project_path):
    # Load configuration first
    config = load_config(project_path)
    
    routes = get_routes(project_path)
    # Get SECRET_KEY from config or environment variable
    SECRET_KEY = config.get("security", {}).get("secret_key", os.environ.get("SECRET_KEY", "a-secret-key-that-should-be-changed"))
    middleware = [
        Middleware(SessionMiddleware, secret_key=SECRET_KEY),
        Middleware(LoggingMiddleware),
        Middleware(SecurityHeadersMiddleware)
    ]
    
    # Pass config and project_path to the app state
    app = Starlette(debug=True, routes=routes, exception_handlers={404: not_found}, middleware=middleware)
    app.state.project_path = project_path
    app.state.config = config
    
    return app

class ChangeEventHandler(FileSystemEventHandler):
    def __init__(self, server_process, shutdown_event):
        self.server_process = server_process
        self.shutdown_event = shutdown_event

    def on_any_event(self, event):
        if event.is_directory:
            return None
        
        print(f"INFO:  Change detected: {event.src_path}")
        self.shutdown_event.set()

def start_dev_server(project_path):
    """
    Starts the development server for the specified project path.
    """
    full_path = os.path.abspath(project_path)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

    print("Bead Development Server is starting...")
    
    try:
        pages_dir = os.path.join(full_path, "pages")
        for root, dirs, files in os.walk(pages_dir):
            for file_name in files:
                if file_name.endswith(".bead"):
                    file_path = os.path.join(root, file_name)
                    parse_bead_file(file_path)
        print("INFO:  All .bead files compiled successfully.")
    except CompilerError as e:
        print(f"ERROR: Compilation error: {e}")
        return

    # Check for port in config file and use default if not found
    try:
        config = load_config(full_path)
        port = config.get("server", {}).get("port", 8000)
    except Exception:
        port = 8000
    
    print(f"Application: http://localhost:{port}")
    print("Watching for file changes...")

    while True:
        try:
            shutdown_event = threading.Event()
            
            # Sunucuyu ayrı bir iş parçacığında (thread) başlat
            server_thread = threading.Thread(target=uvicorn.run, 
                                            args=(get_app(full_path),),
                                            kwargs={"host": "0.0.0.0", "port": port},
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
            server_thread.join(timeout=10) # Bekleme süresini 10 saniyeye çıkardık
            
            # Watchdog izleyicisini durdur
            observer.stop()
            observer.join()

            print("INFO:  Server restarting...")
            time.sleep(1)
        
        except KeyboardInterrupt:
            print("INFO:  Server stopped.")
            break
        except Exception as e:
            if isinstance(e, socket.error) and e.errno == 10048:
                print(f"ERROR: Port {port} is already in use. Waiting for it to be released...")
                time.sleep(10) # Bekleme süresini 10 saniyeye çıkardık
            else:
                print(f"An error occurred: {e}")
                break

if __name__ == "__main__":
    start_dev_server(".")