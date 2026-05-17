<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import CarFace from './CarFace.vue'
import type { Scene } from '../types'

const STORAGE_KEY = 'gk-scenes'

const positions = defineModel<string>('positions', { default: '1,2,3' })
const props = defineProps<{ speed: number }>()

// --- Scene state ---

function load(): Scene[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) return parsed
    }
  } catch { /* ignore */ }
  return [[1], [2], [3]]
}

const scenes = ref<Scene[]>(load())
const selected = ref(0)

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(scenes.value))
}

function scenesToPositions(s: Scene[]): string {
  return s
    .map((scene) => {
      if (scene.length === 0) return ''
      if (scene.length === 1) return String(scene[0])
      return '[' + scene.join(',') + ']'
    })
    .filter(Boolean)
    .join(',')
}

// Sync scenes → positions
const positionsComputed = computed(() => scenesToPositions(scenes.value))
watch(positionsComputed, (val) => { positions.value = val }, { immediate: true })

// --- Actions ---

const currentLights = computed(() => scenes.value[selected.value] ?? [])

function toggleLight(pos: number) {
  const scene = scenes.value[selected.value]
  if (!scene) return

  const has = (p: number) => scene.includes(p)
  const remove = (p: number) => { const i = scene.indexOf(p); if (i >= 0) scene.splice(i, 1) }
  const add = (p: number) => { if (!has(p)) scene.push(p) }

  if (pos === 6 || pos === 7) {
    const other = pos === 6 ? 7 : 6
    if (has(1)) {
      remove(1)
      add(other)
    } else if (has(pos)) {
      remove(pos)
    } else {
      if (has(other)) {
        remove(other)
        add(1)
      } else {
        add(pos)
      }
    }
  } else {
    if (has(pos)) remove(pos)
    else add(pos)
  }

  scene.sort((a, b) => a - b)
  save()
}

function addScene() {
  scenes.value.push([])
  selected.value = scenes.value.length - 1
  save()
}

function removeScene(i: number) {
  scenes.value.splice(i, 1)
  if (scenes.value.length === 0) scenes.value.push([])
  if (selected.value >= scenes.value.length) selected.value = scenes.value.length - 1
  save()
}

function duplicateScene(i: number) {
  scenes.value.splice(i + 1, 0, [...scenes.value[i]])
  selected.value = i + 1
  save()
}

function loadPreset(preset: Scene[]) {
  scenes.value = preset.map((s) => [...s])
  selected.value = 0
  save()
}

// --- Preview playback ---

const playing = ref(false)
let previewTimer: ReturnType<typeof setInterval> | null = null

const previewInterval = computed(() => Math.round(250 / props.speed))

function startPreview() {
  stopPreview()
  playing.value = true
  selected.value = 0
  previewTimer = setInterval(() => {
    selected.value = (selected.value + 1) % scenes.value.length
  }, previewInterval.value)
}

function stopPreview() {
  playing.value = false
  if (previewTimer) { clearInterval(previewTimer); previewTimer = null }
}

watch(previewInterval, () => { if (playing.value) startPreview() })
onUnmounted(() => stopPreview())

defineExpose({ playing, startPreview, stopPreview })

// --- Presets ---

const PRESETS: { label: string; scenes: Scene[] }[] = [
  { label: 'chase HZ,HB,LB', scenes: [[1], [2], [3]] },
  { label: 'full sweep', scenes: [[1], [2], [3], [4], [5]] },
  { label: 'wave', scenes: [[1], [2], [3], [4], [5], [4], [3], [2]] },
  { label: 'slide', scenes: [[1, 2], [2, 3], [3, 4], [4, 5]] },
  { label: 'blast', scenes: [[1, 2, 3], [4, 5], [1, 2, 3]] },
  { label: '全同時', scenes: [[1, 2, 3, 4, 5, 6, 7]] },
  { label: 'HZ→HB+FG→LB+PS', scenes: [[1], [2, 5], [3, 4]] },
  { label: 'TL→TR交互', scenes: [[6], [7]] },
  { label: 'TL+LB→TR+LB', scenes: [[6, 3], [7, 3]] },
  { label: '外→内', scenes: [[6, 7], [3], [2], [4, 5]] },
  { label: '内→外', scenes: [[2], [3], [6, 7], [4, 5]] },
  { label: 'ビルドアップ', scenes: [[6], [6, 3], [6, 3, 2], [6, 3, 2, 4], [6, 3, 2, 4, 5]] },
  { label: 'ping pong', scenes: [[6], [3], [2], [7], [2], [3]] },
  { label: 'ジグザグ', scenes: [[6], [2], [3], [7], [5], [4]] },
  { label: '左流し', scenes: [[7], [2], [3], [6], [4, 5]] },
  { label: '点滅交互', scenes: [[6, 2, 4], [7, 3, 5]] },
  { label: 'ハートビート', scenes: [[1, 2, 3], [], [1, 2, 3], []] },
  { label: '開閉', scenes: [[6, 7], [3, 4, 5], [2], [3, 4, 5], [6, 7]] },
]
</script>

<template>
  <!-- Scene timeline -->
  <div class="flex items-center gap-1.5 overflow-x-auto pb-2 mb-3">
    <template v-for="(scene, i) in scenes" :key="i">
      <div class="scene-card" :class="{ selected: i === selected }" @click="selected = i">
        <div class="text-center text-slate-500 mb-0.5" style="font-size:0.6rem">#{{ i + 1 }}</div>
        <CarFace :lights="scene" mini />
        <div class="flex gap-1 mt-1 justify-center">
          <button class="text-slate-400 hover:text-blue-500" style="font-size:0.6rem"
                  @click.stop="duplicateScene(i)" title="複製">&#x29C9;</button>
          <button class="text-slate-400 hover:text-red-500" style="font-size:0.6rem"
                  @click.stop="removeScene(i)" title="削除">&times;</button>
        </div>
      </div>
      <span v-if="i < scenes.length - 1" class="text-slate-300 shrink-0">&rarr;</span>
    </template>
    <button class="btn btn-ghost text-sm shrink-0 py-2" @click="addScene">+</button>
  </div>

  <!-- Car face editor + presets -->
  <div class="flex flex-col sm:flex-row gap-4 items-start mb-3">
    <div class="shrink-0">
      <div class="text-xs text-slate-500 mb-1 text-center">シーン #{{ selected + 1 }}</div>
      <CarFace :lights="currentLights" :interactive="!playing" @toggle="toggleLight" />
    </div>
    <div class="min-w-0">
      <div class="flex flex-wrap gap-1.5">
        <span class="text-xs text-slate-600 leading-6">プリセット:</span>
        <button v-for="p in PRESETS" :key="p.label"
                class="btn btn-ghost text-xs"
                @click="loadPreset(p.scenes)">
          {{ p.label }}
        </button>
      </div>
    </div>
  </div>
</template>
