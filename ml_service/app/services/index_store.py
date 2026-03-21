import json
import threading
from pathlib import Path
from typing import Dict, List, Optional


class IndexStore:
    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, dict]] = {}

    def _file_path(self, entity_type: str) -> Path:
        return self.index_dir / f"{entity_type}.json"

    def _load(self, entity_type: str) -> Dict[str, dict]:
        if entity_type in self._cache:
            return self._cache[entity_type]

        file_path = self._file_path(entity_type)
        if not file_path.exists():
            self._cache[entity_type] = {}
            return self._cache[entity_type]

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._cache[entity_type] = {item["id"]: item for item in data}
        return self._cache[entity_type]

    def _save(self, entity_type: str):
        file_path = self._file_path(entity_type)
        items = list(self._load(entity_type).values())

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def upsert(self, entity_type: str, items: List[dict]) -> int:
        with self._lock:
            storage = self._load(entity_type)
            for item in items:
                storage[item["id"]] = item
            self._save(entity_type)
            return len(items)

    def delete(self, entity_type: str, ids: List[str]) -> int:
        with self._lock:
            storage = self._load(entity_type)
            removed = 0
            for item_id in ids:
                if item_id in storage:
                    del storage[item_id]
                    removed += 1
            self._save(entity_type)
            return removed

    def get(self, entity_type: str, item_id: str) -> Optional[dict]:
        storage = self._load(entity_type)
        return storage.get(item_id)

    def list_items(self, entity_type: str) -> List[dict]:
        return list(self._load(entity_type).values())

    def stats(self) -> Dict[str, int]:
        result = {}
        for file_path in self.index_dir.glob("*.json"):
            entity_type = file_path.stem
            result[entity_type] = len(self._load(entity_type))
        return result
