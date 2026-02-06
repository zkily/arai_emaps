<template>
  <canvas ref="canvasRef"></canvas>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Chart, BarController, BarElement, LinearScale, CategoryScale, Title, Tooltip, Legend } from 'chart.js'

Chart.register(BarController, BarElement, LinearScale, CategoryScale, Title, Tooltip, Legend)

const props = defineProps<{ labels: string[], data: number[], label: string }>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart

const renderChart = () => {
  if (!canvasRef.value) return
  if (chart) chart.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'bar',
    data: {
      labels: props.labels,
      datasets: [{ label: props.label, data: props.data, backgroundColor: '#67C23A' }]
    }
  })
}

onMounted(() => renderChart())
watch(() => [props.labels, props.data], renderChart)
</script>
