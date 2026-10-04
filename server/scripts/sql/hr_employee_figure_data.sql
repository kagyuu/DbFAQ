-- テスト用データベースの前提②の表 EMPLOYEE_FIGURE へのデータ投入(docs/P006-test-plan.md §3.1)。依頼者が使ったスクリプト
-- 前提: hr_employee_figure.sql(表)と hr_photo_dir.sql(DIRECTORY と READ 権限、画像ファイルの配置)を実行済み
-- 実行: hr ユーザーで実行する。1 回の実行で 107 行(EMPLOYEE_ID 100〜206)。実行した回数だけ行が増える(2026-10-04 の開発用 Oracle は 2 回分の 214 行)
-- 行のデータはテストの前提にしない(テストは表の構造だけを確かめる)
-- 1枚の「ai_model_512_01.png」を全員分（100〜206）に使い回して一括登録するスクリプト
DECLARE
    v_bfile BFILE;
    v_blob  BLOB;
BEGIN
    FOR emp_id IN 100..206 LOOP
        -- 空のBLOBで行を初期化
        INSERT INTO EMPLOYEE_FIGURE (EMPLOYEE_ID, FIGURE)
        VALUES (emp_id, EMPTY_BLOB())
        RETURNING FIGURE INTO v_blob;
        
        -- 全員共通のサンプルファイルを指定
        v_bfile := BFILENAME('PHOTO_DIR', 'ai_model_512_01.png');
        
        DBMS_LOB.FILEOPEN(v_bfile, DBMS_LOB.FILE_READONLY);
        DBMS_LOB.LOADFROMFILE(v_blob, v_bfile, DBMS_LOB.GETLENGTH(v_bfile));
        DBMS_LOB.FILECLOSE(v_bfile);
    END LOOP;
    COMMIT;
END;
/
