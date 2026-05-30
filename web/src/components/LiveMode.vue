<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'
import { useApi } from '../composables/useApi'
import CarFace from './CarFace.vue'

const emit = defineEmits<{ exit: [] }>()

const { connected, active, error, connect, disconnect, noteOn, noteOff, allOff, loopOn, loopOff, setBpm } = useWebSocket()
const { apiCall } = useApi()

// --- Pad definitions ---

interface Pad {
  id: string
  label: string
  key: string
  color: string
  mode: 'hold' | 'pulse'
}

const LIGHT_PADS: Pad[] = [
  { id: 'low_beam',   label: 'LB',  key: 'q', color: 'amber', mode: 'hold' },
  { id: 'high_beam',  label: 'HB',  key: 'w', color: 'amber', mode: 'hold' },
  { id: 'hazard',     label: 'HZ',  key: 'e', color: 'amber', mode: 'hold' },
  { id: 'position',   label: 'PS',  key: 'a', color: 'amber', mode: 'hold' },
  { id: 'fog',        label: 'FG',  key: 's', color: 'amber', mode: 'hold' },
  { id: 'turn_left',  label: 'TL',  key: 'r', color: 'amber', mode: 'hold' },
  { id: 'turn_right', label: 'TR',  key: 'd', color: 'amber', mode: 'hold' },
]

const ACTION_PADS: Pad[] = [
  { id: 'lock',    label: 'LOCK',   key: 'z', color: 'purple', mode: 'pulse' },
  { id: 'unlock',  label: 'UNLOCK', key: 'x', color: 'purple', mode: 'pulse' },
  { id: 'chirp',   label: 'CHIRP',  key: 'c', color: 'purple', mode: 'pulse' },
]

const UTIL_PADS: Pad[] = [
  { id: 'room_lamp',       label: 'ROOM',   key: 't', color: 'amber',  mode: 'hold' },
  { id: 'cargo_light',     label: 'CARGO',  key: 'y', color: 'amber',  mode: 'hold' },
  { id: 'chirp_hold',      label: 'CHIRP+', key: 'u', color: 'purple', mode: 'hold' },
  { id: 'wiper_front_low', label: 'WI-FL',  key: 'g', color: 'blue',   mode: 'hold' },
  { id: 'wiper_front_hi',  label: 'WI-FH',  key: 'h', color: 'blue',   mode: 'hold' },
  { id: 'wiper_rear',      label: 'WI-R',   key: 'j', color: 'blue',   mode: 'hold' },
  { id: 'washer_front',    label: 'WA-F',   key: 'k', color: 'cyan',   mode: 'hold' },
  { id: 'washer_rear',     label: 'WA-R',   key: 'l', color: 'cyan',   mode: 'hold' },
]

const HORN_SHORT_PAD: Pad = { id: 'horn_short', label: 'H.S', key: 'b', color: 'yellow', mode: 'pulse' }
const HORN_PAD: Pad = { id: 'horn', label: 'HORN', key: ' ', color: 'orange', mode: 'hold' }

// --- Launchpad-mirrored grid layout (8 columns × 4 rows) ---
// Mirrors launchpad/keymap-live.conf: 機能行 + 主3段, 中央=ウィンカー
const ALL_PADS: Pad[] = [...LIGHT_PADS, ...ACTION_PADS, ...UTIL_PADS, HORN_SHORT_PAD, HORN_PAD]
const padById = new Map(ALL_PADS.map((p) => [p.id, p]))

const STOP_CELL = 'STOP'
// 4段構成: 1段目=荷室灯+STOP / 2段目=ライト類(中央) / 3段目=ドア/チャープ / 4段目=ROOM+フロントワイパー/ウォッシャーをセットで固める / ホーン系は右下に縦並び
const GRID_LAYOUT: (string | null)[][] = [
  [null, null, null, 'cargo_light', null, null, null, STOP_CELL],
  [null, 'low_beam', 'high_beam', 'hazard', 'position', 'fog', 'turn_left', 'turn_right'],
  [null, null, 'lock', 'unlock', 'chirp', 'chirp_hold', 'horn_short', null],
  [null, 'wiper_rear', 'washer_rear', 'wiper_front_hi', 'wiper_front_low', 'washer_front', 'room_lamp', 'horn'],
]

