<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ angle: number }>()

// OpenDBC STEER_ANGLE is in degrees (scale -0.1 already applied in backend)
// Positive = left, visual rotation: positive angle = counter-clockwise
const rotation = computed(() => {
  const clamped = Math.max(-540, Math.min(540, props.angle))
  return -clamped // negate so left turn rotates wheel left visually
})
</script>

<template>
  <div class="steering-container">
    <span class="label">STEERING</span>
    <svg width="180" height="180" viewBox="0 0 180 180">
      <g :transform="`rotate(${rotation}, 90, 90)`">
        <!-- Outer rim -->
        <circle cx="90" cy="90" r="75" fill="none" stroke="#555" stroke-width="12" />
        <!-- Grip highlights -->
        <circle cx="90" cy="90" r="75" fill="none" stroke="#888" stroke-width="4"
          stroke-dasharray="60 20 60 20 60 20" stroke-dashoffset="30" />
        <!-- Spokes -->
        <line x1="90" y1="90" x2="90" y2="20" stroke="#666" stroke-width="6" stroke-linecap="round" />
        <line x1="90" y1="90" x2="28" y2="120" stroke="#666" stroke-width="6" stroke-linecap="round" />
        <line x1="90" y1="90" x2="152" y2="120" stroke="#666" stroke-width="6" stroke-linecap="round" />
        <!-- Center hub -->
        <circle cx="90" cy="90" r="16" fill="#333" stroke="#555" stroke-width="2" />
        <!-- Top marker -->
        <circle cx="90" cy="17" r="4" fill="#ff9800" />
      </g>
      <!-- Fixed center dot -->
      <circle cx="90" cy="90" r="3" fill="#4f8ff7" />
    </svg>
    <span class="angle-value">{{ props.angle.toFixed(1) }}&deg;</span>
  </div>
</template>

<style scoped>
.steering-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
}

.angle-value {
  font-size: 14px;
  font-weight: 700;
  color: #ff9800;
  font-family: monospace;
}
</style>
