import * as echarts from 'echarts'

export const CHART_INIT_OPTS = {
  devicePixelRatio: Math.min(typeof window !== 'undefined' ? window.devicePixelRatio : 2, 2),
}

export type IpaChartFormatters = {
  fmtInt: (value: number | null | undefined) => string
  fmtPct: (value: number | null | undefined) => string
  fmtEfficiency: (value: number | null | undefined) => string
}

export interface IpaDailyTrendRow {
  day: string
  sum_actual_qty?: number
  efficiency_per_hour?: number | null
}

export interface IpaPersonBarRow {
  person_name?: string | null
  avg_efficiency_per_hour?: number | null
  sum_actual_qty?: number
  defect_rate_percent?: number | null
}

export interface IpaProductBarRow {
  product_cd?: string
  product_name?: string
  sum_actual_qty?: number
  avg_efficiency_per_hour?: number | null
  defect_rate_percent?: number | null
}

export interface IpaRankBarRow {
  person_name?: string | null
  rank?: number
  efficiency_per_hour?: number | null
  sum_actual_qty?: number
  defect_rate_percent?: number | null
}

export type IpaChartTheme = ReturnType<typeof chartTheme>

/** 横向柱状图：多色相渐变（浅 → 深） */
const H_BAR_GRADIENT_STOPS: [string, string][] = [
  ['#818cf8', '#4338ca'],
  ['#34d399', '#047857'],
  ['#fbbf24', '#b45309'],
  ['#f472b6', '#be185d'],
  ['#38bdf8', '#0369a1'],
  ['#a78bfa', '#6d28d9'],
  ['#fb923c', '#c2410c'],
  ['#2dd4bf', '#0f766e'],
  ['#f87171', '#dc2626'],
  ['#4ade80', '#15803d'],
]

function horizontalBarGradient(index: number, highlightFirst = false) {
  if (highlightFirst && index === 0) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#fde68a' },
      { offset: 1, color: '#d97706' },
    ])
  }
  const [light, dark] = H_BAR_GRADIENT_STOPS[index % H_BAR_GRADIENT_STOPS.length]
  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: light },
    { offset: 1, color: dark },
  ])
}

function horizontalBarAccentColor(index: number, highlightFirst = false): string {
  if (highlightFirst && index === 0) return '#b45309'
  return H_BAR_GRADIENT_STOPS[index % H_BAR_GRADIENT_STOPS.length][1]
}

/** 横向柱状图一屏可见条数；超出时显示纵向滚动条 */
const H_BAR_VISIBLE_COUNT = 8

function buildHorizontalBarDataZoom(itemCount: number, accent = '#6366f1') {
  if (itemCount <= H_BAR_VISIBLE_COUNT) return []
  const span = Math.min(H_BAR_VISIBLE_COUNT - 1, itemCount - 1)
  return [
    {
      type: 'slider',
      yAxisIndex: 0,
      orient: 'vertical',
      right: 4,
      width: 10,
      startValue: 0,
      endValue: span,
      minValueSpan: span,
      maxValueSpan: span,
      showDetail: false,
      brushSelect: false,
      borderColor: 'transparent',
      backgroundColor: 'rgba(148, 163, 184, 0.18)',
      fillerColor: `${accent}40`,
      handleSize: '65%',
      handleStyle: { color: accent, borderColor: accent },
      moveHandleSize: 0,
      textStyle: { color: 'transparent' },
    },
    {
      type: 'inside',
      yAxisIndex: 0,
      orient: 'vertical',
      zoomOnMouseWheel: false,
      moveOnMouseMove: true,
      moveOnMouseWheel: true,
    },
  ]
}

function horizontalBarGridRight(itemCount: number, base = 52): number {
  return itemCount > H_BAR_VISIBLE_COUNT ? base + 16 : base
}

export function chartTheme() {
  return {
    text: '#64748b',
    axis: '#e2e8f0',
    split: 'rgba(148, 163, 184, 0.22)',
  }
}

