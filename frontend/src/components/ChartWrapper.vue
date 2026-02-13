<template>
  <div class="chart-wrapper" ref="chartContainer">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  height?: string
}>()

const chartContainer = ref<HTMLElement>()
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  position: relative;
}
</style>
