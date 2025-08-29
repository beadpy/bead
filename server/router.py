# bead/server/router.py

import os
import importlib.util
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from functools import partial
from itsdangerous import TimedSerializer
from itsdangerous import BadSignature
import os
import pathlib
import inspect # inspect modülünü ekledik

from bead.compiler.parser import parse_bead_file, find_return_value
from bead.compiler.renderer import render_page
from bead.styles.compiler import generate_css, extract_classes, get_style_map
from bead.exceptions import CompilerError

# Bu küme, tüm render işlemlerinde bulunan stil sınıflarını toplayacak.
# Set kullanmamızın sebebi, tekrar eden sınıfları otomatik olarak elemesidir.
_all_utility_classes = set()

async def handle_request_and_render(file_path, request):
    """
    İstekleri işler, .bead dosyasını parse eder, HTML olarak render eder ve
    stil sınıflarını toplayarak CSS dosyasını günceller.
    """
    global _all_utility_classes
    _all_utility_classes.clear()

    # Dosyanın içeriğini oku
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>404 Sayfa Bulunamadı</h1>", status_code=404)

    # Dosya içeriğini güvenli bir ortamda çalıştır
    # Tek bir isim alanı (namespace) kullanıyoruz
    page_namespace = {
        '__file__': file_path,
        '__name__': os.path.splitext(os.path.basename(file_path))[0],
        'Page': __import__('bead.ui.core_components').ui.core_components.Page,
        'Text': __import__('bead.ui.core_components').ui.core_components.Text,
        'Button': __import__('bead.ui.core_components').ui.core_components.Button,
        'Card': __import__('bead.ui.core_components').ui.core_components.Card,
        'Stack': __import__('bead.ui.core_components').ui.core_components.Stack,
        'Link': __import__('bead.ui.core_components').ui.core_components.Link,
        'Image': __import__('bead.ui.core_components').ui.core_components.Image,
        'Form': __import__('bead.ui.core_components').ui.core_components.Form,
        'Input': __import__('bead.ui.core_components').ui.core_components.Input,
        # async-test için asyncio ve random ekliyoruz
        'asyncio': __import__('asyncio'),
        'random': __import__('random')
    }

    try:
        # Dosya içeriğini tek bir isim alanında çalıştır
        exec(source_code, page_namespace)
        
        # 'default' fonksiyonunu yeni isim alanından al
        default_func = page_namespace.get('default')

        if not default_func:
            return HTMLResponse("<h1>Derleme Hatası</h1><p>'default' fonksiyonu bulunamadı.</p>", status_code=500)
    
    except Exception as e:
        return HTMLResponse(f"<h1>Derleme Hatası</h1><p>Dosyayı çalıştırırken bir hata oluştu: {e}</p>", status_code=500)

    # Request ve rota parametrelerinden bir context objesi oluştur
    context = {
        "request": request,
        "query": request.query_params,
        "headers": request.headers,
        "session": request.session
    }

    # Dinamik segmentleri parametre olarak işle
    params = request.path_params
    
    # default fonksiyonunu çağır ve Component ağacını al
    try:
        if inspect.iscoroutinefunction(default_func):
            # Eğer fonksiyon asenkron ise await ile çağır
            component_tree = await default_func(params, context)
        else:
            # Fonksiyon senkron ise direkt çağır
            component_tree = default_func(params, context)
    except Exception as e:
        return HTMLResponse(f"<h1>Çalıştırma Hatası</h1><p>Sayfa fonksiyonunu çalıştırırken bir hata oluştu: {e}</p>", status_code=500)

    if not component_tree:
        return HTMLResponse("<h1>Derleme Hatası</h1><p>Bileşen ağacı oluşturulamadı.</p>", status_code=500)
    
    csrf_token = None
    config = request.app.state.config
    security_settings = config.get("security", {})
    if security_settings.get("csrf"):
        # Gizli anahtarı config'den al, yoksa ortam değişkeninden veya varsayılan bir değer kullan.
        secret_key = config.get("security", {}).get("secret_key", os.environ.get("SECRET_KEY", "a-secret-key-that-should-be-changed"))
        s = TimedSerializer(secret_key)
        csrf_token = s.dumps({'_csrf_token': os.urandom(32).hex()})
        request.session['_csrf_token'] = csrf_token
    
    # render_page fonksiyonunu yeni parametreyle çağırıyoruz
    html_content = render_page(component_tree, _all_utility_classes, csrf_token=csrf_token)
    
    # Yapılandırma dosyasından stil haritasını al
    dynamic_style_map = get_style_map(config.settings)
    
    # CSS dosyasını oluştur ve kaydet
    css_content = generate_css(_all_utility_classes, dynamic_style_map)
    
    public_dir = os.path.join(request.app.state.project_path, "public")
    os.makedirs(public_dir, exist_ok=True)
    with open(os.path.join(public_dir, "bead.css"), "w", encoding="utf-8") as f:
        f.write(css_content)
        
    return HTMLResponse(html_content)

