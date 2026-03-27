#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-localhost}"
PORT="${2:-3000}"
URL="http://${HOST}:${PORT}/health"

echo "🔍 Checking health: ${URL}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}" || echo "000")

if [ "${HTTP_CODE}" = "200" ]; then
  echo "✅ Healthy (HTTP ${HTTP_CODE})"
  exit 0
else
  echo "❌ Unhealthy (HTTP ${HTTP_CODE})"
  exit 1
fi