function buildDailyTrendChartOption(
  daily: IpaDailyTrendRow[],
  theme: IpaChartTheme,
  formatters: IpaChartFormatters,
  efficiencyUnit: string,
  options?: { forExport?: boolean },
) {
  const forExport = options?.forExport === true
  const days = daily.map((d) => d.day.slice(5))
  const productionData = daily.map((d) => d.sum_actual_qty ?? 0)
  const efficiencyData = daily.map((d) => d.efficiency_per_hour ?? null)
  const barGradient = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: '#7dd3fc' },
    { offset: 0.55, color: '#6366f1' },
    { offset: 1, color: '#4338ca' },
  ])
  const barGradientEmphasis = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: '#bae6fd' },
    { offset: 0.55, color: '#818cf8' },
    { offset: 1, color: '#4f46e5' },
  ])

  return {
    backgroundColor: forExport ? '#ffffff' : 'transparent',
    animation: !forExport,
    animationDuration: forExport ? 0 : 1100,
    animationDurationUpdate: forExport ? 0 : 750,
    animationEasing: 'cubicOut' as const,
    animationEasingUpdate: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(226, 232, 240, 0.95)',
      borderWidth: 1,
      padding: [12, 16],
      extraCssText:
        'border-radius: 14px; box-shadow: 0 16px 48px rgba(15, 23, 42, 0.12), 0 2px 8px rgba(15, 23, 42, 0.06);',
      textStyle: { color: '#334155', fontSize: 12, lineHeight: 20 },
      axisPointer: {
        type: 'line',
        lineStyle: { color: 'rgba(99, 102, 241, 0.35)', width: 1, type: 'solid' as const },
        label: {
          backgroundColor: '#4f46e5',
          color: '#fff',
          borderRadius: 8,
          padding: [5, 8],
          fontSize: 10,
          fontWeight: 600,
        },
      },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const axis = list[0] as { axisValue?: string; dataIndex?: number }
        const idx = axis.dataIndex ?? 0
        const row = daily[idx]
        if (!row) return ''
        const lines = [`<div style="font-weight:700;margin-bottom:8px;color:#0f172a;letter-spacing:0.02em">${row.day}</div>`]
        for (const p of list) {
          const item = p as { seriesName?: string; value?: number | null; color?: string }
          const dot = `<span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:${item.color};margin-right:8px;vertical-align:middle"></span>`
          if (item.seriesName === '生産数') {
            lines.push(`<div style="margin:4px 0">${dot}<span style="color:#64748b">生産数</span> <b style="color:#4338ca">${formatters.fmtInt(item.value)}</b></div>`)
          } else if (item.seriesName === '能率') {
            lines.push(`<div style="margin:4px 0">${dot}<span style="color:#64748b">能率</span> <b style="color:#047857">${formatters.fmtEfficiency(item.value)}</b> <span style="color:#94a3b8;font-size:11px">${efficiencyUnit}</span></div>`)
          }
        }
        return lines.join('')
      },
    },
    legend: {
      data: ['生産数', '能率'],
      top: 4,
      itemWidth: 16,
      itemHeight: 8,
      itemGap: 24,
      icon: 'roundRect',
      textStyle: { color: '#475569', fontSize: 11, fontWeight: 600 },
    },
    grid: { left: 52, right: 52, top: 72, bottom: 28, containLabel: false },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: true,
      axisLine: { lineStyle: { color: theme.axis, width: 1 } },
      axisTick: { show: false },
      axisLabel: {
        color: '#64748b',
        fontSize: 11,
        fontWeight: 500,
        margin: 12,
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '生産数',
        nameTextStyle: { color: '#6366f1', fontSize: 10, fontWeight: 600, padding: [0, 0, 6, 0] },
        axisLabel: { color: theme.text, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: { color: theme.split, type: 'dashed' as const, width: 1 },
        },
      },
      {
        type: 'value',
        name: '能率',
        nameTextStyle: { color: '#059669', fontSize: 10, fontWeight: 600, padding: [0, 0, 6, 0] },
        axisLabel: { color: theme.text, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '生産数',
        type: 'bar',
        barMaxWidth: 28,
        barCategoryGap: '42%',
        z: 2,
        animationDelay: (idx: number) => idx * 35,
        data: productionData,
        label: {
          show: true,
          position: 'inside',
          verticalAlign: 'middle',
          align: 'center',
          color: '#ffffff',
          fontSize: 9,
          fontWeight: 700,
          textShadowColor: 'rgba(67, 56, 202, 0.55)',
          textShadowBlur: 4,
          formatter: (params: { value?: number | null }) => {
            const v = Number(params.value ?? 0)
            if (!Number.isFinite(v) || v <= 0) return ''
            return formatters.fmtInt(v)
          },
        },
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: barGradient,
          borderColor: 'rgba(255, 255, 255, 0.35)',
          borderWidth: 1,
          shadowColor: 'rgba(67, 56, 202, 0.22)',
          shadowBlur: 10,
          shadowOffsetY: 4,
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: barGradientEmphasis,
            shadowBlur: 16,
            shadowOffsetY: 6,
          },
          label: { fontSize: 11 },
        },
      },
      {
        name: '能率',
        type: 'line',
        yAxisIndex: 1,
        z: 3,
        smooth: 0.38,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 7,
        animationDelay: (idx: number) => idx * 30 + 120,
        lineStyle: {
          width: 2.5,
          color: '#10b981',
          cap: 'round',
          join: 'round',
        },
        itemStyle: {
          color: '#10b981',
          borderWidth: 2,
          borderColor: '#ffffff',
        },
        label: {
          show: true,
          position: 'top',
          distance: 12,
          color: '#047857',
          fontSize: 9,
          fontWeight: 700,
          backgroundColor: 'rgba(255, 255, 255, 0.94)',
          padding: [3, 6],
          borderRadius: 6,
          borderColor: 'rgba(16, 185, 129, 0.32)',
          borderWidth: 1,
          shadowColor: 'rgba(16, 185, 129, 0.12)',
          shadowBlur: 6,
          shadowOffsetY: 2,
          formatter: (params: { value?: number | null }) => {
            const v = params.value
            if (v == null || !Number.isFinite(Number(v))) return ''
            return formatters.fmtEfficiency(Number(v))
          },
        },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(52, 211, 153, 0.22)' },
            { offset: 0.75, color: 'rgba(16, 185, 129, 0.06)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0)' },
          ]),
        },
        emphasis: {
          focus: 'series',
          scale: 1.45,
          itemStyle: {
            borderWidth: 2.5,
            shadowBlur: 10,
            shadowColor: 'rgba(16, 185, 129, 0.35)',
          },
        },
        data: efficiencyData,
      },
    ],
  }
}

