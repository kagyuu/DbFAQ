#!/bin/bash
# A04: 再起動耐性(docs/P009-acceptance-direction/A04-restart-resilience.md)。途中でベースライン復元を挟まない。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
BASE="http://localhost:${DBFAQ_PORT:-8088}"
fail=0
check() { if [ "$2" = "$3" ]; then echo "OK   $1 ($2)"; else echo "FAIL $1 (expected=$3 actual=$2)"; fail=1; fi; }
wait_health() {
  for i in $(seq 1 60); do curl -sf "$BASE/api/health" > /dev/null && return 0; sleep 1; done
  return 1
}
fetched() { curl -s "$BASE/api/schema" | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("snapshot") or {}).get("fetched_at"), len(d["tables"]))'; }

# 手順 8(CR-005): 保存済み Query が残り、再起動でひな型が重複しない
pdb_check() { curl -s "$BASE/api/saved-queries?scope=pdb" | python3 -c 'import json,sys; d=json.load(sys.stdin)["items"]; print(any(q["name"]=="A04-再起動" for q in d), sum(q["is_template"] for q in d))'; }
SQ_ID=$(curl -s -X POST "$BASE/api/saved-queries" -H 'Content-Type: application/json' \
  -d '{"scope":"pdb","name":"A04-再起動","description":"","sql":"SELECT 1 FROM DUAL"}' | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))')

F0=$(fetched); echo "F0=$F0"
docker compose restart api > /dev/null 2>&1
wait_health && echo "OK   restart: api が起動した" || { echo "FAIL restart: api が起動しない"; fail=1; }
check "restart 後のスナップショット" "$(fetched)" "$F0"
check "restart 後の保存済み Query・ひな型の数" "$(pdb_check)" "True 17"

docker compose down > /dev/null 2>&1
docker compose up -d > /dev/null 2>&1
wait_health && echo "OK   down/up: api が起動した" || { echo "FAIL down/up: api が起動しない"; fail=1; }
check "down/up 後のスナップショット" "$(fetched)" "$F0"
check "down/up 後の保存済み Query・ひな型の数" "$(pdb_check)" "True 17"
[ -n "$SQ_ID" ] && curl -s -X DELETE "$BASE/api/saved-queries/$SQ_ID" > /dev/null

N=$(docker compose exec -T api python -c "import sqlite3; print(sqlite3.connect('/data/dbfaq.sqlite3').execute('select count(*) from schema_migrations').fetchone()[0])")
check "schema_migrations の件数" "$N" "2"  # 0001・0002(CR-005)

E=$(docker compose logs api 2>&1 | grep -cE 'Traceback|MigrationError')
check "起動時の例外" "$E" "0"

# 手順 7(CR-002): api コンテナに MCP の子プロセスが無い
M=$(docker compose exec -T api python -c "import os; print(sum(1 for p in os.listdir('/proc') if p.isdigit() and int(p)!=os.getpid() and b'dbfaq_mcp' in open(f'/proc/{p}/cmdline','rb').read()))")
check "dbfaq_mcp のプロセス数" "$M" "0"
status=$(curl -s "$BASE/api/health" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
check "health の status" "$status" "ok"

[ $fail -eq 0 ] && echo "A04 PASS" || echo "A04 FAIL"
exit $fail
