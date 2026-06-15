/** 実績登録 — 工程別サブページ共通定義 */
export const mesRegistrationProcesses = [
  {
    slug: 'cutting',
    name: '切断工程',
    pageTitle: '切断実績登録',
    menuSuffix: 'CUTTING',
    componentPrefix: 'Cutting',
    icon: 'Scissor',
  },
  {
    slug: 'chamfering',
    name: '面取工程',
    pageTitle: '面取実績登録',
    menuSuffix: 'CHAMFERING',
    componentPrefix: 'Chamfering',
    icon: 'Crop',
  },
  {
    slug: 'forming',
    name: '成型工程',
    pageTitle: '成型実績登録',
    menuSuffix: 'FORMING',
    componentPrefix: 'Forming',
    icon: 'SetUp',
  },
  {
    slug: 'plating',
    name: 'メッキ工程',
    pageTitle: 'メッキ実績登録',
    menuSuffix: 'PLATING',
    componentPrefix: 'Plating',
    icon: 'Brush',
  },
  {
    slug: 'welding',
    name: '溶接工程',
    pageTitle: '溶接実績登録',
    menuSuffix: 'WELDING',
    componentPrefix: 'Welding',
    icon: 'Connection',
  },
  {
    slug: 'inspection',
    name: '検査工程',
    pageTitle: '検査実績登録',
    menuSuffix: 'INSPECTION',
    componentPrefix: 'Inspection',
    icon: 'DocumentChecked',
  },
] as const

export type MesRegistrationProcessSlug = (typeof mesRegistrationProcesses)[number]['slug']
