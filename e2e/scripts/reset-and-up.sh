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
# 取得に失敗したら空のベースラインを残さない(空同士の比較で A06 が一致と判定しないように。P202 F009)
rm -f e2e/.baseline-checksum.json
(cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/hr_checksum.py > ../e2e/.baseline-checksum.json.tmp)
mv e2e/.baseline-checksum.json.tmp e2e/.baseline-checksum.json
echo "baseline ready"
