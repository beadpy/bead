# bead/ui/core_components.py

from typing import Optional, List, Literal, Dict, Any

class Component:
    """Tüm Bead UI bileşenleri için temel sınıf."""
    def __init__(self, **kwargs):
        self.props = kwargs
        self.component_type = self.__class__.__name__

    def __repr__(self):
        return f"<{self.component_type} props={self.props}>"

# Temel HTML öğeleri için sarmalayıcı (wrapper) bileşenler.
class Page(Component):
    def __init__(self, title: str, body: List[Component], style: Optional[str] = None, meta: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(title=title, body=body, style=style, meta=meta, **kwargs)

class Text(Component):
    def __init__(self, value: str, style: Optional[str] = None, as_: str = "p", **kwargs):
        super().__init__(value=value, style=style, as_=as_, **kwargs)

class Button(Component):
    def __init__(self, label: str, onclick: Optional[str] = None, href: Optional[str] = None, style: Optional[str] = None, **kwargs):
        super().__init__(label=label, onclick=onclick, href=href, style=style, **kwargs)

class Card(Component):
    def __init__(self, children: List[Component], style: Optional[str] = None, id: Optional[str] = None, **kwargs):
        super().__init__(children=children, style=style, id=id, **kwargs)

class Stack(Component):
    def __init__(self, children: List[Component], direction: Literal["row", "col"] = "col", style: Optional[str] = None, **kwargs):
        super().__init__(children=children, direction=direction, style=style, **kwargs)

class Input(Component):
    # 'error' parametresini ekledik
    def __init__(self, name: str, value: str = "", type: str = "text", placeholder: str = "", style: Optional[str] = None, error: Optional[str] = None, **kwargs):
        super().__init__(name=name, value=value, type=type, placeholder=placeholder, style=style, error=error, **kwargs)

class Form(Component):
    # 'schema' parametresini ekledik
    def __init__(self, children: List[Component], action: Optional[str] = None, method: str = "POST", onsubmit: Optional[str] = None, style: Optional[str] = None, schema: Optional[Dict] = None, **kwargs):
        super().__init__(children=children, action=action, method=method, onsubmit=onsubmit, style=style, schema=schema, **kwargs)

class Link(Component):
    def __init__(self, label: str, href: str, style: Optional[str] = None, **kwargs):
        super().__init__(label=label, href=href, style=style, **kwargs)

class Image(Component):
    def __init__(self, src: str, alt: str = "", style: Optional[str] = None, **kwargs):
        super().__init__(src=src, alt=alt, style=style, **kwargs)