# bead/server/router.py (Final)

import os
import importlib.util
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from functools import partial

from bead.compiler.parser import parse_bead_file
from bead.compiler.renderer import render_page

async def handle_request_and_render(file_path, request):
    """
    İstekleri işler, .bead dosyasını parse eder ve HTML olarak render eder.
    """
    component_tree = parse_bead_file(file_path)

    if not component_tree:
        return HTMLResponse("<h1>Derleme Hatası</h1><p>Bileşen ağacı oluşturulamadı.</p>", status_code=500)
    
    html_content = render_page(component_tree)
    return HTMLResponse(html_content)

async def _handle_action(request, module):
    """
    Olay handler'ını çalıştırır ve yanıtı işler.
    """
    if hasattr(module, '_render_after_event'):
        # Eğer özel bir render fonksiyonu tanımlıysa, onu çağır
        new_component_tree = await module._render_after_event(request)
        if new_component_tree:
            html_content = render_page(new_component_tree)
            return JSONResponse({"patch": html_content})

    # Varsayılan olarak handler'ı çalıştır
    if not hasattr(module, 'handler'):
        return JSONResponse({"error": "Handler function not found in module"}, status_code=500)

    handler_func = getattr(module, 'handler')
    
    try:
        response_data = await handler_func(request)
        return JSONResponse(response_data)
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

def get_routes(project_path):
    """
    pages/ klasörünü tarar ve dinamik olarak rotalar oluşturur.
    """
    pages_dir = os.path.join(project_path, "pages")
    public_dir = os.path.join(project_path, "public")
    routes = []
    
    if not os.path.exists(pages_dir):
        print(f"Hata: 'pages' dizini '{project_path}' içinde bulunamadı.")
        return []
    
    # Favicon için özel bir rota ekliyoruz
    favicon_path = os.path.join(public_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        # Bu satır RedirectResponse ile değiştirildi
        routes.append(Route("/favicon.ico", endpoint=lambda r: RedirectResponse(url="/public/favicon.ico")))

    index_path = os.path.join(pages_dir, "index.bead")
    if os.path.exists(index_path):
        routes.append(Route("/", endpoint=partial(handle_request_and_render, index_path)))
    
    for root, dirs, files in os.walk(pages_dir):
        dirs[:] = [d for d in dirs if not d.startswith("api")]
        files[:] = [f for f in files if not f.startswith("_layout")]
        
        for file_name in files:
            if file_name.endswith(".bead"):
                full_file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(full_file_path, pages_dir)
                
                if relative_path == "index.bead":
                    continue

                url_path = "/" + os.path.splitext(relative_path)[0]
                url_path = url_path.replace("[", "{").replace("]", "}")
                
                routes.append(Route(url_path, endpoint=partial(handle_request_and_render, full_file_path)))
                
    if os.path.exists(public_dir):
        routes.append(Mount("/public", StaticFiles(directory=public_dir, html=True), name="static"))

    # API olaylarını işlemek için özel bir rota ekliyoruz
    # Burada methods=["POST"] argümanını ekleyerek POST isteklerini kabul etmesini sağlıyoruz
    routes.append(Route("/_events/{handler}", endpoint=handle_api_request, methods=["POST"]))

    return routes