import ast
import inspect
import os
from bead.ui.core_components import Component, Page, Text, Button, Card, Stack, Input, Form, Link, Image
from bead.exceptions import CompilerError

_file_cache = {}

def parse_bead_file(file_path: str):
    try:
        last_modified = os.path.getmtime(file_path)

        if file_path in _file_cache and _file_cache[file_path]["last_modified"] == last_modified:
            print(f"INFO:  {file_path} from cache.")
            return _file_cache[file_path]["tree"]
    except FileNotFoundError:
        raise CompilerError(f"File not found: {file_path}", file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        error_message = f"Syntax error: {e.msg}"
        raise CompilerError(error_message, file_path, e.lineno, e.offset)

    default_func = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'default':
            default_func = node
            break

    if not default_func:
        raise CompilerError(f"Function 'default' not found. A .bead file must contain a 'default' function.", file_path)

    component_tree = find_return_value(default_func, file_path)
    
    _file_cache[file_path] = {
        "last_modified": last_modified,
        "tree": component_tree
    }

    return component_tree

def clear_cache():
    _file_cache.clear()

def find_return_value(func_node, file_path: str):
    for node in func_node.body:
        if isinstance(node, ast.Return):
            return process_component_call(node.value, file_path, node.lineno, node.col_offset)

    raise CompilerError(f"The 'default' function must return a Component object.", file_path, func_node.lineno, func_node.col_offset)

def process_component_call(node, file_path: str, line_no: int, col_offset: int):

    if not isinstance(node, ast.Call):
        raise CompilerError(f"Return value must be a component call (e.g., Page(...)).", file_path, line_no, col_offset)
    
    func_name = node.func.id
    
    component_class = globals().get(func_name)
    if not component_class or not inspect.isclass(component_class) or not issubclass(component_class, Component):
        raise CompilerError(f"Invalid component '{func_name}' found.", file_path, line_no, col_offset)

    args = []
    for arg_node in node.args:
        args.append(process_ast_node_value(arg_node, file_path, line_no, col_offset))

    kwargs = {}
    for keyword in node.keywords:
        key = keyword.arg
        value = process_ast_node_value(keyword.value, file_path, line_no, col_offset)
        kwargs[key] = value

    return component_class(*args, **kwargs)

def process_ast_node_value(node, file_path: str, line_no: int, col_offset: int):
    
    if isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.List):
        return [process_component_call(el, file_path, el.lineno, el.col_offset) for el in node.elts]
    elif isinstance(node, ast.Dict):
        return {process_ast_node_value(k, file_path, k.lineno, k.col_offset): process_ast_node_value(v, file_path, v.lineno, v.col_offset) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Attribute):
        return node.attr

    return None