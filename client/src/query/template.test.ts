import { describe, expect, it } from 'vitest'
import type { ErView, TableDetail } from '../api/types'
import { EMPLOYEES_DETAIL } from '../test/detail'
import { HR_VIEW } from '../test/hr'
import { buildSelectTemplate, candidateLabel, listJoinCandidates, quoteIdent } from './template'

const pick = (detail: TableDetail, schema: ErView, ...keys: string[]) =>
  listJoinCandidates(detail, schema).filter((c) => keys.includes(c.key))

describe('quoteIdent', () => {
  it.each([
    ['EMPLOYEES', 'EMPLOYEES'],
    ['A1_$#', 'A1_$#'],
    ['my table', '"my table"'],
    ['lower', '"lower"'],
    ['社員', '"社員"'],
    ['DATE', '"DATE"'],
    ['LEVEL', '"LEVEL"'],
    ['1ABC', '"1ABC"'],
    ['A"B', '"A""B"'],
  ])('%s → %s', (name, expected) => {
    expect(quoteIdent(name)).toBe(expected)
  })
})

describe('listJoinCandidates', () => {
  it('→ を制約名順、続いて ← を制約名順に並べ、相手の列が分からないものは使えない', () => {
    const list = listJoinCandidates(EMPLOYEES_DETAIL, HR_VIEW)
    expect(list.map((c) => c.key)).toEqual([
      'parent:EMP_DEPT_FK',
      'parent:EMP_EXT_FK',
      'parent:EMP_MANAGER_FK',
      'child:DEPT_MGR_FK',
    ])
    expect(list.map((c) => c.available)).toEqual([true, false, true, true])
    expect(list[0].columns.map((c) => c.name)).toEqual(['DEPARTMENT_ID', 'DEPARTMENT_NAME', 'MANAGER_ID', 'LOCATION_ID'])
  })

  it('表示文言', () => {
    const list = listJoinCandidates(EMPLOYEES_DETAIL, HR_VIEW)
    expect(candidateLabel(list[0], 'HR')).toBe('→ DEPARTMENTS  EMP_DEPT_FK (DEPARTMENT_ID)')
    expect(candidateLabel(list[1], 'HR')).toBe('→ OTHER.DEPTS  EMP_EXT_FK (DEPT_CODE)')
    expect(candidateLabel(list[3], 'HR')).toBe('← DEPARTMENTS  DEPT_MGR_FK (MANAGER_ID → EMPLOYEE_ID)')
  })

  it('スキーマ情報が無い・参照先の列が null なら使えない', () => {
    expect(listJoinCandidates(EMPLOYEES_DETAIL, undefined).every((c) => !c.available)).toBe(true)
    const detail: TableDetail = {
      ...EMPLOYEES_DETAIL,
      foreign_keys: [{ ...EMPLOYEES_DETAIL.foreign_keys[0], ref_columns: [null] }],
      referenced_by: [],
    }
    expect(listJoinCandidates(detail, HR_VIEW)[0].available).toBe(false)
  })
})

