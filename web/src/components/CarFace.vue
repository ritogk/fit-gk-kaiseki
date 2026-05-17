<script setup lang="ts">
defineProps<{
  lights: number[]
  mini?: boolean
  interactive?: boolean
}>()

const emit = defineEmits<{
  toggle: [pos: number]
}>()

// Left side (viewer's left): outside → inside = LB, HB, HZ
const LEFT_TOP = [
  { pos: 3, label: 'LB' },
  { pos: 2, label: 'HB' },
  { pos: 1, label: 'HZ' },
]
const LEFT_BOTTOM = [
  { pos: 4, label: 'PS' },
  { pos: 5, label: 'FG' },
]

// Right side (mirrored): inside → outside = HZ, HB, LB
const RIGHT_TOP = [
  { pos: 1, label: 'HZ' },
  { pos: 2, label: 'HB' },
  { pos: 3, label: 'LB' },
]
const RIGHT_BOTTOM = [
  { pos: 5, label: 'FG' },
  { pos: 4, label: 'PS' },
]
</script>

<template>
  <!-- Mini: compact dots for scene cards -->
  <div v-if="mini" class="inline-flex gap-1 items-center">
    <!-- Left -->
    <div class="flex flex-col gap-0.5">
      <div class="flex gap-0.5">
        <span v-for="l in LEFT_TOP" :key="'lt'+l.pos+l.label"
              class="light-mini" :class="{ on: lights.includes(l.pos) }" />
      </div>
      <div class="flex gap-0.5 justify-start">
        <span v-for="l in LEFT_BOTTOM" :key="'lb'+l.pos+l.label"
              class="light-mini" :class="{ on: lights.includes(l.pos) }" />
      </div>
    </div>
    <!-- Divider -->
    <div class="w-px h-3 bg-slate-400" />
    <!-- Right -->
    <div class="flex flex-col gap-0.5">
      <div class="flex gap-0.5">
        <span v-for="l in RIGHT_TOP" :key="'rt'+l.pos+l.label"
              class="light-mini" :class="{ on: lights.includes(l.pos) }" />
      </div>
      <div class="flex gap-0.5 justify-end">
        <span v-for="l in RIGHT_BOTTOM" :key="'rb'+l.pos+l.label"
              class="light-mini" :class="{ on: lights.includes(l.pos) }" />
      </div>
    </div>
  </div>

  <!-- Full: clickable car front face -->
  <div v-else class="bg-slate-800 rounded-lg p-4 inline-flex gap-3 items-start">
    <!-- Left side -->
    <div class="flex flex-col gap-3">
      <div class="flex gap-3">
        <div v-for="l in LEFT_TOP" :key="'lt'+l.pos+l.label"
             class="light" :class="{ on: lights.includes(l.pos), interactive }"
             @click="interactive && emit('toggle', l.pos)">
          {{ l.label }}
        </div>
      </div>
      <div class="flex gap-3 justify-start">
        <div v-for="l in LEFT_BOTTOM" :key="'lb'+l.pos+l.label"
             class="light" :class="{ on: lights.includes(l.pos), interactive }"
             @click="interactive && emit('toggle', l.pos)">
          {{ l.label }}
        </div>
      </div>
    </div>
    <!-- Center grille -->
    <div class="w-px self-stretch bg-slate-600 mx-1" />
    <!-- Right side -->
    <div class="flex flex-col gap-3">
      <div class="flex gap-3">
        <div v-for="l in RIGHT_TOP" :key="'rt'+l.pos+l.label"
             class="light" :class="{ on: lights.includes(l.pos), interactive }"
             @click="interactive && emit('toggle', l.pos)">
          {{ l.label }}
        </div>
      </div>
      <div class="flex gap-3 justify-end">
        <div v-for="l in RIGHT_BOTTOM" :key="'rb'+l.pos+l.label"
             class="light" :class="{ on: lights.includes(l.pos), interactive }"
             @click="interactive && emit('toggle', l.pos)">
          {{ l.label }}
        </div>
      </div>
    </div>
  </div>
</template>
