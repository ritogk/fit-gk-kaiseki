<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'
import { useApi } from '../composables/useApi'
import {
  ALL_PADS,
  getPad,
  padColorClass,
} from '../pads'

const emit = defineEmits<{ exit: []; live: [] }>()

const { connected, error, connect, disconnect, noteOn, noteOff, allOff } = useWebSocket()
const { apiCall } = useApi()

// --- Types & persistence ---
// pattern: コマンドID → ステップ毎の on/off
type Pattern = Record<string, boolean[]>

const STORAGE_KEY = 'gk-seq'
const BANKS_KEY = 'gk-seq-banks'

const DEFAULT_TRACKS = ['hazard', 'high_beam', 'low_beam', 'turn_left', 'turn_right', 'horn_short', 'chirp']

const STEP_OPTIONS = [8, 16, 32]
const SUBDIV_OPTIONS = [
  { label: '1/4', value: 1 },
  { label: '1/8', value: 2 },
  { label: '1/16', value: 4 },
]

function clonePattern(p: Pattern): Pattern {
  const out: Pattern = {}
  for (const id of Object.keys(p)) out[id] = [...p[id]]
  return out
}

function emptyPattern(ids: string[], steps: number): Pattern {
  const out: Pattern = {}
  for (const id of ids) out[id] = Array(steps).fill(false)
  return out
}

function resizePattern(p: Pattern, n: number) {
  for (const id of Object.keys(p)) {
    const a = p[id]
    while (a.length < n) a.push(false)
    if (a.length > n) a.length = n
  }
}

// --- State ---

const bpm = ref(120)
const steps = ref(16)
const stepsPerBeat = ref(4)
const cursor = ref(-1)
const playing = ref(false)

const trackIds = ref<string[]>([...DEFAULT_TRACKS])
const disabled = ref<string[]>([])
const editing = ref<Pattern>(emptyPattern(DEFAULT_TRACKS, 16))
const queue = ref<Pattern[]>([])
const banks = ref<Pattern[]>([])

// 実際に hold 送信中(noteOn 済み・未 noteOff)のID集合。差分送信の基準。
const activeHold = new Set<string>()

// --- Load saved state ---

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const d = JSON.parse(raw)
      if (typeof d.bpm === 'number') bpm.value = d.bpm
      if (typeof d.steps === 'number') steps.value = d.steps
      if (typeof d.stepsPerBeat === 'number') stepsPerBeat.value = d.stepsPerBeat
      if (Array.isArray(d.trackIds) && d.trackIds.length) trackIds.value = d.trackIds
      if (Array.isArray(d.disabled)) disabled.value = d.disabled
      if (d.editing && typeof d.editing === 'object') {
        editing.value = d.editing as Pattern
        resizePattern(editing.value, steps.value)
        for (const id of trackIds.value) if (!editing.value[id]) editing.value[id] = Array(steps.value).fill(false)
      }
    }
  } catch { /* ignore */ }
  try {
    const raw = localStorage.getItem(BANKS_KEY)
    if (raw) {
      const arr = JSON.parse(raw)
      if (Array.isArray(arr)) banks.value = arr as Pattern[]
    }
  } catch { /* ignore */ }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    bpm: bpm.value, steps: steps.value, stepsPerBeat: stepsPerBeat.value,
    trackIds: trackIds.value, disabled: disabled.value, editing: editing.value,
  }))
}

function saveBanks() {
  localStorage.setItem(BANKS_KEY, JSON.stringify(banks.value))
}

// --- Grid editing ---

function isOn(id: string, i: number): boolean {
  return !!editing.value[id]?.[i]
}

function toggleCell(id: string, i: number) {
  if (!editing.value[id]) editing.value[id] = Array(steps.value).fill(false)
  editing.value[id][i] = !editing.value[id][i]
  saveState()
}

// セルの描画クラス。連続する ON は内側の角を落とし隙間を詰めて、
// 横一本の「長押しバー」として連結表示する。
function cellClass(id: string, idx: number): string[] {
  const on = isOn(id, idx)
  const out: string[] = [
    on ? padColorClass(getPad(id), true) : 'bg-slate-800 hover:bg-slate-700',
    cursor.value === idx ? 'ring-2 ring-white z-10' : '',
    idx % stepsPerBeat.value === 0 ? 'border-l border-slate-600' : '',
  ]
  if (!on) { out.push('rounded-sm'); return out }
  const prevOn = idx > 0 && isOn(id, idx - 1)
  const nextOn = idx < steps.value - 1 && isOn(id, idx + 1)
  if (prevOn && nextOn) out.push('rounded-none')
  else if (prevOn) out.push('rounded-l-none rounded-r-sm')
  else if (nextOn) out.push('rounded-r-none rounded-l-sm')
  else out.push('rounded-sm')
  if (nextOn) out.push('-mr-0.5') // gap(0.5) を相殺して次セルと連結
  return out
}

