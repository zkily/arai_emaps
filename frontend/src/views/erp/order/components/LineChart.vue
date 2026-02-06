<template>
  <canvas ref="canvasRef"></canvas>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend } from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend)

const props = defineProps<{ labels: string[], data: number[], label: string }>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart

const renderChart = () => {
  if (!canvasRef.value) return
  if (chart) chart.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels: props.labels,
      datasets: [{ label: props.label, data: props.data, fill: false, borderColor: '#409EFF', tension: 0.3 }]
    }
  })
}

onMounted(() => renderChart())
watch(() => [props.labels, props.data], renderChart)
</script>
