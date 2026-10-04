-- テスト用データベースの前提②のデータ投入の準備(docs/P006-test-plan.md §3.1)
-- 実行: 管理ユーザー(SYS・SYSTEM など)で、HR のある PDB(例: FREEPDB1)に接続して 1 回だけ実行する
-- 画像ファイル ai_model_512_01.png は DB サーバ(コンテナ oracle-db-free)の /opt/oracle/oradata に置く(リポジトリのルートで: docker cp docs/P006-test-plan/ai_model_512_01.png oracle-db-free:/opt/oracle/oradata/ai_model_512_01.png。docs/P006-test-plan.md §3.1.1)
CREATE OR REPLACE DIRECTORY photo_dir AS '/opt/oracle/oradata';
GRANT READ ON DIRECTORY photo_dir TO hr;