function buildPersonBarChartOption(rows: IpaPersonBarRow[], theme: IpaChartTheme, formatters: IpaChartFormatters, efficiencyUnit: string) {
  const names = rows.map((r) => r.person_name ?? '—')
  const dataZoom = buildHorizontalBarDataZoom(rows.length, '#6366f1')

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.08)' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(226, 232, 240, 0.95)',
      borderWidth: 1,
      padding: [10, 14],
      extraCssText: 'border-radius: 12px; box-shadow: 0 12px 36px rgba(15, 23, 42, 0.1);',
      textStyle: { color: '#334155', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b style="color:#312e81">${row.person_name ?? '—'}</b>`,
          `平均能率 <b style="color:#4f46e5">${formatters.fmtEfficiency(row.avg_efficiency_per_hour)}</b> ${efficiencyUnit}`,
          `生産 ${formatters.fmtInt(row.sum_actual_qty)} · 不良率 ${formatters.fmtPct(row.defect_rate_percent)}`,
        ].join('<br/>')
      },
    },
    grid: { left: 92, right: horizontalBarGridRight(rows.length), top: 10, bottom: 12, containLabel: false },
    dataZoom,
    xAxis: {
      type: 'value',
      name: efficiencyUnit,
      nameTextStyle: { color: '#6366f1', fontSize: 10, fontWeight: 600 },
      axisLabel: { color: theme.text, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 11, fontWeight: 500, width: 76, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        animationDelay: (idx: number) => idx * 60,
        data: rows.map((r, i) => ({
          value: r.avg_efficiency_per_hour ?? 0,
          label: { color: horizontalBarAccentColor(i) },
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: horizontalBarGradient(i),
            borderColor: 'rgba(255, 255, 255, 0.45)',
            borderWidth: 1,
            shadowColor: 'rgba(15, 23, 42, 0.12)',
            shadowBlur: 8,
            shadowOffsetX: 3,
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 6,
          fontSize: 10,
          fontWeight: 700,
          formatter: (p: { value?: number }) => formatters.fmtEfficiency(p.value),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 14, shadowOffsetX: 5 },
        },
      },
    ],
  }
}

function buildProductChartOption(rows: IpaProductBarRow[], theme: IpaChartTheme, formatters: IpaChartFormatters, efficiencyUnit: string) {
  const labels = rows.map((r) => {
    const name = (r.product_name ?? '').trim()
    return name.length > 10 ? `${name.slice(0, 10)}…` : name || r.product_cd || '—'
  })
  const dataZoom = buildHorizontalBarDataZoom(rows.length, '#0ea5e9')

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(14, 165, 233, 0.08)' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(226, 232, 240, 0.95)',
      borderWidth: 1,
      padding: [10, 14],
      extraCssText: 'border-radius: 12px; box-shadow: 0 12px 36px rgba(15, 23, 42, 0.1);',
      textStyle: { color: '#334155', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b style="color:#0c4a6e">${row.product_name ?? row.product_cd}</b>`,
          `<span style="color:#64748b">${row.product_cd}</span>`,
          `生産 <b style="color:#0284c7">${formatters.fmtInt(row.sum_actual_qty)}</b>`,
          `能率 ${formatters.fmtEfficiency(row.avg_efficiency_per_hour)} ${efficiencyUnit} · 不良率 ${formatters.fmtPct(row.defect_rate_percent)}`,
        ].join('<br/>')
      },
    },
    grid: { left: 96, right: horizontalBarGridRight(rows.length), top: 10, bottom: 12, containLabel: false },
    dataZoom,
    xAxis: {
      type: 'value',
      name: '生産数',
      nameTextStyle: { color: '#0284c7', fontSize: 10, fontWeight: 600 },
      axisLabel: { color: theme.text, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 10, fontWeight: 500, width: 80, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        animationDelay: (idx: number) => idx * 60,
        data: rows.map((r, i) => ({
          value: r.sum_actual_qty ?? 0,
          label: { color: horizontalBarAccentColor(i) },
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: horizontalBarGradient(i),
            borderColor: 'rgba(255, 255, 255, 0.45)',
            borderWidth: 1,
            shadowColor: 'rgba(15, 23, 42, 0.12)',
            shadowBlur: 8,
            shadowOffsetX: 3,
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 6,
          fontSize: 10,
          fontWeight: 700,
          formatter: (p: { value?: number }) => formatters.fmtInt(p.value),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 14, shadowOffsetX: 5 },
        },
      },
    ],
  }
}


