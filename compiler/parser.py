# bead/compiler/parser.py

import ast
import inspect
from bead.ui.core_components import Component, Page, Text, Button, Card, Stack, Input, Form, Link, Image
from bead.exceptions import CompilerError

def parse_bead_file(file_path: str):
    """
    Reads a .bead file and returns a Component Tree.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Convert source code to AST (Abstract Syntax Tree)
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        # Raise CompilerError with detailed line and column information.
        error_message = f"Syntax error: {e.msg} at line {e.lineno}, column {e.offset}"
        raise CompilerError(error_message, file_path) # Changed to pass file_path to CompilerError

    # Search for a function named 'default'
    default_func = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'default':
            default_func = node
            break

    if not default_func:
        raise CompilerError(f"Function 'default' not found. A .bead file must contain a 'default' function.", file_path)

    # Process the return value of the function
    component_tree = find_return_value(default_func, file_path)
    return component_tree

def find_return_value(func_node, file_path: str):
    """
    Finds the 'return' statement in an AST function node and processes the component.
    """
    for node in func_node.body:
        if isinstance(node, ast.Return):
            return process_component_call(node.value, file_path)
    
    raise CompilerError(f"The 'default' function must return a Component object.", file_path)

def process_component_call(node, file_path: str):
    """
    Converts a component call in the AST into a Component object.
    """
    if not isinstance(node, ast.Call):
        raise CompilerError(f"Return value must be a component call (e.g., Page(...)).", file_path)
    
    func_name = node.func.id
    
    component_class = globals().get(func_name)
    if not component_class or not inspect.isclass(component_class) or not issubclass(component_class, Component):
        raise CompilerError(f"Invalid component '{func_name}' found.", file_path)

    # Process positional arguments
    args = []
    for arg_node in node.args:
        args.append(process_ast_node_value(arg_node, file_path))
        
    # Process keyword arguments (kwargs)
    kwargs = {}
    for keyword in node.keywords:
        key = keyword.arg
        value = process_ast_node_value(keyword.value, file_path)
        kwargs[key] = value

    return component_class(*args, **kwargs)

def process_ast_node_value(node, file_path: str):
    """
    Converts a value from an AST node to a Python data type.
    """
    if isinstance(node, ast.Str): # For Python < 3.8
        return node.s
    elif isinstance(node, ast.Constant): # For Python >= 3.8
        return node.value
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.List):
        return [process_component_call(el, file_path) for el in node.elts]
    elif isinstance(node, ast.Dict):
        return {process_ast_node_value(k, file_path): process_ast_node_value(v, file_path) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Attribute):
        return node.attr

    return None