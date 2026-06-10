/** 実績分析 — 工程別サブページ共通定義 */
export const mesAnalysisProcesses = [
  {
    slug: 'cutting',
    name: '切断工程',
    menuSuffix: 'CUTTING',
    componentPrefix: 'Cutting',
    icon: 'Scissor',
  },
  {
    slug: 'chamfering',
    name: '面取工程',
    menuSuffix: 'CHAMFERING',
    componentPrefix: 'Chamfering',
    icon: 'Crop',
  },
  {
    slug: 'forming',
    name: '成型工程',
    menuSuffix: 'FORMING',
    componentPrefix: 'Forming',
    icon: 'SetUp',
  },
  {
    slug: 'plating',
    name: 'メッキ工程',
    menuSuffix: 'PLATING',
    componentPrefix: 'Plating',
    icon: 'Brush',
  },
  {
    slug: 'welding',
    name: '溶接工程',
    menuSuffix: 'WELDING',
    componentPrefix: 'Welding',
    icon: 'Connection',
  },
  {
    slug: 'inspection',
    name: '検査工程',
    menuSuffix: 'INSPECTION',
    componentPrefix: 'Inspection',
    icon: 'DocumentChecked',
  },
] as const

export type MesAnalysisProcessSlug = (typeof mesAnalysisProcesses)[number]['slug']
