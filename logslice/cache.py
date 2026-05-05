"""Simple file-based cache for parsed log metadata to speed up repeated slicing."""

import json
import hashlib
import os
from datetime import datetime
from typing import Optional


CACHE_DIR = os.path.join(os.path.expanduser("~"), ".logslice", "cache")


def _file_fingerprint(filepath: str) -> str:
    """Generate a fingerprint based on file path, size, and mtime."""
    stat = os.stat(filepath)
    raw = f"{os.path.abspath(filepath)}:{stat.st_size}:{stat.st_mtime}"
    return hashlib.md5(raw.encode()).hexdigest()


class LogCache:
    """Cache for storing and retrieving parsed log file metadata."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, fingerprint: str) -> str:
        return os.path.join(self.cache_dir, f"{fingerprint}.json")

    def get(self, filepath: str) -> Optional[dict]:
        """Return cached metadata for a file if valid, else None."""
        try:
            fingerprint = _file_fingerprint(filepath)
        except FileNotFoundError:
            return None

        cache_path = self._cache_path(fingerprint)
        if not os.path.exists(cache_path):
            return None

        with open(cache_path, "r") as f:
            return json.load(f)

    def set(self, filepath: str, metadata: dict) -> None:
        """Store metadata for a file keyed by its fingerprint."""
        fingerprint = _file_fingerprint(filepath)
        cache_path = self._cache_path(fingerprint)
        serializable = {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in metadata.items()
        }
        with open(cache_path, "w") as f:
            json.dump(serializable, f, indent=2)

    def invalidate(self, filepath: str) -> bool:
        """Remove cached entry for a file. Returns True if entry existed."""
        try:
            fingerprint = _file_fingerprint(filepath)
        except FileNotFoundError:
            return False

        cache_path = self._cache_path(fingerprint)
        if os.path.exists(cache_path):
            os.remove(cache_path)
            return True
        return False

    def clear(self) -> int:
        """Remove all cache entries. Returns count of removed files."""
        count = 0
        for fname in os.listdir(self.cache_dir):
            if fname.endswith(".json"):
                os.remove(os.path.join(self.cache_dir, fname))
                count += 1
        return count
