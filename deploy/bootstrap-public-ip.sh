#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  ./deploy/bootstrap-public-ip.sh <public_ip> [--prod] [--force]

Examples:
  ./deploy/bootstrap-public-ip.sh 203.0.113.10           # 本地构建部署
  ./deploy/bootstrap-public-ip.sh dental.example.com --prod  # 生产镜像部署

What it does:
  1. Creates .env with PUBLIC_HOST, strong random passwords, JWT_SECRET
  2. Generates self-signed SSL certs for the gateway
  3. Prints the exact docker compose command to run next
EOF
}

FORCE=0
PROD=0
PUBLIC_HOST=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --prod)  PROD=1 ;;
    -h|--help) usage; exit 0 ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2; exit 1
      ;;
    *)
      if [ -z "$PUBLIC_HOST" ]; then
        PUBLIC_HOST="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2; exit 1
      fi
      ;;
  esac
  shift
done

if [ -z "$PUBLIC_HOST" ]; then
  usage >&2; exit 1
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
EXAMPLE_ENV="${REPO_ROOT}/.env.example"
TARGET_ENV="${REPO_ROOT}/.env"
CERT_SCRIPT="${REPO_ROOT}/deploy/nginx/generate-self-signed-cert.sh"

if [ ! -f "$EXAMPLE_ENV" ]; then
  echo "Missing: $EXAMPLE_ENV" >&2; exit 1
fi

if [ ! -f "$CERT_SCRIPT" ]; then
  echo "Missing: $CERT_SCRIPT" >&2; exit 1
fi

if [ -f "$TARGET_ENV" ] && [ "$FORCE" -ne 1 ]; then
  echo "$TARGET_ENV already exists. Re-run with --force to overwrite." >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required." >&2; exit 1
fi

random_secret() { openssl rand -hex 16; }

POSTGRES_PASSWORD="$(random_secret)"
MINIO_ROOT_PASSWORD="$(random_secret)"
JWT_SECRET="$(random_secret)"

TMP_ENV="${TARGET_ENV}.tmp"
trap 'rm -f "$TMP_ENV"' EXIT INT TERM

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    PUBLIC_SCHEME=*)   printf 'PUBLIC_SCHEME=https\n' ;;
    PUBLIC_HOST=*)     printf 'PUBLIC_HOST=%s\n' "$PUBLIC_HOST" ;;
    ALLOWED_ORIGINS=*) printf 'ALLOWED_ORIGINS=https://%s,http://%s,https://127.0.0.1,http://127.0.0.1,https://localhost,http://localhost,http://127.0.0.1:5173,http://localhost:5173\n' "$PUBLIC_HOST" "$PUBLIC_HOST" ;;
    POSTGRES_PASSWORD=*)   printf 'POSTGRES_PASSWORD=%s\n' "$POSTGRES_PASSWORD" ;;
    MINIO_ROOT_PASSWORD=*) printf 'MINIO_ROOT_PASSWORD=%s\n' "$MINIO_ROOT_PASSWORD" ;;
    JWT_SECRET=*)          printf 'JWT_SECRET=%s\n' "$JWT_SECRET" ;;
    *) printf '%s\n' "$line" ;;
  esac
done < "$EXAMPLE_ENV" > "$TMP_ENV"

mv "$TMP_ENV" "$TARGET_ENV"
chmod 600 "$TARGET_ENV" 2>/dev/null || true
trap - EXIT INT TERM

sh "$CERT_SCRIPT" "$PUBLIC_HOST" "$PUBLIC_HOST"

if [ "$PROD" -eq 1 ]; then
  COMPOSE_FILE="docker-compose.prod.yml"
  COMPOSE_CMD="docker compose -f docker-compose.prod.yml up -d"
else
  COMPOSE_FILE="docker-compose.yml"
  COMPOSE_CMD="docker compose up -d --build"
fi

cat <<EOF

╔══════════════════════════════════════════════╗
║       智齿 AI — 环境初始化完成               ║
╠══════════════════════════════════════════════╣
║                                              ║
║  .env:    ${TARGET_ENV}
║  cert:    ${REPO_ROOT}/deploy/nginx/certs/server.crt
║  compose: ${COMPOSE_FILE}
║                                              ║
║  生成的强密码:                                ║
║    POSTGRES_PASSWORD                        ║
║    MINIO_ROOT_PASSWORD                      ║
║    JWT_SECRET                               ║
║                                              ║
║  🚀 启动命令:                                 ║
║    ${COMPOSE_CMD}
║                                              ║
║  🌐 访问: https://${PUBLIC_HOST}             ║
║  🔑 登录: admin / admin123 (主任医生)         ║
║                                              ║
║  ⚠️  首次启动后请修改默认密码!                ║
║                                              ║
╚══════════════════════════════════════════════╝
EOF
