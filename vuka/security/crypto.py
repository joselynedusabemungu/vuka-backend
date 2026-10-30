import os
from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    key = os.getenv("MFA_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("MFA_ENCRYPTION_KEY is not configured")
    return Fernet(key.encode())


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
