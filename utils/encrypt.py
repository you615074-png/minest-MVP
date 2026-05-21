"""
加密工具 — 基于 PBKDF2 + XOR 的对称加解密，纯 Python 标准库实现。
"""
import os
import hashlib
import base64


def _derive_key(secret: str, salt: str, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), 200_000, dklen=length)


def encrypt(plaintext: str, secret: str) -> tuple[str, str]:
    """
    加密任意字符串。返回 (密文_b64, 盐_b64)
    """
    salt = base64.b64encode(os.urandom(16)).decode()
    key = _derive_key(secret, salt, len(plaintext))
    cipher_bytes = bytes(a ^ b for a, b in zip(plaintext.encode(), key))
    return base64.b64encode(cipher_bytes).decode(), salt


def decrypt(cipher_b64: str, salt_b64: str, secret: str) -> str:
    """
    解密。返回原始明文字符串。
    """
    cipher_bytes = base64.b64decode(cipher_b64)
    key = _derive_key(secret, salt_b64, len(cipher_bytes))
    plain_bytes = bytes(a ^ b for a, b in zip(cipher_bytes, key))
    return plain_bytes.decode()