function buildProductRankChartOption(
  rows: IpaRankBarRow[],
  theme: IpaChartTheme,
  formatters: IpaChartFormatters,
  efficiencyUnit: string,
) {
  const dataZoom = buildHorizontalBarDataZoom(rows.length, '#f59e0b')

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(245, 158, 11, 0.1)' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(253, 230, 138, 0.9)',
      borderWidth: 1,
      padding: [10, 14],
      extraCssText: 'border-radius: 12px; box-shadow: 0 12px 36px rgba(245, 158, 11, 0.15);',
      textStyle: { color: '#334155', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b style="color:#92400e">${row.person_name ?? '—'}</b>`,
          `順位 <b style="color:#d97706">#${row.rank ?? '—'}</b>`,
          `能率 <b style="color:#059669">${formatters.fmtEfficiency(row.efficiency_per_hour)}</b> ${efficiencyUnit}`,
          `生産 ${formatters.fmtInt(row.sum_actual_qty)} · 不良率 ${formatters.fmtPct(row.defect_rate_percent)}`,
        ].join('<br/>')
      },
    },
    grid: { left: 104, right: horizontalBarGridRight(rows.length, 48), top: 10, bottom: 14, containLabel: false },
    dataZoom,
    xAxis: {
      type: 'value',
      name: efficiencyUnit,
      nameTextStyle: { color: '#d97706', fontSize: 10, fontWeight: 600 },
      axisLabel: { color: theme.text, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => `#${r.rank} ${r.person_name ?? '—'}`),
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 11, fontWeight: 500, width: 96, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        animationDelay: (idx: number) => idx * 55,
        data: rows.map((r, i) => ({
          value: r.efficiency_per_hour ?? 0,
          label: { color: horizontalBarAccentColor(i, true) },
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: horizontalBarGradient(i, true),
            borderColor: 'rgba(255, 255, 255, 0.5)',
            borderWidth: 1,
            shadowColor: 'rgba(245, 158, 11, 0.22)',
            shadowBlur: 10,
            shadowOffsetX: 3,
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 6,
          fontSize: 10,
          fontWeight: 700,
          formatter: (p: { value?: number }) => formatters.fmtEfficiency(p.value),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 16, shadowOffsetX: 5 },
        },
      },
    ],
  }
}


export function createDailyTrendChartOption(
  daily: IpaDailyTrendRow[],
  theme: IpaChartTheme,
  formatters: IpaChartFormatters,
  efficiencyUnit = '個/時',
  options?: { forExport?: boolean },
) {
  return buildDailyTrendChartOption(daily, theme, formatters, efficiencyUnit, options)
}

export function createPersonBarChartOption(
  rows: IpaPersonBarRow[],
  theme: IpaChartTheme,
  formatters: IpaChartFormatters,
  efficiencyUnit = '個/時',
) {
  return buildPersonBarChartOption(rows, theme, formatters, efficiencyUnit)
}

export function createProductBarChartOption(
  rows: IpaProductBarRow[],
  theme: IpaChartTheme,
  formatters: IpaChartFormatters,
  efficiencyUnit = '個/時',
) {
  return buildProductChartOption(rows, theme, formatters, efficiencyUnit)
}

export function createProductRankChartOption(
  rows: IpaRankBarRow[],
  theme: IpaChartTheme,
  formatters: IpaChartFormatters,
  efficiencyUnit = '個/時',
) {
  return buildProductRankChartOption(rows, theme, formatters, efficiencyUnit)
}
