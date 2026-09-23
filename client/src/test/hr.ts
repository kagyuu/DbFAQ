// テスト用の HR 相当の ER 図データ(7 表、外部キー 10 本。うち自己参照 1 本)
import type { ErColumn, ErTable, ErView } from '../api/types'

const col = (name: string, id: number, type = 'NUMBER(6)', extra: Partial<ErColumn> = {}): ErColumn => ({
  name,
  column_id: id,
  data_type_display: type,
  nullable: true,
  is_pk: false,
  is_fk: false,
  ...extra,
})
const pk = { is_pk: true, nullable: false }
const fk = { is_fk: true }

const table = (name: string, columns: ErColumn[], comment: string | null = null): ErTable => ({
  owner: 'HR',
  name,
  comment,
  num_rows: null,
  columns,
})

export const HR_VIEW: ErView = {
  loaded: true,
  snapshot: {
    owner: 'HR',
    fetched_at: '2026-09-23T01:15:02Z',
    oracle_version: '23.26.3.0.0',
    table_count: 7,
    relation_count: 10,
  },
  tables: [
    table('COUNTRIES', [col('COUNTRY_ID', 1, 'CHAR(2)', pk), col('COUNTRY_NAME', 2, 'VARCHAR2(60)'), col('REGION_ID', 3, 'NUMBER', fk)]),
    table('DEPARTMENTS', [col('DEPARTMENT_ID', 1, 'NUMBER(4)', pk), col('DEPARTMENT_NAME', 2, 'VARCHAR2(30)'), col('MANAGER_ID', 3, 'NUMBER(6)', fk), col('LOCATION_ID', 4, 'NUMBER(4)', fk)]),
    table('EMPLOYEES', [col('EMPLOYEE_ID', 1, 'NUMBER(6)', pk), col('LAST_NAME', 2, 'VARCHAR2(25)', { nullable: false }), col('JOB_ID', 3, 'VARCHAR2(10)', fk), col('MANAGER_ID', 4, 'NUMBER(6)', fk), col('DEPARTMENT_ID', 5, 'NUMBER(4)', fk)], 'employees table'),
    table('JOBS', [col('JOB_ID', 1, 'VARCHAR2(10)', pk), col('JOB_TITLE', 2, 'VARCHAR2(35)')]),
    table('JOB_HISTORY', [col('EMPLOYEE_ID', 1, 'NUMBER(6)', { ...pk, ...fk }), col('START_DATE', 2, 'DATE', pk), col('JOB_ID', 3, 'VARCHAR2(10)', fk), col('DEPARTMENT_ID', 4, 'NUMBER(4)', fk)]),
    table('LOCATIONS', [col('LOCATION_ID', 1, 'NUMBER(4)', pk), col('CITY', 2, 'VARCHAR2(30)'), col('COUNTRY_ID', 3, 'CHAR(2)', fk)]),
    table('REGIONS', [col('REGION_ID', 1, 'NUMBER', pk), col('REGION_NAME', 2, 'VARCHAR2(25)')]),
  ],
  relations: [
    ['COUNTR_REG_FK', 'COUNTRIES', 'REGIONS'],
    ['DEPT_LOC_FK', 'DEPARTMENTS', 'LOCATIONS'],
    ['DEPT_MGR_FK', 'DEPARTMENTS', 'EMPLOYEES'],
    ['EMP_DEPT_FK', 'EMPLOYEES', 'DEPARTMENTS'],
    ['EMP_JOB_FK', 'EMPLOYEES', 'JOBS'],
    ['EMP_MANAGER_FK', 'EMPLOYEES', 'EMPLOYEES'],
    ['JHIST_DEPT_FK', 'JOB_HISTORY', 'DEPARTMENTS'],
    ['JHIST_EMP_FK', 'JOB_HISTORY', 'EMPLOYEES'],
    ['JHIST_JOB_FK', 'JOB_HISTORY', 'JOBS'],
    ['LOC_C_ID_FK', 'LOCATIONS', 'COUNTRIES'],
  ].map(([name, from, to]) => ({
    name,
    from_owner: 'HR',
    from_table: from,
    from_columns: ['X'],
    to_owner: 'HR',
    to_table: to,
    to_columns: ['Y'],
  })),
}
