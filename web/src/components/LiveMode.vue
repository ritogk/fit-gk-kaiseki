<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'
import CarFace from './CarFace.vue'

const emit = defineEmits<{ exit: [] }>()

const { connected, active, error, connect, disconnect, noteOn, noteOff, allOff } = useWebSocket()

// --- Pad definitions ---

interface Pad {
  id: string
  label: string
  key: string
  color: string
  mode: 'hold' | 'pulse'
}

const LIGHT_PADS: Pad[] = [
  { id: 'turn_left',  label: 'TL',  key: 'q', color: 'amber',  mode: 'hold' },
  { id: 'low_beam',   label: 'LB',  key: 'w', color: 'yellow', mode: 'hold' },
  { id: 'high_beam',  label: 'HB',  key: 'e', color: 'white',  mode: 'hold' },
  { id: 'turn_right', label: 'TR',  key: 'r', color: 'amber',  mode: 'hold' },
  { id: 'position',   label: 'PS',  key: 'a', color: 'orange', mode: 'hold' },
  { id: 'fog',        label: 'FG',  key: 's', color: 'cyan',   mode: 'hold' },
  { id: 'hazard',     label: 'HZ',  key: 'd', color: 'amber',  mode: 'hold' },
]

const ACTION_PADS: Pad[] = [
  { id: 'lock',    label: 'LOCK',   key: 'z', color: 'green',  mode: 'pulse' },
  { id: 'unlock',  label: 'UNLOCK', key: 'x', color: 'green',  mode: 'pulse' },
  { id: 'trunk',   label: 'TRUNK',  key: 'c', color: 'blue',   mode: 'pulse' },
  { id: 'chirp',   label: 'CHIRP',  key: 'v', color: 'purple', mode: 'pulse' },
]

const HORN_PAD: Pad = { id: 'horn', label: 'HORN', key: ' ', color: 'red', mode: 'hold' }

// --- Interaction ---

const pressedKeys = ref<Set<string>>(new Set())
const pressedPads = ref<Set<string>>(new Set())
const pulsedPads = ref<Set<string>>(new Set())

function padDown(pad: Pad) {
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
}

function handleExit() {
  handleAllOff()
  disconnect()
  emit('exit')
}

function isActive(id: string): boolean {
  return active.value.has(id) || pressedPads.value.has(id) || pulsedPads.value.has(id)
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

// --- Monitor ---

const showMonitor = ref(true)

const CMD_TO_POS: Record<string, number> = {
  hazard: 1, high_beam: 2, low_beam: 3, position: 4, fog: 5, turn_left: 6, turn_right: 7,
}

const monitorLights = computed(() => {
  const lids: number[] = []
  for (const id of [...active.value, ...pressedPads.value]) {
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
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  disconnect()
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
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
        <span v-if="error" class="text-red-400 text-xs">{{ error }}</span>
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

      <!-- Lights -->
      <div class="flex-1 grid grid-cols-4 gap-3" style="grid-template-rows: 1fr 1fr">
        <button v-for="pad in LIGHT_PADS" :key="pad.id"
                :class="[padColorClass(pad), isActive(pad.id) ? 'shadow-lg scale-95' : '']"
                class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75"
                @pointerdown.prevent="padDown(pad)"
                @pointerup.prevent="padUp(pad)"
                @pointerleave="padUp(pad)"
                @pointercancel="padUp(pad)">
          <span class="text-2xl sm:text-3xl font-bold"
                :class="isActive(pad.id) ? 'text-slate-900' : 'text-slate-300'">
            {{ pad.label }}
          </span>
          <span class="text-xs mt-1 opacity-60 uppercase">{{ pad.key === ' ' ? 'SPACE' : pad.key }}</span>
        </button>
      </div>

      <!-- Actions + Horn -->
      <div class="grid gap-3" style="grid-template-columns: repeat(4, 1fr) 2fr; height: 25%">
        <button v-for="pad in ACTION_PADS" :key="pad.id"
                :class="[padColorClass(pad), isActive(pad.id) ? 'shadow-lg scale-95' : '']"
                class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75"
                @pointerdown.prevent="padDown(pad)"
                @pointerup.prevent="padUp(pad)"
                @pointerleave="padUp(pad)"
                @pointercancel="padUp(pad)">
          <span class="text-lg sm:text-xl font-bold"
                :class="isActive(pad.id) ? 'text-slate-900' : 'text-slate-300'">
            {{ pad.label }}
          </span>
          <span class="text-xs mt-1 opacity-60 uppercase">{{ pad.key }}</span>
        </button>

        <!-- Horn -->
        <button :class="[padColorClass(HORN_PAD), isActive(HORN_PAD.id) ? 'shadow-lg scale-95' : '']"
                class="pad rounded-xl flex flex-col items-center justify-center transition-all duration-75 col-span-1"
                @pointerdown.prevent="padDown(HORN_PAD)"
                @pointerup.prevent="padUp(HORN_PAD)"
                @pointerleave="padUp(HORN_PAD)"
                @pointercancel="padUp(HORN_PAD)">
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
      Q W E R / A S D = ライト | Z X C V = アクション | SPACE = ホーン | ESC = 終了
    </div>
  </div>
</template>
