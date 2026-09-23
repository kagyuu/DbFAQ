#!/bin/bash
# A05: 大規模な偽スナップショットを compose の api の SQLite に入れる
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
D=$(mktemp -d)
(cd server && uv run python scripts/gen_large_snapshot.py "$D/large.sqlite3")
docker compose stop api
docker compose cp "$D/large.sqlite3" api:/data/dbfaq.sqlite3
# コピーしたファイルはホストの所有者のままなので、api の実行ユーザー(uid 10001)に変える(F004)
docker compose run --rm --no-deps --user root --entrypoint sh api -c 'chown 10001:10001 /data/dbfaq.sqlite3 && rm -f /data/dbfaq.sqlite3-wal /data/dbfaq.sqlite3-shm'
docker compose start api
for i in $(seq 1 60); do curl -sf "http://localhost:${DBFAQ_PORT:-8088}/api/health" > /dev/null && break; sleep 1; done
curl -s "http://localhost:${DBFAQ_PORT:-8088}/api/schema" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("loaded tables:", len(d["tables"]), "relations:", len(d["relations"]))'
