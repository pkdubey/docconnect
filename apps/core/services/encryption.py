"""
Data encryption utility — README section 10.3.
Used for encrypting sensitive fields (e.g. NMC registration numbers).
"""
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet


class DataEncryption:
    def __init__(self, secret_key: str):
        key = hashlib.sha256(secret_key.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))

    def encrypt(self, data: str) -> Optional[str]:
        if not data:
            return None
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        if not encrypted_data:
            return None
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
        return self.cipher.decrypt(encrypted).decode()


def get_encryptor() -> DataEncryption:
    from django.conf import settings
    return DataEncryption(settings.SECRET_KEY)