function getPad(id: string): Pad {
  return padById.get(id)!
}

// --- Interaction ---

const pressedKeys = ref<Set<string>>(new Set())
const pressedPads = ref<Set<string>>(new Set())
const pulsedPads = ref<Set<string>>(new Set())
const pointerToPad = new Map<number, Pad>()

function padDown(pad: Pad, e?: PointerEvent) {
  if (e) pointerToPad.set(e.pointerId, pad)
  if (pad.mode === 'pulse') {
    noteOn(pad.id)
    pulsedPads.value.add(pad.id)
    setTimeout(() => pulsedPads.value.delete(pad.id), 10)
  } else {
    if (!pressedPads.value.has(pad.id)) {
      pressedPads.value.add(pad.id)
      noteOn(pad.id)
    }
  }
}

function padUp(pad: Pad) {
  if (pressedPads.value.has(pad.id)) {
    pressedPads.value.delete(pad.id)
    if (pad.mode === 'hold') {
      noteOff(pad.id)
    }
  }
}

function releaseAllKeys() {
  for (const id of pressedPads.value) {
    noteOff(id)
  }
  pressedKeys.value.clear()
  pressedPads.value.clear()
}

function onBlur() {
  releaseAllKeys()
}

function onVisibilityChange() {
  if (document.hidden) releaseAllKeys()
}

function onPointerRelease(e: PointerEvent) {
  const pad = pointerToPad.get(e.pointerId)
  if (pad) {
    pointerToPad.delete(e.pointerId)
    padUp(pad)
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.repeat) return
  const key = e.key.toLowerCase()
  if (key === 'escape') { handleExit(); return }
  if (key === 'v') { e.preventDefault(); handleAllOff(); return }
  if (pressedKeys.value.has(key)) return
  pressedKeys.value.add(key)

  const pad = findPadByKey(key)
  if (pad) { e.preventDefault(); padDown(pad) }
}

function onKeyUp(e: KeyboardEvent) {
  const key = e.key.toLowerCase()
  pressedKeys.value.delete(key)

  const pad = findPadByKey(key)
  if (pad) { e.preventDefault(); padUp(pad) }
}

function findPadByKey(key: string): Pad | undefined {
  const k = key === ' ' ? ' ' : key
  return [...LIGHT_PADS, ...ACTION_PADS, ...UTIL_PADS, HORN_SHORT_PAD, HORN_PAD].find((p) => p.key === k)
}

function handleAllOff() {
  allOff()
  pressedPads.value.clear()
  loopPads.value.clear()
  syncLoopTimer()
}

async function emergencyStop() {
  handleAllOff()
  await apiCall('POST', '/api/control/stop_all')
}

function handleExit() {
  handleAllOff()
  if (loopTimer) { clearInterval(loopTimer); loopTimer = null }
  disconnect()
  emit('exit')
}

function isActive(id: string): boolean {
  return pressedPads.value.has(id) || pulsedPads.value.has(id) || isLoopActive(id)
}

