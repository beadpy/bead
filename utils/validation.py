# bead/utils/validation.py
from typing import Dict, Any

class BaseRule:
    """Doğrulama kuralları için temel sınıf."""
    def validate(self, value: Any) -> str | None:
        raise NotImplementedError

class Required(BaseRule):
    """Bir alanın boş olmadığını doğrular."""
    def validate(self, value: Any) -> str | None:
        if not value:
            return "Bu alan gereklidir."
        return None

class MinLength(BaseRule):
    """Bir alanın minimum uzunluğunu doğrular."""
    def __init__(self, length: int, message: str | None = None):
        self.length = length
        self.message = message or f"Minimum {self.length} karakter olmalıdır."

    def validate(self, value: Any) -> str | None:
        if value and len(str(value)) < self.length:
            return self.message
        return None

def validate_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, str] | None:
    """
    Bir veriyi, verilen şemaya göre doğrular.
    Hataları içeren bir sözlük döndürür veya hata yoksa None döndürür.
    """
    errors = {}
    for field, rules in schema.items():
        value = data.get(field)
        for rule in rules:
            error = rule.validate(value)
            if error:
                errors[field] = error
                break  # Bir alandaki ilk hatayı döndür
    
    if errors:
        return errors
    return None 