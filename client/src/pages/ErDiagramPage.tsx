import { Button, Center, Group, Loader, Stack, Text } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  useReactFlow,
  type Edge,
  type NodeChange,
} from '@xyflow/react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRefreshSchema, useSchema } from '../api/hooks'
import type { ErTable } from '../api/types'
import AppShell from '../components/AppShell'
import SelfLoopEdge from '../er/SelfLoopEdge'
import TableNode from '../er/TableNode'
import TableSearch from '../er/TableSearch'
import { buildGraph, nodeId, type TableNode as TableNodeType } from '../er/buildGraph'
import { layoutGraph } from '../er/layout'

const nodeTypes = { table: TableNode }
const edgeTypes = { selfLoop: SelfLoopEdge }
const HIGHLIGHT_MS = 2000

export const tablePath = (owner: string, name: string) => `/tables/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`

function Diagram() {
  const navigate = useNavigate()
  const { data, isPending, error } = useSchema()
  const refresh = useRefreshSchema()
  const { setCenter } = useReactFlow()
  const [nodes, setNodes] = useState<TableNodeType[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [laying, setLaying] = useState(false)
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!data?.loaded) return
    let cancelled = false
    const graph = buildGraph(data)
    setLaying(true)
    layoutGraph(graph.nodes, graph.edges).then((laid) => {
      if (cancelled) return
      setNodes(laid)
      setEdges(graph.edges)
      setLaying(false)
    })
    return () => {
      cancelled = true
    }
  }, [data])

  useEffect(() => () => {
    if (highlightTimer.current) clearTimeout(highlightTimer.current)
  }, [])

  const onNodesChange = useCallback(
    (changes: NodeChange<TableNodeType>[]) => setNodes((ns) => applyNodeChanges(changes, ns)),
    [],
  )

  const doRefresh = () =>
    refresh.mutate(undefined, {
      onSuccess: (r) =>
        notifications.show({
          color: 'green',
          message: `スキーマ情報を更新しました(テーブル ${r.snapshot.table_count} / 関連 ${r.snapshot.relation_count})`,
        }),
      onError: (e) => notifications.show({ color: 'red', title: '再読み込みに失敗しました', message: e.displayMessage, autoClose: 10000 }),
    })

  const focusTable = (t: ErTable) => {
    const id = nodeId(t.owner, t.name)
    const n = nodes.find((x) => x.id === id)
    if (!n) return
    setCenter(n.position.x + (n.width ?? 0) / 2, n.position.y + (n.height ?? 0) / 2, { zoom: 1, duration: 300 })
    setNodes((ns) => ns.map((x) => ({ ...x, data: { ...x.data, highlighted: x.id === id } })))
    if (highlightTimer.current) clearTimeout(highlightTimer.current)
    highlightTimer.current = setTimeout(
      () => setNodes((ns) => ns.map((x) => (x.data.highlighted ? { ...x, data: { ...x.data, highlighted: false } } : x))),
      HIGHLIGHT_MS,
    )
  }

  const refreshButton = (label: string) => (
    <Button onClick={doRefresh} loading={refresh.isPending} disabled={refresh.isPending}>
      {label}
    </Button>
  )

  let body
  if (isPending) {
    body = <Center h="100%"><Loader aria-label="読み込み中" /></Center>
  } else if (error) {
    body = <Center h="100%"><Text c="red">{error.displayMessage}</Text></Center>
  } else if (!data.loaded) {
    body = (
      <Center h="100%">
        <Stack align="center">
          <Text>スキーマ情報がありません</Text>
          {refreshButton('Oracle から読み込む')}
        </Stack>
      </Center>
    )
  } else if (data.tables.length === 0) {
    body = (
      <Center h="100%">
        <Stack align="center">
          <Text>テーブルがありません(スキーマ: {data.snapshot?.owner})</Text>
          {refreshButton('Oracle から再読み込み')}
        </Stack>
      </Center>
    )
  } else if (laying && nodes.length === 0) {
    body = <Center h="100%"><Loader aria-label="レイアウト計算中" /></Center>
  } else {
    body = (
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onNodeClick={(_, n) => navigate(tablePath(n.data.owner, n.data.name))}
        nodeDragThreshold={5}
        nodesConnectable={false}
        minZoom={0.1}
        maxZoom={2}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Controls position="bottom-left" showInteractive={false} />
        <MiniMap position="bottom-right" pannable zoomable />
        <Background />
      </ReactFlow>
    )
  }

  return (
    <>
      <Group px="md" py="xs" gap="md" style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
        <TableSearch
          tables={data?.tables ?? []}
          onFocusTable={focusTable}
          onOpenTable={(t) => navigate(tablePath(t.owner, t.name))}
        />
        {data?.loaded && refreshButton('Oracle から再読み込み')}
        {data?.loaded && (
          <Text size="sm" c="dimmed">
            テーブル {data.tables.length} / 関連 {data.relations.length}
          </Text>
        )}
      </Group>
      <div style={{ flex: 1, minHeight: 0 }}>{body}</div>
    </>
  )
}

export default function ErDiagramPage() {
  return (
    <AppShell>
      <ReactFlowProvider>
        <Diagram />
      </ReactFlowProvider>
    </AppShell>
  )
}