function padColorClass(pad: Pad): string {
  const on = isActive(pad.id)
  const map: Record<string, string> = {
    amber:  on ? 'bg-amber-400 shadow-amber-400/50'  : 'bg-slate-700 hover:bg-slate-600',
    yellow: on ? 'bg-yellow-300 shadow-yellow-300/50' : 'bg-yellow-900 hover:bg-yellow-800',
    white:  on ? 'bg-white shadow-white/50'           : 'bg-slate-700 hover:bg-slate-600',
    orange: on ? 'bg-orange-400 shadow-orange-400/50' : 'bg-orange-900 hover:bg-orange-800',
    cyan:   on ? 'bg-cyan-400 shadow-cyan-400/50'     : 'bg-slate-700 hover:bg-slate-600',
    green:  on ? 'bg-green-400 shadow-green-400/50'   : 'bg-slate-700 hover:bg-slate-600',
    blue:   on ? 'bg-blue-400 shadow-blue-400/50'     : 'bg-slate-700 hover:bg-slate-600',
    purple: on ? 'bg-purple-400 shadow-purple-400/50' : 'bg-slate-700 hover:bg-slate-600',
    red:    on ? 'bg-red-500 shadow-red-500/50'       : 'bg-red-900 hover:bg-red-800',
  }
  return map[pad.color] ?? ''
}

// --- Rhythm loop ---

const loopPads = ref<Set<string>>(new Set())
const bpm = ref(120)
const loopPhase = ref(false)
let loopTimer: ReturnType<typeof setInterval> | null = null

function toggleLoop(pad: Pad) {
  if (loopPads.value.has(pad.id)) {
    loopPads.value.delete(pad.id)
    loopOff(pad.id)
  } else {
    loopPads.value.add(pad.id)
    loopOn(pad.id)
  }
  syncLoopTimer()
}

function onBpmChange(e: Event) {
  const val = Number((e.target as HTMLInputElement).value)
  bpm.value = val
  setBpm(val)
  syncLoopTimer()
}

function syncLoopTimer() {
  if (loopTimer) { clearInterval(loopTimer); loopTimer = null }
  if (loopPads.value.size > 0) {
    const interval = 60000 / bpm.value / 2
    loopPhase.value = true
    loopTimer = setInterval(() => { loopPhase.value = !loopPhase.value }, interval)
  } else {
    loopPhase.value = false
  }
}

function isLoopActive(id: string): boolean {
  return loopPads.value.has(id) && loopPhase.value
}

// --- Monitor ---

const showMonitor = ref(true)

const CMD_TO_POS: Record<string, number> = {
  hazard: 1, high_beam: 2, low_beam: 3, position: 4, fog: 5, turn_left: 6, turn_right: 7,
}

const monitorLights = computed(() => {
  const ids = new Set([...pressedPads.value])
  for (const id of loopPads.value) {
    if (loopPhase.value) ids.add(id)
  }
  const lids: number[] = []
  for (const id of ids) {
    const pos = CMD_TO_POS[id]
    if (pos && !lids.includes(pos)) lids.push(pos)
  }
  return lids
})

// --- Fullscreen ---

const isFullscreen = ref(false)

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// --- Lifecycle ---

onMounted(() => {
  connect()
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('blur', onBlur)
  document.addEventListener('visibilitychange', onVisibilityChange)
  document.addEventListener('pointerup', onPointerRelease)
  document.addEventListener('pointercancel', onPointerRelease)
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  if (loopTimer) clearInterval(loopTimer)
  disconnect()
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  window.removeEventListener('blur', onBlur)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  document.removeEventListener('pointerup', onPointerRelease)
  document.removeEventListener('pointercancel', onPointerRelease)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})
</script>

