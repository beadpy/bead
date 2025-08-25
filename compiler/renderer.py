# bead/compiler/renderer.py

from bead.ui.core_components import Component, Page, Text, Button, Card, Stack

def render_component(component: Component) -> str:
    """
    Tek bir bileşeni HTML string'ine dönüştürür.
    Bu bir recursive (özyinelemeli) fonksiyondur.
    """
    if not isinstance(component, Component):
        # Eğer girdi bir bileşen değilse, string olarak kabul et ve doğrudan döndür
        return str(component)
    
    # Her bileşenin props'unu al
    props = component.props
    component_type = component.component_type

    # Stilleri ve diğer nitelikleri HTML niteliklerine çevir
    attrs = ""
    # Olay (event) niteliklerini işle
    for key, value in props.items():
        if key.startswith("on"):
            # 'onclick' -> 'data-bead-event-onclick'
            attrs += f' data-bead-event-{key}="{value}"'

    if "style" in props:
        attrs += f' class="{props["style"]}"'
    if "href" in props:
        attrs += f' href="{props["href"]}"'
    if "as_" in props:
        tag = props["as_"]
    else:
        # Varsayılan etiketleri belirle
        tag = {
            "Page": "html",
            "Text": "p",
            "Button": "button",
            "Card": "div",
            "Stack": "div"
        }.get(component_type, "div")

    children_html = ""
    if "children" in props and isinstance(props["children"], list):
        # Çocuk bileşenleri recursive olarak render et
        children_html = "".join([render_component(child) for child in props["children"]])

    if component_type == "Page":
        # Page bileşeni özel bir yapıda olduğu için farklı render edilir
        title = props.get("title", "Bead App")
        body_content = "".join([render_component(child) for child in props["body"]])
        return (f"<!DOCTYPE html><html><head><title>{title}</title>"
                f"</head><body>{body_content}</body></html>")

    if component_type == "Text":
        value = props.get("value", "")
        return f'<{tag}{attrs}>{value}</{tag}>'
    
    if component_type == "Button":
        label = props.get("label", "Button")
        # onclick gibi event'ler için özel nitelikler ekleniyor
        return f'<{tag}{attrs}>{label}</{tag}>'

    # Varsayılan olarak çocukları olan bir etikete dönüştür
    return f'<{tag}{attrs}>{children_html}</{tag}>'

def render_page(component_tree: Component) -> str:
    """
    Derlenmiş bileşen ağacını alıp ana HTML sayfasını oluşturur.
    """
    # 1. Bileşenleri HTML'e çevir
    html_content = render_component(component_tree)

    # 2. Sayfanın sonuna event köprüsü için JS kodunu ekle
    # Bu kod, olayları yakalayıp sunucuya JSON olarak gönderir
    js_runtime = """
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        document.body.addEventListener('click', (event) => {
            let target = event.target;
            // Eğer tıklanan öğenin bir event niteliği varsa
            if (target.dataset && target.dataset.beadEventOnclick) {
                const handlerName = target.dataset.beadEventOnclick;
                const requestBody = {
                    event: 'click',
                    handler: handlerName,
                    element: { id: target.id, dataset: target.dataset },
                };
                
                fetch(`/_events/${handlerName}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Sunucu yanıtı:', data);
                    // İleride burada redirect, DOM güncelleme gibi işlemler yapılacak
                })
                .catch(error => {
                    console.error('Hata:', error);
                });
            }
        });
    });
    </script>
    """
    # JS kodunu </body> etiketinden hemen önce ekle
    return html_content.replace('</body>', f'{js_runtime}</body>')