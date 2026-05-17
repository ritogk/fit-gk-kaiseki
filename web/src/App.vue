<script setup lang="ts">
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import SceneEditor from './components/SceneEditor.vue'
import { useApi } from './composables/useApi'
import type { CommandMap } from './types'

const { logs, apiCall } = useApi()

// --- State ---

const health = reactive({ ok: false })
const commands = ref<CommandMap | null>(null)
const durations = reactive<Record<string, number>>({})
const fun = reactive({ bpm: 120, measures: 8 })
const seq = reactive({ positions: '1,2,3', cycles: 80, speed: 1.4, cmd_delay: 0.020 })
const custom = reactive({ lid: '1D', iocp: '0F', on_s: 0.1, off_s: 0.1, cycles: 10 })
const status = reactive({ running: false, kind: null as string | null })
const busy = ref(false)
const hornArmed = ref(false)
let hornArmTimer: ReturnType<typeof setTimeout> | null = null

// --- Helpers ---

function hex(n: number) {
  return Number(n).toString(16).toUpperCase().padStart(2, '0')
}

// --- API actions ---

async function loadCommands() {
  const data = await apiCall('GET', '/api/control/list')
  if (data) {
    commands.value = data as CommandMap
    Object.entries(data as CommandMap).forEach(([name, m]) => {
      durations[name] = m.default_duration_s ?? 5.0
    })
  }
}

async function fire(name: string) {
  busy.value = true
  const meta = commands.value?.[name]
  const params = meta && meta.iocp === 15 ? { duration_s: durations[name] } : null
  await apiCall('POST', `/api/control/${name}`, params)
  busy.value = false
}

function onHornClick() {
  if (hornArmed.value) {
    hornArmed.value = false
    if (hornArmTimer) { clearTimeout(hornArmTimer); hornArmTimer = null }
    fire('horn')
  } else {
    hornArmed.value = true
    if (hornArmTimer) clearTimeout(hornArmTimer)
    hornArmTimer = setTimeout(() => { hornArmed.value = false; hornArmTimer = null }, 3000)
  }
}

async function startSequence() {
  busy.value = true
  const data = await apiCall('POST', '/api/fun/sequence', {
    positions: seq.positions,
    cycles: seq.cycles,
    speed: seq.speed,
    cmd_delay: seq.cmd_delay,
  })
  if (data) status.running = true
  busy.value = false
}

async function startFun(kind: string) {
  busy.value = true
  const data = await apiCall('POST', `/api/fun/${kind}`, { bpm: fun.bpm, measures: fun.measures })
  if (data) status.running = true
  busy.value = false
}

async function startCustom() {
  busy.value = true
  const lid = parseInt(custom.lid, 16)
  const iocp = parseInt(custom.iocp, 16)
  if (isNaN(lid) || isNaN(iocp)) {
    busy.value = false
    return
  }
  const data = await apiCall('POST', '/api/fun/pattern', {
    lid, iocp, on_s: custom.on_s, off_s: custom.off_s, cycles: custom.cycles,
  })
  if (data) status.running = true
  busy.value = false
}

async function stopFun() {
  busy.value = true
  await apiCall('POST', '/api/fun/stop')
  status.running = false
  busy.value = false
}

async function checkHealth() {
  try {
    const r = await fetch('/api/health')
    health.ok = r.ok
  } catch { health.ok = false }
}

async function pollStatus() {
  try {
    const r = await fetch('/api/fun/status')
    if (r.ok) {
      const d = await r.json()
      status.running = !!d.running
      status.kind = d.kind
    }
  } catch { /* ignore */ }
}

// --- Lifecycle ---

let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  checkHealth()
  loadCommands()
  timer = setInterval(() => { checkHealth(); pollStatus() }, 1000)
})

onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="bg-slate-100 min-h-screen">
    <div class="max-w-5xl mx-auto p-4 space-y-6">

      <!-- Header -->
      <header class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-slate-800">Fit GK Kaiseki</h1>
        <div class="flex items-center gap-3 text-sm">
          <span :class="health.ok ? 'bg-green-500' : 'bg-red-500'"
                class="inline-block w-3 h-3 rounded-full" />
          <span>{{ health.ok ? 'API 接続OK' : 'API 切断' }}</span>
          <span v-if="status.running" class="text-amber-600 font-semibold">
            ▶ {{ status.kind }} 演奏中
          </span>
        </div>
      </header>

      <!-- Sequence / Scene Editor -->
      <section class="card">
        <h2 class="text-lg font-bold mb-3">流し系 ループ (1=HZ / 2=HB / 3=LB / 4=PS / 5=FG)</h2>

        <SceneEditor v-model:positions="seq.positions" />

        <div class="flex flex-wrap items-end gap-3">
          <label class="text-sm">
            cycles
            <input v-model.number="seq.cycles" type="number" min="1" max="100" class="input" />
          </label>
          <label class="text-sm">
            cmd_delay (秒)
            <input v-model.number="seq.cmd_delay" type="number"
                   min="0.010" max="0.050" step="0.001" class="input" />
          </label>
          <label class="text-sm flex items-center gap-2">
            speed
            <input v-model.number="seq.speed" type="range" min="0.3" max="2.5" step="0.1" />
            <span class="font-mono w-12 text-right">{{ seq.speed.toFixed(1) }}x</span>
          </label>
          <button class="btn btn-primary" :disabled="busy" @click="startSequence">▶ 実行</button>
          <button class="btn btn-danger text-sm" :disabled="!status.running" @click="stopFun">
            ⏹ 停止
          </button>
        </div>
      </section>

      <!-- Log -->
      <section class="card">
        <h2 class="text-lg font-bold mb-3">ログ (直近 {{ logs.length }} 件)</h2>
        <pre class="font-mono text-xs bg-slate-900 text-slate-100 rounded p-3 max-h-96 overflow-auto">