describe('buildSelectTemplate', () => {
  it('外部キーを選ばないとき', () => {
    expect(buildSelectTemplate(EMPLOYEES_DETAIL, [])).toBe(
      [
        'SELECT',
        '  t0.EMPLOYEE_ID,',
        '  t0.LAST_NAME,',
        '  t0.SALARY,',
        '  t0.MANAGER_ID,',
        '  t0.DEPARTMENT_ID,',
        '  t0.DEPT_CODE',
        'FROM HR.EMPLOYEES t0',
        'ORDER BY t0.EMPLOYEE_ID',
      ].join('\n'),
    )
  })

  it('→ の JOIN(P002 §2.2.7 の例と同じ形。同じ名前の列に別名)', () => {
    const sql = buildSelectTemplate(EMPLOYEES_DETAIL, pick(EMPLOYEES_DETAIL, HR_VIEW, 'parent:EMP_DEPT_FK'))
    expect(sql).toBe(
      [
        'SELECT',
        '  t0.EMPLOYEE_ID,',
        '  t0.LAST_NAME,',
        '  t0.SALARY,',
        '  t0.MANAGER_ID,',
        '  t0.DEPARTMENT_ID,',
        '  t0.DEPT_CODE,',
        '  t1.DEPARTMENT_ID AS T1_DEPARTMENT_ID,',
        '  t1.DEPARTMENT_NAME,',
        '  t1.MANAGER_ID AS T1_MANAGER_ID,',
        '  t1.LOCATION_ID',
        'FROM HR.EMPLOYEES t0',
        '  LEFT JOIN HR.DEPARTMENTS t1 ON t1.DEPARTMENT_ID = t0.DEPARTMENT_ID',
        'ORDER BY t0.EMPLOYEE_ID',
      ].join('\n'),
    )
  })

  it('← の JOIN と自己参照、複数選択では t1, t2, … の順', () => {
    const sel = pick(EMPLOYEES_DETAIL, HR_VIEW, 'parent:EMP_MANAGER_FK', 'child:DEPT_MGR_FK')
    const sql = buildSelectTemplate(EMPLOYEES_DETAIL, sel)
    expect(sql).toContain('  LEFT JOIN HR.EMPLOYEES t1 ON t1.EMPLOYEE_ID = t0.MANAGER_ID\n')
    expect(sql).toContain('  LEFT JOIN HR.DEPARTMENTS t2 ON t2.MANAGER_ID = t0.EMPLOYEE_ID\n')
    expect(sql).toContain('  t1.EMPLOYEE_ID AS T1_EMPLOYEE_ID,')
    expect(sql).toContain('  t2.DEPARTMENT_NAME,')
    expect(sql).toContain('  t2.MANAGER_ID AS T2_MANAGER_ID,')
  })

  it('使えない候補は無視する', () => {
    const sql = buildSelectTemplate(EMPLOYEES_DETAIL, pick(EMPLOYEES_DETAIL, HR_VIEW, 'parent:EMP_EXT_FK'))
    expect(sql).not.toContain('JOIN')
  })

  it('複合外部キー・引用符が要る識別子・主キーなし', () => {
    const detail: TableDetail = {
      ...EMPLOYEES_DETAIL,
      table: { ...EMPLOYEES_DETAIL.table, owner: 'app', name: 'Order Lines' },
      columns: [
        { ...EMPLOYEES_DETAIL.columns[0], column_id: 1, name: 'order_no' },
        { ...EMPLOYEES_DETAIL.columns[0], column_id: 2, name: 'LINE_NO' },
        { ...EMPLOYEES_DETAIL.columns[0], column_id: 3, name: 'DATE' },
      ],
      primary_key: null,
      foreign_keys: [
        {
          name: 'OL_FK', columns: ['order_no', 'LINE_NO'], ref_owner: 'app', ref_table: 'Orders',
          ref_columns: ['ORDER_NO', 'LINE'], delete_rule: 'NO ACTION', ref_in_snapshot: true,
        },
      ],
      referenced_by: [],
    }
    const schema: ErView = {
      ...HR_VIEW,
      tables: [{ owner: 'app', name: 'Orders', comment: null, num_rows: null, columns: [
        { name: 'LINE', column_id: 2, data_type_display: 'NUMBER', nullable: false, is_pk: true, is_fk: false },
        { name: 'ORDER_NO', column_id: 1, data_type_display: 'NUMBER', nullable: false, is_pk: true, is_fk: false },
      ] }],
    }
    const sql = buildSelectTemplate(detail, listJoinCandidates(detail, schema))
    expect(sql).toBe(
      [
        'SELECT',
        '  t0."order_no",',
        '  t0.LINE_NO,',
        '  t0."DATE",',
        '  t1.ORDER_NO,',
        '  t1.LINE',
        'FROM "app"."Order Lines" t0',
        '  LEFT JOIN "app"."Orders" t1 ON t1.ORDER_NO = t0."order_no" AND t1.LINE = t0.LINE_NO',
      ].join('\n'),
    )
  })

  it('別名が 128 文字を超えるときは付けない', () => {
    const long = 'C'.repeat(127)
    const detail: TableDetail = {
      ...EMPLOYEES_DETAIL,
      columns: [{ ...EMPLOYEES_DETAIL.columns[0], name: long }],
      foreign_keys: [{ ...EMPLOYEES_DETAIL.foreign_keys[0], columns: [long], ref_columns: [long] }],
      referenced_by: [],
    }
    const schema: ErView = {
      ...HR_VIEW,
      tables: [{ ...HR_VIEW.tables.find((t) => t.name === 'DEPARTMENTS')!, columns: [
        { name: long, column_id: 1, data_type_display: 'NUMBER', nullable: false, is_pk: true, is_fk: false },
      ] }],
    }
    const sql = buildSelectTemplate(detail, listJoinCandidates(detail, schema))
    expect(sql).toContain(`  t1.${long}\n`)
  })
})
