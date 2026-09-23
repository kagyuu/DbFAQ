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

F0=$(fetched); echo "F0=$F0"
docker compose restart api > /dev/null 2>&1
wait_health && echo "OK   restart: api が起動した" || { echo "FAIL restart: api が起動しない"; fail=1; }
check "restart 後のスナップショット" "$(fetched)" "$F0"

docker compose down > /dev/null 2>&1
docker compose up -d > /dev/null 2>&1
wait_health && echo "OK   down/up: api が起動した" || { echo "FAIL down/up: api が起動しない"; fail=1; }
check "down/up 後のスナップショット" "$(fetched)" "$F0"

N=$(docker compose exec -T api python -c "import sqlite3; print(sqlite3.connect('/data/dbfaq.sqlite3').execute('select count(*) from schema_migrations').fetchone()[0])")
check "schema_migrations の件数" "$N" "1"

E=$(docker compose logs api 2>&1 | grep -cE 'Traceback|MigrationError')
check "起動時の例外" "$E" "0"

docker compose exec -T api python -c "import os,signal; [os.kill(int(p),signal.SIGKILL) for p in os.listdir('/proc') if p.isdigit() and int(p)!=os.getpid() and b'-m\x00dbfaq_mcp' in open(f'/proc/{p}/cmdline','rb').read()]"
status=""
for i in 1 2 3; do
  status=$(curl -s "$BASE/api/health" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
  [ "$status" = "ok" ] && break
  sleep 1
done
check "MCP 強制終了後の回復" "$status" "ok"

[ $fail -eq 0 ] && echo "A04 PASS" || echo "A04 FAIL"
exit $fail
