#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-ai-native-course}"
TAG="${TAG:-local}"

echo "🔨 Building Docker image: ${IMAGE_NAME}:${TAG}"
echo "   Context: ${REPO_ROOT}"

docker build \
  --file "${REPO_ROOT}/docker/Dockerfile" \
  --tag "${IMAGE_NAME}:${TAG}" \
  "${REPO_ROOT}"

echo "✅ Build complete: ${IMAGE_NAME}:${TAG}"
echo "   Run locally: docker-compose -f docker/docker-compose.yml up"
echo "   Or:          docker run -p 3000:80 ${IMAGE_NAME}:${TAG}"