function clearEditing() {
  editing.value = emptyPattern(trackIds.value, steps.value)
  saveState()
}

function setSteps(n: number) {
  resizePattern(editing.value, n)
  for (const p of queue.value) resizePattern(p, n)
  steps.value = n
  if (cursor.value >= n) cursor.value = n - 1
  saveState()
}

function setSubdiv(v: number) {
  stepsPerBeat.value = v
  saveState()
  if (playing.value) armClock()
}

function onBpmChange(e: Event) {
  bpm.value = Number((e.target as HTMLInputElement).value)
  saveState()
  if (playing.value) armClock()
}

// --- Tracks ---

function hasTrack(id: string): boolean {
  return trackIds.value.includes(id)
}

function isDisabled(id: string): boolean {
  return disabled.value.includes(id)
}

function toggleDisabled(id: string) {
  if (isDisabled(id)) {
    disabled.value = disabled.value.filter((t) => t !== id)
  } else {
    disabled.value = [...disabled.value, id]
    // 鳴っている最中なら即停止(再生中ループでは fireStep の差分送信が処理するが念のため)
    if (activeHold.has(id)) { noteOff(id); activeHold.delete(id) }
  }
  saveState()
}

function toggleTrack(id: string) {
  if (hasTrack(id)) {
    trackIds.value = trackIds.value.filter((t) => t !== id)
  } else {
    trackIds.value = [...trackIds.value, id]
    if (!editing.value[id]) editing.value[id] = Array(steps.value).fill(false)
  }
  saveState()
}

// --- Queue ---

function enqueue() {
  queue.value = [...queue.value, clonePattern(editing.value)]
}

function clearQueue() {
  queue.value = []
  if (playing.value) stop()
}

function advanceQueue() {
  // バー頭: キューに次があれば現在(先頭)を捨てて次へ
  if (queue.value.length > 1) queue.value = queue.value.slice(1)
}

// --- Banks ---

function saveBank() {
  banks.value = [...banks.value, clonePattern(editing.value)]
  saveBanks()
}

function loadBank(b: Pattern) {
  editing.value = clonePattern(b)
  trackIds.value = Object.keys(b)
  const first = Object.values(b)[0]
  if (first) steps.value = first.length
  saveState()
}

function deleteBank(i: number) {
  banks.value = banks.value.filter((_, idx) => idx !== i)
  saveBanks()
}

// --- Clock ---

let clockTimer: ReturnType<typeof setInterval> | null = null

function stepIntervalMs(): number {
  return 60000 / bpm.value / stepsPerBeat.value
}

function armClock() {
  if (clockTimer) clearInterval(clockTimer)
  clockTimer = setInterval(tick, stepIntervalMs())
}

function tick() {
  cursor.value = (cursor.value + 1) % steps.value
  if (cursor.value === 0) {
    if (queue.value.length > 1) {
      advanceQueue() // 次が積まれていれば次パターンへ
    } else if (queue.value.length === 1) {
      // ループ中: 再生中の編集を次バーから反映し、以降ずっとその新パターンで鳴らす
      queue.value = [clonePattern(editing.value)]
    }
  }
  fireStep()
}

function fireStep() {
  const cur = queue.value[0]
  if (!cur) { clearHeld(); return }
  const c = cursor.value
  const desired = new Set<string>()
  for (const id of Object.keys(cur)) {
    if (isDisabled(id)) continue
    if (!cur[id][c]) continue
    // 同一トラックで連続する ON は「1回の長押し」として扱う。
    const startOfRun = c === 0 || !cur[id][c - 1]
    if (getPad(id).mode === 'pulse') {
      // pulse はサーバ側で保持不可。連続区間は走り出しで1発のみ(毎ステップ連打しない)。
      if (startOfRun) noteOn(id)
    } else {
      // hold は連続区間を noteOn〜noteOff の長押しとして維持(差分送信に委ねる)。
      desired.add(id)
    }
  }
  // hold系は差分のみ送信
  for (const id of [...activeHold]) {
    if (!desired.has(id)) { noteOff(id); activeHold.delete(id) }
  }
  for (const id of desired) {
    if (!activeHold.has(id)) { noteOn(id); activeHold.add(id) }
  }
}

