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
  { id: 'turn_left',  label: 'TL',  key: 'q', color: 'amber', mode: 'hold' },
  { id: 'low_beam',   label: 'LB',  key: 'w', color: 'amber', mode: 'hold' },
  { id: 'high_beam',  label: 'HB',  key: 'e', color: 'amber', mode: 'hold' },
  { id: 'turn_right', label: 'TR',  key: 'r', color: 'amber', mode: 'hold' },
  { id: 'position',   label: 'PS',  key: 'a', color: 'amber', mode: 'hold' },
  { id: 'fog',        label: 'FG',  key: 's', color: 'amber', mode: 'hold' },
  { id: 'hazard',     label: 'HZ',  key: 'd', color: 'amber', mode: 'hold' },
]

const ACTION_PADS: Pad[] = [
  { id: 'lock',    label: 'LOCK',   key: 'z', color: 'green',  mode: 'pulse' },
  { id: 'unlock',  label: 'UNLOCK', key: 'x', color: 'green',  mode: 'pulse' },
  { id: 'chirp',   label: 'CHIRP',  key: 'c', color: 'purple', mode: 'pulse' },
]

const HORN_PAD: Pad = { id: 'horn', label: 'HORN', key: ' ', color: 'red', mode: 'hold' }

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
    setTimeout(() => pulsedPads.value.delete(pad.id), 200)
  } else {
    if (!pressedPads.value.has(pad.id)) {
      pressedPads.value.add(pad.id)
      noteOn(pad.id)
    }
  }
}

function padUp(pad: Pad) {
  if (pad.mode === 'hold' && pressedPads.value.has(pad.id)) {
    pressedPads.value.delete(pad.id)
    noteOff(pad.id)
  }
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
  return [...LIGHT_PADS, ...ACTION_PADS, HORN_PAD].find((p) => p.key === k)
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
  return active.value.has(id) || pressedPads.value.has(id) || pulsedPads.value.has(id) || isLoopActive(id)
}

function padColorClass(pad: Pad): string {
  const on = isActive(pad.id)
  const map: Record<string, string> = {
    amber:  on ? 'bg-amber-400 shadow-amber-400/50'  : 'bg-slate-700 hover:bg-slate-600',
    yellow: on ? 'bg-yellow-300 shadow-yellow-300/50' : 'bg-slate-700 hover:bg-slate-600',
    white:  on ? 'bg-white shadow-white/50'           : 'bg-slate-700 hover:bg-slate-600',
    orange: on ? 'bg-orange-400 shadow-orange-400/50' : 'bg-slate-700 hover:bg-slate-600',
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
  const ids = new Set([...active.value, ...pressedPads.value])
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
  document.addEventListener('pointerup', onPointerRelease)
  document.addEventListener('pointercancel', onPointerRelease)
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  if (loopTimer) clearInterval(loopTimer)
  disconnect()
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
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

      <!-- Lights -->
      <div class="flex-1 grid grid-cols-4 gap-3" style="grid-template-rows: 1fr 1fr">
        <button v-for="pad in LIGHT_PADS" :key="pad.id"
                :class="[padColorClass(pad), isActive(pad.id) ? 'shadow-lg scale-95' : '', loopPads.has(pad.id) ? 'ring-2 ring-amber-400' : '']"
                class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75"
                @pointerdown.prevent="padDown(pad, $event)">
          <span class="text-2xl sm:text-3xl font-bold"
                :class="isActive(pad.id) ? 'text-slate-900' : 'text-slate-300'">
            {{ pad.label }}
          </span>
          <span v-if="loopPads.has(pad.id)" class="text-xs mt-0.5 text-amber-300 font-bold">LOOP</span>
          <span class="text-xs mt-1 opacity-60 uppercase">{{ pad.key === ' ' ? 'SPACE' : pad.key }}</span>
        </button>
      </div>

      <!-- Actions + Horn -->
      <div class="grid gap-3" style="grid-template-columns: repeat(3, 1fr) 2fr; height: 25%">
        <button v-for="pad in ACTION_PADS" :key="pad.id"
                :class="[padColorClass(pad), isActive(pad.id) ? 'shadow-lg scale-95' : '']"
                class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75"
                @pointerdown.prevent="padDown(pad, $event)">
          <span class="text-lg sm:text-xl font-bold"
                :class="isActive(pad.id) ? 'text-slate-900' : 'text-slate-300'">
            {{ pad.label }}
          </span>
          <span class="text-xs mt-1 opacity-60 uppercase">{{ pad.key }}</span>
        </button>

        <!-- Horn -->
        <button :class="[padColorClass(HORN_PAD), isActive(HORN_PAD.id) ? 'shadow-lg scale-95' : '']"
                class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75 col-span-1"
                @pointerdown.prevent="padDown(HORN_PAD, $event)">
          <span class="text-2xl sm:text-3xl font-bold"
                :class="isActive(HORN_PAD.id) ? 'text-white' : 'text-red-300'">
            HORN
          </span>
          <span class="text-xs mt-1 opacity-60">SPACE</span>
        </button>
      </div>
    </div>

    <!-- Keyboard hint -->
    <div class="text-center text-xs text-slate-500 pb-2">
      Q W E R / A S D = ライト | Z X C = アクション | SPACE = ホーン | ESC = 終了
    </div>
  </div>
</template>
