> **※CR-002 による注記(※P011(CR-002)矛盾点#3にもとづき追加)。** 本書は第 1 リリース時点の実装指示の記録として残す。CR-002 後は `dbfaq_mcp` が無いため、U006-T1 のイメージ確認コマンドの `import dbfaq_api.main, dbfaq_mcp.server` は `import dbfaq_api.main, dbfaq_api.oracle.client` と読み替える。`api.Dockerfile`・`compose.yaml` のコメントは U007-T5 で更新した。

あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U006 — deploy

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U006-T1 [api イメージ](#u006-t1-api-イメージ) — `deploy/api.Dockerfile`
- [x] U006-T2 [web イメージと nginx](#u006-t2-web-イメージと-nginx) — `deploy/web.Dockerfile`・`deploy/nginx.conf`
- [x] U006-T3 [compose](#u006-t3-compose) — `compose.yaml` と構成の検査テスト
- [x] U006-T4 [受入テストの実行環境](#u006-t4-受入テストの実行環境) — `e2e/` の初期化と疎通テスト

---

## U006-T1: api イメージ

### 【目的】

* backend と MCP サーバを 1 つのイメージにする。

### 【作成・編集対象ファイル】

* `deploy/api.Dockerfile`、`.dockerignore`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §1.1、§2、§4.2、§6、`docs/P005-impl-plan.md` U006

### 【実装内容】

* ベース `python:3.12-slim`。`COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`。
* `WORKDIR /app/server`。`server/pyproject.toml`・`server/uv.lock` を先にコピーして `uv sync --frozen --no-dev --no-install-project`、続けて `server/src` をコピーして `uv sync --frozen --no-dev`。
* `ENV PATH=/app/server/.venv/bin:$PATH DBFAQ_CONFIG=/config/config.yaml DBFAQ_SQLITE_PATH=/data/dbfaq.sqlite3 PYTHONUNBUFFERED=1`。
* 非 root ユーザー(`useradd -u 10001 dbfaq`)で実行。`/data` を作って所有者を dbfaq にする。
* `EXPOSE 8000`。`CMD ["uvicorn", "--factory", "dbfaq_api.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]`。
* `HEALTHCHECK` は付けない(compose 側で定義する)。
* `.dockerignore`: `**/node_modules`、`**/.venv`、`**/__pycache__`、`config.yaml`、`data/`、`server/data/`、`client/dist`、`e2e/`、`docs/`、`.git`。

### 【実装してはいけないこと】

* `config.yaml`(パスワード)をイメージに含めない。
* uvicorn を 2 ワーカー以上にしない(P003 §4.2)。

### 【Unit Test内容】

* このタスクはコンテナイメージの定義であり単体テストの対象となるロジックを持たない。確認は下記コマンドで行う: イメージがビルドできる/イメージ内に `config.yaml` が無い/`python -m dbfaq_mcp` と `dbfaq_api` が import できる。

### 【実行コマンド】

* `docker build -f deploy/api.Dockerfile -t dbfaq-api:dev .`
* `docker run --rm dbfaq-api:dev sh -c 'test ! -e /config/config.yaml && test ! -e /app/config.yaml && python -c "import dbfaq_api.main, dbfaq_mcp.server; print(\"ok\")"'`

### 【完了条件】

* 2 つのコマンドがともに成功し、`ok` が表示される。

### 【次タスクに進む前の停止条件】

* ベースイメージの取得に失敗し 3 回試しても解消しない場合は停止して報告する。

---

## U006-T2: web イメージと nginx

### 【目的】

* ビルド済みのフロントエンドを nginx で配信し、`/api` を api コンテナへ中継する。

### 【作成・編集対象ファイル】

* `deploy/web.Dockerfile`、`deploy/nginx.conf`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §1.1、§7

### 【実装内容】

* `web.Dockerfile`: ステージ 1 `node:22-alpine` で `client/package*.json` をコピーして `npm ci`、`client/` をコピーして `npm run build`。ステージ 2 `nginx:1.27-alpine` に `dist/` を `/usr/share/nginx/html`、`deploy/nginx.conf` を `/etc/nginx/conf.d/default.conf`。
* `nginx.conf`:
  * `listen 80;`
  * `location /api/ { proxy_pass http://api:8000; proxy_read_timeout 120s; proxy_set_header Host $host; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; }`(refresh は時間がかかるため 120 秒)
  * `location / { try_files $uri /index.html; }`(SPA のフォールバック)
  * `location /assets/ { expires 7d; }`
  * `server_tokens off;`

### 【実装してはいけないこと】

* TLS を設定しない(P003 §6。運用環境のリバースプロキシで終端する)。

### 【Unit Test内容】

* このタスクは配信設定であり単体テストの対象となるロジックを持たない。確認は下記コマンドで行う: イメージがビルドできる/nginx の設定が文法的に正しい(`api` の名前解決ができない単独起動でも `nginx -t` が通るよう、`--add-host api:127.0.0.1` を付けて検査する)。

### 【実行コマンド】

* `docker build -f deploy/web.Dockerfile -t dbfaq-web:dev .`
* `docker run --rm --add-host api:127.0.0.1 dbfaq-web:dev nginx -t`

### 【完了条件】

* 2 つのコマンドがともに成功する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても解消しない場合は停止して報告する。

---

## U006-T3: compose

### 【目的】

* web と api を Docker Compose で起動できるようにする。

### 【作成・編集対象ファイル】

* `compose.yaml`
* `server/tests/unit/test_compose.py`

### 【参照すべき仕様箇所】

* `docs/P005-impl-plan.md` U006、`docs/P003-backend-spec.md` §2.2、§6

### 【実装内容】

* `compose.yaml`(プロジェクト名 `dbfaq`):
  * `api`: `build: {context: ., dockerfile: deploy/api.Dockerfile}`、`restart: unless-stopped`、**`ports` を書かない**、`environment: DBFAQ_ORACLE_HOST: ${DBFAQ_ORACLE_HOST:-host.docker.internal}`、`extra_hosts: ["host.docker.internal:host-gateway"]`、`volumes: ["./config.yaml:/config/config.yaml:ro", "dbfaq-data:/data"]`、`healthcheck: test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health').status==200 else 1)"]`、`interval: 30s`、`timeout: 10s`、`retries: 3`、`start_period: 20s`。
  * `web`: `build: {context: ., dockerfile: deploy/web.Dockerfile}`、`restart: unless-stopped`、`ports: ["${DBFAQ_PORT:-8088}:80"]`、`depends_on: {api: {condition: service_started}}`。
  * `volumes: {dbfaq-data: {}}`。
* `test_compose.py`(PyYAML で `compose.yaml` を読む): api に `ports` が無い/web だけが `ports` を持つ/api の config マウントが `:ro`/両サービス `restart: unless-stopped`/api に `host.docker.internal:host-gateway`/`dbfaq-data` が `/data` にマウント。

### 【実装してはいけないこと】

* Oracle のコンテナを compose に入れない(開発用 Oracle は既存のものを使う。P005 U001)。
* api のポートをホストに公開しない。

### 【Unit Test内容】

* テスト対象: `compose.yaml` の構成(上記 6 項目)
* 正常系: 6 項目すべて。異常系: なし(構成の検査のため)。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/test_compose.py -q`
* `docker compose config -q`
* `docker compose up -d --build && sleep 15 && curl -s http://localhost:8088/api/health && docker compose ps`

### 【完了条件】

* テストが合格し、`/api/health` が `"status": "ok"`(Oracle に届いている)を返し、`docker compose ps` で api が `healthy`(start_period 後)、web が `running`。確認後も起動したままでよい(U006-T4 で使う)。

### 【次タスクに進む前の停止条件】

* コンテナから Oracle に届かない(`oracle.status=error`)場合は、`docker compose exec api python -c "import socket; socket.create_connection(('host.docker.internal',1521),5)"` で切り分ける。WSL2 等の環境要因と判明した場合は `SKILL.md` の共通指示に従い記録し、回避策(`DBFAQ_ORACLE_HOST` にホストの IP を指定する等)を採る。3 回試しても解消しない場合は停止して報告する。

---

## U006-T4: 受入テストの実行環境

### 【目的】

* Playwright で compose の web に対してブラウザ操作テストを実行できるようにする(テストケース自体は P009 で定義する)。

### 【作成・編集対象ファイル】

* `e2e/package.json`、`e2e/package-lock.json`、`e2e/playwright.config.ts`、`e2e/tsconfig.json`、`e2e/tests/smoke.spec.ts`

### 【参照すべき仕様箇所】

* `docs/P006-test-plan.md` §3.1、§3.3

### 【実装内容】

* `e2e/` を `npm init playwright@latest` 相当の構成で初期化(TypeScript、ブラウザは Chromium のみ)。
* `playwright.config.ts`: `baseURL: process.env.DBFAQ_BASE_URL ?? "http://localhost:8088"`、`workers: 1`、`fullyParallel: false`(テスト間でスナップショットを共有するため順に実行)、`retries: 0`、`reporter: [["list"], ["html", { open: "never" }]]`、`use: { trace: "retain-on-failure", screenshot: "only-on-failure" }`、`timeout: 60_000`。
* `smoke.spec.ts`: トップを開くとヘッダに「DbFAQ」が表示される/`/api/health` を `request` で呼んで 200。

### 【実装してはいけないこと】

* P009 で定義する受入テストのケースをここで先に書かない。

### 【Unit Test内容】

* このタスクはテスト実行環境の整備であり、確認は疎通テスト(`smoke.spec.ts` 2 件)の実行で行う。

### 【実行コマンド】

* `cd e2e && npm install && npx playwright install chromium && npx playwright test tests/smoke.spec.ts`

### 【完了条件】

* 疎通テスト 2 件が合格する(compose が U006-T3 で起動済みであること)。

### 【次タスクに進む前の停止条件】

* Chromium の依存ライブラリが足りず起動できない場合は `npx playwright install-deps chromium` を試す(sudo が要る場合は人間に依頼する旨を停止報告に書く)。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
