import { useEffect, useRef, useState } from 'react'
import { SSEClient } from '../shared/sse'

export type ConnectionState = 'connecting' | 'online' | 'offline'

// Subscribes to /api/sse/orders for the current session and invokes onChange
// whenever an order.status_changed / order.deleted event arrives, plus on
// (re)connect so the caller can refetch a full snapshot.
export function useOrderStream(sessionToken: string | null, onChange: () => void) {
  const [state, setState] = useState<ConnectionState>('connecting')
  const cbRef = useRef(onChange)
  cbRef.current = onChange

  useEffect(() => {
    if (!sessionToken) return
    const client = new SSEClient('/api/sse/orders', sessionToken, {
      events: ['order.status_changed', 'order.deleted'],
      onOpen: () => {
        setState('online')
        cbRef.current()
      },
      onReconnect: () => {
        setState('online')
        cbRef.current() // snapshot resync
      },
      onEvent: () => cbRef.current(),
      onError: () => setState('offline'),
    })
    client.connect()
    return () => client.disconnect()
  }, [sessionToken])

  return state
}
