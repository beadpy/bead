# bead/compiler/renderer.py

from bead.ui.core_components import Component, Page, Text, Button, Card, Stack, Input, Form, Link, Image

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

    # ID ve stil sadece değerleri None değilse eklenir
    if "style" in props and props["style"] is not None:
        attrs += f' class="{props["style"]}"'

    if "id" in props and props["id"] is not None:
      attrs += f' id="{props["id"]}"'
      
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
            "Stack": "div",
            "Input": "input",
            "Form": "form",
            "Link": "a",
            "Image": "img",
        }.get(component_type, "div")

    children_html = ""
    if "children" in props and isinstance(props["children"], list):
        # Çocuk bileşenleri recursive olarak render et
        children_html = "".join([render_component(child) for child in props["children"]])
    
    # Image bileşeni için özel işleme
    if component_type == "Image":
        if "src" in props:
            attrs += f' src="{props["src"]}"'
        if "alt" in props:
            attrs += f' alt="{props["alt"]}"'
        return f'<{tag}{attrs} />'

    # Link bileşeni için özel işleme
    if component_type == "Link":
        label = props.get("label", "")
        return f'<{tag}{attrs}>{label}</{tag}>'

    # Form bileşeni için özel işleme
    if component_type == "Form":
        if "action" in props:
            attrs += f' action="{props["action"]}"'
        if "method" in props:
            attrs += f' method="{props["method"]}"'
        return f'<{tag}{attrs}>{children_html}</{tag}>'

    # Input bileşeni için özel işleme
    if component_type == "Input":
        if "name" in props:
            attrs += f' name="{props["name"]}"'
        if "type" in props:
            attrs += f' type="{props["type"]}"'
        if "value" in props:
            attrs += f' value="{props["value"]}"'
        if "placeholder" in props:
            attrs += f' placeholder="{props["placeholder"]}"'
        return f'<{tag}{attrs} />'

    if component_type == "Page":
        # Page bileşeni özel bir yapıda olduğu için farklı render edilir
        title = props.get("title", "Bead App")
        meta_html = ""
        if "meta" in props and isinstance(props["meta"], dict):
            for name, content in props["meta"].items():
                if name == "favicon":
                    meta_html += f'    <link rel="icon" href="{content}" type="image/x-icon">\n'
                else:
                    meta_html += f'    <meta name="{name}" content="{content}">\n'
        
        body_content = "".join([render_component(child) for child in props["body"]])
        
        # Favicon için meta etiketi ekle
        head_content = f"""
<head>
    <title>{title}</title>
{meta_html}
</head>
"""
        return (f"<!DOCTYPE html><html>{head_content}<body>{body_content}</body></html>")

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

    # 2. Sayfanın sonuna event köprüsü ve morphdom için JS kodunu ekle
    # Bu kod, olayları yakalayıp sunucuya JSON olarak gönderir ve DOM'u günceller
    js_runtime = """
    <script>
    function morphdom(fromNode, toNode) {
      if (!fromNode || !toNode) {
        return toNode;
      }

      if (fromNode.isEqualNode(toNode)) {
        return fromNode;
      }
      
      // Update element attributes
      var toAttrs = toNode.attributes;
      var fromAttrs = fromNode.attributes;

      for (var i = toAttrs.length - 1; i >= 0; --i) {
        var attr = toAttrs[i];
        if (attr.name.startsWith('data-bead-event-')) continue;
        fromNode.setAttribute(attr.name, attr.value);
      }

      for (var i = fromAttrs.length - 1; i >= 0; --i) {
        var attr = fromAttrs[i];
        if (attr.name.startsWith('data-bead-event-')) continue;
        if (!toNode.hasAttribute(attr.name)) {
          fromNode.removeAttribute(attr.name);
        }
      }

      // Update children
      var fromChildren = Array.from(fromNode.childNodes);
      var toChildren = Array.from(toNode.childNodes);

      var fromChildrenLen = fromChildren.length;
      var toChildrenLen = toChildren.length;

      for (var i = 0; i < toChildrenLen; i++) {
        var toChild = toChildren[i];
        if (i < fromChildrenLen) {
          var fromChild = fromChildren[i];
          if (fromChild.nodeType === fromNode.TEXT_NODE && toChild.nodeType === toNode.TEXT_NODE) {
            fromChild.nodeValue = toChild.nodeValue;
          } else {
            morphdom(fromChild, toChild);
          }
        } else {
          fromNode.appendChild(toChild.cloneNode(true));
        }
      }

      while (fromChildrenLen > toChildrenLen) {
        fromNode.removeChild(fromChildren[fromChildrenLen - 1]);
        fromChildrenLen--;
      }

      return fromNode;
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.body.addEventListener('click', (event) => {
            let target = event.target;
            // Eğer tıklanan öğenin bir event niteliği varsa
            while (target && !target.dataset.beadEventOnclick) {
                target = target.parentElement;
            }
            if (target && target.dataset.beadEventOnclick) {
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
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.patch) {
                        const tempElement = document.createElement('div');
                        tempElement.innerHTML = data.patch;
                        const patchElement = tempElement.firstElementChild;
                        
                        if (patchElement && patchElement.id) {
                            const currentElement = document.getElementById(patchElement.id);
                            if (currentElement) {
                                morphdom(currentElement, patchElement);
                            }
                        }
                    }
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