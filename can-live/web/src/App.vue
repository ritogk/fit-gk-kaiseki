<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useLiveCan } from '@/composables/useLiveCan'
import { EngineSynth } from '@/audio/synth'
import LiveView from '@/views/LiveView.vue'

const { connected, alive, current, onFrame, connect, disconnect } = useLiveCan()

const synth = new EngineSynth()
const audioOn = ref(false)
let unsub: (() => void) | null = null

async function toggleAudio() {
  if (!audioOn.value) {
    await synth.start() // ユーザー操作から開始（autoplay 制限回避）
    audioOn.value = true
  } else {
    synth.stop()
    audioOn.value = false
  }
}

onMounted(() => {
  connect()
  // 低遅延: WS 受信ごとに直接発音（描画ループを介さない）
  unsub = onFrame((s) => synth.update(s.rpm, s.steeringAngle))
})

onUnmounted(() => {
  unsub?.()
  synth.stop()
  disconnect()
})
</script>

<template>
  <div id="app">
    <header>
      <h1>CAN Live</h1>
      <span class="subtitle">Honda Fit GK5 — RPM × Steering 演奏</span>
      <button class="play" :class="{ on: audioOn }" @click="toggleAudio">
        {{ audioOn ? '■ 停止' : '▶ 演奏開始' }}
      </button>
      <span class="conn" :class="{ on: connected && alive }">
        <i class="dot"></i>{{ !connected ? 'WS未接続' : alive ? 'can0 受信中' : 'can0 無音' }}
      </span>
    </header>

    <LiveView :current="current" :connected="connected" :alive="alive" :audio-on="audioOn" />

    <p class="hint">
      ▶ 演奏開始 を押してから、<b>空ぶかしで音程</b>・<b>ハンドルで左右パンと音色</b>。
    </p>
  </div>
</template>

<style>
:root {
  --bg: #0f1117;
  --bg-card: #1a1d27;
  --border: #2a2d3a;
  --text: #e1e4ed;
  --text-muted: #8b8fa3;
  --accent: #4f8ff7;
  --accent-dim: #2a4a8a;
  --green: #4caf50;
  --orange: #ff9800;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 14px;
}

#app {
  min-height: 100vh;
  padding: 16px 24px;
}

header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

header h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--accent);
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.play {
  background: var(--bg-card);
  border: 1px solid var(--accent);
  border-radius: 6px;
  color: var(--accent);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 6px 16px;
  cursor: pointer;
  transition: all 0.15s;
}

.play:hover {
  background: var(--accent-dim);
}

.play.on {
  background: #4caf50;
  border-color: #4caf50;
  color: #0f1117;
}

.conn {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.conn .dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #f44336;
}

.conn.on .dot {
  background: var(--green);
}

.hint {
  text-align: center;
  margin-top: 20px;
  font-size: 12px;
  color: var(--text-muted);
}

.hint b {
  color: var(--text);
}
</style>
