from cryptography.fernet import Fernet
from .config import settings

# This is a simple implementation. In a real production environment,
# the key should be managed more securely (e.g., via a KMS).
# For this project, we'll derive a key from the SECRET_KEY.
# IMPORTANT: If SECRET_KEY changes, all encrypted data will be unrecoverable.
import base64
import hashlib

# Use a salt or a better KDF in production
key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
cipher_suite = Fernet(key)

def encrypt_password(password: str) -> bytes:
    """Encrypts a password string and returns bytes."""
    return cipher_suite.encrypt(password.encode())

def decrypt_password(encrypted_password: bytes) -> str:
    """Decrypts an encrypted password and returns a string."""
    return cipher_suite.decrypt(encrypted_password).decode()
