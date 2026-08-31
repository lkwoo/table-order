import { useEffect, useRef, useState } from 'react'
import { SSEClient } from '../shared/sse'

export type ConnectionState = 'connecting' | 'online' | 'offline'

// A2: subscribe to /api/sse/dashboard. On any event or (re)connect, invoke
// onChange to refetch the full dashboard snapshot (last-write-wins, Q9).
// onNewOrder is called separately so the UI can highlight new tables for 3s.
export function useDashboardStream(
  jwt: string | null,
  onChange: () => void,
  onNewOrder?: (data: any) => void,
) {
  const [state, setState] = useState<ConnectionState>('connecting')
  const changeRef = useRef(onChange)
  const newRef = useRef(onNewOrder)
  changeRef.current = onChange
  newRef.current = onNewOrder

  useEffect(() => {
    if (!jwt) return
    const client = new SSEClient('/api/sse/dashboard', jwt, {
      events: ['order.created', 'order.status_changed', 'order.deleted', 'session.ended'],
      onOpen: () => {
        setState('online')
        changeRef.current()
      },
      onReconnect: () => {
        setState('online')
        changeRef.current() // snapshot resync
      },
      onEvent: (type, data) => {
        if (type === 'order.created') newRef.current?.(data)
        changeRef.current()
      },
      onError: () => setState('offline'),
    })
    client.connect()
    return () => client.disconnect()
  }, [jwt])

  return state
}
