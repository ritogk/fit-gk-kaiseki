import { ref } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  const active = ref<Set<string>>(new Set())
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null

  function connect() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}/api/live/ws`)

    ws.onopen = () => { error.value = null }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'ready') {
          connected.value = true
        } else if (msg.type === 'state') {
          active.value = new Set(msg.active as string[])
        } else if (msg.type === 'error') {
          error.value = msg.message
          connected.value = false
        }
      } catch { /* ignore */ }
    }

    ws.onclose = () => {
      connected.value = false
      active.value = new Set()
      ws = null
    }

    ws.onerror = () => {
      error.value = 'WebSocket connection failed'
    }
  }

  function disconnect() {
    ws?.close()
  }

  function noteOn(id: string) {
    ws?.send(JSON.stringify({ type: 'note_on', id }))
  }

  function noteOff(id: string) {
    ws?.send(JSON.stringify({ type: 'note_off', id }))
  }

  function allOff() {
    ws?.send(JSON.stringify({ type: 'all_off' }))
  }

  return { connected, active, error, connect, disconnect, noteOn, noteOff, allOff }
}
