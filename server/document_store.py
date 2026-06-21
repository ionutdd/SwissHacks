from __future__ import annotations

import os
import shutil
import time
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator

from tinydb import TinyDB

from .security import ENCRYPTED_PREFIX, EncryptionManager


class DocumentStoreLock:
    def __init__(self, path: Path, timeout_seconds: int = 120):
        self.path = path
        self.timeout_seconds = timeout_seconds
        self.acquired = False

    def __enter__(self) -> "DocumentStoreLock":
        deadline = time.monotonic() + self.timeout_seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while time.monotonic() < deadline:
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
                os.close(descriptor)
                self.acquired = True
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.timeout_seconds:
                        self.path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                time.sleep(0.05)
        raise TimeoutError("Timed out waiting for the document database lock.")

    def __exit__(self, *_args: object) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)


class DocumentStore:
    """Schema-free TinyDB collections used for pipeline and dashboard documents."""

    def __init__(self, path: Path | str, encryption: EncryptionManager | None = None):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.encryption = encryption

    def initialize(self, seed_path: Path | str | None = None) -> None:
        if self.path.exists():
            if self.encryption:
                self.encrypt_existing_documents()
            return
        with DocumentStoreLock(self.lock_path):
            if self.path.exists():
                return
            if seed_path and Path(seed_path).is_file():
                shutil.copyfile(Path(seed_path), self.path)
            else:
                with TinyDB(self.path):
                    pass
        if self.encryption:
            self.encrypt_existing_documents()

    @contextmanager
    def database(self) -> Iterator[TinyDB]:
        with DocumentStoreLock(self.lock_path):
            database = TinyDB(self.path)
            try:
                yield database
            finally:
                database.close()

    def collection(self, name: str) -> list[dict[str, Any]]:
        with self.database() as database:
            documents = [deepcopy(dict(item)) for item in database.table(name).all()]
        return [self._decode_document(name, document) for document in documents]

    def document(self, name: str, fallback: Any = None) -> Any:
        documents = self.collection(name)
        return documents[0] if documents else fallback

    def replace_collection(self, name: str, documents: list[dict[str, Any]]) -> None:
        if not isinstance(documents, list) or any(not isinstance(item, dict) for item in documents):
            raise ValueError(f"Collection {name} must contain JSON objects.")
        with self.database() as database:
            table = database.table(name)
            table.truncate()
            if documents:
                table.insert_multiple([self._encode_document(name, item) for item in documents])

    def replace_document(self, name: str, document: dict[str, Any]) -> None:
        if not isinstance(document, dict):
            raise ValueError(f"Document {name} must be a JSON object.")
        self.replace_collection(name, [document])

    def table_names(self) -> set[str]:
        with self.database() as database:
            return set(database.tables())

    def encrypt_existing_documents(self) -> None:
        if not self.encryption:
            return
        with self.database() as database:
            for name in database.tables():
                table = database.table(name)
                documents = [dict(item) for item in table.all()]
                if not documents or all(item.get("_sw_encrypted") == 1 for item in documents):
                    continue
                table.truncate()
                table.insert_multiple([self._encode_document(name, item) for item in documents])

    def _encode_document(self, name: str, document: dict[str, Any]) -> dict[str, Any]:
        if not self.encryption:
            return deepcopy(document)
        return {
            "_sw_encrypted": 1,
            "ciphertext": self.encryption.encrypt_json(document, f"tinydb:{name}"),
        }

    def _decode_document(self, name: str, document: dict[str, Any]) -> dict[str, Any]:
        if document.get("_sw_encrypted") != 1:
            return document
        if not self.encryption:
            raise ValueError(f"Collection {name} is encrypted but no data key is configured.")
        ciphertext = str(document.get("ciphertext", ""))
        if not ciphertext.startswith(ENCRYPTED_PREFIX):
            raise ValueError(f"Collection {name} contains an invalid encrypted document.")
        value = self.encryption.decrypt_json(ciphertext, f"tinydb:{name}")
        if not isinstance(value, dict):
            raise ValueError(f"Collection {name} decrypted to a non-document value.")
        return value
