from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from minio import Minio

from app.config import BASE_DIR, MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY, MINIO_SECURE, STORAGE_PROVIDER, UPLOAD_DIR
from app.models import ImageRecord, ReportRecord, ReportRevisionRecord


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

    def build_dataset_object_key(self, filename: str) -> str:
        suffix = Path(filename or 'dataset.zip').suffix or '.zip'
        return f'datasets/{uuid4()}{suffix}'

    def build_report_object_key(self, filename: str) -> str:
        suffix = Path(filename or 'report.pdf').suffix or '.pdf'
        return f'reports/{uuid4()}{suffix}'

    def save_dataset_file(self, *, file_bytes: bytes, filename: str, content_type: str | None) -> StoredObject:
        object_key = self.build_dataset_object_key(filename)
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

    def save_report_file(self, *, file_bytes: bytes, filename: str, content_type: str | None = 'application/pdf') -> StoredObject:
        object_key = self.build_report_object_key(filename)
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

    def _load_binary_file(
        self,
        *,
        provider: str | None,
        bucket: str | None,
        object_key: str | None,
        file_path: str | None,
        media_type: str,
        not_found_label: str,
    ) -> StoredFileContent:
        if provider == 'minio' and self.minio_client is not None and object_key:
            self.ensure_bucket()
            response = self.minio_client.get_object(bucket or MINIO_BUCKET, object_key)
            try:
                content = response.read()
            finally:
                response.close()
                response.release_conn()
            return StoredFileContent(content=content, media_type=media_type)

        if not file_path:
            raise HTTPException(status_code=404, detail=f'{not_found_label}不存在')
        resolved_path = (BASE_DIR / file_path).resolve()
        base_path = BASE_DIR.resolve()
        if base_path not in resolved_path.parents and resolved_path != base_path:
            raise HTTPException(status_code=400, detail=f'{not_found_label}路径非法')
        if not resolved_path.exists() or not resolved_path.is_file():
            raise HTTPException(status_code=404, detail=f'{not_found_label}不存在')
        return StoredFileContent(content=resolved_path.read_bytes(), media_type=media_type)

    def load_file(self, image: ImageRecord) -> StoredFileContent:
        media_type = mimetypes.guess_type(image.filename)[0] or 'application/octet-stream'
        return self._load_binary_file(
            provider=image.storage_provider,
            bucket=image.storage_bucket,
            object_key=image.storage_object_key,
            file_path=image.file_path,
            media_type=media_type,
            not_found_label='影像文件',
        )

    def load_report_file(self, report: ReportRecord) -> StoredFileContent:
        return self._load_binary_file(
            provider=report.pdf_storage_provider,
            bucket=report.pdf_storage_bucket,
            object_key=report.pdf_storage_object_key,
            file_path=report.pdf_file_path,
            media_type='application/pdf',
            not_found_label='报告 PDF',
        )

    def load_report_revision_file(self, revision: ReportRevisionRecord) -> StoredFileContent:
        return self._load_binary_file(
            provider=revision.pdf_storage_provider,
            bucket=revision.pdf_storage_bucket,
            object_key=revision.pdf_storage_object_key,
            file_path=revision.pdf_file_path,
            media_type='application/pdf',
            not_found_label='报告版本 PDF',
        )


storage_service = StorageService()
