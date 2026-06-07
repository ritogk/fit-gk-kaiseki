<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: number
  min: number
  max: number
  unit: string
  ticks: number
  color: string
}>()

const SIZE = 200
const CX = 100
const CY = 110
const R = 80
const START_ANGLE = 225
const END_ANGLE = -45
const SWEEP = START_ANGLE - END_ANGLE // 270 degrees

function polarToCart(angleDeg: number, r: number) {
  const rad = (angleDeg * Math.PI) / 180
  return {
    x: CX + r * Math.cos(rad),
    y: CY - r * Math.sin(rad),
  }
}

const needleAngle = computed(() => {
  const ratio = Math.max(0, Math.min(1, (props.value - props.min) / (props.max - props.min)))
  return START_ANGLE - ratio * SWEEP
})

const needleTip = computed(() => polarToCart(needleAngle.value, R - 10))

const arcPath = computed(() => {
  const s = polarToCart(START_ANGLE, R)
  const e = polarToCart(END_ANGLE, R)
  return `M ${s.x} ${s.y} A ${R} ${R} 0 1 1 ${e.x} ${e.y}`
})

const tickMarks = computed(() => {
  const marks = []
  for (let i = 0; i < props.ticks; i++) {
    const ratio = i / (props.ticks - 1)
    const angle = START_ANGLE - ratio * SWEEP
    const outer = polarToCart(angle, R + 2)
    const inner = polarToCart(angle, R - 8)
    const labelPos = polarToCart(angle, R - 18)
    const val = props.min + ratio * (props.max - props.min)
    marks.push({ outer, inner, labelPos, val: Math.round(val) })
  }
  return marks
})
</script>

<template>
  <svg :width="SIZE" :height="SIZE * 0.7" :viewBox="`0 20 ${SIZE} ${SIZE * 0.65}`">
    <!-- Arc background -->
    <path :d="arcPath" fill="none" stroke="#2a2d3a" stroke-width="6" stroke-linecap="round" />

    <!-- Tick marks -->
    <g v-for="(t, i) in tickMarks" :key="i">
      <line :x1="t.inner.x" :y1="t.inner.y" :x2="t.outer.x" :y2="t.outer.y" stroke="#555" stroke-width="1.5" />
      <text :x="t.labelPos.x" :y="t.labelPos.y" text-anchor="middle" dominant-baseline="middle"
        fill="#8b8fa3" font-size="9" font-family="monospace">{{ t.val }}</text>
    </g>

    <!-- Needle -->
    <line :x1="CX" :y1="CY" :x2="needleTip.x" :y2="needleTip.y"
      :stroke="color" stroke-width="2.5" stroke-linecap="round" />
    <circle :cx="CX" :cy="CY" r="5" :fill="color" />

    <!-- Value -->
    <text :x="CX" :y="CY + 22" text-anchor="middle" :fill="color" font-size="16" font-weight="700" font-family="monospace">
      {{ Math.round(value) }}
    </text>
    <text :x="CX" :y="CY + 34" text-anchor="middle" fill="#8b8fa3" font-size="9" font-family="monospace">
      {{ unit }}
    </text>

    <!-- Label -->
    <text :x="CX" :y="30" text-anchor="middle" fill="#8b8fa3" font-size="10" font-weight="600"
      font-family="monospace" letter-spacing="1">{{ label }}</text>
  </svg>
</template>
