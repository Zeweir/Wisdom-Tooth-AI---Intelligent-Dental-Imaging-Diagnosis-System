import os
from pathlib import Path


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


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

JWT_SECRET = os.getenv('JWT_SECRET', 'wisdom-tooth-ai-dev-secret-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = env_int('JWT_EXPIRE_MINUTES', 480)

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = env_flag('CELERY_TASK_ALWAYS_EAGER', False)

OLLAMA_ENABLED = env_flag('OLLAMA_ENABLED', True)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://10.41.33.17:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:9b')
OLLAMA_TIMEOUT_SECONDS = env_int('OLLAMA_TIMEOUT_SECONDS', 120)

YOLO_ENABLED = env_flag('YOLO_ENABLED', True)
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', '')
YOLO_CONF_THRESHOLD = env_float('YOLO_CONF_THRESHOLD', 0.25)
YOLO_IMAGE_SIZE = env_int('YOLO_IMAGE_SIZE', 1024)
YOLO_DEVICE = os.getenv('YOLO_DEVICE', '')
YOLO_CLASS_MAP_JSON = os.getenv('YOLO_CLASS_MAP_JSON', '')

ALLOWED_ORIGINS = [
    *env_list(
        'ALLOWED_ORIGINS',
        [
            'http://localhost:5173',
            'http://127.0.0.1:5173',
        ],
    ),
]
