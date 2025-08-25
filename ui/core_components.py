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
    def __init__(self, title: str, body: List[Component], style: Optional[str] = None, meta: Optional[Dict[str, str]] = None):
        super().__init__(title=title, body=body, style=style, meta=meta)

class Text(Component):
    def __init__(self, value: str, style: Optional[str] = None, as_: str = "p"):
        super().__init__(value=value, style=style, as_=as_)

class Button(Component):
    def __init__(self, label: str, onclick: Optional[str] = None, href: Optional[str] = None, style: Optional[str] = None):
        super().__init__(label=label, onclick=onclick, href=href, style=style)

class Card(Component):
    def __init__(self, children: List[Component], style: Optional[str] = None):
        super().__init__(children=children, style=style)

class Stack(Component):
    def __init__(self, children: List[Component], direction: Literal["row", "col"] = "col", style: Optional[str] = None, **kwargs):
        super().__init__(children=children, direction=direction, style=style, **kwargs)

# Diğer temel bileşenleri de buraya ekleyeceğiz.
# Örn: Input, Form, Image, Link, vs.
# Şimdilik bu temel set ile devam edebiliriz.