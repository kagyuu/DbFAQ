#!/bin/bash
# A07: 受入テストのスイート全体(A01〜A06)を順に実行し、各テストの PASS/FAIL を 1 行ずつ出力する
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
LOG=$(mktemp -d)
res() { if [ "$2" -eq 0 ]; then echo "$1 PASS"; else echo "$1 FAIL"; fi; }
wait_ok() { for i in $(seq 1 90); do curl -s "http://localhost:${DBFAQ_PORT:-8088}/api/health" 2>/dev/null | grep -q '"status":"ok"' && return 0; sleep 1; done; return 1; }

bash e2e/scripts/reset-and-up.sh > "$LOG/reset.log" 2>&1; res RESET $?
(cd e2e && npx playwright test tests/a01-er-diagram.spec.ts > "$LOG/a01.log" 2>&1); res A01 $?
(cd e2e && npx playwright test tests/a02-table-detail.spec.ts > "$LOG/a02.log" 2>&1); res A02 $?

DBFAQ_ORACLE_HOST=oracle-unreachable.invalid docker compose up -d --no-deps --force-recreate api > "$LOG/a03-up.log" 2>&1
for i in $(seq 1 60); do curl -sf "http://localhost:${DBFAQ_PORT:-8088}/api/health" > /dev/null && break; sleep 1; done
(cd e2e && npx playwright test tests/a03-oracle-down.spec.ts -g unreachable > "$LOG/a03.log" 2>&1); a03=$?
docker compose up -d --no-deps --force-recreate api >> "$LOG/a03-up.log" 2>&1
wait_ok
(cd e2e && npx playwright test tests/a03-oracle-down.spec.ts -g recovered >> "$LOG/a03.log" 2>&1); a03b=$?
res A03 $((a03 + a03b))

bash e2e/scripts/a04-restart.sh > "$LOG/a04.log" 2>&1; res A04 $?

a05=0
bash e2e/scripts/a05-perf-api.sh hr > "$LOG/a05.log" 2>&1 || a05=1
(cd e2e && npx playwright test tests/a05-performance.spec.ts -g "hr:" >> "$LOG/a05.log" 2>&1) || a05=1
bash e2e/scripts/a05-load-large.sh >> "$LOG/a05.log" 2>&1 || a05=1
bash e2e/scripts/a05-perf-api.sh large >> "$LOG/a05.log" 2>&1 || a05=1
(cd e2e && npx playwright test tests/a05-performance.spec.ts -g "large:" >> "$LOG/a05.log" 2>&1) || a05=1
bash e2e/scripts/a05-restore-hr.sh >> "$LOG/a05.log" 2>&1 || a05=1
res A05 $a05

bash e2e/scripts/a06-security.sh > "$LOG/a06.log" 2>&1; res A06 $?
echo "logs: $LOG" >&2
