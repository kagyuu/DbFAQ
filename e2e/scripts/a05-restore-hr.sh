#!/bin/bash
# A05: HR のスナップショットに戻す
set -euo pipefail
BASE="http://localhost:${DBFAQ_PORT:-8088}"
curl -s -X POST "$BASE/api/schema/refresh" > /dev/null
N=$(curl -s "$BASE/api/schema" | python3 -c 'import json,sys; print(json.load(sys.stdin)["snapshot"]["table_count"])')
[ "$N" = "8" ] && echo "HR restored (8 tables)" || { echo "restore failed: $N"; exit 1; }
