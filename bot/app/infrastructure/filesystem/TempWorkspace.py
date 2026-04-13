import shutil
import logging
from pathlib import Path
from contextlib import contextmanager

class TempWorkspace:
    def __init__(self, basePath: Path):
        self.basePath = basePath
        self.logger = logging.getLogger(__name__)
        
    def _createFolder(self, folderName: str) -> Path:
        path = self.basePath / folderName
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _deleteFolder(self, folderName: str) -> None:
        path = self.basePath / folderName
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
            except Exception as e:
                self.logger.error(f"🔴 Error al eliminar la carpeta {path}: {e}")

    @contextmanager
    def useTempFolder(self, folderName: str, persistent: bool = False):
        path = self._createFolder(folderName)
        try:
            yield path
        finally:
            if not persistent:
                self._deleteFolder(folderName)
