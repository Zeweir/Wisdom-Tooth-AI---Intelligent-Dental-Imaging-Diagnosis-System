from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from minio import Minio

from app.config import BASE_DIR, MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY, MINIO_SECURE, STORAGE_PROVIDER, UPLOAD_DIR
from app.models import ImageRecord


@dataclass
class StoredObject:
    provider: str
    bucket: str | None
    object_key: str | None
    file_path: str


@dataclass
class StoredFileContent:
    content: bytes
    media_type: str


class StorageService:
    def __init__(self) -> None:
        self.provider = STORAGE_PROVIDER
        self.minio_client = None
        self.bucket_ready = False
        if self.provider == 'minio':
            self.minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
            )

    def ensure_bucket(self) -> None:
        if self.minio_client is None or self.bucket_ready:
            return
        if not self.minio_client.bucket_exists(MINIO_BUCKET):
            self.minio_client.make_bucket(MINIO_BUCKET)
        self.bucket_ready = True

    def build_object_key(self, filename: str) -> str:
        suffix = Path(filename or 'image.bin').suffix or '.bin'
        return f'images/{uuid4()}{suffix}'

    def save_upload(self, *, file_bytes: bytes, filename: str, content_type: str | None) -> StoredObject:
        object_key = self.build_object_key(filename)
        if self.provider == 'minio' and self.minio_client is not None:
            self.ensure_bucket()
            self.minio_client.put_object(
                MINIO_BUCKET,
                object_key,
                BytesIO(file_bytes),
                len(file_bytes),
                content_type=content_type or 'application/octet-stream',
            )
            return StoredObject(
                provider='minio',
                bucket=MINIO_BUCKET,
                object_key=object_key,
                file_path=object_key,
            )

        target_path = UPLOAD_DIR / object_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_bytes)
        return StoredObject(
            provider='local',
            bucket=None,
            object_key=object_key,
            file_path=str(target_path.relative_to(BASE_DIR)),
        )

    def load_file(self, image: ImageRecord) -> StoredFileContent:
        media_type = mimetypes.guess_type(image.filename)[0] or 'application/octet-stream'
        if image.storage_provider == 'minio' and self.minio_client is not None and image.storage_object_key:
            self.ensure_bucket()
            response = self.minio_client.get_object(image.storage_bucket or MINIO_BUCKET, image.storage_object_key)
            try:
                content = response.read()
            finally:
                response.close()
                response.release_conn()
            return StoredFileContent(content=content, media_type=media_type)

        resolved_path = (BASE_DIR / image.file_path).resolve()
        base_path = BASE_DIR.resolve()
        if base_path not in resolved_path.parents and resolved_path != base_path:
            raise HTTPException(status_code=400, detail='影像路径非法')
        if not resolved_path.exists() or not resolved_path.is_file():
            raise HTTPException(status_code=404, detail='影像文件不存在')
        return StoredFileContent(content=resolved_path.read_bytes(), media_type=media_type)


storage_service = StorageService()
