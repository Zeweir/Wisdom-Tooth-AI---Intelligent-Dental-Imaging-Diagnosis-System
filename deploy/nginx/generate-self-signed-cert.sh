#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/certs"
HOST_IP="${1:-127.0.0.1}"
COMMON_NAME="${2:-${HOST_IP}}"

mkdir -p "${CERT_DIR}"

openssl req \
  -x509 \
  -nodes \
  -newkey rsa:2048 \
  -keyout "${CERT_DIR}/server.key" \
  -out "${CERT_DIR}/server.crt" \
  -days 825 \
  -subj "/CN=${COMMON_NAME}" \
  -addext "subjectAltName=IP:${HOST_IP},DNS:localhost,IP:127.0.0.1"

echo "Generated:"
echo "  ${CERT_DIR}/server.crt"
echo "  ${CERT_DIR}/server.key"
