// SSEClientBase: EventSource wrapper.
// - Token is passed as a `?token=` query param (EventSource cannot set headers).
// - Auto-reconnect is native to EventSource; on each (re)open after the first,
//   we invoke onReconnect so the caller can refetch a full snapshot
//   (last-write-wins resync per functional design Q9).

export interface SSEHandlers {
  /** Named events to listen for (e.g. order.created, order.status_changed). */
  events: string[]
  onEvent: (type: string, data: any) => void
  /** Called when the connection opens for the first time. */
  onOpen?: () => void
  /** Called on every re-open after the first (network recovered). */
  onReconnect?: () => void
  /** Called when the connection errors / drops. */
  onError?: () => void
}

export class SSEClient {
  private es: EventSource | null = null
  private opened = false

  constructor(
    private path: string,
    private token: string,
    private handlers: SSEHandlers,
  ) {}

  connect() {
    this.disconnect()
    const url = `${this.path}?token=${encodeURIComponent(this.token)}`
    const es = new EventSource(url)
    this.es = es

    es.onopen = () => {
      if (this.opened) {
        this.handlers.onReconnect?.()
      } else {
        this.opened = true
        this.handlers.onOpen?.()
      }
    }

    es.onerror = () => {
      // EventSource will auto-reconnect; surface the drop for offline UI.
      this.handlers.onError?.()
    }

    for (const evt of this.handlers.events) {
      es.addEventListener(evt, (e: MessageEvent) => {
        let data: any = undefined
        try {
          data = e.data ? JSON.parse(e.data) : undefined
        } catch {
          data = e.data
        }
        this.handlers.onEvent(evt, data)
      })
    }
  }

  disconnect() {
    if (this.es) {
      this.es.close()
      this.es = null
    }
  }
}
