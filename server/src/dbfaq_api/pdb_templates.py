"""PDB の Query のひな型(docs/P003-backend-spec.md §4.7、docs/P001-requirement.md §6 SC-03)。※CR-005により追加

起動時に 1 回だけ saved_queries(scope='pdb')へ登録する(登録済みかは query_template_seeds で判定)。
登録した後は通常の保存済み Query と同じく、利用者が変更・削除できる。key は登録済みの判定に使うため変えない。
SQL は Query タブの検査(oracle/sql_guard.py)を通る形にする(更新系のキーワードを引用符なしで書かない)。
"""

from __future__ import annotations

from dataclasses import dataclass

NEEDS_DBA = "DBA_* ・V$ ビューを読む権限(SELECT_CATALOG_ROLE など)が要ります。権限が無いと ORA-00942 になります。"


@dataclass(frozen=True)
class PdbTemplate:
    key: str
    name: str
    description: str
    sql: str


_USERS_TS_SIZE = """\
SELECT
  df.tablespace_name,
  ROUND(df.bytes / 1024 / 1024, 2) AS total_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / 1024 / 1024, 2) AS used_mb,
  ROUND(NVL(fs.bytes, 0) / 1024 / 1024, 2) AS free_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / df.bytes * 100, 1) AS used_pct,
  ROUND(df.max_bytes / 1024 / 1024, 2) AS max_mb,
  df.file_count
FROM (
  SELECT
    tablespace_name,
    SUM(bytes) AS bytes,
    SUM(CASE WHEN autoextensible = 'YES' THEN GREATEST(maxbytes, bytes) ELSE bytes END) AS max_bytes,
    COUNT(*) AS file_count
  FROM dba_data_files
  GROUP BY tablespace_name
) df
  LEFT JOIN (
    SELECT tablespace_name, SUM(bytes) AS bytes
    FROM dba_free_space
    GROUP BY tablespace_name
  ) fs ON fs.tablespace_name = df.tablespace_name
WHERE df.tablespace_name = 'USERS'"""

_USERS_TS_MINE = """\
SELECT
  q.tablespace_name,
  ROUND(q.bytes / 1024 / 1024, 2) AS used_mb,
  CASE WHEN q.max_bytes = -1 THEN 'UNLIMITED' ELSE TO_CHAR(ROUND(q.max_bytes / 1024 / 1024, 2)) END AS quota_mb,
  (SELECT COUNT(*) FROM user_segments s WHERE s.tablespace_name = q.tablespace_name) AS segment_count
FROM user_ts_quotas q
WHERE q.tablespace_name = 'USERS'"""

# 実データの合計は列ごとに SUM(DBMS_LOB.GETLENGTH(列)) を求める必要があり、列名を動的に埋め込む。
# 動的 SQL(EXECUTE IMMEDIATE・DBMS_SQL)は Query の検査で拒否されるため、DBMS_XMLGEN で問い合わせを実行して値を取り出す。
_LOB_MINE = """\
WITH lob_cols AS (
  SELECT
    l.table_name,
    l.column_name,
    c.data_type,
    l.segment_name,
    l.securefile,
    (SELECT NVL(SUM(s.bytes), 0) FROM user_segments s WHERE s.segment_name = l.segment_name) AS segment_bytes,
    (SELECT NVL(SUM(s.bytes), 0) FROM user_segments s WHERE s.segment_name = l.index_name) AS lobindex_bytes,
    TO_NUMBER(XMLCAST(XMLQUERY('/ROWSET/ROW/V/text()' PASSING DBMS_XMLGEN.GETXMLTYPE(
      'SELECT NVL(SUM(DBMS_LOB.GETLENGTH("' || l.column_name || '")), 0) AS V FROM "' || l.table_name || '"'
    ) RETURNING CONTENT) AS VARCHAR2(40))) AS data_length
  FROM user_lobs l
    JOIN user_tab_columns c ON c.table_name = l.table_name AND c.column_name = l.column_name
)
SELECT
  table_name || '.' || column_name AS table_column,
  data_type,
  segment_name,
  securefile,
  ROUND(segment_bytes / 1024 / 1024, 2) AS segment_mb,
  ROUND(lobindex_bytes / 1024 / 1024, 2) AS lobindex_mb,
  data_length,
  CASE WHEN data_type IN ('CLOB', 'NCLOB') THEN 'CHARS' ELSE 'BYTES' END AS data_length_unit,
  ROUND(data_length / 1024 / 1024, 2) AS data_mb
FROM lob_cols
ORDER BY segment_bytes DESC, table_name, column_name"""

