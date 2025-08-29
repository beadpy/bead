# bead/server/router.py

import os
import importlib.util
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from functools import partial
from itsdangerous import TimedSerializer
from itsdangerous import BadSignature
import os
import pathlib
import inspect
import asyncio
# HTTPException'ı buraya ekliyoruz
from starlette.exceptions import HTTPException
from bead.compiler.parser import parse_bead_file, find_return_value
from bead.compiler.renderer import render_page
from bead.styles.compiler import generate_css, extract_classes, get_style_map
from bead.exceptions import CompilerError

# Bu küme, tüm render işlemlerinde bulunan stil sınıflarını toplayacak.
# Set kullanmamızın sebebi, tekrar edenleri otomatik olarak elemesidir.
_all_utility_classes = set()

async def handle_request_and_render(file_path, request):
    """
    İstekleri işler, .bead dosyasını parse eder, HTML olarak render eder ve
    stil sınıflarını toplayarak CSS dosyasını günceller.
    """
    global _all_utility_classes
    _all_utility_classes.clear()

    # Dosya bulunamazsa HTTPException fırlat
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Page not found.")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File read error: {e}")

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
        'asyncio': __import__('asyncio'),
        'random': __import__('random')
    }

    try:
        exec(source_code, page_namespace)
        default_func = page_namespace.get('default')

        if not default_func:
            raise HTTPException(status_code=500, detail="'default' function not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compilation error: {e}")

    context = {
        "request": request,
        "query": request.query_params,
        "headers": request.headers,
        "session": request.session
    }
    params = request.path_params
    
    try:
        if inspect.iscoroutinefunction(default_func):
            component_tree = await default_func(params, context)
        else:
            component_tree = default_func(params, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Runtime error in page function: {e}")

    # Düzeltme burada: Eğer layout varsa, sayfa içeriğini layout'un içine yerleştir
    layout_path = os.path.join(os.path.dirname(file_path), "_layout.bead")
    if os.path.exists(layout_path):
        try:
            with open(layout_path, "r", encoding="utf-8") as f:
                layout_source_code = f.read()

            layout_namespace = page_namespace.copy()
            exec(layout_source_code, layout_namespace)
            layout_func = layout_namespace.get('default')

            if inspect.iscoroutinefunction(layout_func):
                layout_tree = await layout_func(params, context, children=component_tree)
            else:
                layout_tree = layout_func(params, context, children=component_tree)

            component_tree = layout_tree
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Layout error: {e}")

    if not component_tree:
        raise HTTPException(status_code=500, detail="Component tree could not be created.")
    
    csrf_token = None
    config = request.app.state.config
    security_settings = config.get("security", {})
    if security_settings.get("csrf"):
        secret_key = config.get("security", {}).get("secret_key", os.environ.get("SECRET_KEY", "a-secret-key-that-should-be-changed"))
        s = TimedSerializer(secret_key)
        csrf_token = s.dumps({'_csrf_token': os.urandom(32).hex()})
        request.session['_csrf_token'] = csrf_token
    
    html_content = await render_page(component_tree, _all_utility_classes, csrf_token=csrf_token)
    
    dynamic_style_map = get_style_map(config.settings)
    
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
        config = request.app.state.config
        security_settings = config.get("security", {})
        if security_settings.get("csrf"):
            csrf_token = request.session.get('_csrf_token')
            if not csrf_token:
                raise HTTPException(status_code=403, detail="CSRF token not found in session.")
            
            try:
                data = await request.json()
                form_token = data.get("csrf_token")
                secret_key = config.get("security", {}).get("secret_key", os.environ.get("SECRET_KEY", "a-secret-key-that-should-be-changed"))
                s = TimedSerializer(secret_key)
                s.loads(form_token)
                if form_token != csrf_token:
                    raise HTTPException(status_code=403, detail="CSRF token mismatch.")
            except (BadSignature, ValueError, KeyError):
                raise HTTPException(status_code=403, detail="Invalid CSRF token.")

    if hasattr(module, '_render_after_event'):
        new_component_tree = await module._render_after_event(request)
        if new_component_tree:
            html_content = render_page(new_component_tree)
            return JSONResponse({"patch": html_content})

    if not hasattr(module, 'handler'):
        raise HTTPException(status_code=500, detail="Handler function not found in module.")

    handler_func = getattr(module, 'handler')
    
    # Handler asenkron ise await ile çağır
    if inspect.iscoroutinefunction(handler_func):
        response_data = await handler_func(request)
    else:
        response_data = handler_func(request)

    try:
        if isinstance(response_data, RedirectResponse):
            return response_data
        
        # Eğer yanıt bir sözlükse, JSONResponse'a dönüştür.
        if isinstance(response_data, dict):
            return JSONResponse(response_data)
        
        # Mevcut JSONResponse ve diğer yanıt türleri için
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Runtime error in API handler: {e}")

async def handle_api_request(request):
    """
    _events/ adresine gelen istekleri işler ve API handler'larına yönlendirir.
    """
    handler_name = request.path_params.get("handler")
    api_dir = os.path.join(request.app.state.project_path, "pages", "api")
    handler_path = os.path.join(api_dir, f"{handler_name}.py")

    if not os.path.exists(handler_path):
        raise HTTPException(status_code=404, detail="Handler not found.")

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
        raise HTTPException(status_code=404, detail="Handler not found.")

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
    
    # Layout dosyalarını ve normal sayfaları ayır
    layout_routes = []
    page_routes = []
    
    # .bead dosyalarını bul ve rotalarını oluştur
    for file_path in pages_path.rglob('*.bead'):
        # Özel _layout dosyaları için ayrı bir rota oluştur
        if file_path.name.startswith('_layout'):
            continue
        
        # Relatif yolu al ve URL formatına çevir
        relative_path_parts = file_path.relative_to(pages_path).parts
        
        # Uzantıyı kaldır
        page_name = relative_path_parts[-1].removesuffix('.bead')
        path_parts = list(relative_path_parts[:-1]) + [page_name]
        
        # Dinamik segmentleri { } ile değiştir
        url_parts = []
        for p in path_parts:
            # [...slug] -> {slug:path}
            if p.startswith("[...") and p.endswith("]"):
                param_name = p[4:-1]
                url_parts.append(f"{{{param_name}:path}}")
            # [id] -> {id}
            elif p.startswith("[") and p.endswith("]"):
                param_name = p[1:-1]
                url_parts.append(f"{{{param_name}}}")
            else:
                url_parts.append(p)

        url_path = "/" + "/".join(url_parts)
        
        print(f"INFO:  Rota oluşturuldu: {url_path} -> {file_path}")
        
        page_routes.append(Route(url_path, endpoint=partial(handle_request_and_render, str(file_path))))

    # index.bead için özel rota
    index_file = pages_path / "index.bead"
    if index_file.exists():
        page_routes.append(Route("/", endpoint=partial(handle_request_and_render, str(index_file))))

    # Normal rotaları layout rotalarından önce ekle
    routes.extend(page_routes)
    routes.extend(layout_routes)
    
    # Özel API rotalarını ekle (bu kısım daha önce yerleştirilmeli)
    routes.append(Route("/_events/{handler}", endpoint=handle_api_request, methods=["POST"]))
    routes.append(Route("/api/{handler}", endpoint=handle_api_endpoint, methods=["POST"]))

    return routes