<span v-for="(l, i) in logs" :key="i" :class="l.error ? 'text-red-300' : ''">[{{ l.time }}] {{ l.method }} {{ l.url }} → {{ l.text }}
</span>
        </pre>
      </section>

      <!-- Individual commands -->
      <details class="card">
        <summary class="text-lg font-bold cursor-pointer">個別操作 (/api/control)</summary>
        <div v-if="!commands" class="text-slate-500 text-sm mt-3">読み込み中…</div>
        <div v-else class="space-y-1 mt-3">
          <div v-for="(meta, name) in commands" :key="name"
               :class="name === 'horn' ? 'border border-red-300 bg-red-50' : 'border border-slate-200 bg-slate-50'"
               class="rounded px-3 py-1.5 flex items-center gap-3 text-sm">
            <span class="font-semibold w-24 shrink-0">{{ name }}</span>
            <span class="text-xs text-slate-400 w-28 shrink-0">
              0x{{ hex(meta.lid) }} / 0x{{ hex(meta.iocp) }}
            </span>
            <input v-if="meta.iocp === 15" v-model.number="durations[name as string]"
                   type="number" min="0.1" step="0.1" class="input" style="width:4.5rem" />
            <button v-if="name !== 'horn'"
                    class="btn btn-primary text-xs py-1 px-2"
                    :disabled="busy" @click="fire(name as string)">実行</button>
            <button v-else
                    :class="hornArmed
                      ? 'btn btn-danger text-xs py-1 px-2 animate-pulse'
                      : 'btn text-xs py-1 px-2 bg-white text-red-600 border border-red-500 hover:bg-red-100'"
                    :disabled="busy" @click="onHornClick">
              <span v-if="!hornArmed">🔒 ホーン</span>
              <span v-else>🔥 確認</span>
            </button>
          </div>
        </div>
      </details>

      <!-- Fun patterns -->
      <section class="card">
        <h2 class="text-lg font-bold mb-3">パリピ演奏 (/api/fun)</h2>
        <div class="flex flex-wrap items-center gap-3 mb-3">
          <label class="text-sm">
            BPM <input v-model.number="fun.bpm" type="number" min="40" max="240" class="input" />
          </label>
          <label class="text-sm">
            小節数 <input v-model.number="fun.measures" type="number" min="1" max="64" class="input" />
          </label>
          <button class="btn btn-danger text-sm" :disabled="!status.running" @click="stopFun">
            ⏹ 停止
          </button>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button class="btn btn-primary" :disabled="busy" @click="startFun('3way')">
            3way (HB+LB+HZ)
          </button>
          <button class="btn btn-primary" :disabled="busy" @click="startFun('beat')">
            beat (HB+PS)
          </button>
          <button class="btn btn-primary" :disabled="busy" @click="startFun('stereo')">
            stereo (L+R+HB)
          </button>
          <button class="btn btn-primary" :disabled="busy" @click="startFun('polyrhythm')">
            polyrhythm 4:3
          </button>
        </div>
      </section>

      <!-- Custom pattern -->
      <section class="card">
        <h2 class="text-lg font-bold mb-3">カスタムパターン (/api/fun/pattern)</h2>
        <div class="flex flex-wrap items-end gap-3">
          <label class="text-sm">
            LID (hex) <input v-model="custom.lid" class="input" placeholder="1D" />
          </label>
          <label class="text-sm">
            IOCP (hex) <input v-model="custom.iocp" class="input" placeholder="0F" />
          </label>
          <label class="text-sm">
            on (秒) <input v-model.number="custom.on_s" type="number" step="0.05" class="input" />
          </label>
          <label class="text-sm">
            off (秒) <input v-model.number="custom.off_s" type="number" step="0.05" class="input" />
          </label>
          <label class="text-sm">
            cycles <input v-model.number="custom.cycles" type="number" min="1" class="input" />
          </label>
          <button class="btn btn-primary" :disabled="busy" @click="startCustom">スタート</button>
        </div>
      </section>

      <footer class="text-xs text-slate-500 text-center pt-4">
        Honda Fit GK5 RS MT — research project, own vehicle only. No vehicle is harmed in production of beats.
      </footer>
    </div>
  </div>
</template>