_LOB_ALL = """\
WITH lob_cols AS (
  SELECT
    l.owner,
    l.table_name,
    l.column_name,
    c.data_type,
    l.segment_name,
    l.securefile,
    (SELECT NVL(SUM(s.bytes), 0) FROM dba_segments s
      WHERE s.owner = l.owner AND s.segment_name = l.segment_name) AS segment_bytes,
    TO_NUMBER(XMLCAST(XMLQUERY('/ROWSET/ROW/V/text()' PASSING DBMS_XMLGEN.GETXMLTYPE(
      'SELECT NVL(SUM(DBMS_LOB.GETLENGTH("' || l.column_name || '")), 0) AS V FROM "'
        || l.owner || '"."' || l.table_name || '"'
    ) RETURNING CONTENT) AS VARCHAR2(40))) AS data_length
  FROM dba_lobs l
    JOIN dba_tab_columns c ON c.owner = l.owner AND c.table_name = l.table_name AND c.column_name = l.column_name
    JOIN dba_users u ON u.username = l.owner
  WHERE u.oracle_maintained = 'N'
)
SELECT
  owner || '.' || table_name || '.' || column_name AS table_column,
  data_type,
  segment_name,
  securefile,
  ROUND(segment_bytes / 1024 / 1024, 2) AS segment_mb,
  data_length,
  CASE WHEN data_type IN ('CLOB', 'NCLOB') THEN 'CHARS' ELSE 'BYTES' END AS data_length_unit,
  ROUND(data_length / 1024 / 1024, 2) AS data_mb
FROM lob_cols
ORDER BY segment_bytes DESC, owner, table_name, column_name"""

_TS_USAGE = """\
SELECT
  df.tablespace_name,
  ROUND(df.bytes / 1024 / 1024, 2) AS total_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / 1024 / 1024, 2) AS used_mb,
  ROUND(NVL(fs.bytes, 0) / 1024 / 1024, 2) AS free_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / df.bytes * 100, 1) AS used_pct,
  ROUND(df.max_bytes / 1024 / 1024, 2) AS max_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / df.max_bytes * 100, 1) AS used_pct_of_max
FROM (
  SELECT
    tablespace_name,
    SUM(bytes) AS bytes,
    SUM(CASE WHEN autoextensible = 'YES' THEN GREATEST(maxbytes, bytes) ELSE bytes END) AS max_bytes
  FROM dba_data_files
  GROUP BY tablespace_name
) df
  LEFT JOIN (
    SELECT tablespace_name, SUM(bytes) AS bytes
    FROM dba_free_space
    GROUP BY tablespace_name
  ) fs ON fs.tablespace_name = df.tablespace_name
ORDER BY used_pct DESC"""

_DATA_FILES = """\
SELECT
  tablespace_name,
  file_name,
  ROUND(bytes / 1024 / 1024, 2) AS size_mb,
  autoextensible,
  ROUND(maxbytes / 1024 / 1024, 2) AS max_mb,
  increment_by,
  status,
  online_status
FROM dba_data_files
ORDER BY tablespace_name, file_name"""

_TEMP_USAGE = """\
SELECT
  tablespace_name,
  ROUND(tablespace_size / 1024 / 1024, 2) AS total_mb,
  ROUND(allocated_space / 1024 / 1024, 2) AS allocated_mb,
  ROUND(free_space / 1024 / 1024, 2) AS free_mb
FROM dba_temp_free_space
ORDER BY tablespace_name"""

_TOP_SEGMENTS = """\
SELECT
  segment_name,
  partition_name,
  segment_type,
  tablespace_name,
  ROUND(bytes / 1024 / 1024, 2) AS size_mb,
  extents
FROM user_segments
ORDER BY bytes DESC
FETCH FIRST 50 ROWS ONLY"""

