from bead.ui.core_components import Component
from functools import wraps

def component(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
        
    return wrapper