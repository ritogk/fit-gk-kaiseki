<script setup lang="ts">
import { computed } from 'vue'
import type { LiveSignals } from '@/types'
import GaugeSvg from '@/components/GaugeSvg.vue'
import SteeringWheel from '@/components/SteeringWheel.vue'

const props = defineProps<{
  current: LiveSignals
  connected: boolean
  alive: boolean
  audioOn: boolean
}>()

const current = props.current

// ステア角 → パン位置（-1..1）の表示用
const pan = computed(() => Math.max(-1, Math.min(1, current.steeringAngle / 450)))
</script>

<template>
  <div class="live" :class="{ dimmed: !alive }">
    <div class="row">
      <GaugeSvg label="RPM" :value="current.rpm" :min="0" :max="8000" unit="rpm" :ticks="9" color="#ff6384" />
      <div class="center">
        <SteeringWheel :angle="current.steeringAngle" />
      </div>
    </div>

    <!-- ステア → 左右パンのインジケータ -->
    <div class="pan">
      <span class="pan-label">PAN L</span>
      <div class="pan-track">
        <div class="pan-dot" :style="{ left: `${(pan + 1) * 50}%` }"></div>
        <div class="pan-mid"></div>
      </div>
      <span class="pan-label">R</span>
    </div>
  </div>
</template>

<style scoped>
.live {
  max-width: 760px;
  margin: 0 auto;
}

.live.dimmed {
  opacity: 0.35;
  transition: opacity 0.2s;
}

.row {
  display: flex;
  gap: 48px;
  justify-content: center;
  align-items: center;
  padding-top: 16px;
}

.center {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pan {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 28px auto 0;
  max-width: 420px;
}

.pan-label {
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.pan-track {
  position: relative;
  flex: 1;
  height: 6px;
  background: #1a1d27;
  border: 1px solid var(--border);
  border-radius: 3px;
}

.pan-mid {
  position: absolute;
  left: 50%;
  top: -3px;
  width: 1px;
  height: 12px;
  background: var(--border);
}

.pan-dot {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--orange);
  transform: translate(-50%, -50%);
  transition: left 0.05s linear;
}
</style>
