import os
from pathlib import Path


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg://postgres:postgres@localhost:5432/wisdom_tooth_ai',
)
STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'local')
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', '127.0.0.1:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'wisdom-tooth-images')
MINIO_SECURE = env_flag('MINIO_SECURE', False)

LOGTO_ENDPOINT = os.getenv('LOGTO_ENDPOINT', 'http://127.0.0.1:3001')
LOGTO_ISSUER = os.getenv('LOGTO_ISSUER', f"{LOGTO_ENDPOINT.rstrip('/')}/oidc")
LOGTO_JWKS_URI = os.getenv('LOGTO_JWKS_URI', f'{LOGTO_ISSUER}/jwks')
LOGTO_API_RESOURCE = os.getenv('LOGTO_API_RESOURCE', 'https://api.wisdom-tooth-ai.local')

ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