function clearHeld() {
  for (const id of [...activeHold]) { noteOff(id); activeHold.delete(id) }
}

function play() {
  if (playing.value) return
  if (queue.value.length === 0) enqueue() // 何も無ければ編集中パターンを投入
  playing.value = true
  cursor.value = -1
  tick()       // 先頭ステップを即発火
  armClock()
}

function stop() {
  playing.value = false
  if (clockTimer) { clearInterval(clockTimer); clockTimer = null }
  cursor.value = -1
  allOff()
  activeHold.clear()
}

function togglePlay() {
  playing.value ? stop() : play()
}

// --- Controls ---

function handleAllOff() {
  allOff()
  activeHold.clear()
}

async function emergencyStop() {
  stop()
  await apiCall('POST', '/api/control/stop_all')
}

function handleExit() {
  stop()
  disconnect()
  emit('exit')
}

function switchToLive() {
  stop()
  disconnect()
  emit('live')
}

// --- Fullscreen ---

const isFullscreen = ref(false)
function toggleFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen()
  else document.exitFullscreen()
}
function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// --- Keyboard / visibility ---

function onKeyDown(e: KeyboardEvent) {
  if (e.repeat) return
  const key = e.key.toLowerCase()
  if (key === 'escape') { handleExit(); return }
  if (key === ' ') { e.preventDefault(); togglePlay(); return }
}

function onVisibilityChange() {
  // タブ非アクティブでタイマーが間引かれクロックが乱れるため停止
  if (document.hidden && playing.value) stop()
}

function onBlur() {
  if (playing.value) stop()
}

// --- Lifecycle ---

onMounted(() => {
  loadState()
  connect()
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('blur', onBlur)
  document.addEventListener('visibilitychange', onVisibilityChange)
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  stop()
  disconnect()
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('blur', onBlur)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})
</script>

