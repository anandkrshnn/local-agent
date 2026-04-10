"""Secure Sandbox for File Operations"""

import os
import re
from typing import List, Optional

class SandboxPath:
    """Enforces all file operations within a sandbox directory"""
    
    def __init__(self, sandbox_root: str = None, allowed_patterns: List[str] = None):
        if sandbox_root is None:
            sandbox_root = os.path.expanduser("~/LocalAgentSandbox")
        self.sandbox_root = os.path.abspath(sandbox_root)
        os.makedirs(self.sandbox_root, exist_ok=True)
        
        self.allowed_patterns = allowed_patterns or [
            "*.txt", "*.md", "*.json", "*.log", "*.csv",
            "config/*", "logs/*", "data/*", "temp/*", "output/*"
        ]
        self.denied_patterns = ["*.key", "*.pem", "*.env", "*.db", "*.sqlite"]
    
    def resolve(self, user_path: str, check_patterns: bool = True) -> str:
        """Convert user path to absolute path within sandbox"""
        if '..' in user_path or user_path.startswith('/') or user_path.startswith('\\'):
            raise PermissionError(f"Path '{user_path}' attempts to escape sandbox or is absolute")
            
        clean_path = re.sub(r'[<>:"|?*]', '_', user_path)
        
        full_path = os.path.abspath(os.path.join(self.sandbox_root, clean_path))
        
        if not full_path.startswith(self.sandbox_root):
            raise PermissionError(f"Path '{user_path}' attempts to escape sandbox")
        
        if check_patterns:
            self._validate_patterns(full_path)
        
        return full_path
    
    def _validate_patterns(self, path: str):
        path_str = str(path)
        for pattern in self.denied_patterns:
            if pattern.endswith("*"):
                if path_str.endswith(pattern[:-1]):
                    raise PermissionError(f"File pattern '{pattern}' is not allowed")
            elif pattern in path_str:
                raise PermissionError(f"File pattern '{pattern}' is not allowed")
    
    def ensure_dir(self, path: str):
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    
    def list_sandbox(self) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(self.sandbox_root):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), self.sandbox_root)
                files.append(rel_path)
        return files
