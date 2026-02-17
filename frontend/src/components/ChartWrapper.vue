<template>
  <div class="chart-wrapper" ref="chartWrapperRef" :style="wrapperStyle">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import { Chart } from 'chart.js'
import { registerChartJS } from '@/utils/chartRegistration'

const props = withDefaults(
  defineProps<{
    data?: Record<string, unknown> | null
    options?: Record<string, unknown> | null
    height?: string
  }>(),
  {
    data: () => null,
    options: () => null,
    height: '300px',
  },
)

const emit = defineEmits<{
  error: [error: unknown]
  retry: []
}>()

const chartWrapperRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const wrapperStyle = computed(() => ({
  width: '100%',
  height: props.height || '300px',
  position: 'relative' as const,
}))

function ensureRegistered() {
  registerChartJS()
}

function createOrUpdateChart() {
  if (!canvasRef.value) return
  ensureRegistered()
  const data = props.data
  const options = props.options
  if (!data || !data.labels || !Array.isArray(data.datasets)) {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
    return
  }
  try {
    if (chartInstance) {
      chartInstance.data = data as any
      chartInstance.options = options as any
      chartInstance.update()
    } else {
      chartInstance = new Chart(canvasRef.value, {
        type: 'bar',
        data: data as any,
        options: (options || {}) as any,
      })
    }
  } catch (err) {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
    emit('error', err)
  }
}

onMounted(() => {
  createOrUpdateChart()
})

watch(
  () => [props.data, props.options],
  () => {
    createOrUpdateChart()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})

defineExpose({
  chartInstance: () => chartInstance,
  retry: createOrUpdateChart,
})
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  position: relative;
}

.chart-wrapper canvas {
  display: block;
  max-width: 100%;
}
</style>
