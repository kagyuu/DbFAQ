import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ApiError } from './client'
import { getHealth, getPdbInfo, getSchema, getTableDetail, getTableRows, listSavedQueries, refreshSchema } from './client'
import type { ErView, Health, PdbInfo, RefreshResult, RowsPage, SavedQueryList, SavedQueryTarget, TableDetail } from './types'

export const useSchema = () => useQuery<ErView, ApiError>({ queryKey: ['schema'], queryFn: getSchema })

export function useRefreshSchema() {
  const qc = useQueryClient()
  return useMutation<RefreshResult, ApiError>({
    mutationFn: refreshSchema,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schema'] }),
  })
}

export const useHealth = () =>
  useQuery<Health, ApiError>({ queryKey: ['health'], queryFn: getHealth, refetchInterval: 60_000 })

export const useTableDetail = (owner: string, table: string) =>
  useQuery<TableDetail, ApiError>({
    queryKey: ['detail', owner, table],
    queryFn: () => getTableDetail(owner, table),
  })

export const useTableRows = (owner: string, table: string, offset: number, limit: number, enabled: boolean) =>
  useQuery<RowsPage, ApiError>({
    queryKey: ['rows', owner, table, offset, limit],
    queryFn: () => getTableRows(owner, table, offset, limit),
    enabled,
    placeholderData: keepPreviousData,
  })

/** 保存済み Query の一覧のキー(保存・変更・削除の成功時に無効化する。P002 §2.2.8。※CR-005により追加) */
export const savedQueriesKey = (t: SavedQueryTarget) =>
  t.scope === 'table' ? ['saved-queries', 'table', t.owner, t.table] : ['saved-queries', 'pdb']

export const useSavedQueries = (target: SavedQueryTarget) =>
  useQuery<SavedQueryList, ApiError>({ queryKey: savedQueriesKey(target), queryFn: () => listSavedQueries(target) })

export const usePdbInfo = (enabled: boolean) =>
  useQuery<PdbInfo, ApiError>({ queryKey: ['pdb'], queryFn: getPdbInfo, enabled })
