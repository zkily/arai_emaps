import type { Component } from 'vue'

export interface MetricSummaryCard {
  label: string
  value: string
  sub: string
}

export interface MetricAnalysisRow {
  axis: string
  content: string
  source: string
}

export interface ProductionMetricConfig {
  title: string
  description: string
  icon: Component
  gradient: string
  formula: string
  note: string
  summaryCards: MetricSummaryCard[]
  analysisRows: MetricAnalysisRow[]
  implementationMemos: string[]
}
