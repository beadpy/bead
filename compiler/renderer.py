# bead/compiler/renderer.py

from bead.ui.core_components import Component, Page, Text, Button, Card, Stack, Input, Form, Link, Image
from bead.styles.compiler import extract_classes

# Bu küme, tüm render işlemlerinde bulunan özel CSS stillerini toplayacak.
_all_custom_styles = set()
_all_utility_classes = set()

def render_component(component: Component, utility_classes: set) -> str:
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
            
    # Özel stil toplama işlemini burada yapıyoruz
    if "custom_style" in props and props["custom_style"] is not None:
        # Rastgele değerler içerebildiği için direkt olarak kümeye ekle
        _all_custom_styles.add(f' .custom-style-{id(component)} {{ {props["custom_style"]} }}')
        # Oluşturulan benzersiz sınıf adını class listesine ekle
        if "style" in props and props["style"] is not None:
            props["style"] += f" custom-style-{id(component)}"
        else:
            props["style"] = f" custom-style-{id(component)}"

    # Sınıf toplama işlemini burada yapıyoruz
    if "style" in props and props["style"] is not None:
        attrs += f' class="{props["style"]}"'
        # Stilleri çıkar ve kümeye ekle
        found_classes = extract_classes(f'class="{props["style"]}"')
        utility_classes.update(found_classes)

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
        # Çocuk bileşenleri recursive olarak render et ve sınıflarını topla
        children_html = "".join([render_component(child, utility_classes) for child in props["children"]])
    
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
        
        body_content = "".join([render_component(child, utility_classes) for child in props["body"]])
        
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

def render_page(component_tree: Component, utility_classes: set) -> str:
    """
    Derlenmiş bileşen ağacını alıp ana HTML sayfasını oluşturur.
    """
    html_content = render_component(component_tree, utility_classes)

    # Yeni eklenen CSS dosyasını burada sayfaya ekliyoruz
    css_link = '<link rel="stylesheet" href="/public/bead.css">'
    html_content = html_content.replace('</head>', f'    {css_link}\n</head>')
    
    # Özel stil blokunu ekle
    custom_styles_str = "\n".join(list(_all_custom_styles))
    if custom_styles_str:
        style_block = f'\n    <style>{custom_styles_str}</style>\n'
        html_content = html_content.replace('</head>', f'{style_block}\n</head>')

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
            while (target && !target.dataset.beadEventOnclick) {
                target = target.parentElement;
            }
            if (target && target.dataset.beadEventOnclick) {
                event.preventDefault();
                handleEvent(target, target.dataset.beadEventOnclick);
            }
        });

        document.body.addEventListener('submit', (event) => {
            let target = event.target;
            while (target && target.tagName !== 'FORM') {
                target = target.parentElement;
            }
            if (target && target.dataset.beadEventOnsubmit) {
                event.preventDefault();
                handleEvent(target, target.dataset.beadEventOnsubmit);
            }
        });

        function handleEvent(target, handlerName) {
            let requestBody = {};
            if (target.tagName === 'FORM') {
                const formData = new FormData(target);
                requestBody = Object.fromEntries(formData.entries());
            }

            fetch(`/_events/${handlerName}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(error => {
                        window.alert(error.error);
                        throw new Error(error.error);
                    });
                }
                return response.json();
            })
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
                    } else {
                        morphdom(document.body, tempElement.querySelector('body'));
                    }
                }
            })
            .catch(error => {
                console.error('Hata:', error);
            });
        }
    });
    </script>
    """
    
    return html_content.replace('</body>', f'{js_runtime}</body>')