import type { DetailColumn, TableDetail } from '../api/types'

const col = (id: number, name: string, display: string, extra: Partial<DetailColumn> = {}): DetailColumn => ({
  column_id: id,
  name,
  data_type: display.replace(/\(.*$/, ''),
  data_type_display: display,
  data_length: null,
  data_precision: null,
  data_scale: null,
  nullable: true,
  data_default: null,
  comment: null,
  pk_position: null,
  is_fk: false,
  ...extra,
})

export const EMPLOYEES_DETAIL: TableDetail = {
  snapshot: { owner: 'HR', fetched_at: '2026-09-23T01:15:02Z' },
  table: { owner: 'HR', name: 'EMPLOYEES', comment: 'employees table', num_rows: 107, last_analyzed: '2026-09-22T08:12:32Z', iot: false },
  columns: [
    col(1, 'EMPLOYEE_ID', 'NUMBER(6)', { nullable: false, pk_position: 1, comment: 'Primary key' }),
    col(2, 'LAST_NAME', 'VARCHAR2(25)', { nullable: false }),
    col(3, 'SALARY', 'NUMBER(8,2)', { data_default: '0' }),
    col(4, 'MANAGER_ID', 'NUMBER(6)', { is_fk: true }),
    col(5, 'DEPARTMENT_ID', 'NUMBER(4)', { is_fk: true }),
    col(6, 'DEPT_CODE', 'VARCHAR2(10)', { is_fk: true }),
  ],
  primary_key: { name: 'EMP_EMP_ID_PK', columns: ['EMPLOYEE_ID'] },
  unique_keys: [{ name: 'EMP_EMAIL_UK', columns: ['EMAIL'] }],
  foreign_keys: [
    { name: 'EMP_DEPT_FK', columns: ['DEPARTMENT_ID'], ref_owner: 'HR', ref_table: 'DEPARTMENTS', ref_columns: ['DEPARTMENT_ID'], delete_rule: 'NO ACTION', ref_in_snapshot: true },
    { name: 'EMP_EXT_FK', columns: ['DEPT_CODE'], ref_owner: 'OTHER', ref_table: 'DEPTS', ref_columns: ['CODE'], delete_rule: 'CASCADE', ref_in_snapshot: false },
    { name: 'EMP_MANAGER_FK', columns: ['MANAGER_ID'], ref_owner: 'HR', ref_table: 'EMPLOYEES', ref_columns: ['EMPLOYEE_ID'], delete_rule: 'NO ACTION', ref_in_snapshot: true },
  ],
  referenced_by: [
    { name: 'DEPT_MGR_FK', from_owner: 'HR', from_table: 'DEPARTMENTS', from_columns: ['MANAGER_ID'], columns: ['EMPLOYEE_ID'] },
  ],
  indexes: [
    { name: 'EMP_EMP_ID_PK', unique: true, index_type: 'NORMAL', columns: [{ name: 'EMPLOYEE_ID', descending: false }] },
    { name: 'EMP_SAL_IX', unique: false, index_type: 'NORMAL', columns: [{ name: 'SALARY', descending: true }] },
  ],
}
