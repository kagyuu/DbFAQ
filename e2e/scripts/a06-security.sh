#!/bin/bash
# A06: 読み取りのみ・秘密情報・公開範囲(docs/P009-acceptance-direction/A06-security-readonly.md)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
BASE="http://localhost:${DBFAQ_PORT:-8088}"
PW=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml'))['oracle']['password'])")
fail=0
ok() { echo "OK   $1"; }
ng() { echo "FAIL $1"; fail=1; }

# 6(※CR-004により追加)。チェックサム(手順 1)より先に送り、送った後に HR が変わっていないことを手順 1 で確かめる
for sql in "UPDATE HR.EMPLOYEES SET SALARY = SALARY + 1" "DELETE FROM HR.EMPLOYEES" "DROP TABLE HR.EMPLOYEES" \
           "BEGIN NULL; END;" "SELECT * FROM HR.EMPLOYEES FOR UPDATE" "SELECT 1 FROM DUAL; DELETE FROM HR.EMPLOYEES"; do
  for path in /api/query /api/query/csv; do
    body=$(python3 -c 'import json,sys; print(json.dumps({"sql": sys.argv[1]}))' "$sql")
    res=$(curl -s -w '\n%{http_code}' -H 'Content-Type: application/json' -d "$body" "$BASE$path")
    code=$(echo "$res" | tail -1); err=$(echo "$res" | head -n -1 | python3 -c 'import json,sys; print(json.load(sys.stdin)["error"]["code"])' 2>/dev/null)
    [ "$code" = "422" ] && [ "$err" = "SQL_REJECTED" ] && ok "$path が拒否: $sql" || ng "$path が拒否しない($code $err): $sql"
  done
done

# 1
# 取得に失敗した・ベースラインが無いときは FAIL にする(空同士を一致と判定しない。P202 F009)
if ! NOW=$(cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/hr_checksum.py) || [ -z "$NOW" ]; then
  ng "HR のチェックサムを取得できない"
elif [ ! -s e2e/.baseline-checksum.json ]; then
  ng "ベースラインのチェックサム(e2e/.baseline-checksum.json)が無い"
elif [ "$NOW" = "$(cat e2e/.baseline-checksum.json)" ]; then ok "HR のチェックサムがベースラインと一致"; else ng "HR のチェックサムが違う"; diff <(echo "$NOW") e2e/.baseline-checksum.json; fi

# 2(パスワード自体は出力しない)
for what in health schema; do
  path=$([ $what = health ] && echo /api/health || echo /api/schema)
  curl -s "$BASE$path" | grep -qF -- "$PW" && ng "パスワードが $path の応答に含まれる" || ok "$path の応答にパスワードなし"
done
docker compose logs api web 2>&1 | grep -qF -- "$PW" && ng "パスワードがログに含まれる" || ok "ログにパスワードなし"
IMG=$(docker compose images -q api | head -1)
docker image inspect "$IMG" | grep -qF -- "$PW" && ng "パスワードがイメージ情報に含まれる" || ok "イメージ情報にパスワードなし"
docker run --rm --entrypoint sh "$IMG" -c "grep -rlF -- '$PW' /app 2>/dev/null" | grep -q . && ng "パスワードがイメージ内のファイルに含まれる" || ok "イメージ内のファイルにパスワードなし"

# 3
PUB=$(docker compose ps --format json | python3 -c '
import json,sys
pub=set()
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    items=json.loads(line)
    for s in (items if isinstance(items,list) else [items]):
        for p in s.get("Publishers") or []:
            if p.get("PublishedPort"): pub.add(s["Service"] + ":" + str(p["PublishedPort"]))
print(" ".join(sorted(pub)))')
[ "$PUB" = "web:8088" ] && ok "公開ポートは web:8088 のみ" || ng "公開ポート: $PUB"

# 4
curl -s -i -H 'Origin: http://evil.example' "$BASE/api/schema" | grep -qi '^access-control-allow-origin' && ng "CORS ヘッダがある" || ok "CORS ヘッダなし"

# 5
[ -z "$(git ls-files config.yaml)" ] && ok "config.yaml はリポジトリに無い" || ng "config.yaml がリポジトリにある"

[ $fail -eq 0 ] && echo "A06 PASS" || echo "A06 FAIL"
exit $fail
