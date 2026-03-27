#!/usr/bin/env bash
set -euo pipefail

# Usage: ./deploy.sh user@server.com [image_tag]
SERVER="${1:?Usage: ./deploy.sh user@server.com [image_tag]}"
TAG="${2:-latest}"
IMAGE="ghcr.io/${GITHUB_REPOSITORY:-your-org/ai-native-course}:${TAG}"
REMOTE_DIR="/opt/ai-native-course"

echo "🚀 Deploying ${IMAGE} to ${SERVER}"

scp "$(dirname "${BASH_SOURCE[0]}")/../docker-compose.yml" \
  "${SERVER}:${REMOTE_DIR}/docker-compose.yml"

ssh "${SERVER}" bash <<EOF
set -euo pipefail

mkdir -p "${REMOTE_DIR}"
cd "${REMOTE_DIR}"

echo "${GHCR_TOKEN:-}" | docker login ghcr.io -u "${GITHUB_ACTOR:-deploy}" --password-stdin || true
docker pull "${IMAGE}"

export IMAGE="${IMAGE}"

docker-compose up -d --force-recreate

sleep 5
curl -sf http://localhost:3000/health || (echo "❌ Health check failed" && exit 1)

echo "✅ Deployed successfully"
EOF
