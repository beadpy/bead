import re
from typing import Dict, Any

# Tailwind benzeri utility sınıflarının CSS karşılıklarını içeren harita.
# Bu sözlük, ileride projenin konfigürasyon dosyasına taşınabilir.
STATIC_STYLE_MAP = {
    # Sizing
    "w-full": "width: 100%;",
    "h-full": "height: 100%;",
    "max-w-xl": "max-width: 36rem;",
    "w-12": "width: 3rem;",
    "h-12": "height: 3rem;",
    "w-20": "width: 5rem;",
    "h-20": "height: 5rem;",
    "w-24": "width: 6rem;",
    "h-24": "height: 6rem;",
    "w-40": "width: 10rem;",
    
    # Typography
    "text-xs": "font-size: 0.75rem;",
    "text-sm": "font-size: 0.875rem;",
    "text-base": "font-size: 1rem;",
    "text-lg": "font-size: 1.125rem;",
    "text-xl": "font-size: 1.25rem;",
    "text-2xl": "font-size: 1.5rem;",
    "text-3xl": "font-size: 1.875rem;",
    "font-bold": "font-weight: 700;",
    "font-semibold": "font-weight: 600;",
    "font-medium": "font-weight: 500;",
    "text-center": "text-align: center;",
    "font-inter": "font-family: 'Inter', sans-serif;",
    "no-underline": "text-decoration: none;",
    
    # Spacing (p-*, px-*, py-*, m-*, mx-*, my-*)
    "p-0": "padding: 0;",
    "p-1": "padding: 0.25rem;",
    "p-2": "padding: 0.5rem;",
    "p-3": "padding: 0.75rem;",
    "p-4": "padding: 1rem;",
    "p-5": "padding: 1.25rem;",
    "p-6": "padding: 1.5rem;",
    "px-4": "padding-left: 1rem; padding-right: 1rem;",
    "py-2": "padding-top: 0.5rem; padding-bottom: 0.5rem;",
    "mt-1": "margin-top: 0.25rem;",
    "mt-2": "margin-top: 0.5rem;",
    "mt-4": "margin-top: 1rem;",
    "mt-6": "margin-top: 1.5rem;",
    "mt-12": "margin-top: 3rem;",
    "mb-4": "margin-bottom: 1rem;",
    "mx-auto": "margin-left: auto; margin-right: auto;",

    # Flexbox
    "flex": "display: flex;",
    "flex-col": "flex-direction: column;",
    "flex-row": "flex-direction: row;",
    "items-center": "align-items: center;",
    "justify-center": "justify-content: center;",
    "gap-2": "gap: 0.5rem;",
    "gap-4": "gap: 1rem;",
    "gap-6": "gap: 1.5rem;",
    "gap-8": "gap: 2rem;",
    
    # Backgrounds & Borders
    "bg-white": "background-color: #ffffff;",
    "bg-gray-100": "background-color: #f3f4f6;",
    "bg-gray-50": "background-color: #f9fafb;",
    "bg-indigo-600": "background-color: #4f46e5;",
    "border": "border-width: 1px; border-style: solid; border-color: #e5e7eb;",
    "border-gray-200": "border-color: #e5e7eb;",
    "rounded-lg": "border-radius: 0.5rem;",
    "rounded-xl": "border-radius: 0.75rem;",
    "rounded-2xl": "border-radius: 1rem;",
    
    # Effects
    "shadow": "box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);",
    "shadow-xl": "box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);",

    # Colors
    "text-gray-600": "color: #4b5563;",
    "text-gray-800": "color: #1f2937;",
    "text-gray-900": "color: #111827;",
    "text-white": "color: #ffffff;",
    "text-indigo-600": "color: #4f46e5;",
    
    # State Variants
    "hover:bg-indigo-700": "&:hover { background-color: #4338ca; }",
    "hover:text-indigo-700": "&:hover { color: #4338ca; }",
    "hover:bg-gray-200": "&:hover { background-color: #e5e7eb; }",
}

def generate_css(utility_classes: set, style_map: Dict[str, str]) -> str:
    """
    Verilen utility sınıf listesine göre CSS içeriği oluşturur.
    """
    css_rules = []
    
    # `@import` kuralını CSS dosyasının başına ekle
    css_rules.append("@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');")

    for class_name in sorted(list(utility_classes)):
        # Haritada karşılığı olan sınıfları al
        css_rule = style_map.get(class_name)
        
        if css_rule:
            # & sembolü varsa (variant'lar için), onu .sınıf_adı ile değiştir
            if "&" in css_rule:
                selector = f".{class_name.replace(':', '\\:')}"
                css_rules.append(f"{css_rule.replace('&', selector)}")
            else:
                css_rules.append(f".{class_name} {{ {css_rule} }}")
    
    # CSS kurallarını birleştir
    return "\n".join(css_rules)

def extract_classes(html_content: str) -> set:
    """
    HTML içeriğinden tüm stil sınıflarını (class="..." veya style="...") çıkarır.
    """
    # Regex ile class niteliklerini bul
    classes_from_html = re.findall(r'class="([^"]*)"', html_content)
    
    # Tüm sınıfları bir set içinde topla (tekrar edenleri kaldırmak için)
    all_classes = set()
    for class_string in classes_from_html:
        # Boşluklara göre ayır ve sete ekle
        all_classes.update(class_string.split())
        
    return all_classes

def get_style_map(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Tema ayarlarını kullanarak dinamik STYLE_MAP'i oluşturur.
    """
    # Mevcut statik haritayı kopyala
    style_map = STATIC_STYLE_MAP.copy()
    
    theme_settings = config.get("theme", {})
    
    # Renkleri haritaya ekle
    if "colors" in theme_settings:
        for name, value in theme_settings["colors"].items():
            # bg- ve text- varyantları
            style_map[f"bg-{name}"] = f"background-color: {value};"
            style_map[f"text-{name}"] = f"color: {value};"
            # border- varyantı
            style_map[f"border-{name}"] = f"border-color: {value};"

    return style_map