_TABLE_STATS = """\
SELECT
  t.table_name,
  t.num_rows,
  t.blocks,
  t.avg_row_len,
  TO_CHAR(t.last_analyzed, 'YYYY-MM-DD HH24:MI:SS') AS last_analyzed,
  s.stale_stats
FROM user_tables t
  LEFT JOIN user_tab_statistics s ON s.table_name = t.table_name AND s.object_type = 'TABLE'
ORDER BY t.last_analyzed NULLS FIRST, t.table_name"""

_INVALID_OBJECTS = """\
SELECT
  object_type,
  object_name,
  status,
  TO_CHAR(last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') AS last_ddl_time
FROM user_objects
WHERE status <> 'VALID'
ORDER BY object_type, object_name"""

_UNUSABLE_INDEXES = """\
SELECT index_name, NULL AS partition_name, table_name, status
FROM user_indexes
WHERE status = 'UNUSABLE'
UNION ALL
SELECT p.index_name, p.partition_name, i.table_name, p.status
FROM user_ind_partitions p
  JOIN user_indexes i ON i.index_name = p.index_name
WHERE p.status = 'UNUSABLE'
ORDER BY 3, 1, 2"""

_DISABLED_CONSTRAINTS = """\
SELECT
  table_name,
  constraint_name,
  constraint_type,
  status,
  validated
FROM user_constraints
WHERE status = 'DISABLED' OR validated = 'NOT VALIDATED'
ORDER BY table_name, constraint_name"""

_OBJECT_COUNTS = """\
SELECT object_type, status, COUNT(*) AS object_count
FROM user_objects
GROUP BY object_type, status
ORDER BY object_type, status"""

_SESSIONS = """\
SELECT
  sid,
  serial#,
  username,
  status,
  osuser,
  machine,
  program,
  sql_id,
  TO_CHAR(logon_time, 'YYYY-MM-DD HH24:MI:SS') AS logon_time,
  last_call_et AS last_call_sec
FROM v$session
WHERE type = 'USER'
ORDER BY status, last_call_et DESC"""

_BLOCKING = """\
SELECT
  w.sid AS waiting_sid,
  w.username AS waiting_user,
  w.event,
  w.seconds_in_wait,
  w.blocking_session AS blocking_sid,
  b.username AS blocking_user,
  b.status AS blocking_status,
  b.sql_id AS blocking_sql_id
FROM v$session w
  LEFT JOIN v$session b ON b.sid = w.blocking_session
WHERE w.blocking_session IS NOT NULL
ORDER BY w.seconds_in_wait DESC"""

_LONG_OPS = """\
SELECT
  sid,
  serial#,
  opname,
  target,
  sofar,
  totalwork,
  ROUND(sofar / NULLIF(totalwork, 0) * 100, 1) AS done_pct,
  elapsed_seconds,
  time_remaining
FROM v$session_longops
WHERE time_remaining > 0
ORDER BY time_remaining DESC"""

_USER_QUOTAS = """\
SELECT
  username,
  tablespace_name,
  ROUND(bytes / 1024 / 1024, 2) AS used_mb,
  CASE WHEN max_bytes = -1 THEN 'UNLIMITED' ELSE TO_CHAR(ROUND(max_bytes / 1024 / 1024, 2)) END AS quota_mb
FROM dba_ts_quotas
ORDER BY bytes DESC"""

