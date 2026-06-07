import { reactive, ref } from 'vue'
import {
  ZERO_SIGNALS,
  type FrameMessage,
  type LiveSignals,
  type RawFrame,
  type RawGauge,
} from '@/types'

/**
 * ライブ can0 信号を WebSocket で購読する。
 *
 * 既存リポジトリの useWebSocket.ts（接続/自動再接続パターン）を踏襲。
 * 低遅延のため、フレーム受信時に
 *   (a) 描画用の reactive `current` を更新（Vue が再描画）
 *   (b) onFrame(cb) で登録された購読者へ生信号を即時コールバック
 *       …将来の Web Audio はこちらに繋ぎ、Vue の描画ループを介さず最短で発音する。
 * の両系統を回す。
 */
export function useLiveCan() {
  const connected = ref(false) // WS が開いているか
  const alive = ref(false) // can0 にフレームが流れているか
  const current = reactive<LiveSignals>({ ...ZERO_SIGNALS })
  const raw = ref<RawGauge[]>([])
  const frames = ref<RawFrame[]>([])

  const frameSubs = new Set<(s: LiveSignals) => void>()

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let intentionalClose = false

  function connect() {
    intentionalClose = false
    cleanup()
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}/api/canlive/ws`)

    ws.onopen = () => {
      connected.value = true
    }

    ws.onmessage = (e) => {
      let msg: FrameMessage
      try {
        msg = JSON.parse(e.data)
      } catch {
        return
      }
      if (msg.type !== 'frame') return
      alive.value = msg.alive
      raw.value = msg.raw
      frames.value = msg.frames
      Object.assign(current, msg.signals)
      // 音用の即時購読者へ（描画を待たない）
      for (const cb of frameSubs) cb(msg.signals)
    }

    ws.onclose = () => {
      connected.value = false
      alive.value = false
      ws = null
      if (!intentionalClose) {
        reconnectTimer = setTimeout(connect, 1000)
      }
    }

    ws.onerror = () => {
      // onclose が続けて呼ばれるので再接続はそちらで。
    }
  }

  function cleanup() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function disconnect() {
    intentionalClose = true
    cleanup()
    ws?.close()
  }

  /** 生信号の即時購読を登録。戻り値を呼ぶと解除。 */
  function onFrame(cb: (s: LiveSignals) => void) {
    frameSubs.add(cb)
    return () => frameSubs.delete(cb)
  }

  return { connected, alive, current, raw, frames, onFrame, connect, disconnect }
}
