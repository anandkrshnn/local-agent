from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
from typing import Optional

class VaultKeyManager:
    """Manages encryption key for a Sovereign Vault."""
    
    def __init__(self, vault_root: Path, password: Optional[str] = None):
        self.vault_root = Path(vault_root)
        self.salt_path = self.vault_root / ".vault_salt"
        
        if password:
            self.key = self._derive_key(password)
            self.fernet = Fernet(self.key)
            self.enabled = True
        else:
            self.enabled = False
            self.fernet = None

    def _derive_key(self, password: str) -> bytes:
        """Derive Fernet key using PBKDF2."""
        if self.salt_path.exists():
            salt = self.salt_path.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_path.write_bytes(salt)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt data string. Returns plaintext if encryption is disabled."""
        if not self.enabled or self.fernet is None:
            return data
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        """Decrypt data string. Returns plaintext if encryption is disabled."""
        if not self.enabled or self.fernet is None:
            return data
        try:
            return self.fernet.decrypt(data.encode()).decode()
        except Exception:
            # If decryption fails but encryption was expected, it might be plaintext (migration)
            # or a wrong password. 
            raise ValueError("Invalid vault password or corrupted data")

    def is_encrypted(self) -> bool:
        return self.enabled
