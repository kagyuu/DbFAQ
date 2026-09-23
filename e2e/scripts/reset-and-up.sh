#!/bin/bash
# 受入テストのスイートのベースライン復元(docs/P006-test-plan.md §3.2)。アプリを起動する前に 1 回だけ実行する。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
docker compose down -v --remove-orphans
docker compose up -d --build
for i in $(seq 1 60); do
  if curl -sf "http://localhost:${DBFAQ_PORT:-8088}/api/health" > /dev/null; then break; fi
  sleep 1
done
curl -sf "http://localhost:${DBFAQ_PORT:-8088}/api/health" > /dev/null
(cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/hr_checksum.py > ../e2e/.baseline-checksum.json)
echo "baseline ready"
