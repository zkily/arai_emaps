/// <reference types="vite/client" />

declare module 'element-plus/dist/locale/en.js'
declare module 'element-plus/dist/locale/ja.js'
declare module 'element-plus/dist/locale/zh-cn.js'
declare module 'element-plus/dist/locale/vi.js'

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

