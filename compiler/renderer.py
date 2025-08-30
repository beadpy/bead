import html
from bead.ui.core_components import Component, Page, Text, Button, Card, Stack, Input, Form, Link, Image
from bead.styles.compiler import extract_classes, get_style_map
from typing import Optional, Awaitable, List
import asyncio

_all_custom_styles = set()
_all_utility_classes = set()

def escape_html(text: str) -> str:
    # NoneType hatasını engellemek için metnin varlığını kontrol edin
    if text is None:
        return ""
    return html.escape(text, quote=True)

async def render_component(component: Component, utility_classes: set, csrf_token: Optional[str] = None) -> str:
    if not isinstance(component, Component):
        return escape_html(str(component))

    props = component.props
    component_type = component.component_type
    attrs = ""

    for key, value in props.items():
        if key.startswith("on"):
            attrs += f' data-bead-event-{key}="{escape_html(str(value))}"'
            
    if "custom_style" in props and props["custom_style"] is not None:
        _all_custom_styles.add(f' .custom-style-{id(component)} {{ {props["custom_style"]} }}')
        if "style" in props and props["style"] is not None:
            props["style"] += f" custom-style-{id(component)}"
        else:
            props["style"] = f" custom-style-{id(component)}"

    if "style" in props and props["style"] is not None:
        attrs += f' class="{escape_html(props["style"])}"'
        found_classes = extract_classes(f'class="{props["style"]}"')
        utility_classes.update(found_classes)

    if "id" in props and props["id"] is not None:
      attrs += f' id="{escape_html(props["id"])}"'
      
    if "href" in props and props["href"] is not None:
        attrs += f' href="{escape_html(props["href"])}"'
    
    if "as_" in props:
        tag = props["as_"]
    else:
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
    # Çocukları listelerden veya adlandırılmış slot sözlüğünden al
    children_prop = props.get("children", {})
    if isinstance(children_prop, dict):
        all_children = []
        for slot_name, slot_children in children_prop.items():
            if isinstance(slot_children, list):
                all_children.extend(slot_children)
        render_tasks = [render_component(child, utility_classes, csrf_token=csrf_token) for child in all_children]
        children_html = "".join(await asyncio.gather(*render_tasks))
    elif isinstance(children_prop, list):
        render_tasks = [render_component(child, utility_classes, csrf_token=csrf_token) for child in children_prop]
        children_html = "".join(await asyncio.gather(*render_tasks))
    
    if component_type == "Image":
        if "src" in props:
            attrs += f' src="{escape_html(props["src"])}"'
        if "alt" in props:
            attrs += f' alt="{escape_html(props["alt"])}"'
        if "loading" in props and props["loading"] is not None:
            attrs += f' loading="{escape_html(props["loading"])}"'
        return f'<{tag}{attrs} />'

    if component_type == "Link":
        label = escape_html(props.get("label", ""))
        return f'<{tag}{attrs}>{label}</{tag}>'

    if component_type == "Form":
        if "action" in props:
            attrs += f' action="{escape_html(props["action"])}"'
        if "method" in props:
            attrs += f' method="{escape_html(props["method"])}"'
        
        if csrf_token is not None:
            csrf_input = f'<input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}" />'
            children_html += csrf_input
            
        return f'<{tag}{attrs}>{children_html}</{tag}>'

    if component_type == "Input":
        if "name" in props:
            attrs += f' name="{escape_html(props["name"])}"'
        if "type" in props:
            attrs += f' type="{escape_html(props["type"])}"'
        if "value" in props:
            attrs += f' value="{escape_html(props["value"])}"'
        if "placeholder" in props:
            attrs += f' placeholder="{escape_html(props["placeholder"])}"'
        return f'<{tag}{attrs} />'

    if component_type == "Page":
        title = escape_html(props.get("title", "Bead App"))
        meta_html = ""
        if "meta" in props and isinstance(props["meta"], dict):
            for name, content in props["meta"].items():
                if name == "favicon":
                    meta_html += f'    <link rel="icon" href="{escape_html(content)}" type="image/x-icon">\n'
                else:
                    meta_html += f'    <meta name="{escape_html(name)}" content="{escape_html(content)}">\n'
        
        render_tasks = [render_component(child, utility_classes, csrf_token=csrf_token) for child in props["children"]['default']]
        body_content = "".join(await asyncio.gather(*render_tasks))
        
        head_content = f"""
<head>
    <title>{title}</title>
{meta_html}
</head>
"""
        return (f"<!DOCTYPE html><html>{head_content}<body>{body_content}</body></html>")

    if component_type == "Text":
        value = escape_html(props.get("value", ""))
        return f'<{tag}{attrs}>{value}</{tag}>'
    
    if component_type == "Button":
        label = escape_html(props.get("label", "Button"))
        return f'<{tag}{attrs}>{label}</{tag}>'

    return f'<{tag}{attrs}>{children_html}</{tag}>'

async def render_page(component_tree: Component, utility_classes: set, csrf_token: Optional[str] = None) -> str:
    html_content = await render_component(component_tree, utility_classes, csrf_token=csrf_token)

    css_link = '<link rel="stylesheet" href="/public/bead.css">'
    html_content = html_content.replace('</head>', f'    {css_link}\n</head>')
    
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