<template>
  <div class="fixed inset-0 bg-slate-900 text-white flex flex-col select-none z-50" style="touch-action: none">

    <!-- Header -->
    <div class="flex items-center gap-2 px-3 py-2 bg-slate-800 shrink-0">
      <div class="flex items-center gap-2 shrink-0">
        <h1 class="text-base sm:text-lg font-bold">SEQ</h1>
        <span :class="connected ? 'bg-green-500' : 'bg-red-500'" class="inline-block w-2.5 h-2.5 rounded-full" />
        <span v-if="!connected && !error" class="text-yellow-400 text-xs">接続中…</span>
        <span v-if="error" class="text-red-400 text-xs">K-Line未接続</span>
      </div>
      <div class="hdr-scroll">
        <div class="flex items-center justify-end gap-1.5 w-max ml-auto">
          <button class="hdr-btn bg-amber-600 hover:bg-amber-500 font-bold" @click="switchToLive">◀ LIVE</button>
          <button class="hdr-btn bg-slate-700 hover:bg-slate-600" @click="toggleFullscreen">
            {{ isFullscreen ? '⊙' : '⛶' }}
          </button>
          <button class="hdr-btn bg-amber-600 hover:bg-amber-500" @click="handleAllOff">ALL OFF</button>
          <button class="hdr-btn bg-red-600 hover:bg-red-500 font-bold" @click="emergencyStop">全停止</button>
          <button class="hdr-btn bg-slate-600 hover:bg-slate-500" @click="handleExit">EXIT</button>
        </div>
      </div>
    </div>

    <div class="flex-1 flex flex-col gap-2 p-3 overflow-hidden">

      <!-- Controls (1行集約) -->
      <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5 shrink-0">
        <button class="px-4 py-1.5 rounded font-bold text-sm"
                :class="playing ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500'"
                @click="togglePlay">
          {{ playing ? '⏹ STOP' : '▶ PLAY' }}
        </button>

        <button class="px-3 py-1 rounded text-xs bg-emerald-600 hover:bg-emerald-500 font-bold" @click="enqueue">
          ＋キュー
        </button>
        <button class="px-2 py-1 rounded text-xs bg-slate-700 hover:bg-slate-600" @click="clearQueue">
          Qクリア
        </button>
        <button class="px-2 py-1 rounded text-xs bg-slate-700 hover:bg-slate-600" @click="clearEditing">
          消去
        </button>
        <button class="px-2 py-1 rounded text-xs bg-indigo-600 hover:bg-indigo-500" @click="saveBank">
          💾
        </button>

        <!-- Queue chips -->
        <div class="flex items-center gap-1">
          <span class="text-xs text-slate-500">Q:</span>
          <span v-if="queue.length === 0" class="text-xs text-slate-600">空</span>
          <span v-for="(_, i) in queue" :key="i"
                :class="i === 0 && playing ? 'bg-green-500 text-slate-900' : 'bg-slate-700 text-slate-300'"
                class="px-2 py-0.5 rounded text-xs font-mono">
            {{ i === 0 && playing ? '▶' : '' }}{{ i + 1 }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs text-slate-400 font-bold">BPM</span>
          <input type="range" min="40" max="240" step="1" :value="bpm" @input="onBpmChange" class="w-32" />
          <span class="text-xs text-slate-400 font-mono w-8">{{ bpm }}</span>
        </div>

        <div class="flex items-center gap-1">
          <span class="text-xs text-slate-400 font-bold mr-1">STEP</span>
          <button v-for="n in STEP_OPTIONS" :key="n"
                  :class="steps === n ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-300'"
                  class="px-2 py-0.5 rounded text-xs font-bold" @click="setSteps(n)">{{ n }}</button>
        </div>

        <div class="flex items-center gap-1">
          <button v-for="o in SUBDIV_OPTIONS" :key="o.value"
                  :class="stepsPerBeat === o.value ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-300'"
                  class="px-2 py-0.5 rounded text-xs font-bold" @click="setSubdiv(o.value)">{{ o.label }}</button>
        </div>
      </div>

      <!-- Banks -->
      <div v-if="banks.length" class="flex flex-wrap items-center gap-1.5 shrink-0">
        <span class="text-xs text-slate-500">バンク:</span>
        <div v-for="(b, i) in banks" :key="i"
             class="flex items-center gap-1 bg-slate-800 rounded px-1.5 py-0.5">
          <button class="text-xs text-slate-300 hover:text-white" @click="loadBank(b)">#{{ i + 1 }}</button>
          <button class="text-xs text-slate-500 hover:text-red-400" @click="deleteBank(i)">×</button>
        </div>
      </div>

      <!-- Grid (空き領域いっぱいに行を広げる) -->
      <div class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-1">
        <div v-for="id in trackIds" :key="id" class="flex items-stretch gap-1 flex-1 min-h-[2rem]">
          <!-- Row label (クリックでトラック無効/有効) -->
          <button :class="[padColorClass(getPad(id), false), isDisabled(id) ? 'opacity-40 line-through' : '']"
                  class="w-16 shrink-0 rounded text-center text-xs font-bold flex items-center justify-center text-slate-200"
                  @click="toggleDisabled(id)">
            {{ getPad(id).label }}
          </button>
          <!-- Step cells -->
          <div class="flex-1 grid gap-0.5" :class="isDisabled(id) ? 'opacity-30' : ''"
               :style="{ gridTemplateColumns: `repeat(${steps}, 1fr)` }">
            <button v-for="i in steps" :key="i"
                    :class="cellClass(id, i - 1)"
                    class="h-full min-h-[1.75rem] transition-colors"
                    @click="toggleCell(id, i - 1)" />
          </div>
        </div>
      </div>

      <!-- Track picker -->
      <div class="flex flex-wrap items-center gap-1 shrink-0 pt-1 border-t border-slate-800">
        <span class="text-xs text-slate-500 mr-1">トラック:</span>
        <button v-for="pad in ALL_PADS" :key="pad.id"
                :class="hasTrack(pad.id) ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-400'"
                class="px-2 py-0.5 rounded text-xs font-bold" @click="toggleTrack(pad.id)">
          {{ pad.label }}
        </button>
      </div>
    </div>

    <!-- Hint -->
    <div class="text-center text-xs text-slate-500 pb-1.5 shrink-0">
      SPACE = 再生/停止 | 行ラベルをタップでトラック無効/有効 | 連続ONは長押し扱い | 再生中の編集は次ループから反映 | ＋でキューに積むとバー頭で次へ切替 | ESC = 終了
    </div>
  </div>
</template>
