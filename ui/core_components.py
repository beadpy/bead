from typing import Optional, List, Literal, Dict, Any, Union

class Component:
    def __init__(self, children: Optional[Union[List['Component'], Dict[str, List['Component']]]] = None, **kwargs):
        self.props = kwargs
        if children is not None:
            # Tek bir liste yerine adlandırılmış bir slot (varsayılan) olarak işleyin
            if isinstance(children, list):
                self.props['children'] = {'default': children}
            else:
                self.props['children'] = children
        self.component_type = self.__class__.__name__

    def render(self) -> str:
        raise NotImplementedError("Component alt sınıfları 'render' metodunu uygulamalıdır.")

    def __repr__(self):
        return f"<{self.component_type} props={self.props}>"

class Page(Component):
    def __init__(self, title: str, body: List[Component], style: Optional[str] = None, custom_style: Optional[str] = None, meta: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(children=body, title=title, style=style, custom_style=custom_style, meta=meta, **kwargs)

class Text(Component):
    def __init__(self, value: str, style: Optional[str] = None, custom_style: Optional[str] = None, as_: str = "p", **kwargs):
        super().__init__(value=value, style=style, custom_style=custom_style, as_=as_, **kwargs)
        
    def render(self) -> str:
        tag = self.props.get('as_', 'p')
        value = self.props.get('value', '')
        style = self.props.get('style', '')
        return f'<{tag} class="{style}">{value}</{tag}>'

class Button(Component):
    def __init__(self, label: str, onclick: Optional[str] = None, href: Optional[str] = None, style: Optional[str] = None, custom_style: Optional[str] = None, **kwargs):
        super().__init__(label=label, onclick=onclick, href=href, style=style, custom_style=custom_style, **kwargs)

    def render(self) -> str:
        tag = 'button' if not self.props.get('href') else 'a'
        label = self.props.get('label', 'Button')
        style = self.props.get('style', '')
        onclick = f' data-bead-event-onclick="{self.props["onclick"]}"' if self.props.get("onclick") else ""
        href = f' href="{self.props["href"]}"' if self.props.get("href") else ""
        return f'<{tag} class="{style}"{onclick}{href}>{label}</{tag}>'

class Card(Component):
    def __init__(self, children: Union[List[Component], Dict[str, List[Component]]], style: Optional[str] = None, custom_style: Optional[str] = None, id: Optional[str] = None, **kwargs):
        super().__init__(children=children, style=style, custom_style=custom_style, id=id, **kwargs)

class Stack(Component):
    def __init__(self, children: List[Component], direction: Literal["row", "col"] = "col", style: Optional[str] = None, custom_style: Optional[str] = None, **kwargs):
        super().__init__(children=children, direction=direction, style=style, custom_style=custom_style, **kwargs)

class Input(Component):
    def __init__(self, name: str, value: str = "", type: str = "text", placeholder: str = "", style: Optional[str] = None, custom_style: Optional[str] = None, error: Optional[str] = None, **kwargs):
        super().__init__(name=name, value=value, type=type, placeholder=placeholder, style=style, custom_style=custom_style, error=error, **kwargs)

class Form(Component):
    def __init__(self, children: List[Component], action: Optional[str] = None, method: str = "POST", onsubmit: Optional[str] = None, style: Optional[str] = None, custom_style: Optional[str] = None, schema: Optional[Dict] = None, csrf_token: Optional[str] = None, **kwargs):
        super().__init__(children=children, action=action, method=method, onsubmit=onsubmit, style=style, custom_style=custom_style, schema=schema, csrf_token=csrf_token, **kwargs)

class Link(Component):
    def __init__(self, label: str, href: str, style: Optional[str] = None, custom_style: Optional[str] = None, **kwargs):
        super().__init__(label=label, href=href, style=style, custom_style=custom_style, **kwargs)

class Image(Component):
    def __init__(self, src: str, alt: str = "", style: Optional[str] = None, custom_style: Optional[str] = None, loading: str = "lazy", **kwargs):
        super().__init__(src=src, alt=alt, style=style, custom_style=custom_style, loading=loading, **kwargs)