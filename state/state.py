from typing import Dict, Any

class State:
    def __init__(self, initial_state: Dict[str, Any] = None):
        if initial_state is None:
            initial_state = {}
        self._data = initial_state
        
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value

    def __delitem__(self, key: str):
        del self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, new_state: Dict[str, Any]):
        self._data.update(new_state)

    def __repr__(self) -> str:
        return f"State({self._data})"

    def __contains__(self, key: str) -> bool:
        return key in self._data