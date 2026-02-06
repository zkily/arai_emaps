import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import jaJp from 'element-plus/dist/locale/ja.js'
import dayjs from 'dayjs'
import 'dayjs/locale/ja'
import 'dayjs/locale/en'
import 'dayjs/locale/zh-cn'
import 'dayjs/locale/vi'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

import App from './App.vue'
import router from './shared/router'
import { i18n, getLocale } from './i18n'

// 日本ローカル時区 (Asia/Tokyo) をデフォルトに設定
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.tz.setDefault('Asia/Tokyo')
const dayjsLocaleMap: Record<string, string> = { en: 'en', ja: 'ja', zh: 'zh-cn', vi: 'vi' }
dayjs.locale(dayjsLocaleMap[getLocale()] || 'ja')

const app = createApp(App)

// Pinia状態管理
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// Vue Router
app.use(router)

// i18n（语言切换）
app.use(i18n)

// Element Plus（切换语言时在 App.vue 通过 ConfigProvider 更新 locale）
app.use(ElementPlus, {
  locale: jaJp,
})

// Element Plus Icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')

