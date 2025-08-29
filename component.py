from bead.ui.core_components import Component
from functools import wraps
from bead.utils.validation import validate_data
import inspect

def component(schema=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if schema:
                errors = validate_data(kwargs, schema)
                if errors:
                    error_messages = ", ".join([f"'{field}': {msg}" for field, msg in errors.items()])
                    raise TypeError(f"Bileşen '{func.__name__}' için geçersiz prop'lar: {error_messages}")
            
            result = func(*args, **kwargs)
            
            return result
        
        return wrapper
    
    if inspect.isfunction(schema):
        return decorator(schema)
    else:
        return decorator