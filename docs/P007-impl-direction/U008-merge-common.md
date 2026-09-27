あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U008 — merge-common(※CR-003により追加)

共通部品パッケージ `dbfaq_common` を `dbfaq_api` に統合する。**設定の読み込みとログの処理の中身は変えない。** 変更要求: `docs/P901-cr-direction/CR-003.md`。

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U008-T1 [モジュールを移して import を直す](#u008-t1-モジュールを移して-import-を直す) — `config.py`・`log.py` への移設、`src`・`tests`・`scripts` の import、`pyproject.toml`

---

## U008-T1: モジュールを移して import を直す

### 【目的】

* `dbfaq_common` の 2 モジュールを `dbfaq_api` に移し、パッケージを 1 つにする。

### 【作成・編集対象ファイル】

* `git mv server/src/dbfaq_common/config.py server/src/dbfaq_api/config.py`
* `git mv server/src/dbfaq_common/logging.py server/src/dbfaq_api/log.py`
* 削除: `server/src/dbfaq_common/__init__.py`(ディレクトリごと)
* import の変更: `server/src/dbfaq_api/`(`main.py`・`services.py`・`oracle/client.py`・`oracle/db.py`・`oracle/errors.py`)、`server/tests/`(`dbfaq_common` を import しているすべてのファイル)、`server/scripts/`(`check_oracle.py`・`hr_checksum.py`)
* `server/pyproject.toml`(`[tool.hatch.build.targets.wheel] packages` を `["src/dbfaq_api"]` に)、`server/uv.lock`
* 移したモジュールの docstring(「MCP サーバは stream=sys.stderr で呼ぶ」などの古い記述があれば直す)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §1.2、§2、§4.5

### 【実装内容】

* `dbfaq_api` パッケージ内のモジュールは相対 import(`from .config import ...`、`from ..log import ...`)、テスト・スクリプトは絶対 import(`from dbfaq_api.config import ...`、`from dbfaq_api.log import ...`)にする。
* `tests/unit/test_packages.py` は `dbfaq_common` の import を削除し、`dbfaq_api.config`・`dbfaq_api.log` の import に置き換える。
* 名前(`load_config`、`AppConfig`、`OracleConfig`、`ConfigError`、`config_file_path`、`setup_logging`、`JsonFormatter`、`mask_secret`)と中身は変えない。

### 【実装してはいけないこと】

* 設定の項目・既定値・検証・環境変数の上書き、ログの形式を変えない。
* 画面・API・データモデルに関わるコードを変えない。

### 【Unit Test内容】

* 既存の `tests/unit/test_config.py`・`test_logging.py` を含む単体テストが、import 先の変更だけで全件合格する(期待値は変えない)。
* 合格条件: すべて合格。`grep -rn "dbfaq_common" server/src server/tests server/scripts server/pyproject.toml` が 0 件。

### 【実行コマンド】

* `cd server && uv lock && uv sync && uv run pytest tests/unit -q && uv run ruff check src tests scripts`
* `grep -rn "dbfaq_common" server/src server/tests server/scripts server/pyproject.toml`(出力なし)
* `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py`(`7`)

### 【完了条件】

* 単体テストが合格し、`dbfaq_common` の参照が残っておらず、`check_oracle.py` が `7` を出す。ruff の指摘が CR-003 前より増えていない。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
