"""File-related tools: read, write, delete"""

import os
from ..core.sandbox import SandboxPath
from ..core.memory import VectorMemory

class FileTools:
    def __init__(self, agent):
        self.agent = agent
        self.sandbox = SandboxPath()
    
    def read_file(self, path: str, token: str) -> str:
        """Read content of a file from sandbox"""
        if not self.agent.broker.validate_and_consume(token, "read_file", path):
            return "Permission denied"
        
        try:
            safe_path = self.sandbox.resolve(path)
            with open(safe_path, 'r') as f:
                content = f.read()
            
            # Store event in memory
            self.agent.memory.store("file_read", {"path": path, "content_snippet": content[:100]})
            
            return content
        except Exception as e:
            return f"Error reading file: {e}"
    
    def write_file(self, path: str, content: str, token: str) -> str:
        """Write content to a file in sandbox"""
        if not self.agent.broker.validate_and_consume(token, "write_file", path):
            return "Permission denied"
        
        try:
            safe_path = self.sandbox.resolve(path)
            self.sandbox.ensure_dir(safe_path)
            with open(safe_path, 'w') as f:
                f.write(content)
            
            # Store event in memory
            self.agent.memory.store("file_write", {"path": path, "content_length": len(content)})
            
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"
