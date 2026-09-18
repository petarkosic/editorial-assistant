import json
from abc import ABC, abstractmethod
from pathlib import Path

from common.config import RUNS_DIR


class ArtifactStore(ABC):
    @abstractmethod
    def write_json(self, key: str, obj: dict) -> None: ...

    @abstractmethod
    def write_text(self, key: str, text: str) -> None: ...

    @abstractmethod
    def read_json(self, key: str) -> dict: ...

    @abstractmethod
    def read_text(self, key: str) -> str: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete_prefix(self, prefix: str) -> None: ...


class LocalFsStore(ArtifactStore):
    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError(f"key escapes store root: {key!r}")
        return p

    def write_json(self, key: str, obj: dict) -> None:
        self.write_text(key, json.dumps(obj, indent=2, default=str))

    def write_text(self, key: str, text: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def read_json(self, key: str) -> dict:
        return json.loads(self._path(key).read_text(encoding="utf-8"))

    def read_text(self, key: str) -> str:
        return self._path(key).read_text(encoding="utf-8")

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete_prefix(self, prefix: str) -> None:
        p = self._path(prefix)
        if p.is_dir():
            for child in sorted(p.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                else:
                    child.rmdir()
            p.rmdir()
        elif p.exists():
            p.unlink()


def get_store() -> ArtifactStore:
    return LocalFsStore(RUNS_DIR)
