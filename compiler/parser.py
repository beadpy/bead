# bead/compiler/parser.py (Final)

import ast
import inspect
from bead.ui.core_components import Component, Page, Text, Button, Card, Stack, Input, Form, Link, Image

def parse_bead_file(file_path: str):
    """
    .bead dosyasını okur ve bir Bileşen Ağacı (Component Tree) döndürür.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Kaynak kodu AST'ye (Abstract Syntax Tree) dönüştür
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        print(f"Hata: {file_path} dosyasında sözdizimi hatası: {e}")
        return None

    # 'default' adında bir fonksiyon arıyoruz
    default_func = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'default':
            default_func = node
            break

    if not default_func:
        print(f"Hata: '{file_path}' dosyasında 'default' fonksiyonu bulunamadı.")
        return None

    # Fonksiyonun döndürdüğü değeri bul ve işle
    component_tree = find_return_value(default_func)
    return component_tree

def find_return_value(func_node):
    """
    AST'deki bir fonksiyonun 'return' ifadesini bulur ve bileşeni işler.
    """
    for node in func_node.body:
        if isinstance(node, ast.Return):
            return process_component_call(node.value)
    return None

def process_component_call(node):
    """
    AST'deki bir bileşen çağrısını bir Component nesnesine dönüştürür.
    """
    if not isinstance(node, ast.Call):
        raise ValueError("dönüş değeri bir bileşen çağrısı olmalıdır")
    
    func_name = node.func.id
    
    component_class = globals().get(func_name)
    if not component_class or not inspect.isclass(component_class) or not issubclass(component_class, Component):
        raise ValueError(f"Geçersiz bileşen: {func_name}")

    # Konumsal argümanları işle
    args = []
    for arg_node in node.args:
        args.append(process_ast_node_value(arg_node))
        
    # Anahtar kelime argümanları (kwargs) işle
    kwargs = {}
    for keyword in node.keywords:
        key = keyword.arg
        value = process_ast_node_value(keyword.value)
        kwargs[key] = value

    return component_class(*args, **kwargs)

def process_ast_node_value(node):
    """
    AST düğümündeki değeri Python veri tiplerine dönüştürür.
    """
    if isinstance(node, ast.Str): # Python 3.8 öncesi için
        return node.s
    elif isinstance(node, ast.Constant): # Python 3.8+
        return node.value
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.List):
        return [process_component_call(el) for el in node.elts]
    
    # Yeni eklenenler:
    elif isinstance(node, ast.Dict):
        return {process_ast_node_value(k): process_ast_node_value(v) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Attribute):
        # Örnek: from bead.ui import ...
        # Bu durumda, sadece en son parçayı alıyoruz.
        return node.attr

    return None