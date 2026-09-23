#!/bin/bash
# A05 の API 側の測定。引数 hr: 手順 1〜3、large: 手順 5
set -uo pipefail
BASE="http://localhost:${DBFAQ_PORT:-8088}"
median() { sort -n | awk '{a[NR]=$1} END {print a[int((NR+1)/2)]}'; }
fail=0
judge() { if python3 -c "import sys; sys.exit(0 if float('$2') < float('$3') else 1)"; then echo "OK   $1 = $2 s (< $3)"; else echo "FAIL $1 = $2 s (>= $3)"; fail=1; fi; }
if [ "${1:-hr}" = "hr" ]; then
  RAW=$(for i in 1 2 3 4 5; do curl -s -o /dev/null -w '%{time_total}\n' "$BASE/api/schema"; done)
  echo "schema raw: $(echo $RAW)"; judge "HR GET /api/schema 中央値" "$(echo "$RAW" | median)" 1
  judge "HR POST /api/schema/refresh" "$(curl -s -o /dev/null -w '%{time_total}' -X POST "$BASE/api/schema/refresh")" 10
  OUT=$(curl -s -w '\n%{time_total}' "$BASE/api/schema/tables/HR/EMPLOYEES/rows?offset=0&limit=50")
  T=$(echo "$OUT" | tail -1); MS=$(echo "$OUT" | head -1 | python3 -c 'import json,sys; print(json.load(sys.stdin)["elapsed_ms"])')
  judge "HR rows のオーバーヘッド(total - elapsed_ms)" "$(python3 -c "print(round($T - $MS/1000, 3))")" 1
else
  RAW=$(for i in 1 2 3 4 5; do curl -s -o /dev/null -w '%{time_total}\n' "$BASE/api/schema"; done)
  echo "large schema raw: $(echo $RAW)"; judge "大規模 GET /api/schema 中央値" "$(echo "$RAW" | median)" 3
fi
exit $fail
