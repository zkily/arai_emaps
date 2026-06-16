import type { MonitorProcessKey } from './monitorTypes'

export interface MonitorProcessConfig {
  key: MonitorProcessKey
  slug: string
  componentName: string
  pageTitle: string
  menuCode: string
  menuName: string
  label: string
  icon: string
  color: string
  gradient: string
  headerIconColor: string
}

export const mesMonitoringProcesses: MonitorProcessConfig[] = [
  {
    key: 'inspection',
    slug: 'inspection',
    componentName: 'InspectionMonitor',
    pageTitle: '検査モニタ',
    menuCode: 'MES_MONITOR_INSPECTION',
    menuName: '検査モニタ',
    label: '検査工程',
    icon: '🔍',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #047857 0%, #059669 42%, #10b981 100%)',
    headerIconColor: '#059669',
  },
  {
    key: 'welding',
    slug: 'welding',
    componentName: 'WeldingMonitor',
    pageTitle: '溶接モニタ',
    menuCode: 'MES_MONITOR_WELDING',
    menuName: '溶接モニタ',
    label: '溶接工程',
    icon: '⚡',
    color: '#e6a23c',
    gradient: 'linear-gradient(135deg, #e6a23c 0%, #f0c060 100%)',
    headerIconColor: '#e6a23c',
  },
]

export function monitorProcessByKey(key: MonitorProcessKey): MonitorProcessConfig {
  const found = mesMonitoringProcesses.find((p) => p.key === key)
  if (!found) throw new Error(`Unknown monitor process: ${key}`)
  return found
}

export function monitorProcessBySlug(slug: string): MonitorProcessConfig | undefined {
  return mesMonitoringProcesses.find((p) => p.slug === slug)
}
