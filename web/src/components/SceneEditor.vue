<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import CarFace from './CarFace.vue'
import type { Scene } from '../types'

const STORAGE_KEY = 'gk-scenes'

const positions = defineModel<string>('positions', { default: '1,2,3' })

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
  const idx = scene.indexOf(pos)
  if (idx >= 0) scene.splice(idx, 1)
  else {
    scene.push(pos)
    scene.sort((a, b) => a - b)
  }
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

// --- Presets ---

const PRESETS: { label: string; scenes: Scene[] }[] = [
  { label: 'chase 1,2,3', scenes: [[1], [2], [3]] },
  { label: 'full 1→5', scenes: [[1], [2], [3], [4], [5]] },
  { label: 'slide [1,2]→[4,5]', scenes: [[1, 2], [2, 3], [3, 4], [4, 5]] },
  { label: 'blast', scenes: [[1, 2, 3], [4, 5], [1, 2, 3]] },
  { label: 'wave 1→5→2', scenes: [[1], [2], [3], [4], [5], [4], [3], [2]] },
  { label: 'sandwich', scenes: [[2, 3], [1], [4, 5], [1]] },
  { label: '全同時', scenes: [[1, 2, 3, 4, 5]] },
  { label: 'HZ→HB+FG→LB+PS', scenes: [[1], [2, 5], [3, 4]] },
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
      <CarFace :lights="currentLights" interactive @toggle="toggleLight" />
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
      <div class="text-xs text-slate-500 mt-2">
        ⚠ HZ (1) は 0.15s 物理floor で clamp。FG (5) はライトON時のみ視認可。[1,2]で同時点灯。
      </div>
      <div class="text-xs text-slate-400 mt-1 font-mono">positions: {{ positionsComputed }}</div>
    </div>
  </div>
</template>
