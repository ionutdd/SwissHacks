from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from pathlib import Path
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from argon2.low_level import Type
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)

ENCRYPTED_PREFIX = "swenc:v1:"
SENSITIVE_FIELD_PARTS = {
    "account",
    "amount",
    "beneficial_owner",
    "counterparty",
    "date_of_birth",
    "email",
    "iban",
    "passport",
    "payment",
    "phone",
    "purpose",
    "swift",
    "tax_id",
    "transaction_id",
}


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))


class EncryptionManager:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("The SignalWatch data key must be exactly 32 bytes.")
        self._key = key
        self._aes = AESGCM(key)

    @classmethod
    def load_or_create(cls, key_path: Path, environment_name: str = "SIGNALWATCH_DATA_KEY") -> "EncryptionManager":
        encoded = os.getenv(environment_name, "").strip()
        if encoded:
            try:
                return cls(_b64decode(encoded))
            except (ValueError, TypeError) as error:
                raise ValueError(f"{environment_name} must be URL-safe base64 for a 32-byte key.") from error

        key_path.parent.mkdir(parents=True, exist_ok=True)
        if key_path.exists():
            return cls(_b64decode(key_path.read_text(encoding="ascii").strip()))

        key = secrets.token_bytes(32)
        descriptor = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            os.write(descriptor, (_b64encode(key) + "\n").encode("ascii"))
        finally:
            os.close(descriptor)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass
        return cls(key)

    def derive(self, purpose: str) -> bytes:
        return hmac.new(self._key, purpose.encode("utf-8"), hashlib.sha256).digest()

    def token_digest(self, token: str, purpose: str = "session-token") -> str:
        return hmac.new(self.derive(purpose), token.encode("utf-8"), hashlib.sha256).hexdigest()

    def encrypt_bytes(self, plaintext: bytes, associated_data: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = self._aes.encrypt(nonce, plaintext, associated_data.encode("utf-8"))
        return f"{ENCRYPTED_PREFIX}{_b64encode(nonce)}:{_b64encode(ciphertext)}"

    def decrypt_bytes(self, value: str, associated_data: str) -> bytes:
        if not value.startswith(ENCRYPTED_PREFIX):
            return value.encode("utf-8")
        try:
            nonce_text, ciphertext_text = value[len(ENCRYPTED_PREFIX) :].split(":", 1)
            return self._aes.decrypt(
                _b64decode(nonce_text),
                _b64decode(ciphertext_text),
                associated_data.encode("utf-8"),
            )
        except (ValueError, InvalidTag) as error:
            raise ValueError("Encrypted data failed authentication; the key or ciphertext is invalid.") from error

    def encrypt_json(self, value: Any, associated_data: str) -> str:
        serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return self.encrypt_bytes(serialized, associated_data)

    def decrypt_json(self, value: str, associated_data: str) -> Any:
        return json.loads(self.decrypt_bytes(value, associated_data).decode("utf-8"))


def validate_password(password: str) -> None:
    failures: list[str] = []
    if len(password) < 14:
        failures.append("at least 14 characters")
    if not re.search(r"[a-z]", password):
        failures.append("a lowercase letter")
    if not re.search(r"[A-Z]", password):
        failures.append("an uppercase letter")
    if not re.search(r"\d", password):
        failures.append("a number")
    if not re.search(r"[^A-Za-z0-9]", password):
        failures.append("a symbol")
    if failures:
        raise ValueError("Password must contain " + ", ".join(failures) + ".")


def hash_password(password: str) -> str:
    validate_password(password)
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> tuple[bool, str | None]:
    try:
        PASSWORD_HASHER.verify(password_hash, password)
        replacement = PASSWORD_HASHER.hash(password) if PASSWORD_HASHER.check_needs_rehash(password_hash) else None
        return True, replacement
    except (VerifyMismatchError, InvalidHashError):
        return False, None


def new_session_token() -> str:
    return secrets.token_urlsafe(48)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def mask_sensitive(value: Any) -> Any:
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    if not isinstance(value, dict):
        return value
    masked: dict[str, Any] = {}
    for key, item in value.items():
        normalized = key.lower()
        if any(part in normalized for part in SENSITIVE_FIELD_PARTS):
            if isinstance(item, str) and len(item) > 4:
                masked[key] = f"***{item[-4:]}"
            elif item is None:
                masked[key] = None
            else:
                masked[key] = "[REDACTED]"
        else:
            masked[key] = mask_sensitive(item)
    return masked
