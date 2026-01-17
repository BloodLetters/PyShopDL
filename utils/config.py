import json
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path or "config.json")
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not self._path.is_file():
            raise FileNotFoundError(f"Config file tidak ditemukan: {self._path}")

        with self._path.open("r", encoding="utf-8") as f:
            self._data = json.load(f)

    def get(self, key: Optional[str] = None, default: Any = None) -> Any:
        if key is None:
            return self._data

        value: Any = self._data
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def __getitem__(self, key: str) -> Any:
        result = self.get(key)
        if result is None and key not in self._data:
            raise KeyError(key)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)