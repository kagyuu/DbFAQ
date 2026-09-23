# Build History

| Build ID | Version | Date/Time | Commit | Build Command | Test Command | Result | Notes |
|---|---|---|---|---|---|---|---|
| B001 | 0.1.0 | 2026-09-23 03:10 JST | e0afb86 + 未コミットの作業ツリー | `docker compose up -d --build` | `uv run pytest tests/unit`、`npm test`、P008 T01〜T12 | FAIL | P103。T05 FAIL(MCP の JSON ログなし)。docs/test-records/20260923-0315-test-record.md |
| B002 | 0.1.0 | 2026-09-23 03:20 JST | e0afb86 + 未コミットの作業ツリー | `bash e2e/scripts/reset-and-up.sh`(compose を再構築) | P009 A01〜A06(`e2e/scripts/run-suite.sh`) | FAIL | P201 1 回目。A01・A02・A05・A06 がテストコード/手順の欠陥で FAIL。docs/test-records/20260923-0320-test-record.md |
| B003 | 0.1.0 | 2026-09-23 03:35〜03:50 JST | e0afb86 + 未コミットの作業ツリー(F001〜F006 適用後) | `bash e2e/scripts/reset-and-up.sh`(compose を再構築、2 回) | 単体 131 + 54、T01〜T09 を 2 回、T10〜T12、A01〜A06 を 2 回(A07) | PASS | P205。docs/test-records/20260923-0350-test-record.md |

* コミット: 本リポジトリは初期コミット(e0afb86)の後、作業ツリーが未コミットのまま。人間がコミットした時点でコミット ID を追記する。
