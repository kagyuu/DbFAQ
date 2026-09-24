#!/bin/bash
# A08: 同時利用者 10 名(docs/P009-acceptance-direction/A08-concurrent-users.md)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/server"
uv run python scripts/a08_concurrent_load.py --base "http://localhost:${DBFAQ_PORT:-8088}"