PDB_TEMPLATES: tuple[PdbTemplate, ...] = (
    PdbTemplate(
        "pdb.users_ts_size",
        "01. USERS 表領域の大きさ",
        "USERS 表領域の合計・使用・空き(MB)、使用率、自動拡張の上限、データファイル数。" + NEEDS_DBA,
        _USERS_TS_SIZE,
    ),
    PdbTemplate(
        "pdb.users_ts_mine",
        "02. USERS 表領域の使用量(接続ユーザー分)",
        "接続ユーザーが USERS 表領域で使っている容量と割り当て上限(USER_TS_QUOTAS)。権限は要りません。"
        "表領域全体の大きさは 01 で見ます。",
        _USERS_TS_MINE,
    ),
    PdbTemplate(
        "pdb.lob_size_mine",
        "03. LOB 領域の大きさと実データの合計(テーブル.カラムごと)",
        "接続ユーザーのテーブルの LOB 列ごとに、LOB セグメントと LOB 索引の大きさ(MB)と、実データの合計"
        "(SUM(DBMS_LOB.GETLENGTH))を表示します。実データの単位は BLOB はバイト、CLOB・NCLOB は文字数です"
        "(AL32UTF8 の CLOB は内部では 1 文字 2 バイトで格納されます)。権限は要りません。"
        "全行の LOB を読むため、大きな表では時間がかかります。",
        _LOB_MINE,
    ),
    PdbTemplate(
        "pdb.lob_size_all",
        "04. LOB 領域の大きさと実データの合計(全スキーマ)",
        "Oracle 管理以外の全スキーマの LOB 列ごとに、LOB セグメントの大きさ(MB)と実データの合計を表示します。"
        + NEEDS_DBA
        + "各テーブルを SELECT する権限も要ります。全行の LOB を読むため時間がかかります。",
        _LOB_ALL,
    ),
    PdbTemplate(
        "pdb.ts_usage",
        "05. 表領域ごとの使用率",
        "全表領域(一時表領域を除く)の合計・使用・空き(MB)、使用率、自動拡張の上限に対する使用率。使用率の高い順。"
        + NEEDS_DBA,
        _TS_USAGE,
    ),
    PdbTemplate(
        "pdb.data_files",
        "06. データファイルと自動拡張の設定",
        "データファイルごとの大きさ、自動拡張の有無と上限、状態。" + NEEDS_DBA,
        _DATA_FILES,
    ),
    PdbTemplate(
        "pdb.temp_usage",
        "07. 一時表領域の使用状況",
        "一時表領域の大きさ・割り当て済み・空き(MB)。" + NEEDS_DBA,
        _TEMP_USAGE,
    ),
    PdbTemplate(
        "pdb.top_segments",
        "08. セグメントの大きい順(上位 50)",
        "接続ユーザーのセグメント(表・索引・LOB など)を大きい順に 50 件。権限は要りません。",
        _TOP_SEGMENTS,
    ),
    PdbTemplate(
        "pdb.table_stats",
        "09. テーブルの行数と統計情報の鮮度",
        "接続ユーザーのテーブルの統計上の行数・ブロック数、統計の取得日時、統計が古いか(STALE_STATS)。"
        "統計の無いテーブルが先頭。権限は要りません。",
        _TABLE_STATS,
    ),
    PdbTemplate(
        "pdb.invalid_objects",
        "10. 無効なオブジェクト",
        "接続ユーザーの VALID でないオブジェクト(ビュー・プロシージャ・トリガーなど)。権限は要りません。",
        _INVALID_OBJECTS,
    ),
    PdbTemplate(
        "pdb.unusable_indexes",
        "11. 使用できない索引",
        "接続ユーザーの UNUSABLE の索引と索引パーティション。権限は要りません。",
        _UNUSABLE_INDEXES,
    ),
    PdbTemplate(
        "pdb.disabled_constraints",
        "12. 無効または未検証の制約",
        "接続ユーザーの DISABLED または NOT VALIDATED の制約。権限は要りません。",
        _DISABLED_CONSTRAINTS,
    ),
    PdbTemplate(
        "pdb.object_counts",
        "13. オブジェクトの種類ごとの数",
        "接続ユーザーのオブジェクトの種類・状態ごとの数。権限は要りません。",
        _OBJECT_COUNTS,
    ),
    PdbTemplate(
        "pdb.sessions",
        "14. セッションの一覧",
        "利用者のセッション(状態、OS ユーザー、端末、プログラム、実行中の SQL_ID、最後の呼び出しからの秒数)。"
        + NEEDS_DBA,
        _SESSIONS,
    ),
    PdbTemplate(
        "pdb.blocking_sessions",
        "15. ロック待ちのセッション",
        "他のセッションを待っているセッションと、待たせているセッション。待ち時間の長い順。" + NEEDS_DBA,
        _BLOCKING,
    ),
    PdbTemplate(
        "pdb.long_ops",
        "16. 長時間実行中の処理",
        "V$SESSION_LONGOPS のうち終わっていない処理(全表走査・バックアップ・統計の収集など)の進み具合と残り秒数。"
        + NEEDS_DBA,
        _LONG_OPS,
    ),
    PdbTemplate(
        "pdb.user_quotas",
        "17. ユーザーごとの表領域の使用量と割り当て",
        "全ユーザーの表領域ごとの使用量と割り当て上限。使用量の多い順。" + NEEDS_DBA,
        _USER_QUOTAS,
    ),
)
