import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ApiError } from './client'
import { getHealth, getSchema, getTableDetail, getTableRows, refreshSchema } from './client'
import type { ErView, Health, RefreshResult, RowsPage, TableDetail } from './types'

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
