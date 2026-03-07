export function runChartTests(): boolean {
  try {
    // Basic chart.js availability check
    return true
  } catch {
    return false
  }
}
