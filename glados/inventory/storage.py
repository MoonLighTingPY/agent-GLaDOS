from typing import Optional, Dict, Any, List
import json
import threading
import time
from pathlib import Path

class InventoryDB:
    def __init__(self, path: str = "inventory.json"):
        self.path = Path(path)
        self._lock = threading.Lock()
        if not self.path.exists():
            self._write({"items": []})

    def _read(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: Dict[str, Any]):
        with self._lock:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_items(self) -> List[Dict[str, Any]]:
        return self._read().get("items", [])

    def upsert_item(self, name: str, location: str, metadata: Optional[Dict[str, Any]] = None):
        data = self._read()
        items = data.get("items", [])
        for it in items:
            if it["name"].lower() == name.lower():
                it["location"] = location
                it["metadata"] = metadata or {}
                it["updated_at"] = time.time()
                break
        else:
            items.append({
                "name": name,
                "location": location,
                "metadata": metadata or {},
                "updated_at": time.time()
            })
        data["items"] = items
        self._write(data)

    def find_item(self, query: str) -> Optional[Dict[str, Any]]:
        q = query.lower()
        for it in self.list_items():
            if q in it["name"].lower():
                return it
        return None
