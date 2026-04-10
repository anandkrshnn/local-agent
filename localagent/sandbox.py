from pathlib import Path
import re

class SandboxPath:
    def __init__(self, root: Path = None):
        if root is None:
            root = Path.home() / "LocalAgentSandbox"
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, user_path: str) -> Path:
        if not user_path:
            raise ValueError("Path cannot be empty")
        # Ensure path is a string and remove leading separators
        clean = str(user_path).strip().lstrip("/\\")
        # Precaution against relative path traversal
        clean = re.sub(r'(\.\.[/\\])+', '', clean)
        full_path = (self.root / clean).resolve()
        # Verify path containment
        if not str(full_path).startswith(str(self.root)):
            raise PermissionError(f"Path '{user_path}' escapes sandbox")
        return full_path

    def ensure_parent(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
