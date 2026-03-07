import {
  Chart as ChartJS,
  BarController,
  LineController,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

export type { ChartData, ChartOptions } from 'chart.js'

/** 折线图「完了率」数据点上方显示百分比的插件 */
const completionRateDatalabelsPlugin = {
  id: 'completionRateDatalabels',
  afterDraw(chart: InstanceType<typeof ChartJS>) {
    const ctx = chart.ctx
    const datasets = chart.data.datasets || []
    for (let dsIndex = 0; dsIndex < datasets.length; dsIndex++) {
      const ds = datasets[dsIndex] as { label?: string; data?: unknown[] }
      if (ds.label !== '完了率 (%)' || !ds.data) continue
      const meta = chart.getDatasetMeta(dsIndex)
      if (!meta?.data?.length) continue
      meta.data.forEach((point: { x: number; y: number }, index: number) => {
        const value = ds.data![index]
        if (value == null) return
        const text = typeof value === 'number' ? `${value}%` : `${value}`
        const x = point.x
        const y = point.y - 10
        ctx.save()
        ctx.fillStyle = '#f59e0b'
        ctx.font = 'bold 11px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'bottom'
        ctx.fillText(text, x, y)
        ctx.restore()
      })
      break
    }
  },
}

let registered = false

export function registerChartJS() {
  if (registered) return
  ChartJS.register(
    BarController,
    LineController,
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    ArcElement,
    RadialLinearScale,
    Title,
    Tooltip,
    Legend,
    Filler,
    completionRateDatalabelsPlugin,
  )
  registered = true
}
