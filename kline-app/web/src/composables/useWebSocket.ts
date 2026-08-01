import { ref } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  const active = ref<Set<string>>(new Set())
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null
  let pingTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let intentionalClose = false

  function connect() {
    intentionalClose = false
    cleanup()
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}/api/live/ws`)

    ws.onopen = () => {
      error.value = null
      pingTimer = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 5000)
    }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'ready') {
          connected.value = true
          error.value = null
        } else if (msg.type === 'pong') {
          // pong に載った K-Line ワーカーの生存状態で緑ランプを連動させる。
          // WS は生きていてもワーカーが死んでいれば false になり、表示が実態と一致する。
          if (msg.alive) {
            connected.value = true
            error.value = null
          } else {
            connected.value = false
            error.value = 'K-Line未接続'
          }
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
      stopPing()
      if (!intentionalClose) {
        reconnectTimer = setTimeout(connect, 1000)
      }
      ws = null
    }

    ws.onerror = () => {
      error.value = 'WebSocket connection failed'
    }
  }

  function stopPing() {
    if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
  }

  function cleanup() {
    stopPing()
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  }

  function disconnect() {
    intentionalClose = true
    cleanup()
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'exit' }))
    }
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

  function loopOn(id: string) {
    ws?.send(JSON.stringify({ type: 'loop_on', id }))
  }

  function loopOff(id: string) {
    ws?.send(JSON.stringify({ type: 'loop_off', id }))
  }

  function setBpm(bpm: number) {
    ws?.send(JSON.stringify({ type: 'bpm', bpm }))
  }

  return { connected, active, error, connect, disconnect, noteOn, noteOff, allOff, loopOn, loopOff, setBpm }
}
