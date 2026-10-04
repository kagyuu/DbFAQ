-- テスト用データベースの前提(docs/P006-test-plan.md §3.1・§3.2)
--   ① Oracle 配布の HR サンプルスキーマ(https://github.com/oracle/db-sample-schemas/releases/latest の human_resources)
--   ② ①には LOB 列が無いため、次の表を追加する(LOB の表示・CSV・チェックサムを確かめるため)
-- 実行: HR をインストールした後に、hr ユーザーで 1 回だけ実行する(例: sqlplus hr@//localhost:1521/FREEPDB1 @hr_employee_figure.sql)
-- 行のデータはテストの前提にしない(0 行でもよい)。テストが確かめるのは表・列・制約・インデックスの構造だけ
CREATE TABLE EMPLOYEE_FIGURE (
    FIGURE_ID   NUMBER(6,0) GENERATED ALWAYS AS IDENTITY,
    EMPLOYEE_ID NUMBER(6,0) NOT NULL,
    FIGURE      BLOB,
    CONSTRAINT PK_EMPLOYEE_FIGURE PRIMARY KEY (FIGURE_ID),
    CONSTRAINT FK_EMPLOYEE_FIGURE_EMP FOREIGN KEY (EMPLOYEE_ID)
        REFERENCES EMPLOYEES (EMPLOYEE_ID)
);