<template>
  <div class="fixed inset-0 bg-slate-900 text-white flex flex-col select-none z-50"
       style="touch-action: none">

    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-slate-800 shrink-0">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-bold">LIVE MODE</h1>
        <span :class="connected ? 'bg-green-500' : 'bg-red-500'"
              class="inline-block w-2.5 h-2.5 rounded-full" />
        <span v-if="!connected && !error" class="text-yellow-400 text-xs">接続中…</span>
        <span v-if="error" class="text-red-400 text-xs">K-Lineデバイス未接続</span>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-3 py-1 rounded text-xs bg-slate-700 hover:bg-slate-600"
                @click="showMonitor = !showMonitor">
          {{ showMonitor ? 'モニター非表示' : 'モニター表示' }}
        </button>
        <button class="px-3 py-1 rounded text-xs bg-slate-700 hover:bg-slate-600"
                @click="toggleFullscreen">
          {{ isFullscreen ? '縮小' : '全画面' }}
        </button>
        <button class="px-3 py-1 rounded text-xs bg-amber-600 hover:bg-amber-500"
                @click="handleAllOff">
          ALL OFF
        </button>
        <button class="px-3 py-1 rounded text-xs bg-slate-500 hover:bg-slate-400"
                @click="emergencyStop">
          全停止
        </button>
        <button class="px-3 py-1 rounded text-xs bg-slate-600 hover:bg-slate-500"
                @click="handleExit">
          EXIT
        </button>
      </div>
    </div>

    <!-- Monitor -->
    <div v-if="showMonitor" class="flex justify-center py-2 bg-slate-850 shrink-0">
      <CarFace :lights="monitorLights" />
    </div>

    <!-- Pad grid -->
    <div class="flex-1 flex flex-col gap-3 p-4 overflow-hidden">

      <!-- Loop controls -->
      <div class="flex items-center gap-3 px-1 shrink-0">
        <span class="text-xs text-slate-400 font-bold">LOOP</span>
        <input type="range" min="40" max="240" step="1"
               :value="bpm" @input="onBpmChange"
               class="flex-1 max-w-48" />
        <span class="text-xs text-slate-400 font-mono w-20">{{ bpm }} BPM</span>
        <div class="flex gap-1">
          <button v-for="pad in LIGHT_PADS" :key="'l'+pad.id"
                  :class="loopPads.has(pad.id) ? 'bg-amber-500 text-slate-900' : 'bg-slate-700 text-slate-400'"
                  class="px-2 py-0.5 rounded text-xs font-bold transition-colors"
                  @click="toggleLoop(pad)">
            {{ pad.label }}
          </button>
        </div>
      </div>

      <!-- Pad grid (Launchpad-mirrored: 3段, 中央=ウィンカー) -->
      <div class="flex-1 grid gap-3" style="grid-template-rows: repeat(4, 1fr)">
        <div v-for="(row, ri) in GRID_LAYOUT" :key="ri"
             class="grid gap-3" style="grid-template-columns: repeat(8, 1fr)">
          <template v-for="(cell, ci) in row" :key="ci">
            <!-- empty slot -->
            <div v-if="cell === null" />

            <!-- STOP (全停止) -->
            <button v-else-if="cell === STOP_CELL"
                    class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75 bg-red-700 hover:bg-red-600 active:bg-red-500 active:scale-95"
                    @pointerdown.prevent="handleAllOff">
              <span class="text-xl sm:text-2xl font-bold text-white">STOP</span>
              <span class="text-xs mt-1 opacity-60">V</span>
            </button>

            <!-- normal pad -->
            <button v-else
                    :class="[padColorClass(getPad(cell)), isActive(cell) ? 'shadow-lg scale-95' : '', loopPads.has(cell) ? 'ring-2 ring-amber-400' : '']"
                    class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75"
                    @pointerdown.prevent="padDown(getPad(cell), $event)">
              <span class="text-xl sm:text-2xl font-bold"
                    :class="getPad(cell).color === 'red'
                      ? (isActive(cell) ? 'text-white' : 'text-red-300')
                      : (isActive(cell) ? 'text-slate-900' : 'text-slate-300')">
                {{ getPad(cell).label }}
              </span>
              <span v-if="loopPads.has(cell)" class="text-xs mt-0.5 text-amber-300 font-bold">LOOP</span>
              <span class="text-xs mt-1 opacity-60 uppercase">{{ getPad(cell).key === ' ' ? 'SPACE' : getPad(cell).key }}</span>
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- Keyboard hint -->
    <div class="text-center text-xs text-slate-500 pb-2">
      Z X C B SPACE V = アクション/ホーン/全停止 | Q W E / A S = ライト | T Y U = 室内/チャープ | R D = 左右ウィンカー | K L = ウォッシャー | G H J = ワイパー | ESC = 終了
    </div>
  </div>
</template>
