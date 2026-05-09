#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  ./deploy/bootstrap-public-ip.sh <public_ip> [common_name] [--force]

Examples:
  ./deploy/bootstrap-public-ip.sh 203.0.113.10
  ./deploy/bootstrap-public-ip.sh 203.0.113.10 dental.example.com --force

This script:
  1. Creates root .env from .env.example
  2. Sets PUBLIC_SCHEME/PUBLIC_HOST/ALLOWED_ORIGINS for public-IP HTTPS access
  3. Generates strong passwords for PostgreSQL, Logto PostgreSQL, and MinIO
  4. Clears VITE_LOGTO_APP_ID so it can be filled after Logto initialization
  5. Generates a self-signed gateway certificate
EOF
}

FORCE=0
PUBLIC_HOST=""
COMMON_NAME=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force)
      FORCE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [ -z "$PUBLIC_HOST" ]; then
        PUBLIC_HOST="$1"
      elif [ -z "$COMMON_NAME" ]; then
        COMMON_NAME="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      ;;
  esac
  shift
done

if [ -z "$PUBLIC_HOST" ]; then
  usage >&2
  exit 1
fi

if [ -z "$COMMON_NAME" ]; then
  COMMON_NAME="$PUBLIC_HOST"
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
EXAMPLE_ENV="${REPO_ROOT}/.env.example"
TARGET_ENV="${REPO_ROOT}/.env"
CERT_SCRIPT="${REPO_ROOT}/deploy/nginx/generate-self-signed-cert.sh"

if [ ! -f "$EXAMPLE_ENV" ]; then
  echo "Missing env template: $EXAMPLE_ENV" >&2
  exit 1
fi

if [ ! -f "$CERT_SCRIPT" ]; then
  echo "Missing certificate script: $CERT_SCRIPT" >&2
  exit 1
fi

if [ -f "$TARGET_ENV" ] && [ "$FORCE" -ne 1 ]; then
  echo "$TARGET_ENV already exists. Re-run with --force to overwrite it." >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required to generate passwords and certificates." >&2
  exit 1
fi

random_secret() {
  openssl rand -hex 16
}

POSTGRES_PASSWORD="$(random_secret)"
LOGTO_POSTGRES_PASSWORD="$(random_secret)"
MINIO_ROOT_PASSWORD="$(random_secret)"

TMP_ENV="${TARGET_ENV}.tmp"
trap 'rm -f "$TMP_ENV"' EXIT INT TERM

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    PUBLIC_SCHEME=*)
      printf '%s\n' 'PUBLIC_SCHEME=https'
      ;;
    PUBLIC_HOST=*)
      printf 'PUBLIC_HOST=%s\n' "$PUBLIC_HOST"
      ;;
    ALLOWED_ORIGINS=*)
      printf 'ALLOWED_ORIGINS=https://%s,http://%s,https://127.0.0.1,http://127.0.0.1,https://localhost,http://localhost,http://127.0.0.1:5173,http://localhost:5173\n' "$PUBLIC_HOST" "$PUBLIC_HOST"
      ;;
    POSTGRES_PASSWORD=*)
      printf 'POSTGRES_PASSWORD=%s\n' "$POSTGRES_PASSWORD"
      ;;
    LOGTO_POSTGRES_PASSWORD=*)
      printf 'LOGTO_POSTGRES_PASSWORD=%s\n' "$LOGTO_POSTGRES_PASSWORD"
      ;;
    MINIO_ROOT_PASSWORD=*)
      printf 'MINIO_ROOT_PASSWORD=%s\n' "$MINIO_ROOT_PASSWORD"
      ;;
    VITE_LOGTO_APP_ID=*)
      printf '%s\n' 'VITE_LOGTO_APP_ID='
      ;;
    *)
      printf '%s\n' "$line"
      ;;
  esac
done < "$EXAMPLE_ENV" > "$TMP_ENV"

mv "$TMP_ENV" "$TARGET_ENV"
chmod 600 "$TARGET_ENV" 2>/dev/null || true
trap - EXIT INT TERM

sh "$CERT_SCRIPT" "$PUBLIC_HOST" "$COMMON_NAME"

cat <<EOF
Prepared deployment files:
  .env: ${TARGET_ENV}
  cert: ${REPO_ROOT}/deploy/nginx/certs/server.crt
  key : ${REPO_ROOT}/deploy/nginx/certs/server.key

Generated strong passwords for:
  POSTGRES_PASSWORD
  LOGTO_POSTGRES_PASSWORD
  MINIO_ROOT_PASSWORD

Next steps:
  1. Review ${TARGET_ENV} and adjust mirrors, OLLAMA, and YOLO options if needed.
  2. Start Logto only: docker compose up -d logto-postgres logto
  3. Open https://${PUBLIC_HOST}:3002 and create the SPA app plus API resource.
  4. Fill VITE_LOGTO_APP_ID in ${TARGET_ENV}.
  5. Run: docker compose up -d --build
EOF