async def _handle_action(request, module):
    """
    Olay handler'ını çalıştırır ve yanıtı işler.
    """
    if request.method == "POST":
        # CSRF korumasını kontrol et
        config = request.app.state.config
        security_settings = config.get("security", {})
        if security_settings.get("csrf"):
            csrf_token = request.session.get('_csrf_token')
            if not csrf_token:
                return JSONResponse({"error": "CSRF token not found in session."}, status_code=403)
            
            try:
                data = await request.json()
                form_token = data.get("csrf_token")
                secret_key = config.get("security", {}).get("secret_key", os.environ.get("SECRET_KEY", "a-secret-key-that-should-be-changed"))
                s = TimedSerializer(secret_key)
                s.loads(form_token) # Token'ı doğrula
                if form_token != csrf_token:
                    return JSONResponse({"error": "CSRF token mismatch."}, status_code=403)
            except (BadSignature, ValueError, KeyError):
                return JSONResponse({"error": "Invalid CSRF token."}, status_code=403)

    if hasattr(module, '_render_after_event'):
        new_component_tree = await module._render_after_event(request)
        if new_component_tree:
            html_content = render_page(new_component_tree)
            return JSONResponse({"patch": html_content})

    if not hasattr(module, 'handler'):
        return JSONResponse({"error": "Handler function not found in module"}, status_code=500)

    handler_func = getattr(module, 'handler')
    
    try:
        response_data = await handler_func(request)
        if isinstance(response_data, RedirectResponse):
            return JSONResponse({"redirect": str(response_data.url)})
        if isinstance(response_data, JSONResponse):
            return response_data
        
        return response_data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def handle_api_request(request):
    """
    _events/ adresine gelen istekleri işler ve API handler'larına yönlendirir.
    """
    handler_name = request.path_params.get("handler")
    api_dir = os.path.join(request.app.state.project_path, "pages", "api")
    handler_path = os.path.join(api_dir, f"{handler_name}.py")

    if not os.path.exists(handler_path):
        return JSONResponse({"error": "Handler not found"}, status_code=404)

    spec = importlib.util.spec_from_file_location(handler_name, handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return await _handle_action(request, module)

async def handle_api_endpoint(request):
    """
    /api/ adresine gelen standart POST isteklerini işler.
    """
    handler_name = request.path_params.get("handler")
    api_dir = os.path.join(request.app.state.project_path, "pages", "api")
    handler_path = os.path.join(api_dir, f"{handler_name}.py")

    if not os.path.exists(handler_path):
        return JSONResponse({"error": "Handler not found"}, status_code=404)

    spec = importlib.util.spec_from_file_location(handler_name, handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return await _handle_action(request, module)

def get_routes(project_path):
    """
    pages/ klasörünü tarar ve dinamik olarak rotalar oluşturur.
    """
    pages_path = pathlib.Path(project_path) / "pages"
    public_path = pathlib.Path(project_path) / "public"
    routes = []
    
    if not pages_path.exists():
        print(f"Hata: 'pages' dizini '{project_path}' içinde bulunamadı.")
        return []

    # Statik dosyalar için rota oluştur
    if public_path.exists():
        routes.append(Mount("/public", StaticFiles(directory=public_path, html=True), name="static"))
    
    # .bead dosyalarını bul ve rotalarını oluştur
    for file_path in pages_path.rglob('*.bead'):
        # Özel dosyaları atla
        if file_path.name.startswith('_layout') or file_path.name == 'index.bead':
            continue

        # Relatif yolu al ve URL formatına çevir
        relative_path_parts = file_path.relative_to(pages_path).parts
        
        # Uzantıyı kaldır
        page_name = relative_path_parts[-1].removesuffix('.bead')
        path_parts = list(relative_path_parts[:-1]) + [page_name]
        
        # Dinamik segmentleri { } ile değiştir
        url_parts = [p.replace("[", "{").replace("]", "}") for p in path_parts]
        url_path = "/" + "/".join(url_parts)
        
        print(f"INFO:  Rota oluşturuldu: {url_path} -> {file_path}")
        
        routes.append(Route(url_path, endpoint=partial(handle_request_and_render, str(file_path))))

    # index.bead için özel rota
    index_file = pages_path / "index.bead"
    if index_file.exists():
        routes.append(Route("/", endpoint=partial(handle_request_and_render, str(index_file))))
    
    # Özel API rotalarını ekle (bu kısım daha önce yerleştirilmeli)
    routes.append(Route("/_events/{handler}", endpoint=handle_api_request, methods=["POST"]))
    routes.append(Route("/api/{handler}", endpoint=handle_api_endpoint, methods=["POST"]))

    return routes